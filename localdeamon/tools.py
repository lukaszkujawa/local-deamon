"""
Built-in tools for Local Daemon.

This module contains the core tool implementations for command execution,
file operations, web fetching, and search functionality.
"""

import subprocess
from pathlib import Path
from localdeamon.tool_registry import tool, Tool


@tool
def exec(command: str) -> str:
    """
    Execute a shell command and return output.

    Args:
        command: Shell command to execute

    Returns:
        Command output (stdout + stderr)
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout
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
        return f"Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {e}"


@tool
def read(file_path: str) -> str:
    """
    Read and return contents of a text file.

    Args:
        file_path: Path to the file to read

    Returns:
        File contents as string
    """
    try:
        path = Path(file_path)

        # Check if file exists
        if not path.exists():
            return f"Error: File '{file_path}' not found"

        # Check if it's a file (not directory)
        if not path.is_file():
            return f"Error: '{file_path}' is not a file"

        # Check file size (limit to 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if path.stat().st_size > max_size:
            return f"Error: File too large (max 10MB). File size: {path.stat().st_size / 1024 / 1024:.2f}MB"

        # Try to read with UTF-8, fallback to latin-1
        try:
            content = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                content = path.read_text(encoding='latin-1')
            except Exception as e:
                return f"Error: Could not decode file (binary file?): {e}"

        return content

    except PermissionError:
        return f"Error: Permission denied reading '{file_path}'"
    except Exception as e:
        return f"Error reading file: {e}"


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
        script_path = Path(__file__).resolve().parent.parent / "tools" / "get_url.sh"

        if not script_path.exists():
            return f"Error: Script not found at {script_path}"

        result = subprocess.run(
            [str(script_path), url],
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout for network requests
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


@tool
def search(query: str) -> str:
    """
    Search the web for a query string..

    Args:
        query: Search query string

    Returns:
        Search results
    """
    try:
        script_path = Path(__file__).resolve().parent.parent / "tools" / "web_search.sh"

        if not script_path.exists():
            return f"Error: Script not found at {script_path}"

        result = subprocess.run(
            [str(script_path), query],
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout for search
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
        return f"Error: Search timed out after 60 seconds"
    except Exception as e:
        return f"Error performing search: {e}"
