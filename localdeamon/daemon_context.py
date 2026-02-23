from contextvars import ContextVar
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from localdeamon.deamon import Deamon

_current_daemon: ContextVar[Optional["Deamon"]] = ContextVar('current_daemon', default=None)


def set_current_daemon(daemon: "Deamon") -> None:
    _current_daemon.set(daemon)


def get_current_daemon() -> Optional["Deamon"]:
    return _current_daemon.get()


def clear_current_daemon() -> None:
    _current_daemon.set(None)
