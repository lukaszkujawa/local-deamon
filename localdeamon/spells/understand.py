"""Understand spell: Refines and clarifies user tasks."""

from localdeamon.spell import spell
from localdeamon.prompt import Prompt
from localdeamon.llm import get_llm
from localdeamon.context import Context
from localdeamon.console import _normalize_content
from localdeamon import console as c
from localdeamon.prompt_logger import invoke_with_logging


@spell
def understand(task: str) -> str:
    """
    Refine and clarify user task using UNDERSTAND prompt.

    Args:
        task: Raw user task string

    Returns:
        Refined task description
    """
    prompt = Prompt.load("UNDERSTAND")
    ctx = Context.fromPrompt(prompt, task=task)
    resp = invoke_with_logging(get_llm(), ctx.messages)

    c.task_output(resp.content)
    c.divider()

    return _normalize_content(resp.content)
