from localdeamon.llm import get_bound_llm
from localdeamon.context import Context
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from localdeamon.tool_registry import Tool
from localdeamon.console import _normalize_content
from localdeamon import console as c
from localdeamon.prompt_logger import invoke_with_logging
from localdeamon.daemon_context import set_current_daemon
from localdeamon.token_utils import extract_token_usage, extract_completion_duration, extract_total_duration, calculate_tokens_per_second, format_tokens

try:
    from ollama._types import ResponseError
except ImportError:
    class ResponseError(Exception):
        pass


class Deamon:

    def __init__(self):
        Tool.register_builtin()
        self.ctx: Context | None = None
        self.llm: BaseChatModel = get_bound_llm()

    def _safe_invoke(self, messages: list, retry: int = 0) -> AIMessage:
        try:
            return invoke_with_logging(self.llm, messages)


        except ResponseError as e:
            if "json" in str(e).lower() and retry < 2:
                c.warning(f"Retry {retry + 1}/2 - Malformed tool call JSON")
                return self._safe_invoke(messages + [HumanMessage(content="Invalid JSON in your tool call. Retry with valid formatting.")], retry + 1)
            raise

    def run(self, ctx: Context) -> str:
        self.ctx = ctx
        set_current_daemon(self)

        initial_response = self._safe_invoke(self.ctx.messages)

        prompt_tokens, completion_tokens = extract_token_usage(initial_response)
        completion_duration = extract_completion_duration(initial_response)
        total_duration = extract_total_duration(initial_response)
        if prompt_tokens > 0 or completion_tokens > 0:
            tokens_per_sec = calculate_tokens_per_second(completion_tokens, completion_duration)
            c.info(f"LLM Tokens: {format_tokens(prompt_tokens)} prompt + {format_tokens(completion_tokens)} completion = {format_tokens(prompt_tokens + completion_tokens)} total ({tokens_per_sec:.1f} tok/s, {total_duration:.2f}s)")

        return self._agentic_run(initial_response)

    def _agentic_run(self, initial_response: AIMessage, max_iterations: int = 200) -> str:
        current_response = initial_response
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            self.ctx.add_ai_message(current_response)
            self.ctx.clean_up()

            if not current_response.tool_calls:
                return _normalize_content(current_response.content)

            context_size = self.ctx.size_kb()
            c.iteration(iteration, context_size)
            results = Tool.execute_tool_calls(current_response.tool_calls, daemon=self, verbose=True)

            for tool_call_id, result in results.items():
                self.ctx.add_tool_message(tool_call_id, result)

            current_response = self._safe_invoke(self.ctx.messages)

            prompt_tokens, completion_tokens = extract_token_usage(current_response)
            completion_duration = extract_completion_duration(current_response)
            total_duration = extract_total_duration(current_response)
            if prompt_tokens > 0 or completion_tokens > 0:
                tokens_per_sec = calculate_tokens_per_second(completion_tokens, completion_duration)
                c.info(f"LLM Tokens: {format_tokens(prompt_tokens)} prompt + {format_tokens(completion_tokens)} completion = {format_tokens(prompt_tokens + completion_tokens)} total ({tokens_per_sec:.1f} tok/s, {total_duration:.2f}s)")

        c.warning(f"Max iterations ({max_iterations}) reached")
        return _normalize_content(current_response.content)
