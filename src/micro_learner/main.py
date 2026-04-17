import click
import asyncio
from micro_learner.state import bootstrap
from micro_learner.repl import start_repl
from micro_learner.logic import (
    execute_status,
    execute_resume,
    execute_start,
    execute_next,
)

def coro(f):
    """Decorator to allow click to run async functions."""
    import functools
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Micro-Learner CLI: Turn idle time into learning."""
    bootstrap()
    if ctx.invoked_subcommand is None:
        asyncio.run(start_repl())

@cli.command()
def status():
    """Check the current learning status."""
    execute_status()

@cli.command()
@coro
async def resume():
    """Browse and activate a cached syllabus."""
    await execute_resume()

@cli.command()
@click.argument('topic')
@coro
async def start(topic):
    """Start a new learning topic by generating a syllabus."""
    await execute_start(topic)

@cli.command()
@coro
async def next():
    """Fetch and display the next lesson in the current syllabus."""
    await execute_next()

@cli.command()
@coro
async def shell():
    """Launch the interactive REPL shell."""
    await start_repl()

def main():
    cli()

if __name__ == "__main__":
    main()
