from io import StringIO
from dataclasses import dataclass

from rich.console import Console, Group
from rich.theme import Theme
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.progress_bar import ProgressBar
from rich.text import Text
from rich.align import Align
from prompt_toolkit.styles import Style


@dataclass(frozen=True)
class UITheme:
    name: str
    rich_styles: dict[str, str]
    prompt_toolkit_styles: dict[str, str]
    prompt_label_color: str
    prompt_symbol_color: str
    lesson_panel_style: str
    answer_panel_style: str
    intervention_panel_style: dict[str, str]
    progress_bar_width: int
    toolbar_fill_char: str
    toolbar_empty_char: str
    toolbar_background_style: str
    toolbar_box_style: str
    toolbar_topic_style: str
    toolbar_suffix_styles: dict[str, str]


THEMES: dict[str, UITheme] = {
    "Modern": UITheme(
        name="Modern",
        rich_styles={
            "info": "cyan",
            "warning": "bold #f59e0b",
            "error": "bold #fb7185",
            "success": "bold #34d399",
            "header": "bold #f472b6",
            "topic": "bold #60a5fa",
            "quiz_answer": "bold #ecfeff on #0f766e",
            "panel_surface": "#dbeafe on #0f172a",
            "answer_surface": "#ecfeff on #064e3b",
            "toolbar_back": "#e0f2fe on #0f172a",
            "toolbar_box": "#7dd3fc on #0f172a",
            "toolbar_topic": "bold #bfdbfe on #0f172a",
            "toolbar_suffix_success": "bold #6ee7b7 on #0f172a",
            "toolbar_suffix_warning": "bold #fcd34d on #0f172a",
            "toolbar_suffix_error": "bold #fda4af on #0f172a",
            "toolbar_suffix_info": "bold #a5f3fc on #0f172a",
        },
        prompt_toolkit_styles={
            "dialog": "bg:#111827 #d1d5db",
            "dialog.body": "bg:#111827 #d1d5db",
            "dialog frame.label": "bold #f472b6",
            "dialog shadow": "bg:#030712",
            "label": "#93c5fd",
            "radio": "#93c5fd",
            "radio-selected": "bold #34d399",
            "radio-checked": "bold #34d399",
            "radio-checked-selected": "bold #34d399",
            "textarea": "bg:#0f172a #e5e7eb",
            "search": "bg:#0f172a #e5e7eb",
            "search-field": "bg:#0f172a #e5e7eb",
            "search-field.prompt": "#22d3ee",
        },
        prompt_label_color="#22d3ee",
        prompt_symbol_color="#f8fafc",
        lesson_panel_style="panel_surface",
        answer_panel_style="answer_surface",
        intervention_panel_style={
            "info": "panel_surface",
            "warning": "warning",
            "error": "error",
            "success": "success",
        },
        progress_bar_width=40,
        toolbar_fill_char="█",
        toolbar_empty_char="░",
        toolbar_background_style="toolbar_back",
        toolbar_box_style="toolbar_box",
        toolbar_topic_style="toolbar_topic",
        toolbar_suffix_styles={
            "success": "toolbar_suffix_success",
            "warning": "toolbar_suffix_warning",
            "error": "toolbar_suffix_error",
            "info": "toolbar_suffix_info",
        },
    ),
    "Classic": UITheme(
        name="Classic",
        rich_styles={
            "info": "#f3e9d2",
            "warning": "bold #f4d35e",
            "error": "bold #ff6b6b",
            "success": "bold #7bd389",
            "header": "bold #f8f4e3",
            "topic": "bold #9bd1e5",
            "quiz_answer": "bold #2f1b0c on #efe6d1",
            "panel_surface": "#efe6d1 on #3b2f2f",
            "answer_surface": "#fdf6e3 on #5b3a29",
            "toolbar_back": "#efe6d1 on #2b1f1a",
            "toolbar_box": "#c8a97e on #2b1f1a",
            "toolbar_topic": "bold #b8e1ff on #2b1f1a",
            "toolbar_suffix_success": "bold #7bd389 on #2b1f1a",
            "toolbar_suffix_warning": "bold #f4d35e on #2b1f1a",
            "toolbar_suffix_error": "bold #ff6b6b on #2b1f1a",
            "toolbar_suffix_info": "bold #f3e9d2 on #2b1f1a",
        },
        prompt_toolkit_styles={
            "dialog": "bg:#3b2f2f #efe6d1",
            "dialog.body": "bg:#3b2f2f #efe6d1",
            "dialog frame.label": "bold #f8f4e3",
            "dialog shadow": "bg:#1f1613",
            "label": "#d8c3a5",
            "radio": "#d8c3a5",
            "radio-selected": "bold #f8f4e3 bg:#5b3a29",
            "radio-checked": "bold #7bd389",
            "radio-checked-selected": "bold #7bd389 bg:#5b3a29",
            "textarea": "bg:#2b1f1a #f8f4e3",
            "search": "bg:#2b1f1a #f8f4e3",
            "search-field": "bg:#2b1f1a #f8f4e3",
            "search-field.prompt": "#d8c3a5",
        },
        prompt_label_color="#f5f5f5",
        prompt_symbol_color="#67e8f9",
        lesson_panel_style="panel_surface",
        answer_panel_style="answer_surface",
        intervention_panel_style={
            "info": "panel_surface",
            "warning": "warning",
            "error": "error",
            "success": "success",
        },
        progress_bar_width=34,
        toolbar_fill_char="■",
        toolbar_empty_char="·",
        toolbar_background_style="toolbar_back",
        toolbar_box_style="toolbar_box",
        toolbar_topic_style="toolbar_topic",
        toolbar_suffix_styles={
            "success": "toolbar_suffix_success",
            "warning": "toolbar_suffix_warning",
            "error": "toolbar_suffix_error",
            "info": "toolbar_suffix_info",
        },
    ),
    "Matrix": UITheme(
        name="Matrix",
        rich_styles={
            "info": "#22c55e",
            "warning": "bold #86efac",
            "error": "bold #fb7185",
            "success": "bold #4ade80",
            "header": "bold #86efac",
            "topic": "bold #22c55e",
            "quiz_answer": "bold #001100 on #86efac",
            "panel_surface": "#86efac on #001100",
            "answer_surface": "#bbf7d0 on #052e16",
            "toolbar_back": "#86efac on #001100",
            "toolbar_box": "#14532d on #001100",
            "toolbar_topic": "bold #bbf7d0 on #001100",
            "toolbar_suffix_success": "bold #86efac on #001100",
            "toolbar_suffix_warning": "bold #dcfce7 on #001100",
            "toolbar_suffix_error": "bold #fda4af on #001100",
            "toolbar_suffix_info": "bold #4ade80 on #001100",
        },
        prompt_toolkit_styles={
            "dialog": "bg:#001100 #66ff66",
            "dialog.body": "bg:#001100 #66ff66",
            "dialog frame.label": "bold #99ff99",
            "dialog shadow": "bg:#000600",
            "label": "#66ff66",
            "radio": "#66ff66",
            "radio-selected": "bold #ccffcc",
            "radio-checked": "bold #99ff99",
            "radio-checked-selected": "bold #99ff99",
            "textarea": "bg:#000b00 #ccffcc",
            "search": "bg:#000b00 #ccffcc",
            "search-field": "bg:#000b00 #ccffcc",
            "search-field.prompt": "#66ff66",
        },
        prompt_label_color="#00ff66",
        prompt_symbol_color="#99ff99",
        lesson_panel_style="panel_surface",
        answer_panel_style="answer_surface",
        intervention_panel_style={
            "info": "panel_surface",
            "warning": "warning",
            "error": "error",
            "success": "success",
        },
        progress_bar_width=46,
        toolbar_fill_char="▓",
        toolbar_empty_char="·",
        toolbar_background_style="toolbar_back",
        toolbar_box_style="toolbar_box",
        toolbar_topic_style="toolbar_topic",
        toolbar_suffix_styles={
            "success": "toolbar_suffix_success",
            "warning": "toolbar_suffix_warning",
            "error": "toolbar_suffix_error",
            "info": "toolbar_suffix_info",
        },
    ),
}

DEFAULT_THEME_NAME = "Modern"
_active_theme_name = DEFAULT_THEME_NAME
console = Console(theme=Theme(THEMES[DEFAULT_THEME_NAME].rich_styles))


def get_available_theme_names() -> list[str]:
    return list(THEMES.keys())


def resolve_theme_name(theme_name: str | None) -> str | None:
    if not theme_name:
        return None
    for name in THEMES:
        if name.lower() == theme_name.lower():
            return name
    return None


def get_theme(theme_name: str | None = None) -> UITheme:
    resolved_name = resolve_theme_name(theme_name)
    if not resolved_name:
        return THEMES[DEFAULT_THEME_NAME]
    return THEMES[resolved_name]


def get_current_theme() -> UITheme:
    return get_theme(_active_theme_name)


def set_current_theme(theme_name: str) -> UITheme:
    global _active_theme_name
    theme = get_theme(theme_name)
    _active_theme_name = theme.name
    theme_styles = Theme(theme.rich_styles).styles
    console._theme_stack._entries[:] = [theme_styles]
    return theme


def build_prompt_style(theme_name: str | None = None) -> Style:
    theme = get_theme(theme_name) if theme_name else get_current_theme()
    return Style.from_dict(theme.prompt_toolkit_styles)


def build_prompt_message(theme_name: str | None = None) -> str:
    theme = get_theme(theme_name) if theme_name else get_current_theme()
    return (
        f'<style color="{theme.prompt_label_color}">micro-learner</style> '
        f'<style color="{theme.prompt_symbol_color}">></style> '
    )

def render_lesson(title: str, content: str, subtitle: str = None) -> Panel:
    """Wraps lesson content in a stylized Rich Panel."""
    md = Markdown(content)
    theme = get_current_theme()
    return Panel(
        md,
        title=f"[header]{title}[/header]",
        subtitle=f"[info]{subtitle}[/info]" if subtitle else None,
        border_style="topic",
        padding=(1, 2),
        expand=True,
        style=theme.lesson_panel_style,
    )

def render_answer(answer_text: str) -> Panel:
    """Creates a stylized panel for the revealed answer."""
    theme = get_current_theme()
    content = Text.assemble(
        ("💡 Key Insight & Answer:\n\n", "header"),
        (answer_text, "success")
    )
    return Panel(
        Align.center(content),
        border_style="success",
        padding=(1, 2),
        title="[success]✔ Correct Answer Revealed[/success]",
        expand=True,
        style=theme.answer_panel_style,
    )

def render_intervention(title: str, content: str, style: str) -> Panel:
    """Wraps an intervention (analogy or code) in a stylized Rich Panel."""
    md = Markdown(content)
    theme = get_current_theme()
    return Panel(
        md,
        title=f"[{style}]{title}[/{style}]",
        border_style=style,
        padding=(1, 2),
        expand=True,
        style=theme.intervention_panel_style.get(style, theme.lesson_panel_style),
    )

def render_progress(current: int, total: int, topic_name: str) -> Group:
    """Creates a stylized progress bar and status text."""
    percentage = (current / total) * 100 if total > 0 else 0
    theme = get_current_theme()
    
    pb = ProgressBar(
        total=total,
        completed=current,
        width=theme.progress_bar_width,
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
        ansi_console = Console(
            file=buf,
            force_terminal=True,
            theme=Theme(get_current_theme().rich_styles),
            width=console.width,
        )
        ansi_console.print(renderable, end="")
        return buf.getvalue()


def render_to_text(renderable, width: int | None = None) -> str:
    """Renders a Rich renderable to plain terminal-safe text without ANSI codes."""
    with StringIO() as buf:
        text_console = Console(
            file=buf,
            force_terminal=False,
            color_system=None,
            theme=Theme(get_current_theme().rich_styles),
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
    theme = get_current_theme()

    bar_width = 20
    filled = 0 if total <= 0 else min(bar_width, round((current / total) * bar_width))
    empty = bar_width - filled
    progress_bar = theme.toolbar_fill_char * filled + theme.toolbar_empty_char * empty

    toolbar_text = Text()
    toolbar_text.append(" ", style=theme.toolbar_background_style)
    toolbar_text.append(f"{percentage:>3.0f}%", style="success")
    toolbar_text.append(" ", style=theme.toolbar_background_style)
    toolbar_text.append(progress_bar, style=theme.toolbar_box_style)
    toolbar_text.append(" [", style=theme.toolbar_background_style)
    toolbar_text.append(f"{current}/{total}", style="success")
    toolbar_text.append("] ", style=theme.toolbar_background_style)
    toolbar_text.append(topic_name, style=theme.toolbar_topic_style)

    if suffix:
        toolbar_text.append(" ", style=theme.toolbar_background_style)
        toolbar_text.append(
            suffix,
            style=theme.toolbar_suffix_styles.get(suffix_style, theme.toolbar_background_style),
        )
    else:
        toolbar_text.append(" ", style=theme.toolbar_background_style)

    toolbar_text.truncate(max_width or console.width, overflow="ellipsis")

    return render_to_ansi(toolbar_text)
