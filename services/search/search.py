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
from pathlib import Path

# Load project .env so TAVILY_API_KEY etc. are set when running from services/search
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


SEARCH_HOST = os.environ.get("SEARCH_HOST", "127.0.0.1")
SEARCH_PORT = int(os.environ.get("SEARCH_PORT", "8001"))

app = FastAPI(
    title="Research Agent – Web Search",
    description="Microservice for web search. Supports multiple providers (Tavily, etc.) with a unified API.",
)


class SearchBody(BaseModel):
    query: str
    provider: str = "tavily"
    max_results: int = 10
    include_answer: bool = False


@app.get("/health")
async def health():
    return {"status": "ok", "service": "search", "providers_available": get_available_providers()}


@app.get("/providers")
async def providers():
    """List all registered providers and which have valid config."""
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
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
        )


def main():
    uvicorn.run(
        "search:app",
        host=SEARCH_HOST,
        port=SEARCH_PORT,
        reload=os.environ.get("SEARCH_RELOAD", "").lower() in ("1", "true", "yes"),
    )


if __name__ == "__main__":
    main()
