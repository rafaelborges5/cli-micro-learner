from rich.console import Console
from rich.theme import Theme

# Define a custom theme for the application
micro_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "header": "bold magenta",
    "topic": "bold blue",
})

console = Console(theme=micro_theme)
