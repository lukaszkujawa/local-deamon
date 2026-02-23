import os
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from typing import Union

force_color = os.getenv("FORCE_COLOR", "").lower() in ("1", "true", "yes")
console = Console(force_terminal=force_color or None)

def _normalize_content(content: Union[str, list, dict]) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text' and 'text' in item:
                    parts.append(item['text'])
                elif item.get('type') == 'reasoning':
                    continue
                elif 'text' in item:
                    parts.append(item['text'])
                else:
                    parts.append(str(item))
            elif isinstance(item, str):
                parts.append(item)
            else:
                parts.append(str(item))
        return ''.join(parts)

    if isinstance(content, dict):
        if content.get('type') == 'text' and 'text' in content:
            return content['text']
        if 'text' in content:
            return content['text']
        if 'content' in content:
            return _normalize_content(content['content'])

    return str(content)

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

def iteration(num: int, context_size_kb: float = None):
    if context_size_kb is not None:
        console.print(f"\n[bold magenta]Iteration {num}[/bold magenta] [dim](ctx: {context_size_kb:.1f}KB)[/dim]")
    else:
        console.print(f"\n[bold magenta]Iteration {num}[/bold magenta]")

def task_output(content: Union[str, list]):
    normalized = _normalize_content(content)
    console.print(Panel(Markdown(normalized), border_style="cyan", padding=(1, 2)))

def divider():
    console.print("[dim]─" * console.width + "[/dim]")
