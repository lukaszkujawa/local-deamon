import subprocess
from pathlib import Path
from localdeamon.tool_registry import tool
from localdeamon.subprocess_utils import run_command


@tool
def fetch(url: str) -> str:
    """
    Fetch content from a URL.

    Args:
        url: The URL to fetch

    Returns:
        Content from the URL
    """
    try:
        script_path = Path(__file__).resolve().parent.parent.parent / "tools" / "get_url.sh"

        if not script_path.exists():
            return f"Error: Script not found at {script_path}"

        return run_command([str(script_path), url], timeout=60)

    except subprocess.TimeoutExpired:
        return f"Error: Request timed out after 60 seconds"
    except (OSError, subprocess.SubprocessError) as e:
        return f"Error fetching URL: {e}"
