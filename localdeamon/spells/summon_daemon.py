"""Summon daemon spell: Executes tasks using the agentic loop."""

from localdeamon.spell import spell
from localdeamon.deamon import Deamon
from localdeamon.context import Context


@spell
def summon_daemon(task: str) -> str:
    """
    Execute task using the daemon's agentic loop.

    Args:
        task: Task to execute

    Returns:
        Final daemon response
    """
    ctx = Context()
    ctx.add_user_message(task)
    deamon = Deamon()

    return deamon.run(ctx)
