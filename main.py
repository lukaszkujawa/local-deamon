import argparse
from localdeamon.console import console, _normalize_content
from rich.panel import Panel
from rich.markdown import Markdown
from localdeamon.config import get_config
from localdeamon.spells import understand, summon_daemon
from localdeamon.post_processors import extract_search_results, extract_web_doc
from localdeamon.health import verify_services_or_exit
from localdeamon.tool_registry import Tool

def main():
    parser = argparse.ArgumentParser(description='Local Daemon - Minimalistic LLM agent framework')
    parser.add_argument('task', nargs='?', help='Task for the agent to perform')
    parser.add_argument('--no-understand', action='store_true', help='Skip the UNDERSTAND phase')

    args = parser.parse_args()

    if not args.task:
        parser.print_help()
        return

    config = get_config()
    verify_services_or_exit(config)

    """
    Reduce the size of web search results and documents with LLM post processing
    """
    #Tool.register_post_processor("search", extract_search_results)
    Tool.register_post_processor("fetch", extract_web_doc)

    if args.no_understand:
        resp = summon_daemon(args.task)
    else:
        pipeline = understand | summon_daemon
        resp = pipeline(args.task)

    console.print(Panel(Markdown(_normalize_content(resp)), title="[bold green]Final Response[/bold green]", border_style="green", padding=(1, 2)))

if __name__ == '__main__':
    main()