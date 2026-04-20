import asyncio
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.formatted_text import HTML, ANSI
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from micro_learner.ui import console, render_toolbar
from micro_learner.state import load_active_syllabus, mark_syllabus_cache_complete, save_lesson_artifacts, load_syllabus_record
from micro_learner.llm import LLMManager
from micro_learner.logic import (
    execute_status,
    execute_resume,
    execute_start,
    execute_next,
)

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
        self.prefetch_status = None
        self.just_finished_lesson = False

    async def cmd_help(self, *args):
        """Displays available commands with detailed descriptions."""
        console.print("[header]Interactive Shell Help[/header]")
        console.print("\n[info]Learn and track your progress without leaving the terminal.[/info]")
        
        table_data = [
            ("/start <topic>", "Generate a new 15-step syllabus and begin learning."),
            ("/next", "Fetch your next bite-sized lesson or quiz."),
            ("/status", "Show your current progress bar and active topic."),
            ("/resume", "Browse your saved syllabi and switch active topics."),
            ("/help", "Show this help directory."),
            ("/quit", "Cleanly exit the learning session."),
        ]
        
        for cmd, desc in table_data:
            console.print(f"  [topic]{cmd:<16}[/topic] [info]{desc}[/info]")
        
        console.print("\n[header]💡 Pro-Tip:[/header] Use [topic]Tab[/topic] to auto-complete commands and [topic]Up Arrow[/topic] for history.")


    async def cmd_quit(self, *args):
        """Exits the REPL shell."""
        console.print("[info]Goodbye! Keep learning.[/info]")
        sys.exit(0)

    async def cmd_status(self, *args):
        """Shows the current status."""
        execute_status()

    async def cmd_resume(self, *args):
        """Resumes a syllabus."""
        await execute_resume()

    async def cmd_start(self, *args):
        """Starts a new topic."""
        if not args:
            console.print("[error]Usage: /start <topic>[/error]")
            return
        
        if self.prefetch_task and not self.prefetch_task.done():
            self.prefetch_task.cancel()

        topic = " ".join(args)
        result = await execute_start(topic, background=True)
        if result:
            remainder, record_id = result
            self.prefetch_status = f"1/{len(remainder)+1}"
            self.prefetch_task = asyncio.create_task(
                self._background_prefetch(topic, remainder, record_id)
            )

    async def _background_prefetch(self, topic, remainder, record_id):
        """Task to generate remaining lessons in the background."""
        try:
            llm = LLMManager()
            total = len(remainder) + 1
            
            def on_progress(idx, total_steps, sub_topic, lesson_type):
                self.prefetch_status = f"{idx+2}/{total}"

            artifacts = await llm.generate_cached_lessons(
                topic, remainder, start_step=2, progress_callback=on_progress
            )
            
            save_lesson_artifacts(record_id, artifacts)
            record = load_syllabus_record(record_id)
            if record:
                mark_syllabus_cache_complete(record)
            self.prefetch_status = "complete"
        except asyncio.CancelledError:
            pass
        except Exception:
            self.prefetch_status = "failed"

    async def cmd_next(self, *args):
        """Fetches the next lesson."""
        await execute_next()
        self.just_finished_lesson = True

    def _get_toolbar(self):
        """Generates the content for the bottom toolbar."""
        active = load_active_syllabus()
        if not active:
            return ANSI("\x1b[36m [No active topic] Type /start to begin\x1b[0m")
        
        toolbar_ansi = render_toolbar(
            active.current_lesson_index,
            active.total_lessons,
            active.topic
        )

        if self.prefetch_task and not self.prefetch_task.done():
            status = self.prefetch_status or "..."
            toolbar_ansi += f" \x1b[33m[Caching {status}]\x1b[0m"
        elif self.prefetch_status == "failed":
            toolbar_ansi += " \x1b[31m[Cache Error]\x1b[0m"
        
        return ANSI(toolbar_ansi)

    async def run(self):
        """Main REPL loop."""
        console.print("[header]Welcome to Micro-Learner Interactive Shell![/header]")
        console.print("[info]Type [topic]/help[/topic] to see available commands or [topic]/quit[/topic] to exit.[/info]")
        
        while True:
            try:
                with patch_stdout():
                    user_input = await self.session.prompt_async(
                        HTML('<style color="cyan">micro-learner</style> <style color="white">></style> '),
                        bottom_toolbar=self._get_toolbar
                    )
                
                user_input = user_input.strip()
                if not user_input:
                    continue

                if user_input.startswith("/"):
                    self.just_finished_lesson = False
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
            except Exception as e:
                console.print(f"[error]An error occurred: {e}[/error]")

async def start_repl():
    shell = REPLShell()
    await shell.run()
