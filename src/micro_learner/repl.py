import asyncio
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.formatted_text import HTML
from micro_learner.ui import console
from micro_learner.logic import (
    execute_status,
    execute_resume,
    execute_start,
    execute_next,
)

class REPLShell:
    def __init__(self):
        self.session = PromptSession()
        self.commands = {
            "/help": self.cmd_help,
            "/quit": self.cmd_quit,
            "/exit": self.cmd_quit,
            "/status": self.cmd_status,
            "/resume": self.cmd_resume,
            "/start": self.cmd_start,
            "/next": self.cmd_next,
        }

    async def cmd_help(self, *args):
        """Displays available commands."""
        console.print("[header]Available Commands:[/header]")
        console.print("  [topic]/start <topic>[/topic] - Start a new learning topic")
        console.print("  [topic]/next[/topic]         - Fetch the next lesson")
        console.print("  [topic]/status[/topic]       - Show current progress")
        console.print("  [topic]/resume[/topic]       - Browse and resume a syllabus")
        console.print("  [topic]/help[/topic]         - Show this help message")
        console.print("  [topic]/quit[/topic] or [topic]/exit[/topic] - Exit the shell")

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
        topic = " ".join(args)
        await execute_start(topic)

    async def cmd_next(self, *args):
        """Fetches the next lesson."""
        await execute_next()

    async def run(self):
        """Main REPL loop."""
        console.print("[header]Welcome to Micro-Learner Interactive Shell![/header]")
        console.print("[info]Type [topic]/help[/topic] to see available commands or [topic]/quit[/topic] to exit.[/info]")
        
        while True:
            try:
                with patch_stdout():
                    user_input = await self.session.prompt_async(
                        HTML('<style color="cyan">micro-learner</style> <style color="white">></style> ')
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
            except Exception as e:
                console.print(f"[error]An error occurred: {e}[/error]")

async def start_repl():
    shell = REPLShell()
    await shell.run()
