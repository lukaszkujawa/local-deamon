"""Service health check utilities."""

import sys
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import List
from rich.panel import Panel
from localdeamon.console import console
from localdeamon.config import Config


@dataclass
class ServiceHealth:
    """Health status of a service."""
    name: str
    url: str
    healthy: bool


def check_service_health(service_name: str, url: str) -> bool:
    """
    Check if a service is healthy by hitting its /health endpoint.

    Args:
        service_name: Name of the service (for logging)
        url: Base URL of the service

    Returns:
        True if service is healthy, False otherwise
    """
    try:
        req = urllib.request.Request(f"{url}/health", method='GET')
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.status == 200
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return False


def check_all_services(config: Config) -> List[ServiceHealth]:
    """
    Check all required services.

    Args:
        config: Configuration object

    Returns:
        List of ServiceHealth objects
    """
    scraper_url = config.get_scraper_url()
    search_url = config.get_search_url()

    return [
        ServiceHealth("SCRAPER", scraper_url, check_service_health("SCRAPER", scraper_url)),
        ServiceHealth("SEARCH", search_url, check_service_health("SEARCH", search_url))
    ]


def verify_services_or_exit(config: Config) -> None:
    """
    Verify all required services are healthy, exit with error if not.

    Args:
        config: Configuration object
    """
    services = check_all_services(config)

    if all(s.healthy for s in services):
        return

    error_parts = [
        "[bold red]Service Health Check Failed[/bold red]\n",
        "This project requires both SCRAPER and SEARCH services to be running:\n"
    ]

    for service in services:
        if service.healthy:
            error_parts.append(f"  ✓ {service.name} service: [green]{service.url}/health[/green] (healthy)")
        else:
            error_parts.append(f"  ✗ {service.name} service: [red]{service.url}/health[/red] (unavailable)")

    error_parts.extend([
        "\n[bold]Configuration:[/bold]",
        "  Edit .env file to configure service URLs:",
        f"    HOST_GET_URL={config.get_scraper_url()}",
        f"    HOST_WEB_SEARCH={config.get_search_url()}",
        "\n[bold]To start services:[/bold]",
        "  Ensure both services are running and /health endpoints are accessible"
    ])

    console.print(Panel(
        "\n".join(error_parts),
        title="[bold red]Startup Error[/bold red]",
        border_style="red",
        padding=(1, 2)
    ))
    sys.exit(1)
