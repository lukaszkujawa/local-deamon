import subprocess
from pathlib import Path
from localdeamon.tool_registry import tool
from localdeamon.subprocess_utils import run_command


@tool
def search(query: str) -> str:
    """
    Search the web for a query string.

    Args:
        query: Search query string

    Returns:
        Search results
    """
    try:
        script_path = Path(__file__).resolve().parent.parent.parent / "tools" / "web_search.sh"

        if not script_path.exists():
            return f"Error: Script not found at {script_path}"

        return run_command([str(script_path), query], timeout=60)

    except subprocess.TimeoutExpired:
        return f"Error: Search timed out after 60 seconds"
    except (OSError, subprocess.SubprocessError) as e:
        return f"Error performing search: {e}"
