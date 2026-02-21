from typing import Callable, Optional, Any
from contextlib import contextmanager
import threading
from beartype import beartype
from beartype.roar import BeartypeException
from localdeamon import console as c

_context = threading.local()


@contextmanager
def spell_context(spell_name: str):
    """Context manager to track the currently executing spell"""
    previous = getattr(_context, 'current_spell', None)
    _context.current_spell = spell_name
    try:
        yield
    finally:
        _context.current_spell = previous


def get_current_spell() -> Optional[str]:
    """Get the name of the currently executing spell"""
    return getattr(_context, 'current_spell', None)


class SpellCastingFailed(Exception):
    """Raised when spell casting fails due to type mismatch"""
    pass


class Spell:
    """A typed function wrapper with runtime type checking and composition support"""

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
        """Compose two spells into a pipeline using | operator"""
        def chained(*args: Any, **kwargs: Any) -> Any:
            intermediate = self(*args, **kwargs)
            return other(intermediate)

        return Spell(chained, name=f"{self.name}|{other.name}")


def spell(fn: Callable[[Any], Any]) -> Spell:
    """Decorator to create a Spell from a function"""
    return Spell(fn)
