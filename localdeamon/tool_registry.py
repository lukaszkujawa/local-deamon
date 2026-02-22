"""
Tool registry system for automatic LangChain tool registration.

This module provides a decorator-based tool registration system that
automatically registers tools with LangChain and maintains a central registry.

Supports optional post-processors for tool outputs to transform raw results
before they are added to the agent context.
"""

from typing import Callable, List, Optional, Dict, Union, TYPE_CHECKING
from langchain_core.tools import tool as langchain_tool, BaseTool
from localdeamon import console as c
from localdeamon.token_utils import estimate_tokens, format_tokens
from localdeamon.tool_response import ToolResponse

if TYPE_CHECKING:
    from localdeamon.deamon import Deamon
    from localdeamon.post_processor import PostProcessor


class ToolRegistry:
    """
    Central registry for LangChain tools with auto-registration.

    Tools decorated with @tool are automatically registered here.
    Provides convenient access to all tools for agent initialization.

    Supports post-processors: callables that transform tool output before
    it's added to the agent context (e.g., summarizing JSON to markdown).

    Example:
        from localdeamon.tool_registry import tool, Tool

        @tool
        def my_function(x: int) -> str:
            '''Does something useful'''
            return str(x)

        # With post-processor
        def summarize_output(raw_output: str) -> str:
            return f"Summary: {raw_output[:100]}"

        @tool(post_processor=summarize_output)
        def search(query: str) -> str:
            '''Search for something'''
            return long_json_result

        # Later, get all registered tools
        all_tools = Tool.all()
        specific_tool = Tool.get("my_function")
    """

    _registry: List[BaseTool] = []
    _post_processors: Dict[str, Union["PostProcessor", Callable[["Deamon", str], str]]] = {}

    @classmethod
    def register(cls, tool_instance: BaseTool) -> BaseTool:
        """
        Register a tool in the central registry.

        Args:
            tool_instance: LangChain BaseTool instance to register

        Returns:
            The registered tool instance
        """
        cls._registry.append(tool_instance)
        return tool_instance

    @classmethod
    def all(cls) -> List[BaseTool]:
        """
        Get all registered tools.

        Returns:
            List of all registered BaseTool instances
        """
        return cls._registry.copy()

    @classmethod
    def get(cls, name: str) -> Optional[BaseTool]:
        """
        Get a specific tool by name.

        Args:
            name: Tool name to retrieve

        Returns:
            BaseTool instance or None if not found
        """
        return next((t for t in cls._registry if t.name == name), None)

    @classmethod
    def names(cls) -> List[str]:
        """
        Get list of all registered tool names.

        Returns:
            List of tool name strings
        """
        return [t.name for t in cls._registry]

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered tools and post-processors.

        Useful for testing or reloading tools.
        """
        cls._registry.clear()
        cls._post_processors.clear()

    @classmethod
    def register_post_processor(
        cls,
        tool_name: str,
        processor: Union["PostProcessor", Callable[["Deamon", str], str]]
    ) -> None:
        """
        Register a post-processor for a tool.

        The post-processor transforms the raw tool output before it's added
        to the agent context. Useful for summarizing verbose outputs like
        search results or fetched web pages.

        Args:
            tool_name: Name of the tool to attach processor to
            processor: PostProcessor or callable with signature (daemon, raw_output) -> str

        Example:
            @post_processor
            def extract_results(daemon, raw_json):
                # Use daemon.ctx for context-aware extraction
                return clean_markdown

            Tool.register_post_processor("search", extract_results)
        """
        cls._post_processors[tool_name] = processor

    @classmethod
    def get_post_processor(
        cls,
        tool_name: str
    ) -> Optional[Union["PostProcessor", Callable[["Deamon", str], str]]]:
        """
        Get the post-processor for a tool, if registered.

        Args:
            tool_name: Name of the tool

        Returns:
            Post-processor or None if not registered
        """
        return cls._post_processors.get(tool_name)

    @classmethod
    def register_builtin(cls) -> None:
        """
        Explicitly register all built-in tools.

        Imports tool modules which triggers @tool decorator registration.
        Call this once during daemon initialization.
        """
        from localdeamon.tools import exec, read, write, fetch, search, think

    @classmethod
    def execute_tool_call(cls, tool_call: dict, daemon: Optional["Deamon"] = None, verbose: bool = True) -> ToolResponse:
        """
        Execute a single tool call and apply post-processor if registered.

        Args:
            tool_call: Tool call dict with 'name', 'args', and 'id'
            daemon: Daemon instance (required if tool has post-processor)
            verbose: Whether to print execution details

        Returns:
            ToolResponse wrapping the result (behaves like string but has tool_name attribute)
            If post-processor is registered, returns processed output
        """
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        if verbose:
            c.tool_call(tool_name, tool_args)

        tool = cls.get(tool_name)
        if not tool:
            error_msg = f"Tool '{tool_name}' not found"
            if verbose:
                c.error(error_msg)
            return ToolResponse(error_msg, tool_name=tool_name)

        try:
            result = tool.invoke(tool_args)
            result_str = str(result)

            post_processor = cls.get_post_processor(tool_name)
            if post_processor:
                if verbose:
                    c.info(f"Running post-processor for {tool_name}...")
                try:
                    result_str = post_processor(daemon, result_str)
                    if verbose:
                        c.success("Post-processing complete")
                except Exception as pp_error:
                    if verbose:
                        c.warning(f"Post-processor failed: {pp_error}, using raw output")

            if verbose:
                preview = result_str[:80] + '...' if len(result_str) > 80 else result_str
                token_count = estimate_tokens(result_str)
                c.success(f"Result: {preview}")
                c.info(f"Tokens: {format_tokens(token_count)}")

            return ToolResponse(result_str, tool_name=tool_name)

        except Exception as e:
            error_msg = f"{tool_name} failed: {e}"
            if verbose:
                c.error(error_msg)
            return ToolResponse(error_msg, tool_name=tool_name)

    @classmethod
    def execute_tool_calls(cls, tool_calls: list, daemon: Optional["Deamon"] = None, verbose: bool = True) -> dict[str, ToolResponse]:
        """
        Execute multiple tool calls and return results.

        Args:
            tool_calls: List of tool call dicts
            daemon: Daemon instance (required if tools have post-processors)
            verbose: Whether to print execution details

        Returns:
            Dict mapping tool_call_id to ToolResponse (behaves like str but has tool_name)
        """
        results = {}

        for tool_call in tool_calls:
            tool_call_id = tool_call["id"]
            result = cls.execute_tool_call(tool_call, daemon=daemon, verbose=verbose)
            results[tool_call_id] = result

        return results


def tool(func: Optional[Callable] = None, *, name: Optional[str] = None) -> Callable:
    """
    Decorator that creates a LangChain tool and auto-registers it.

    Supports both @tool and @tool(name="custom_name") syntax.
    Tools are automatically added to the ToolRegistry.

    Args:
        func: Function to decorate
        name: Optional custom tool name (supports dotted names like "browser.search")

    Returns:
        Decorated LangChain BaseTool instance

    Example:
        @tool
        def search(query: str) -> str:
            '''Search for files'''
            return f"Results for {query}"

        @tool(name="browser.search")
        def web_search(query: str) -> str:
            '''Search the web'''
            return f"Results for {query}"
    """
    def decorator(f: Callable) -> BaseTool:
        # Create LangChain tool with custom name if provided
        if name:
            lc_tool = langchain_tool(f)
            lc_tool.name = name
        else:
            lc_tool = langchain_tool(f)

        # Auto-register in central registry
        ToolRegistry.register(lc_tool)

        return lc_tool

    # Support both @tool and @tool(name="...")
    if func is None:
        return decorator
    else:
        return decorator(func)


# Convenient alias
Tool = ToolRegistry
