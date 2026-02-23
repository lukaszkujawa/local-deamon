from typing import Callable, Optional, Any
from contextlib import contextmanager
import threading
from beartype import beartype
from beartype.roar import BeartypeException
from localdeamon import console as c

_context = threading.local()


@contextmanager
def spell_context(spell_name: str):
    previous = getattr(_context, 'current_spell', None)
    _context.current_spell = spell_name
    try:
        yield
    finally:
        _context.current_spell = previous


def get_current_spell() -> Optional[str]:
    return getattr(_context, 'current_spell', None)


class SpellCastingFailed(Exception):
    pass


class Spell:

    def __init__(self, fn: Callable[[Any], Any], name: Optional[str] = None):
        self.fn = beartype(fn)
        self.name = name or getattr(fn, '__name__', 'spell')

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        with spell_context(self.name):
            c.info(f"Casting spell: {self.name}")

            try:
                result = self.fn(*args, **kwargs)
                c.success(f"Spell '{self.name}' completed")
                return result
            except BeartypeException as e:
                raise SpellCastingFailed(
                    f"Spell '{self.name}' casting failed: {e}"
                ) from e

    def __or__(self, other: 'Spell') -> 'Spell':
        def chained(*args: Any, **kwargs: Any) -> Any:
            intermediate = self(*args, **kwargs)
            return other(intermediate)

        return Spell(chained, name=f"{self.name}|{other.name}")


def spell(fn: Callable[[Any], Any]) -> Spell:
    return Spell(fn)
