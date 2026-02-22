import argparse
import os
from pathlib import Path
from localdeamon.console import console, _normalize_content
from rich.panel import Panel
from rich.markdown import Markdown
from localdeamon.config import get_config
from localdeamon.spells import summon_daemon
from localdeamon.post_processors import extract_web_doc, extract_search_results
from localdeamon.health import verify_services_or_exit
from localdeamon.tool_registry import Tool

def main():
    parser = argparse.ArgumentParser(description='Local Daemon - Minimalistic LLM agent framework')
    parser.add_argument('task', nargs='?', help='Task for the agent to perform')

    args = parser.parse_args()

    if not args.task:
        parser.print_help()
        return

    config = get_config()
    verify_services_or_exit(config)

    workspace_dir = config.get_workspace_dir()
    workspace_path = Path(workspace_dir)
    workspace_path.mkdir(parents=True, exist_ok=True)
    os.chdir(workspace_path)

    Tool.register_post_processor("fetch", extract_web_doc)
    Tool.register_post_processor("search", extract_search_results)

    resp = summon_daemon(args.task)

    console.print(Panel(Markdown(_normalize_content(resp)), title="[bold green]Final Response[/bold green]", border_style="green", padding=(1, 2)))

if __name__ == '__main__':
    main()