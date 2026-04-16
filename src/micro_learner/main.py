import click
import asyncio
import random
import time
from rich.markdown import Markdown
from micro_learner.state import bootstrap, load_state, save_state, initialize_topic
from micro_learner.ui import console, render_lesson, render_progress, render_answer
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

@cli.command()
def status():
    """Check the current learning status."""
    state = load_state()
    
    console.print("[header]Welcome to Micro-Learner CLI![/header]")
    
    if not state.active_topic:
        console.print("[info]No active topic. Use 'micro-learner start <topic>' to begin.[/info]")
    else:
        console.print(render_progress(state.current_lesson_index, state.total_lessons, state.active_topic))
        console.print()
        
        if state.syllabus and state.current_lesson_index < state.total_lessons:
            next_lesson = state.syllabus[state.current_lesson_index]
            console.print(f"[info]Next Up:[/info] Step {state.current_lesson_index + 1}: {next_lesson}")
        elif state.total_lessons > 0:
            console.print("[success]Congratulations! You've completed this syllabus.[/success]")

@cli.command()
@click.argument('topic')
@coro
async def start(topic):
    """Start a new learning topic by generating a syllabus."""
    llm = LLMManager()
    
    with console.status(f"[info]Architecting syllabus for '{topic}'...[/info]"):
        syllabus = await llm.generate_syllabus(topic)
    
    if syllabus:
        initialize_topic(topic, syllabus)
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
    
    if not state.active_topic or not state.syllabus:
        console.print("[warning]No active topic. Use 'micro-learner start <topic>' first.[/warning]")
        return

    if state.current_lesson_index >= state.total_lessons:
        console.print("[success]You have already completed the syllabus for this topic![/success]")
        console.print("[info]Use 'micro-learner start <new topic>' to learn something else.[/info]")
        return

    sub_topic = state.syllabus[state.current_lesson_index]
    llm = LLMManager()
    
    # 30% chance for a quiz
    is_quiz = random.random() < 0.3
    progress_str = f"Step {state.current_lesson_index + 1} of {state.total_lessons}"

    if is_quiz:
        with console.status(get_random_status()):
            content = await llm.generate_quiz(state.active_topic, sub_topic)
        
        if content:
            if "ANSWER:" in content:
                question_part, answer_part = content.split("ANSWER:", 1)
            else:
                question_part, answer_part = content, "No answer key provided."

            console.print(render_lesson(f"Quiz: {sub_topic}", question_part.strip(), subtitle=progress_str))
            console.print("\n" + "─" * console.width)
            
            click.pause(info="Think about your answer, then press any key to reveal...")
            
            # Subtle delay for effect
            with console.status("[success]Revealing answer...[/success]"):
                time.sleep(1)
            
            console.print(render_answer(answer_part.strip()))
            console.print("\n" + "─" * console.width)
            click.pause(info="Press any key to complete this lesson...")
        else:
            is_quiz = False

    if not is_quiz:
        with console.status(get_random_status()):
            lesson_text = await llm.generate_lesson(state.active_topic, sub_topic)
        
        if lesson_text:
            console.print(render_lesson(sub_topic, lesson_text, subtitle=progress_str))
            console.print("\n" + "─" * console.width)
            click.pause(info="Press any key to complete this lesson...")
        else:
            console.print("[error]Failed to fetch the lesson. Please check your connection and try again.[/error]")
            return

    # Common progress update logic
    state.current_lesson_index += 1
    save_state(state)
    console.print(f"[success]Lesson complete![/success]")
    console.print(render_progress(state.current_lesson_index, state.total_lessons, state.active_topic))

def main():
    cli()

if __name__ == "__main__":
    main()
