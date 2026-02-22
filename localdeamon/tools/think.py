from pyexpat.errors import messages

from localdeamon.tool_registry import tool
from localdeamon.llm import get_llm
from localdeamon.prompt import Prompt
from localdeamon.prompt_logger import invoke_with_logging
from localdeamon import console as c
from localdeamon.daemon_context import get_current_daemon
from langchain_core.messages import HumanMessage

@tool
def think(question: str) -> str:
    """
    Use this when you need to plan, reflect, or think through a problem.

    Use this tool when:
    - The task requires breaking down into steps
    - You're stuck and need to reconsider your approach
    - You need to analyze what you've learned so far
    - The current strategy isn't working
    - You need to plan next steps based on tool results

    Args:
        question: What you want to think about or plan for

    Returns:
        Your structured thinking and plan
    """
    try:

        think_prompt = Prompt.load("THINK").render(question=question)

        messages = get_current_daemon().ctx.messages.copy()

        llm = get_llm()
        response = invoke_with_logging(llm, messages + [HumanMessage(content=think_prompt)])

        content = response.content if isinstance(response.content, str) else str(response.content)

        c.task_output(content)

        return content

    except Exception as e:
        error_msg = f"Error during thinking: {e}"
        c.error(error_msg)
        return error_msg
