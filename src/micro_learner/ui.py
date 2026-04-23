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
from prompt_toolkit.formatted_text import FormattedText
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
            "toolbar_back": "#94a3b8 on #000000",
            "toolbar_box": "#38bdf8 on #000000",
            "toolbar_topic": "bold #e2e8f0 on #000000",
            "toolbar_suffix_success": "bold #86efac on #000000",
            "toolbar_suffix_warning": "bold #fbbf24 on #000000",
            "toolbar_suffix_error": "bold #fda4af on #000000",
            "toolbar_suffix_info": "bold #7dd3fc on #000000",
        },
        prompt_toolkit_styles={
            "dialog": "bg:#111827 #d1d5db",
            "dialog.body": "bg:#111827 #d1d5db",
            "dialog frame.label": "bold #f472b6",
            "dialog shadow": "bg:#030712",
            "bottom-toolbar": "noreverse bg:#3a3a3a #94a3b8",
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
            "toolbar_back": "#c7b39a on #000000",
            "toolbar_box": "#a16207 on #000000",
            "toolbar_topic": "bold #f3f4f6 on #000000",
            "toolbar_suffix_success": "bold #7bd389 on #000000",
            "toolbar_suffix_warning": "bold #f4d35e on #000000",
            "toolbar_suffix_error": "bold #ff8b8b on #000000",
            "toolbar_suffix_info": "bold #d6d3d1 on #000000",
        },
        prompt_toolkit_styles={
            "dialog": "bg:#3b2f2f #efe6d1",
            "dialog.body": "bg:#3b2f2f #efe6d1",
            "dialog frame.label": "bold #f8f4e3",
            "dialog shadow": "bg:#1f1613",
            "bottom-toolbar": "noreverse bg:#3a3a3a #c7b39a",
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
            "toolbar_back": "#4ade80 on #000000",
            "toolbar_box": "#166534 on #000000",
            "toolbar_topic": "bold #dcfce7 on #000000",
            "toolbar_suffix_success": "bold #86efac on #000000",
            "toolbar_suffix_warning": "bold #dcfce7 on #000000",
            "toolbar_suffix_error": "bold #fda4af on #000000",
            "toolbar_suffix_info": "bold #4ade80 on #000000",
        },
        prompt_toolkit_styles={
            "dialog": "bg:#001100 #66ff66",
            "dialog.body": "bg:#001100 #66ff66",
            "dialog frame.label": "bold #99ff99",
            "dialog shadow": "bg:#000600",
            "bottom-toolbar": "noreverse bg:#3a3a3a #4ade80",
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
    theme = get_current_theme()
    return Panel(
        Markdown(answer_text),
        border_style="success",
        padding=(1, 2),
        title="[success]Answer[/success]",
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

@dataclass(frozen=True)
class _ToolbarSegments:
    progress_bar: str
    count_label: str
    percentage_label: str
    topic_segment: str
    suffix_segment: str
    include_percentage: bool
    fill_count: int


def _compute_toolbar_segments(
    current: int,
    total: int,
    topic_name: str,
    suffix: str,
    available_width: int,
    theme: UITheme,
) -> _ToolbarSegments:
    """Compute all width-aware layout decisions for the toolbar.

    All truncation and slot allocation lives here so both the ANSI and
    FormattedText rendering paths share a single source of truth.

    Priority: progress bar + count > topic > suffix > percentage.
    Bar width scales with terminal width: 8 chars minimum, 20 maximum.
    """
    percentage = (current / total) * 100 if total > 0 else 0
    bar_width = max(8, min(20, (available_width - 30) // 3))
    filled = 0 if total <= 0 else min(bar_width, round((current / total) * bar_width))
    progress_bar = theme.toolbar_fill_char * filled + theme.toolbar_empty_char * (bar_width - filled)
    count_label = f"[{current}/{total}]"
    percentage_label = f"{percentage:>3.0f}%"
    minimum_topic_width = 6

    # leading space + bar + space + count
    base_width = 1 + len(progress_bar) + 1 + len(count_label)
    remaining = max(0, available_width - base_width)

    topic_segment = ""
    if topic_name and remaining >= minimum_topic_width + 1:
        t = Text(topic_name)
        t.truncate(remaining - 1, overflow="ellipsis")
        topic_segment = t.plain
        remaining = max(0, remaining - (1 + len(topic_segment)))

    suffix_segment = ""
    if suffix and remaining >= len(suffix) + 1:
        suffix_segment = suffix
        remaining -= 1 + len(suffix_segment)

    include_percentage = remaining >= len(percentage_label) + 1
    if include_percentage:
        remaining -= 1 + len(percentage_label)

    return _ToolbarSegments(
        progress_bar=progress_bar,
        count_label=count_label,
        percentage_label=percentage_label,
        topic_segment=topic_segment,
        suffix_segment=suffix_segment,
        include_percentage=include_percentage,
        fill_count=remaining,
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
            color_system="truecolor",
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
    """Render the REPL toolbar as an ANSI escape-code string."""
    theme = get_current_theme()
    available_width = max_width or console.width
    seg = _compute_toolbar_segments(current, total, topic_name, suffix, available_width, theme)

    def parse_style(style_name: str) -> tuple[str | None, str | None, bool]:
        style_spec = theme.rich_styles.get(style_name, "")
        bold = "bold" in style_spec.split()
        fg = None
        bg = None
        if " on " in style_spec:
            left, bg = style_spec.split(" on ", 1)
            tokens = left.split()
        else:
            tokens = style_spec.split()
        for token in tokens:
            if token != "bold":
                fg = token
                break
        return fg, bg, bold

    def style_ansi(text: str, *, fg: str | None = None, bg: str | None = None, bold: bool = False) -> str:
        codes: list[str] = []
        if bold:
            codes.append("1")
        if fg and fg.startswith("#") and len(fg) == 7:
            r, g, b = int(fg[1:3], 16), int(fg[3:5], 16), int(fg[5:7], 16)
            codes.append(f"38;2;{r};{g};{b}")
        if bg and bg.startswith("#") and len(bg) == 7:
            r, g, b = int(bg[1:3], 16), int(bg[3:5], 16), int(bg[5:7], 16)
            codes.append(f"48;2;{r};{g};{b}")
        if not codes:
            return text
        return f"\x1b[{';'.join(codes)}m{text}\x1b[0m"

    toolbar_fg, toolbar_bg, _ = parse_style(theme.toolbar_background_style)
    box_fg, box_bg, box_bold = parse_style(theme.toolbar_box_style)
    topic_fg, _, topic_bold = parse_style(theme.toolbar_topic_style)
    success_fg, _, success_bold = parse_style("success")

    out = ""
    out += style_ansi(" ", fg=toolbar_fg, bg=toolbar_bg)
    out += style_ansi(seg.progress_bar, fg=box_fg, bg=box_bg or toolbar_bg, bold=box_bold)
    out += style_ansi(" ", fg=toolbar_fg, bg=toolbar_bg)
    out += style_ansi(seg.count_label, fg=success_fg, bg=toolbar_bg, bold=success_bold)
    if seg.include_percentage:
        out += style_ansi(" ", fg=toolbar_fg, bg=toolbar_bg)
        out += style_ansi(seg.percentage_label, fg=success_fg, bg=toolbar_bg, bold=success_bold)
    if seg.topic_segment:
        out += style_ansi(" ", fg=toolbar_fg, bg=toolbar_bg)
        out += style_ansi(seg.topic_segment, fg=topic_fg, bg=toolbar_bg, bold=topic_bold)
    if seg.suffix_segment:
        suffix_style_name = theme.toolbar_suffix_styles.get(suffix_style, theme.toolbar_background_style)
        suffix_fg, _, suffix_bold = parse_style(suffix_style_name)
        out += style_ansi(" ", fg=toolbar_fg, bg=toolbar_bg)
        out += style_ansi(seg.suffix_segment, fg=suffix_fg, bg=toolbar_bg, bold=suffix_bold)
    if seg.fill_count > 0:
        out += style_ansi(" " * seg.fill_count, fg=toolbar_fg, bg=toolbar_bg)
    return out


def render_toolbar_formatted_text(
    current: int,
    total: int,
    topic_name: str,
    *,
    suffix: str = "",
    suffix_style: str = "warning",
    max_width: int | None = None,
) -> FormattedText:
    """Render toolbar content as prompt-toolkit FormattedText for the live REPL footer."""
    theme = get_current_theme()
    available_width = max_width or console.width
    footer_bg = "#3a3a3a"
    seg = _compute_toolbar_segments(current, total, topic_name, suffix, available_width, theme)

    def parse_style(style_name: str) -> tuple[str | None, bool]:
        style_spec = theme.rich_styles.get(style_name, "")
        tokens = style_spec.split()
        bold = "bold" in tokens
        fg = None
        for token in tokens:
            if token != "bold" and token != "on":
                if token.startswith("#"):
                    fg = token
                    break
        return fg, bold

    def style_fragment(style_name: str, *, force_bg: str | None = footer_bg) -> str:
        fg, bold = parse_style(style_name)
        style_parts: list[str] = ["noreverse"]
        if bold:
            style_parts.append("bold")
        if fg:
            style_parts.append(fg)
        if force_bg:
            style_parts.append(f"bg:{force_bg}")
        return " ".join(style_parts)

    base_style = style_fragment(theme.toolbar_background_style)
    box_style = style_fragment(theme.toolbar_box_style)
    success_style = style_fragment("success")
    topic_style = style_fragment(theme.toolbar_topic_style)
    suffix_style_spec = style_fragment(theme.toolbar_suffix_styles.get(suffix_style, theme.toolbar_background_style))

    fragments: list[tuple[str, str]] = []
    fragments.append((base_style, " "))
    fragments.append((box_style, seg.progress_bar))
    fragments.append((base_style, " "))
    fragments.append((success_style, seg.count_label))
    if seg.include_percentage:
        fragments.append((base_style, " "))
        fragments.append((success_style, seg.percentage_label))
    if seg.topic_segment:
        fragments.append((base_style, " "))
        fragments.append((topic_style, seg.topic_segment))
    if seg.suffix_segment:
        fragments.append((base_style, " "))
        fragments.append((suffix_style_spec, seg.suffix_segment))
    if seg.fill_count > 0:
        fragments.append((base_style, " " * seg.fill_count))

    return FormattedText(fragments)
