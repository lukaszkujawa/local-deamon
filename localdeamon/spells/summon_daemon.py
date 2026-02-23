
from localdeamon.spell import spell
from localdeamon.deamon import Deamon
from localdeamon.context import Context


@spell
def summon_daemon(task: str) -> str:
    ctx = Context()
    ctx.add_user_message(task)
    deamon = Deamon()

    return deamon.run(ctx)
