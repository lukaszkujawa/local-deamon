"""Utilities for executing subprocess commands with consistent error handling."""

import subprocess
from pathlib import Path
from typing import List


def run_command(cmd: List[str], timeout: int = 30) -> str:
    """
    Execute a command and return formatted output.

    Args:
        cmd: Command and arguments as list
        timeout: Timeout in seconds

    Returns:
        Formatted output string including stdout, stderr, and exit code

    Raises:
        subprocess.TimeoutExpired: If command exceeds timeout
    """
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
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
