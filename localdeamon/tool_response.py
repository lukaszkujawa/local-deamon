
class ToolResponse(str):

    def __new__(cls, content: str, tool_name: str):
        instance = super().__new__(cls, content)
        instance._tool_name = tool_name
        return instance

    @property
    def tool_name(self) -> str:
        return self._tool_name
