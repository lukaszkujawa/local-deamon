from localdeamon.config import get_config
from localdeamon.llm import get_llm
from localdeamon.context import Context
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from localdeamon.tool_registry import Tool
from localdeamon.prompt import Prompt
import json
import re

# Import tools to register them
import localdeamon.tools

try:
    from ollama._types import ResponseError
except ImportError:
    # If ollama is not installed, create a dummy exception class
    class ResponseError(Exception):
        pass


class Deamon:
    """
    Main agent daemon that orchestrates LLM and tool interactions.

    Manages the agentic loop: LLM -> Tool Calls -> Results -> LLM
    until the task is complete.
    """

    ctx: Context
    llm: BaseChatModel

    def __init__(self):
        self.ctx = Context()
        self.llm = get_llm().bind_tools(Tool.all())

    def _fix_json(self, malformed_json: str) -> str:
        """Attempt to fix common JSON errors in tool call arguments."""
        # Remove trailing commas before closing braces/brackets
        # Also handles cases like ,"} or ," } where an incomplete key was started
        fixed = re.sub(r',\s*"?\s*}', '}', malformed_json)
        fixed = re.sub(r',\s*"?\s*]', ']', fixed)

        # Remove trailing commas at the end (before EOF)
        fixed = re.sub(r',\s*$', '', fixed)

        return fixed

    def _safe_invoke(self, messages: list, retry_count: int = 0, max_retries: int = 2) -> AIMessage:
        try:
            return self.llm.invoke(messages)
        except ResponseError as e:
            error_msg = str(e)
            if ("parsing tool call" in error_msg.lower() or "json" in error_msg.lower()) and retry_count < max_retries:
                raw_match = re.search(r"raw='([^']*)'", error_msg)

                print(f"\n[Warning] LLM generated malformed tool call JSON (attempt {retry_count + 1}/{max_retries})")
                print(f"[Error] {error_msg}")

                # Add feedback message to help LLM correct itself
                feedback = (
                    "Your previous response contained a malformed JSON tool call. "
                    "Common errors: trailing commas before closing braces, unescaped quotes, incomplete JSON. "
                    "Please try again with valid JSON formatting."
                )

                if raw_match:
                    malformed = raw_match.group(1)
                    print(f"[Debug] Malformed JSON: {malformed}")

                    try:
                        fixed = self._fix_json(malformed)
                        if fixed != malformed:
                            print(f"[Debug] Auto-fixed to: {fixed}")
                            # Try to parse to validate the fix
                            json.loads(fixed)
                            feedback += f"\n\nNote: Your JSON had fixable errors (e.g., trailing commas). The corrected version would be: {fixed}"
                    except:
                        pass

                # Add feedback to context and retry
                messages_with_feedback = messages + [HumanMessage(content=feedback)]
                print("[Info] Retrying with feedback to LLM...")
                return self._safe_invoke(messages_with_feedback, retry_count + 1, max_retries)
            else:
                # Either not a JSON error or max retries exceeded
                raise

    def run(self, task: str) -> str:
        tmp_ctx = Context()
        understand_prompt = Prompt.load("UNDERSTAND").render(task=task)
        tmp_ctx.add_user_message(understand_prompt)

        refined_task_response = self._safe_invoke(tmp_ctx.messages)

        self.ctx.add_user_message(refined_task_response.content)
        print(refined_task_response.content)
        print("-----")

        initial_response = self._safe_invoke(self.ctx.messages)

        return self._agentic_run(initial_response)

    def _agentic_run(self, initial_response: AIMessage, max_iterations: int = 20) -> str:
        current_response = initial_response
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            self.ctx.add_ai_message(current_response)

            if not current_response.tool_calls:
                return current_response.content

            print(f"\n[Iteration {iteration}]", end=" ")
            results = Tool.execute_tool_calls(current_response.tool_calls, verbose=True)

            for tool_call_id, result in results.items():
                self.ctx.add_tool_message(tool_call_id, result)

            current_response = self._safe_invoke(self.ctx.messages)

        print(f"\n[Warning] Max iterations ({max_iterations}) reached")
        return current_response.content
