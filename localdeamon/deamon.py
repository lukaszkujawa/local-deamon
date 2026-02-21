from localdeamon.llm import get_llm
from localdeamon.context import Context
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from localdeamon.tool_registry import Tool
from localdeamon.console import _normalize_content
from localdeamon import console as c

try:
    from ollama._types import ResponseError
except ImportError:
    class ResponseError(Exception):
        pass


class Deamon:
    """
    Main agent daemon that orchestrates LLM and tool interactions.

    Manages the agentic loop: LLM -> Tool Calls -> Results -> LLM
    until the task is complete.
    """

    ctx: Context = None
    llm: BaseChatModel = None

    def __init__(self):
        Tool.register_builtin()
        self.llm = get_llm().bind_tools(Tool.all())

    def _safe_invoke(self, messages: list, retry: int = 0) -> AIMessage:
        try:
            return self.llm.invoke(messages)
        except ResponseError as e:
            if "json" in str(e).lower() and retry < 2:
                c.warning(f"Retry {retry + 1}/2 - Malformed tool call JSON")
                return self._safe_invoke(messages + [HumanMessage(content="Invalid JSON in your tool call. Retry with valid formatting.")], retry + 1)
            raise

    def run(self, ctx: Context) -> str:
        self.ctx = ctx
        initial_response = self._safe_invoke(self.ctx.messages)
        return self._agentic_run(initial_response)

    def _agentic_run(self, initial_response: AIMessage, max_iterations: int = 20) -> str:
        current_response = initial_response
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            self.ctx.add_ai_message(current_response)

            if not current_response.tool_calls:
                return _normalize_content(current_response.content)

            c.iteration(iteration)
            results = Tool.execute_tool_calls(current_response.tool_calls, daemon=self, verbose=True)

            for tool_call_id, result in results.items():
                self.ctx.add_tool_message(tool_call_id, result)

            current_response = self._safe_invoke(self.ctx.messages)

        c.warning(f"Max iterations ({max_iterations}) reached")
        return _normalize_content(current_response.content)
