from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

def info(msg: str):
    console.print(f"[cyan]ℹ[/cyan] {msg}")

def warning(msg: str):
    console.print(f"[yellow]⚠[/yellow] {msg}", style="yellow")

def error(msg: str):
    console.print(f"[red]✗[/red] {msg}", style="red")

def success(msg: str):
    console.print(f"[green]✓[/green] {msg}", style="green")

def tool_call(name: str, args: dict):
    args_str = ", ".join(f"{k}={repr(v)}" for k, v in args.items())
    console.print(f"  [blue]→[/blue] [bold]{name}[/bold]({args_str})")

def iteration(num: int):
    console.print(f"\n[bold magenta]Iteration {num}[/bold magenta]")

def task_output(content: str):
    console.print(Panel(Markdown(content), border_style="cyan", padding=(1, 2)))

def divider():
    console.print("[dim]─" * console.width + "[/dim]")
