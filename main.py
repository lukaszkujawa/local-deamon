import argparse
import sys
import urllib.request
import urllib.error
from localdeamon.deamon import Deamon
from localdeamon.console import console, _normalize_content
from rich.panel import Panel
from rich.markdown import Markdown
from localdeamon.spell import spell
from localdeamon.prompt import Prompt
from localdeamon.llm import get_llm
from localdeamon.context import Context
from localdeamon import console as c
from localdeamon.config import get_config

@spell
def understand(task: str) -> str:
    prompt = Prompt.load("UNDERSTAND")
    ctx = Context.fromPrompt(prompt, task=task)
    resp = get_llm().invoke(ctx.messages)

    c.task_output(resp.content)
    c.divider()

    return _normalize_content(resp.content)

@spell
def summon_deamon(task: str) -> str:
    ctx = Context()
    ctx.add_user_message(task)
    deamon = Deamon()

    return deamon.run(ctx)

@spell
def extract_search_results(search_results_json: str) -> str:
    results = ""
    return results

def check_service_health(service_name: str, url: str) -> bool:
    try:
        req = urllib.request.Request(f"{url}/health", method='GET')
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.status == 200
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return False

def verify_services() -> None:
    config = get_config()
    scraper_url = config.get_scraper_url()
    search_url = config.get_search_url()

    scraper_healthy = check_service_health("SCRAPER", scraper_url)
    search_healthy = check_service_health("SEARCH", search_url)

    if not scraper_healthy or not search_healthy:
        error_parts = []
        error_parts.append("[bold red]Service Health Check Failed[/bold red]\n")
        error_parts.append("This project requires both SCRAPER and SEARCH services to be running:\n")

        if not scraper_healthy:
            error_parts.append(f"  ✗ SCRAPER service: [red]{scraper_url}/health[/red] (unavailable)")
        else:
            error_parts.append(f"  ✓ SCRAPER service: [green]{scraper_url}/health[/green] (healthy)")

        if not search_healthy:
            error_parts.append(f"  ✗ SEARCH service: [red]{search_url}/health[/red] (unavailable)")
        else:
            error_parts.append(f"  ✓ SEARCH service: [green]{search_url}/health[/green] (healthy)")

        error_parts.append("\n[bold]Configuration:[/bold]")
        error_parts.append("  Edit .env file to configure service URLs:")
        error_parts.append(f"    HOST_GET_URL={scraper_url}")
        error_parts.append(f"    HOST_WEB_SEARCH={search_url}")
        error_parts.append("\n[bold]To start services:[/bold]")
        error_parts.append("  Ensure both services are running and /health endpoints are accessible")

        console.print(Panel("\n".join(error_parts), title="[bold red]Startup Error[/bold red]", border_style="red", padding=(1, 2)))
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Local Daemon - Minimalistic LLM agent framework')
    parser.add_argument('task', nargs='?', help='Task for the agent to perform')
    parser.add_argument('--no-understand', action='store_true', help='Skip the UNDERSTAND phase')

    args = parser.parse_args()

    if not args.task:
        parser.print_help()
        return

    verify_services()

    if args.no_understand:
        resp = summon_deamon(args.task)
    else:
        pipeline = understand | summon_deamon
        resp = pipeline(args.task)

    console.print(Panel(Markdown(_normalize_content(resp)), title="[bold green]Final Response[/bold green]", border_style="green", padding=(1, 2)))

if __name__ == '__main__':
    main()