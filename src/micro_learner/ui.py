import time
from io import StringIO
from rich.console import Console, Group
from rich.theme import Theme
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.progress_bar import ProgressBar
from rich.text import Text
from rich.align import Align

# Define a custom theme for the application
micro_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "header": "bold magenta",
    "topic": "bold blue",
    "quiz_answer": "bold white on green",
})

console = Console(theme=micro_theme)

def render_lesson(title: str, content: str, subtitle: str = None) -> Panel:
    """Wraps lesson content in a stylized Rich Panel."""
    md = Markdown(content)
    return Panel(
        md,
        title=f"[header]{title}[/header]",
        subtitle=f"[info]{subtitle}[/info]" if subtitle else None,
        border_style="topic",
        padding=(1, 2),
        expand=True
    )

def render_answer(answer_text: str) -> Panel:
    """Creates a stylized panel for the revealed answer."""
    content = Text.assemble(
        ("💡 Key Insight & Answer:\n\n", "header"),
        (answer_text, "success")
    )
    return Panel(
        Align.center(content),
        border_style="success",
        padding=(1, 2),
        title="[success]✔ Correct Answer Revealed[/success]",
        expand=True
    )

def render_intervention(title: str, content: str, style: str) -> Panel:
    """Wraps an intervention (analogy or code) in a stylized Rich Panel."""
    md = Markdown(content)
    return Panel(
        md,
        title=f"[{style}]{title}[/{style}]",
        border_style=style,
        padding=(1, 2),
        expand=True
    )

def render_progress(current: int, total: int, topic_name: str) -> Group:
    """Creates a stylized progress bar and status text."""
    percentage = (current / total) * 100 if total > 0 else 0
    
    pb = ProgressBar(
        total=total,
        completed=current,
        width=40,
        style="info",
        complete_style="success",
        finished_style="success"
    )
    
    status_text = Text.assemble(
        (f"{percentage:>3.0f}%", "success"),
        (" | ", "info"),
        ("Topic: ", "info"),
        (topic_name, "topic"),
        (" | ", "info"),
        ("Lesson: ", "info"),
        (f"{current}/{total}", "success")
    )
    
    return Group(pb, status_text)


def render_syllabus_browser(records, active_syllabus_id: str | None) -> Table:
    """Renders a numbered syllabus browser for resume selection."""
    table = Table(title="[header]Resume A Syllabus[/header]", expand=True)
    table.add_column("#", style="info", no_wrap=True)
    table.add_column("Topic", style="topic")
    table.add_column("Progress", style="success", no_wrap=True)
    table.add_column("Complete", style="info", no_wrap=True)
    table.add_column("Status", style="warning", no_wrap=True)

    for index, record in enumerate(records, start=1):
        completion = f"{(record.current_lesson_index / record.total_lessons * 100) if record.total_lessons else 0:.0f}%"
        status = []
        if record.id == active_syllabus_id:
            status.append("Active")
        if record.current_lesson_index >= record.total_lessons and record.total_lessons > 0:
            status.append("Completed")
        table.add_row(
            str(index),
            record.topic,
            f"{record.current_lesson_index}/{record.total_lessons}",
            completion,
            ", ".join(status) if status else "Available",
        )

    table.add_row(str(len(records) + 1), "Start a new topic", "-", "-", "Action")
    return table


def build_generation_progress() -> Progress:
    """Creates a progress display for long-running cache generation."""
    return Progress(
        TextColumn("[info]{task.fields[label]}[/info]"),
        BarColumn(bar_width=32),
        TaskProgressColumn(),
        TextColumn("[topic]{task.fields[sub_topic]}[/topic]"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    )

def render_to_ansi(renderable) -> str:
    """Renders a Rich renderable to a string containing ANSI codes."""
    with StringIO() as buf:
        ansi_console = Console(file=buf, force_terminal=True, theme=micro_theme, width=console.width)
        ansi_console.print(renderable, end="")
        return buf.getvalue()


def render_to_text(renderable, width: int | None = None) -> str:
    """Renders a Rich renderable to plain terminal-safe text without ANSI codes."""
    with StringIO() as buf:
        text_console = Console(
            file=buf,
            force_terminal=False,
            color_system=None,
            theme=micro_theme,
            width=width or console.width,
        )
        text_console.print(renderable, end="")
        return buf.getvalue()

def render_toolbar(
    current: int,
    total: int,
    topic_name: str,
    *,
    suffix: str = "",
    suffix_style: str = "warning",
    max_width: int | None = None,
) -> str:
    """Renders a single-line version of the progress bar for the REPL toolbar."""
    percentage = (current / total) * 100 if total > 0 else 0

    bar_width = 20
    filled = 0 if total <= 0 else min(bar_width, round((current / total) * bar_width))
    empty = bar_width - filled
    progress_bar = "█" * filled + "░" * empty

    toolbar_text = Text()
    toolbar_text.append(f" {percentage:>3.0f}% ", style="success")
    toolbar_text.append(progress_bar, style="info")
    toolbar_text.append(" [", style="info")
    toolbar_text.append(f"{current}/{total}", style="success")
    toolbar_text.append("] ", style="info")
    toolbar_text.append(topic_name, style="topic")

    if suffix:
        toolbar_text.append(" ", style="info")
        toolbar_text.append(suffix, style=suffix_style)

    toolbar_text.truncate(max_width or console.width, overflow="ellipsis")

    return render_to_ansi(toolbar_text)
