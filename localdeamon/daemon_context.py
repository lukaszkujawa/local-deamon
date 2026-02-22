from contextvars import ContextVar
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from localdeamon.deamon import Deamon

_current_daemon: ContextVar[Optional["Deamon"]] = ContextVar('current_daemon', default=None)


def set_current_daemon(daemon: "Deamon") -> None:
    """
    Set the currently active daemon instance in context.

    This makes the daemon accessible to tools without passing it as a parameter.
    Uses Python's contextvars for clean, thread-safe context propagation.

    Args:
        daemon: The daemon instance to set as current
    """
    _current_daemon.set(daemon)


def get_current_daemon() -> Optional["Deamon"]:
    """
    Get the currently active daemon instance from context.

    Tools can use this to access the daemon's context, configuration, etc.
    without having the daemon as a function parameter.

    Returns:
        The current daemon instance, or None if not set

    Example:
        from localdeamon.daemon_context import get_current_daemon

        @tool
        def my_tool(param: str) -> str:
            daemon = get_current_daemon()
            if daemon and daemon.ctx:
                # Access conversation context
                messages = daemon.ctx.messages
            return result
    """
    return _current_daemon.get()


def clear_current_daemon() -> None:
    """
    Clear the current daemon from context.

    Useful for testing or cleanup.
    """
    _current_daemon.set(None)
