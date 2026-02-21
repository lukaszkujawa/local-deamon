"""
Tool registry system for automatic LangChain tool registration.

This module provides a decorator-based tool registration system that
automatically registers tools with LangChain and maintains a central registry.
"""

from typing import Callable, List, Optional
from langchain_core.tools import tool as langchain_tool, BaseTool
from localdeamon import console as c


class ToolRegistry:
    """
    Central registry for LangChain tools with auto-registration.

    Tools decorated with @tool are automatically registered here.
    Provides convenient access to all tools for agent initialization.

    Example:
        from localdeamon.tool_registry import tool, Tool

        @tool
        def my_function(x: int) -> str:
            '''Does something useful'''
            return str(x)

        # Later, get all registered tools
        all_tools = Tool.all()
        specific_tool = Tool.get("my_function")
    """

    _registry: List[BaseTool] = []

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
        Clear all registered tools.

        Useful for testing or reloading tools.
        """
        cls._registry.clear()

    @classmethod
    def execute_tool_call(cls, tool_call: dict, verbose: bool = True) -> str:
        """
        Execute a single tool call.

        Args:
            tool_call: Tool call dict with 'name', 'args', and 'id'
            verbose: Whether to print execution details

        Returns:
            Result string from tool execution (or error message)
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
            return error_msg

        try:
            result = tool.invoke(tool_args)
            result_str = str(result)

            if verbose:
                preview = result_str[:80] + '...' if len(result_str) > 80 else result_str
                c.success(f"Result: {preview}")

            return result_str

        except Exception as e:
            error_msg = f"{tool_name} failed: {e}"
            if verbose:
                c.error(error_msg)
            return error_msg

    @classmethod
    def execute_tool_calls(cls, tool_calls: list, verbose: bool = True) -> dict[str, str]:
        """
        Execute multiple tool calls.

        Args:
            tool_calls: List of tool call dicts
            verbose: Whether to print execution details

        Returns:
            Dict mapping tool_call_id to result string
        """
        results = {}

        for tool_call in tool_calls:
            tool_call_id = tool_call["id"]
            result = cls.execute_tool_call(tool_call, verbose=verbose)
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
