"""
Web search microservice for the research agent.

Supports multiple search APIs via the provider parameter. Normalized response shape.
- GET /health
- GET /search?q=...&provider=tavily&max_results=10
- POST /search  body: { "query": "...", "provider": "tavily", "max_results": 10 }

Config: SEARCH_HOST, SEARCH_PORT, TAVILY_API_KEY (and per-provider keys).
Loads .env from project root when run from services/search.
"""
import os
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    _root = Path(__file__).resolve().parent.parent.parent
    load_dotenv(_root / ".env")
except ImportError:
    pass

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel

from providers.registry import get_available_providers, get_provider, list_providers


@dataclass(frozen=True)
class SearchConfig:
    host: str
    port: int
    reload: bool
    tavily_api_key: Optional[str]

    @classmethod
    def from_env(cls) -> "SearchConfig":
        return cls(
            host=os.getenv("SEARCH_HOST", "127.0.0.1"),
            port=int(os.getenv("SEARCH_PORT", "8001")),
            reload=os.getenv("SEARCH_RELOAD", "").lower() in ("1", "true", "yes", "on"),
            tavily_api_key=os.getenv("TAVILY_API_KEY", "").strip() or None,
        )

    def validate(self) -> None:
        if not self.tavily_api_key:
            self._exit_with_error()

    def _exit_with_error(self) -> None:
        error_lines = [
            "",
            "=" * 80,
            "CONFIGURATION ERROR: Missing TAVILY_API_KEY",
            "=" * 80,
            "",
            "The search microservice requires a valid Tavily API key to function.",
            "",
            "Configuration:",
            "  1. Get an API key from https://tavily.com",
            "  2. Add it to your .env file in the project root:",
            "",
            "     TAVILY_API_KEY=tvly-your-api-key-here",
            "",
            f"  Expected .env location: {_root / '.env'}",
            "",
            "Current status:",
            f"  TAVILY_API_KEY: {'[SET]' if self.tavily_api_key else '[NOT SET]'}",
            "",
            "=" * 80,
            "",
        ]
        print("\n".join(error_lines), file=sys.stderr)
        sys.exit(1)


config = SearchConfig.from_env()


class SearchError(Exception):
    pass


class SearchBody(BaseModel):
    query: str
    provider: str = "tavily"
    max_results: int = 10
    include_answer: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    config.validate()
    available = get_available_providers()
    print(f"Search service starting with providers: {available}")
    if not available:
        print("WARNING: No search providers are available!", file=sys.stderr)
    yield


app = FastAPI(
    title="Research Agent – Web Search",
    description="Microservice for web search. Supports multiple providers (Tavily, etc.) with a unified API.",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "search", "providers_available": get_available_providers()}


@app.get("/providers")
async def providers():
    return {
        "all": list_providers(),
        "available": get_available_providers(),
    }


@app.get("/search")
async def search_get(
    q: str = Query(..., description="Search query"),
    provider: str = Query("tavily", description="Search provider to use"),
    max_results: int = Query(10, ge=1, le=20),
    include_answer: bool = Query(False, description="Include LLM answer (Tavily)"),
):
    return await _run_search(q, provider, max_results, include_answer)


@app.post("/search")
async def search_post(body: SearchBody):
    return await _run_search(
        body.query,
        body.provider,
        body.max_results,
        body.include_answer,
    )


async def _run_search(
    query: str,
    provider_name: str,
    max_results: int,
    include_answer: bool,
):
    prov = get_provider(provider_name)
    if not prov:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider: {provider_name}. Available: {list_providers()}",
        )
    if not prov.is_available():
        raise HTTPException(
            status_code=503,
            detail=f"Provider '{provider_name}' is not configured (missing API key?). Available: {get_available_providers()}",
        )
    try:
        response = await prov.search(
            query=query,
            max_results=max_results,
            include_answer=include_answer,
        )
        return JSONResponse(
            content=response.model_dump(mode="json"),
            status_code=200,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


def main() -> None:
    uvicorn.run(
        "search:app",
        host=config.host,
        port=config.port,
        reload=config.reload,
    )


if __name__ == "__main__":
    main()
