"""Registry of search providers. Add new providers here."""
from .base import SearchProvider
from .tavily_provider import TavilyProvider

_PROVIDERS: dict[str, SearchProvider] = {
    "tavily": TavilyProvider(),
}


def get_provider(name: str) -> SearchProvider | None:
    return _PROVIDERS.get(name.lower())


def list_providers() -> list[str]:
    return list(_PROVIDERS.keys())


def get_available_providers() -> list[str]:
    return [p for p in _PROVIDERS if _PROVIDERS[p].is_available()]
