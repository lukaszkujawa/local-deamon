"""Base types for search providers: normalized response shape."""
from typing import Protocol

from pydantic import BaseModel


class SearchResult(BaseModel):
    """A single search result, same shape for all providers."""
    title: str
    url: str
    snippet: str
    score: float | None = None


class SearchResponse(BaseModel):
    """Normalized search response returned by every provider."""
    query: str
    results: list[SearchResult]
    answer: str | None = None  # LLM-style answer when supported (e.g. Tavily)
    provider_meta: dict | None = None  # provider-specific extras


class SearchProvider(Protocol):
    """Protocol for search backends. Add new APIs by implementing this."""

    name: str

    def is_available(self) -> bool:
        """True if API key/config is present and the provider can be used."""
        ...

    async def search(
        self,
        query: str,
        *,
        max_results: int = 10,
        **kwargs: object,
    ) -> SearchResponse:
        """Run search and return normalized results."""
        ...
