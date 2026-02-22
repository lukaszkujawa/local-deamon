"""Tool response wrapper that carries metadata while behaving as a string."""


class ToolResponse(str):
    """
    String wrapper for tool execution results with metadata.

    Behaves exactly like a string in all contexts but carries
    additional metadata about which tool produced the result.

    Usage:
        result = ToolResponse("file contents here", tool_name="read")
        print(result)  # Works like a string
        str(result)    # Returns the content
        result.tool_name  # Access metadata
    """

    def __new__(cls, content: str, tool_name: str):
        instance = super().__new__(cls, content)
        instance._tool_name = tool_name
        return instance

    @property
    def tool_name(self) -> str:
        """Name of the tool that produced this result."""
        return self._tool_name
