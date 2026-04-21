import asyncio
import sys
from dataclasses import dataclass
from typing import Literal

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML, ANSI
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.patch_stdout import patch_stdout

from micro_learner.llm import LLMManager
from micro_learner.logic import TerminalIO, execute_next, execute_resume, execute_start, execute_status
from micro_learner.state import (
    load_lesson_artifact,
    load_active_syllabus,
    load_syllabus_record,
    mark_syllabus_cache_complete,
    save_lesson_artifact,
)
from micro_learner.ui import console, render_progress, render_toolbar


class REPLIO(TerminalIO):
    """REPL IO uses the standard terminal output path."""


@dataclass
class ActiveTopicView:
    topic: str
    current_lesson_index: int
    total_lessons: int
    syllabus_id: str


@dataclass
class PrefetchViewState:
    status: Literal["idle", "warming", "complete", "failed"] = "idle"
    progress_label: str = ""


@dataclass
class REPLSessionState:
    active_topic: ActiveTopicView | None = None
    prefetch: PrefetchViewState = None
    show_context_header: bool = True

    def __post_init__(self):
        if self.prefetch is None:
            self.prefetch = PrefetchViewState()


class REPLShell:
    def __init__(self):
        self.commands = {
            "/help": self.cmd_help,
            "/quit": self.cmd_quit,
            "/exit": self.cmd_quit,
            "/status": self.cmd_status,
            "/resume": self.cmd_resume,
            "/start": self.cmd_start,
            "/next": self.cmd_next,
        }
        self.completer = WordCompleter(list(self.commands.keys()), ignore_case=True)
        self.history = InMemoryHistory()
        self.session = PromptSession(completer=self.completer, history=self.history)
        self.prefetch_task = None
        self.state = REPLSessionState()
        self.io = REPLIO()
        self._refresh_view_state()

    def _refresh_view_state(self):
        """Refresh the derived REPL view state from persisted data."""
        active = load_active_syllabus()
        if not active:
            self.state.active_topic = None
            return

        self.state.active_topic = ActiveTopicView(
            topic=active.topic,
            current_lesson_index=active.current_lesson_index,
            total_lessons=active.total_lessons,
            syllabus_id=active.id,
        )

    def _suppress_next_context_header(self):
        """Skip the extra context header after commands that already rendered output."""
        self.state.show_context_header = False

    def _consume_context_header_flag(self) -> bool:
        """Return whether to show the context header for this prompt cycle."""
        should_show = self.state.show_context_header
        self.state.show_context_header = True
        return should_show

    def _mark_prefetch_started(self, initial_progress: str):
        self.state.prefetch = PrefetchViewState(status="warming", progress_label=initial_progress)

    def _mark_prefetch_progress(self, progress_label: str):
        self.state.prefetch.status = "warming"
        self.state.prefetch.progress_label = progress_label

    def _mark_prefetch_complete(self):
        self.state.prefetch.status = "complete"
        self.state.prefetch.progress_label = ""

    def _mark_prefetch_failed(self):
        self.state.prefetch.status = "failed"
        self.state.prefetch.progress_label = ""

    def _reset_prefetch_view(self):
        self.state.prefetch = PrefetchViewState()

    def _toolbar_suffix(self) -> tuple[str, str]:
        """Build toolbar suffix text from the current view state."""
        if self.state.prefetch.status == "warming":
            status = self.state.prefetch.progress_label or "..."
            return f"[Caching {status}]", "warning"
        if self.state.prefetch.status == "complete":
            return "[Cache Ready]", "success"
        if self.state.prefetch.status == "failed":
            return "[Cache Error]", "error"
        return "", "warning"

    async def cmd_help(self, *args):
        """Displays available commands with detailed descriptions."""
        console.print("[header]Interactive Shell Help[/header]")
        console.print("\n[info]Learn and track your progress without leaving the terminal.[/info]")

        table_data = [
            ("/start <topic>", "Generate a new syllabus and begin learning."),
            ("/next", "Fetch your next bite-sized lesson or quiz."),
            ("/status", "Show your current progress and active topic."),
            ("/resume", "Browse your saved syllabi and switch active topics."),
            ("/help", "Show this help directory."),
            ("/quit", "Cleanly exit the learning session."),
        ]

        for cmd, desc in table_data:
            console.print(f"  [topic]{cmd:<16}[/topic] [info]{desc}[/info]")

    async def cmd_quit(self, *args):
        """Exits the REPL shell."""
        console.print("[info]Goodbye! Keep learning.[/info]")
        sys.exit(0)

    async def cmd_status(self, *args):
        """Shows the current status."""
        execute_status(io=self.io)
        self._refresh_view_state()
        self._suppress_next_context_header()

    async def cmd_resume(self, *args):
        """Resumes a syllabus."""
        await execute_resume(io=self.io)
        self._refresh_view_state()
        self._suppress_next_context_header()

    async def cmd_start(self, *args):
        """Starts a new topic."""
        if not args:
            console.print("[error]Usage: /start <topic>[/error]")
            return

        if self.prefetch_task and not self.prefetch_task.done():
            self.prefetch_task.cancel()
        self._reset_prefetch_view()

        topic = " ".join(args)
        result = await execute_start(topic, background=True, io=self.io)
        self._refresh_view_state()
        if result:
            remainder, record_id = result
            self._mark_prefetch_started(f"1/{len(remainder)+1}")
            self.prefetch_task = asyncio.create_task(
                self._background_prefetch(topic, remainder, record_id)
            )
        self._suppress_next_context_header()

    async def _background_prefetch(self, topic, remainder, record_id):
        """Task to generate remaining lessons in the background."""
        try:
            llm = LLMManager()
            total = len(remainder) + 1

            def on_progress(idx, total_steps, sub_topic, lesson_type):
                self._mark_prefetch_progress(f"{idx + 2}/{total}")

            def on_artifact(artifact):
                save_lesson_artifact(record_id, artifact)

            await llm.generate_cached_lessons(
                topic,
                remainder,
                start_step=2,
                progress_callback=on_progress,
                artifact_callback=on_artifact,
            )

            record = load_syllabus_record(record_id)
            if record:
                mark_syllabus_cache_complete(record)
            self._refresh_view_state()
            self._mark_prefetch_complete()
            console.print("[success]Background cache warmup complete.[/success]")
        except asyncio.CancelledError:
            pass
        except Exception:
            self._mark_prefetch_failed()
            console.print("[error]Background cache warmup failed.[/error]")

    async def cmd_next(self, *args):
        """Fetches the next lesson."""
        self._refresh_view_state()
        active = self.state.active_topic
        if active and active.current_lesson_index < active.total_lessons:
            step_number = active.current_lesson_index + 1
            artifact = load_lesson_artifact(active.syllabus_id, step_number)
            if not artifact and self.prefetch_task and not self.prefetch_task.done():
                for _ in range(20):
                    await asyncio.sleep(0.1)
                    artifact = load_lesson_artifact(active.syllabus_id, step_number)
                    if artifact:
                        break
                if not artifact:
                    console.print("[warning]Your next lesson is still being cached. Try again in a moment.[/warning]")
                    self._suppress_next_context_header()
                    return

        await execute_next(io=self.io)
        self._refresh_view_state()
        self._suppress_next_context_header()

    def _get_toolbar(self):
        """Generates the content for the bottom toolbar."""
        self._refresh_view_state()
        active = self.state.active_topic
        if not active:
            return ANSI("\x1b[36m [No active topic] Type /start to begin\x1b[0m")

        suffix, suffix_style = self._toolbar_suffix()

        toolbar_ansi = render_toolbar(
            active.current_lesson_index,
            active.total_lessons,
            active.topic,
            suffix=suffix,
            suffix_style=suffix_style,
        )

        return ANSI(toolbar_ansi)

    def _print_context_header(self):
        """Print a compact context snapshot above the next prompt."""
        self._refresh_view_state()
        active = self.state.active_topic
        if not active:
            console.print("[info]No active topic. Use /start to begin.[/info]")
            return

        console.print(
            render_progress(
                active.current_lesson_index,
                active.total_lessons,
                active.topic,
            )
        )
        if self.state.prefetch.status == "warming":
            console.print(
                f"[warning]Caching in background:[/warning] [info]{self.state.prefetch.progress_label or '...'}[/info]"
            )

    async def run(self):
        """Main REPL loop."""
        console.print("[header]Welcome to Micro-Learner Interactive Shell![/header]")
        console.print("[info]Type [topic]/help[/topic] to see available commands or [topic]/quit[/topic] to exit.[/info]")

        while True:
            try:
                if self._consume_context_header_flag():
                    self._print_context_header()
                with patch_stdout():
                    user_input = await self.session.prompt_async(
                        HTML('<style color="cyan">micro-learner</style> <style color="white">></style> '),
                        bottom_toolbar=self._get_toolbar,
                    )
                user_input = user_input.strip()
                if not user_input:
                    continue

                if user_input.startswith("/"):
                    parts = user_input.split()
                    cmd = parts[0].lower()
                    args = parts[1:]

                    if cmd in self.commands:
                        await self.commands[cmd](*args)
                    else:
                        console.print(f"[error]Unknown command: {cmd}. Type /help for assistance.[/error]")
                else:
                    console.print("[warning]Please use slash commands (e.g., /next). Type /help for a list of commands.[/warning]")

            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception as exc:
                console.print(f"[error]An error occurred: {exc}[/error]")


async def start_repl():
    shell = REPLShell()
    await shell.run()
