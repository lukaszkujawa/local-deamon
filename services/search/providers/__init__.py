"""
Search providers: pluggable backends (Tavily, Bing, Google, etc.).
Each provider returns a normalized SearchResponse.
"""
from .base import SearchResult, SearchResponse
from .registry import get_provider, list_providers

__all__ = [
    "SearchResult",
    "SearchResponse",
    "get_provider",
    "list_providers",
]
