import subprocess
from pathlib import Path
from localdeamon.tool_registry import tool


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

        result = subprocess.run(
            [str(script_path), url],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=Path.cwd()
        )

        output = []
        if result.stdout:
            output.append(result.stdout)
        if result.stderr:
            output.append(f"[stderr]: {result.stderr}")
        if result.returncode != 0:
            output.append(f"[exit code: {result.returncode}]")

        return "\n".join(output) if output else "[no output]"

    except subprocess.TimeoutExpired:
        return f"Error: Request timed out after 60 seconds"
    except Exception as e:
        return f"Error fetching URL: {e}"
