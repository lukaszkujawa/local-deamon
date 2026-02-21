"""Post-processor decorator for tool output transformation."""

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from localdeamon.deamon import Deamon


class PostProcessor:
    """
    A post-processor that transforms tool output before adding to context.

    Unlike spells, post-processors:
    - Always take (daemon, raw_output) signature
    - Are registered with specific tools
    - Don't participate in spell composition
    - Focus on cleaning/extracting from raw tool results
    - Logging handled by ToolRegistry.execute_tool_call()
    """

    def __init__(self, fn: Callable[["Deamon", str], str], name: str | None = None):
        self.fn = fn
        self.name = name or getattr(fn, '__name__', 'post_processor')

    def __call__(self, daemon: "Deamon", raw_output: str) -> str:
        """
        Process tool output with daemon context.

        Args:
            daemon: Daemon instance with conversation context
            raw_output: Raw tool output to process

        Returns:
            Processed output string
        """
        return self.fn(daemon, raw_output)


def post_processor(fn: Callable[["Deamon", str], str]) -> PostProcessor:
    """
    Decorator to create a PostProcessor from a function.

    Post-processors transform raw tool output into clean, relevant summaries
    using the daemon's conversation context.

    Example:
        @post_processor
        def extract_search_results(daemon, raw_json: str) -> str:
            '''Extract relevant search results using daemon context'''
            # Parse JSON, use daemon.ctx.messages for context
            # Return clean Markdown summary
            return processed_markdown

    Args:
        fn: Function with signature (Deamon, str) -> str

    Returns:
        PostProcessor instance callable as (daemon, raw_output) -> str
    """
    return PostProcessor(fn)
