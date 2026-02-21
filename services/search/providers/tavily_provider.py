"""Tavily search API provider with quality filtering."""
import os

from tavily import AsyncTavilyClient

from .base import SearchResponse, SearchResult


# Default domains to exclude (low-quality for research)
DEFAULT_EXCLUDED_DOMAINS = [
    # Video platforms (not text-based research)
    "youtube.com",
    "youtu.be",
    "vimeo.com",
    "dailymotion.com",
    "twitch.tv",

    # Social media (opinions, not authoritative)
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "tiktok.com",
    "linkedin.com",
    "reddit.com",

    # Content aggregators (secondary sources)
    "pinterest.com",
    "quora.com",

    # Paywalled content that can't be scraped
    "nytimes.com",
    "wsj.com",
    "ft.com",

    # Low-quality content farms
    "medium.com",  # Variable quality, often paywalled
]

# High-quality domains to prioritize (optional, can be configured)
HIGH_QUALITY_DOMAINS = [
    # Academic/Research
    "arxiv.org",
    "scholar.google.com",
    "ieee.org",
    "acm.org",
    "nature.com",
    "science.org",

    # Technical documentation
    "github.com",
    "docs.python.org",
    "developer.mozilla.org",

    # Reputable tech publications
    "arstechnica.com",
    "techcrunch.com",
    "wired.com",
    "theverge.com",
]


class TavilyProvider:
    name = "tavily"

    def __init__(self) -> None:
        self._api_key = os.environ.get("TAVILY_API_KEY", "").strip()

        # Load configuration from environment
        self._search_depth = os.environ.get("TAVILY_SEARCH_DEPTH", "advanced").strip()
        self._exclude_domains = self._load_excluded_domains()
        self._include_domains = self._load_included_domains()
        self._min_score_threshold = float(os.environ.get("TAVILY_MIN_SCORE", "0.0"))

    def _load_excluded_domains(self) -> list[str]:
        """Load excluded domains from env or use defaults."""
        env_excluded = os.environ.get("TAVILY_EXCLUDE_DOMAINS", "").strip()
        if env_excluded:
            # Custom list from env
            return [d.strip() for d in env_excluded.split(",") if d.strip()]
        else:
            # Use defaults
            return DEFAULT_EXCLUDED_DOMAINS.copy()

    def _load_included_domains(self) -> list[str] | None:
        """Load included domains from env (optional)."""
        env_included = os.environ.get("TAVILY_INCLUDE_DOMAINS", "").strip()
        if env_included:
            return [d.strip() for d in env_included.split(",") if d.strip()]
        return None  # None means no restriction

    def is_available(self) -> bool:
        return bool(self._api_key)

    async def search(
        self,
        query: str,
        *,
        max_results: int = 10,
        search_depth: str | None = None,
        include_answer: bool = False,
        exclude_domains: list[str] | None = None,
        include_domains: list[str] | None = None,
        **kwargs: object,
    ) -> SearchResponse:
        """Search with Tavily API and apply quality filtering.

        Args:
            query: Search query
            max_results: Maximum number of results (0-20)
            search_depth: "basic" or "advanced" (default: from config)
            include_answer: Include LLM-generated answer
            exclude_domains: Override default excluded domains
            include_domains: Override default included domains

        Returns:
            SearchResponse with filtered, high-quality results
        """
        if not self._api_key:
            raise RuntimeError("TAVILY_API_KEY is not set")

        client = AsyncTavilyClient(api_key=self._api_key)

        # Use configured search depth if not specified
        depth = search_depth or self._search_depth

        # Use configured domain filters if not overridden
        excluded = exclude_domains if exclude_domains is not None else self._exclude_domains
        included = include_domains if include_domains is not None else self._include_domains

        # Tavily allows 0–20 results, request more than needed for filtering
        tavily_max = min(20, max(0, max_results * 2))  # Request 2x for filtering

        # Build Tavily API call parameters
        api_params = {
            "query": query,
            "max_results": tavily_max,
            "search_depth": depth,
            "include_answer": include_answer,
        }

        # Add domain filters if configured
        if excluded:
            api_params["exclude_domains"] = excluded
        if included:
            api_params["include_domains"] = included

        response = await client.search(**api_params)

        # Parse and filter results
        results = []
        for r in response.get("results", []):
            score = r.get("score")

            # Apply minimum score threshold
            if score is not None and score < self._min_score_threshold:
                continue

            # Truncate snippet to 50 characters to avoid confusing LLM with long/outdated content
            snippet = r.get("content") or ""
            if len(snippet) > 50:
                snippet = snippet[:50] + "..."

            results.append(
                SearchResult(
                    title=r.get("title") or "",
                    url=r.get("url") or "",
                    snippet=snippet,
                    score=score,
                )
            )

        # Sort by score (descending) and limit to requested max
        results.sort(key=lambda x: x.score or 0.0, reverse=True)
        results = results[:max_results]

        answer = response.get("answer") if include_answer else None

        return SearchResponse(
            query=response.get("query", query),
            results=results,
            answer=answer,
            provider_meta={
                "response_time": response.get("response_time"),
                "usage": response.get("usage"),
                "search_depth": depth,
                "excluded_domains_count": len(excluded) if excluded else 0,
                "included_domains_count": len(included) if included else 0,
                "results_before_filtering": len(response.get("results", [])),
                "results_after_filtering": len(results),
            },
        )
