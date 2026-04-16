import time
from rich.console import Console, Group
from rich.theme import Theme
from rich.panel import Panel
from rich.markdown import Markdown
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
