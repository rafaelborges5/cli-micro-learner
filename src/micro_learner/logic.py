import asyncio
import random
import time
import click
from datetime import datetime, timezone
from contextlib import contextmanager
from micro_learner.state import (
    LessonArtifact,
    NoteEntry,
    activate_syllabus,
    append_note_entry,
    create_syllabus_record,
    delete_syllabus_record,
    is_syllabus_resumable,
    load_lesson_artifact,
    load_active_syllabus,
    list_syllabus_records,
    load_state,
    mark_syllabus_cache_complete,
    save_lesson_artifacts,
    save_syllabus_record,
)
from micro_learner.ui import (
    build_generation_progress,
    console,
    render_answer,
    render_lesson,
    render_intervention,
    render_progress,
    render_syllabus_browser,
)
from micro_learner.llm import LLMManager


class TerminalIO:
    """Abstraction layer for user-facing IO across CLI and REPL flows."""

    def print(self, renderable):
        console.print(renderable)

    @contextmanager
    def status(self, message: str):
        with console.status(message):
            yield

    async def prompt_select(self, text: str, min_value: int, max_value: int) -> int:
        return click.prompt(text, type=click.IntRange(min_value, max_value))

    async def read_key(self, prompt_text: str) -> str:
        click.echo(click.style(
            f"{prompt_text} (E: Analogy, D: Code, Any other key: Continue)",
            fg="cyan",
        ))
        return await asyncio.to_thread(click.getchar)


DEFAULT_IO = TerminalIO()

def get_random_status():
    """Returns a random encouraging status message."""
    messages = [
        "Synthesizing concepts...",
        "Drafting your micro-lesson...",
        "Consulting the expert curriculum...",
        "Optimizing cognitive load...",
        "Preparing your bite-sized insight...",
    ]
    return f"[info]{random.choice(messages)}[/info]"


def build_note_entry(
    syllabus_id: str,
    lesson_type: str,
    topic: str,
    sub_topic: str,
    step_number: int,
    total_lessons: int,
    content: str,
    answer: str | None = None,
    interventions: list[dict] | None = None,
) -> NoteEntry:
    """Normalizes a completed lesson for markdown export."""
    return NoteEntry(
        syllabus_id=syllabus_id,
        lesson_type=lesson_type,
        topic=topic,
        sub_topic=sub_topic,
        step_number=step_number,
        total_lessons=total_lessons,
        completed_at=datetime.now(timezone.utc).isoformat(),
        content=content,
        answer=answer,
        interventions=interventions or [],
    )


def build_note_entry_from_artifact(
    artifact: LessonArtifact,
    syllabus_id: str,
    topic: str,
    total_lessons: int,
    interventions: list[dict] | None = None,
) -> NoteEntry:
    """Converts a cached lesson artifact to a note export payload."""
    return build_note_entry(
        syllabus_id=syllabus_id,
        lesson_type=artifact.lesson_type,
        topic=topic,
        sub_topic=artifact.sub_topic,
        step_number=artifact.step_number,
        total_lessons=total_lessons,
        content=artifact.content,
        answer=artifact.answer,
        interventions=interventions,
    )


def render_active_syllabus_summary(io: TerminalIO = DEFAULT_IO):
    """Prints the current active syllabus summary."""
    state_data = load_state()
    active_syllabus = load_active_syllabus()

    io.print("[header]Welcome to Micro-Learner CLI![/header]")

    if not state_data.active_syllabus_id or not active_syllabus:
        io.print("[info]No active topic. Use 'micro-learner start <topic>' to begin.[/info]")
        return

    io.print(
        render_progress(
            active_syllabus.current_lesson_index,
            active_syllabus.total_lessons,
            active_syllabus.topic,
        )
    )
    io.print("")

    if (
        active_syllabus.syllabus
        and active_syllabus.current_lesson_index < active_syllabus.total_lessons
    ):
        next_lesson = active_syllabus.syllabus[active_syllabus.current_lesson_index]
        io.print(
            f"[info]Next Up:[/info] Step {active_syllabus.current_lesson_index + 1}: {next_lesson}"
        )
    elif active_syllabus.total_lessons > 0:
        io.print("[success]Congratulations! You've completed this syllabus.[/success]")

def execute_status(io: TerminalIO = DEFAULT_IO):
    """Logic for the status command."""
    render_active_syllabus_summary(io=io)


async def execute_resume(io: TerminalIO = DEFAULT_IO):
    """Logic for the resume command."""
    records = list_syllabus_records()
    active_state = load_state()

    if not records:
        io.print("[info]No saved syllabi available. Use 'micro-learner start <topic>' to begin.[/info]")
        return

    io.print(render_syllabus_browser(records, active_state.active_syllabus_id))

    selection = await io.prompt_select(
        "Select a syllabus number",
        1,
        len(records) + 1,
    )

    if selection == len(records) + 1:
        io.print("[info]Start a new topic with: micro-learner start <topic>[/info]")
        return

    record = records[selection - 1]
    if not is_syllabus_resumable(record):
        io.print("[error]That syllabus cannot be resumed because its cache is incomplete or missing.[/error]")
        return

    activate_syllabus(record.id)
    io.print(f"[success]Resumed topic:[/success] [topic]{record.topic}[/topic]")
    render_active_syllabus_summary(io=io)


async def execute_start(
    topic: str,
    background: bool = False,
    io: TerminalIO = DEFAULT_IO,
) -> tuple[list[str], str] | None:
    """Logic for the start command. 
    If background=True, generates only the first lesson and returns the remainder.
    """
    llm = LLMManager()
    
    with io.status(f"[info]Architecting syllabus for '{topic}'...[/info]"):
        syllabus = await llm.generate_syllabus(topic)
    
    if not syllabus:
        io.print("[error]Failed to generate syllabus. Please try again.[/error]")
        return None

    record = create_syllabus_record(topic, syllabus)
    
    try:
        if background:
            # Immediate setup: only first lesson
            with io.status("[info]Preparing your first lesson...[/info]"):
                first_lesson_artifacts = await llm.generate_cached_lessons(
                    topic, syllabus[:1], start_step=1
                )
            if not first_lesson_artifacts:
                raise ValueError("Failed to generate the first lesson.")
            
            save_lesson_artifacts(record.id, first_lesson_artifacts)
            activate_syllabus(record.id)
            
            io.print(f"[success]Topic initialized:[/success] [topic]{topic}[/topic]")
            io.print(f"[info]Step 1: {syllabus[0]}[/info]")
            io.print("[info]Rest of the lessons are caching in the background...[/info]")
            return (syllabus[1:], record.id)
        else:
            # Blocking setup: all lessons
            with build_generation_progress() as progress:
                task_id = progress.add_task(
                    "cache-generation",
                    total=len(syllabus),
                    completed=0,
                    label="Generating cached lessons",
                    sub_topic="-",
                )

                def on_generation_progress(completed_steps: int, total_steps: int, sub_topic: str, lesson_type: str):
                    progress.update(
                        task_id,
                        total=total_steps,
                        completed=completed_steps,
                        label=f"Generating {lesson_type}",
                        sub_topic=f"{completed_steps + (0 if completed_steps == total_steps else 1)}/{total_steps}: {sub_topic}",
                    )

                lesson_artifacts = await llm.generate_cached_lessons(
                    topic,
                    syllabus,
                    progress_callback=on_generation_progress,
                )

            if len(lesson_artifacts) != len(syllabus):
                raise ValueError("Cached lesson generation returned an incomplete artifact set.")

            save_lesson_artifacts(record.id, lesson_artifacts)
            mark_syllabus_cache_complete(record)
            activate_syllabus(record.id)
            
            io.print(f"[success]Successfully initialized topic:[/success] [topic]{topic}[/topic]")
            io.print("[info]Syllabus Overview:[/info]")
            for i, step in enumerate(syllabus[:5], 1):
                io.print(f"  {i}. {step}")
            if len(syllabus) > 5:
                io.print(f"  ... and {len(syllabus) - 5} more steps.")
            io.print("\n[info]Run 'micro-learner next' to start your first lesson![/info]")
            return None

    except (OSError, ValueError) as exc:
        delete_syllabus_record(record.id)
        io.print(f"[error]Failed to initialize cached lessons: {exc}[/error]")
        return None


async def interactive_wait(
    topic: str,
    sub_topic: str,
    content: str,
    prompt_text: str,
    io: TerminalIO = DEFAULT_IO,
) -> list[dict]:
    llm = LLMManager()
    interventions = []
    while True:
        char = await io.read_key(prompt_text)
        
        if not char:
            break
            
        if char.lower() == 'e':
            with io.status("[warning]Thinking of an analogy...[/warning]"):
                analogy = await llm.generate_analogy(topic, sub_topic, content)
            io.print(render_intervention("Simpler Analogy", analogy, "warning"))
            interventions.append({"type": "analogy", "content": analogy})
        elif char.lower() == 'd':
            with io.status("[info]Writing code example...[/info]"):
                code = await llm.generate_code_example(topic, sub_topic, content)
            io.print(render_intervention("Code Example", code, "info"))
            interventions.append({"type": "code", "content": code})
        else:
            break
    return interventions


async def execute_next(io: TerminalIO = DEFAULT_IO):
    """Logic for the next command."""
    state_data = load_state()
    active_syllabus = load_active_syllabus()
    
    if not state_data.active_syllabus_id or not active_syllabus or not active_syllabus.syllabus:
        io.print("[warning]No active topic. Use 'micro-learner start <topic>' first.[/warning]")
        return

    if active_syllabus.current_lesson_index >= active_syllabus.total_lessons:
        io.print("[success]You have already completed the syllabus for this topic![/success]")
        io.print("[info]Use 'micro-learner start <new topic>' to learn something else.[/info]")
        return

    step_number = active_syllabus.current_lesson_index + 1
    artifact = load_lesson_artifact(active_syllabus.id, step_number)
    if not artifact:
        io.print("[error]Failed to load the cached lesson artifact for this step.[/error]")
        return

    progress_str = (
        f"Step {step_number} of {active_syllabus.total_lessons}"
    )
    if artifact.lesson_type == "quiz":
        io.print(render_lesson(f"Quiz: {artifact.sub_topic}", artifact.content, subtitle=progress_str))
        io.print("\n" + "─" * console.width)

        interventions = await interactive_wait(
            active_syllabus.topic,
            artifact.sub_topic,
            artifact.content,
            "Think about your answer, then press any key to reveal...",
            io=io,
        )

        with io.status("[success]Revealing answer...[/success]"):
            await asyncio.sleep(1)

        io.print(render_answer((artifact.answer or "No answer key provided.").strip()))
        io.print("\n" + "─" * console.width)
        interventions.extend(
            await interactive_wait(
                active_syllabus.topic,
                artifact.sub_topic,
                artifact.answer or "",
                "Press any key to complete this lesson...",
                io=io,
            )
        )
    else:
        io.print(render_lesson(artifact.sub_topic, artifact.content, subtitle=progress_str))
        io.print("\n" + "─" * console.width)
        interventions = await interactive_wait(
            active_syllabus.topic,
            artifact.sub_topic,
            artifact.content,
            "Press any key to complete this lesson...",
            io=io,
        )

    note_entry = build_note_entry_from_artifact(
        artifact=artifact,
        syllabus_id=active_syllabus.id,
        topic=active_syllabus.topic,
        total_lessons=active_syllabus.total_lessons,
        interventions=interventions,
    )

    try:
        append_note_entry(note_entry)
    except OSError as exc:
        io.print(f"[error]Failed to export lesson notes: {exc}[/error]")
        return

    # Common progress update logic
    active_syllabus.current_lesson_index += 1
    active_syllabus.updated_at = datetime.now(timezone.utc).isoformat()
    save_syllabus_record(active_syllabus)
    io.print(f"[success]Lesson complete![/success]")
    io.print(
        render_progress(
            active_syllabus.current_lesson_index,
            active_syllabus.total_lessons,
            active_syllabus.topic,
        )
    )
