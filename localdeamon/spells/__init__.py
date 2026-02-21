"""Spell collection for the daemon framework."""

from localdeamon.spells.understand import understand
from localdeamon.spells.summon_daemon import summon_daemon
from localdeamon.spells.extract_search import extract_search_results
from localdeamon.spells.extract_web_doc import extract_web_doc

__all__ = ["understand", "summon_daemon", "extract_search_results", "extract_web_doc"]
