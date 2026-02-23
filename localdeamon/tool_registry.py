from typing import Callable, List, Optional, Dict, Union, TYPE_CHECKING
from langchain_core.tools import tool as langchain_tool, BaseTool
from localdeamon import console as c
from localdeamon.token_utils import estimate_tokens, format_tokens
from localdeamon.tool_response import ToolResponse

if TYPE_CHECKING:
    from localdeamon.deamon import Deamon
    from localdeamon.post_processor import PostProcessor


class ToolRegistry:
    _registry: List[BaseTool] = []
    _post_processors: Dict[str, Union["PostProcessor", Callable[["Deamon", str], str]]] = {}

    @classmethod
    def register(cls, tool_instance: BaseTool) -> BaseTool:
        cls._registry.append(tool_instance)
        return tool_instance

    @classmethod
    def all(cls) -> List[BaseTool]:
        return cls._registry.copy()

    @classmethod
    def get(cls, name: str) -> Optional[BaseTool]:
        return next((t for t in cls._registry if t.name == name), None)

    @classmethod
    def names(cls) -> List[str]:
        return [t.name for t in cls._registry]

    @classmethod
    def clear(cls) -> None:
        cls._registry.clear()
        cls._post_processors.clear()

    @classmethod
    def register_post_processor(
        cls,
        tool_name: str,
        processor: Union["PostProcessor", Callable[["Deamon", str], str]]
    ) -> None:
        cls._post_processors[tool_name] = processor

    @classmethod
    def get_post_processor(
        cls,
        tool_name: str
    ) -> Optional[Union["PostProcessor", Callable[["Deamon", str], str]]]:
        return cls._post_processors.get(tool_name)

    @classmethod
    def register_builtin(cls) -> None:
        from localdeamon.tools import exec, read, write, fetch, search, think

    @classmethod
    def execute_tool_call(cls, tool_call: dict, daemon: Optional["Deamon"] = None, verbose: bool = True) -> ToolResponse:
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
        results = {}

        for tool_call in tool_calls:
            tool_call_id = tool_call["id"]
            result = cls.execute_tool_call(tool_call, daemon=daemon, verbose=verbose)
            results[tool_call_id] = result

        return results


def tool(func: Optional[Callable] = None, *, name: Optional[str] = None) -> Callable:
    def decorator(f: Callable) -> BaseTool:

        if name:
            lc_tool = langchain_tool(f)
            lc_tool.name = name
        else:
            lc_tool = langchain_tool(f)


        ToolRegistry.register(lc_tool)

        return lc_tool


    if func is None:
        return decorator
    else:
        return decorator(func)



Tool = ToolRegistry
