
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from localdeamon.deamon import Deamon


class PostProcessor:

    def __init__(self, fn: Callable[["Deamon", str], str], name: str | None = None):
        self.fn = fn
        self.name = name or getattr(fn, '__name__', 'post_processor')

    def __call__(self, daemon: "Deamon", raw_output: str) -> str:
        return self.fn(daemon, raw_output)


def post_processor(fn: Callable[["Deamon", str], str]) -> PostProcessor:
    return PostProcessor(fn)
