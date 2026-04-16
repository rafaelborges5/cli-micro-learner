import click
import asyncio
import random
import time
from datetime import datetime, timezone
from micro_learner.state import (
    LessonArtifact,
    NoteEntry,
    activate_syllabus,
    append_note_entry,
    bootstrap,
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
    render_progress,
    render_syllabus_browser,
)
from micro_learner.llm import LLMManager

def coro(f):
    """Decorator to allow click to run async functions."""
    import functools
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

@click.group()
def cli():
    """Micro-Learner CLI: Turn idle time into learning."""
    bootstrap()

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
    )


def build_note_entry_from_artifact(
    artifact: LessonArtifact,
    syllabus_id: str,
    topic: str,
    total_lessons: int,
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
    )


def render_active_syllabus_summary():
    """Prints the current active syllabus summary."""
    state = load_state()
    active_syllabus = load_active_syllabus()

    console.print("[header]Welcome to Micro-Learner CLI![/header]")

    if not state.active_syllabus_id or not active_syllabus:
        console.print("[info]No active topic. Use 'micro-learner start <topic>' to begin.[/info]")
        return

    console.print(
        render_progress(
            active_syllabus.current_lesson_index,
            active_syllabus.total_lessons,
            active_syllabus.topic,
        )
    )
    console.print()

    if (
        active_syllabus.syllabus
        and active_syllabus.current_lesson_index < active_syllabus.total_lessons
    ):
        next_lesson = active_syllabus.syllabus[active_syllabus.current_lesson_index]
        console.print(
            f"[info]Next Up:[/info] Step {active_syllabus.current_lesson_index + 1}: {next_lesson}"
        )
    elif active_syllabus.total_lessons > 0:
        console.print("[success]Congratulations! You've completed this syllabus.[/success]")

@cli.command()
def status():
    """Check the current learning status."""
    render_active_syllabus_summary()


@cli.command()
def resume():
    """Browse and activate a cached syllabus."""
    records = list_syllabus_records()
    active_state = load_state()

    if not records:
        console.print("[info]No saved syllabi available. Use 'micro-learner start <topic>' to begin.[/info]")
        return

    console.print(render_syllabus_browser(records, active_state.active_syllabus_id))

    selection = click.prompt(
        "Select a syllabus number",
        type=click.IntRange(1, len(records) + 1),
    )

    if selection == len(records) + 1:
        console.print("[info]Start a new topic with: micro-learner start <topic>[/info]")
        return

    record = records[selection - 1]
    if not is_syllabus_resumable(record):
        console.print("[error]That syllabus cannot be resumed because its cache is incomplete or missing.[/error]")
        return

    activate_syllabus(record.id)
    console.print(f"[success]Resumed topic:[/success] [topic]{record.topic}[/topic]")
    render_active_syllabus_summary()

@cli.command()
@click.argument('topic')
@coro
async def start(topic):
    """Start a new learning topic by generating a syllabus."""
    llm = LLMManager()
    
    with console.status(f"[info]Architecting syllabus for '{topic}'...[/info]"):
        syllabus = await llm.generate_syllabus(topic)
    
    if syllabus:
        record = create_syllabus_record(topic, syllabus)
        try:
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
        except (OSError, ValueError) as exc:
            delete_syllabus_record(record.id)
            console.print(f"[error]Failed to initialize cached lessons: {exc}[/error]")
            return

        console.print(f"[success]Successfully initialized topic:[/success] [topic]{topic}[/topic]")
        console.print("[info]Syllabus Overview:[/info]")
        for i, step in enumerate(syllabus[:5], 1):
            console.print(f"  {i}. {step}")
        if len(syllabus) > 5:
            console.print(f"  ... and {len(syllabus) - 5} more steps.")
        console.print("\n[info]Run 'micro-learner next' to start your first lesson![/info]")
    else:
        console.print("[error]Failed to generate syllabus. Please try again.[/error]")

@cli.command()
@coro
async def next():
    """Fetch and display the next lesson in the current syllabus."""
    state = load_state()
    active_syllabus = load_active_syllabus()
    
    if not state.active_syllabus_id or not active_syllabus or not active_syllabus.syllabus:
        console.print("[warning]No active topic. Use 'micro-learner start <topic>' first.[/warning]")
        return

    if active_syllabus.current_lesson_index >= active_syllabus.total_lessons:
        console.print("[success]You have already completed the syllabus for this topic![/success]")
        console.print("[info]Use 'micro-learner start <new topic>' to learn something else.[/info]")
        return

    step_number = active_syllabus.current_lesson_index + 1
    artifact = load_lesson_artifact(active_syllabus.id, step_number)
    if not artifact:
        console.print("[error]Failed to load the cached lesson artifact for this step.[/error]")
        return

    progress_str = (
        f"Step {step_number} of {active_syllabus.total_lessons}"
    )
    note_entry = build_note_entry_from_artifact(
        artifact=artifact,
        syllabus_id=active_syllabus.id,
        topic=active_syllabus.topic,
        total_lessons=active_syllabus.total_lessons,
    )

    if artifact.lesson_type == "quiz":
        console.print(render_lesson(f"Quiz: {artifact.sub_topic}", artifact.content, subtitle=progress_str))
        console.print("\n" + "─" * console.width)

        click.pause(info="Think about your answer, then press any key to reveal...")

        with console.status("[success]Revealing answer...[/success]"):
            time.sleep(1)

        console.print(render_answer((artifact.answer or "No answer key provided.").strip()))
        console.print("\n" + "─" * console.width)
        click.pause(info="Press any key to complete this lesson...")
    else:
        console.print(render_lesson(artifact.sub_topic, artifact.content, subtitle=progress_str))
        console.print("\n" + "─" * console.width)
        click.pause(info="Press any key to complete this lesson...")

    try:
        append_note_entry(note_entry)
    except OSError as exc:
        console.print(f"[error]Failed to export lesson notes: {exc}[/error]")
        return

    # Common progress update logic
    active_syllabus.current_lesson_index += 1
    active_syllabus.updated_at = datetime.now(timezone.utc).isoformat()
    save_syllabus_record(active_syllabus)
    console.print(f"[success]Lesson complete![/success]")
    console.print(
        render_progress(
            active_syllabus.current_lesson_index,
            active_syllabus.total_lessons,
            active_syllabus.topic,
        )
    )

def main():
    cli()

if __name__ == "__main__":
    main()
