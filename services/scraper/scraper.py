"""
Scraper microservice for the research agent.

Fetches documents from the web via Playwright (JS support + stealth), exposes:
- GET /health       – health check
- GET /fetch        – raw HTML as JSON
- GET /fetch_raw    – raw HTML as text/html
- GET /fetch_content?url=...&text_only=false – cleaned HTML or plain text

Config: SCRAPER_HOST, SCRAPER_PORT, SCRAPER_FETCH_TIMEOUT_MS,
        SCRAPER_NETWORK_IDLE_TIMEOUT_MS, SCRAPER_ALLOW_PRIVATE_NETWORK,
        SCRAPER_ENABLE_LAZY_LOAD, SCRAPER_MAX_SCROLL_ATTEMPTS
"""
import argparse
import asyncio
import ipaddress
import logging
import os
import random
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse, Response
import uvicorn
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout


def setup_logging() -> None:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"scraper_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers = [
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]


setup_logging()
logger = logging.getLogger(__name__)


class WaitStrategy(str, Enum):
    COMMIT = "commit"
    DOMCONTENTLOADED = "domcontentloaded"
    LOAD = "load"
    NETWORKIDLE = "networkidle"


@dataclass(frozen=True)
class ScraperConfig:
    host: str
    port: int
    fetch_timeout_ms: int
    network_idle_timeout_ms: int
    allow_private_network: bool
    enable_lazy_load: bool
    max_scroll_attempts: int
    reload: bool

    @classmethod
    def from_env(cls) -> "ScraperConfig":
        return cls(
            host=os.getenv("SCRAPER_HOST", "127.0.0.1"),
            port=int(os.getenv("SCRAPER_PORT", "8000")),
            fetch_timeout_ms=int(os.getenv("SCRAPER_FETCH_TIMEOUT_MS", "15000")),
            network_idle_timeout_ms=int(os.getenv("SCRAPER_NETWORK_IDLE_TIMEOUT_MS", "5000")),
            allow_private_network=os.getenv("SCRAPER_ALLOW_PRIVATE_NETWORK", "").lower() in ("1", "true", "yes", "on"),
            enable_lazy_load=os.getenv("SCRAPER_ENABLE_LAZY_LOAD", "true").lower() in ("1", "true", "yes", "on"),
            max_scroll_attempts=int(os.getenv("SCRAPER_MAX_SCROLL_ATTEMPTS", "3")),
            reload=os.getenv("SCRAPER_RELOAD", "").lower() in ("1", "true", "yes", "on"),
        )


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.2478.67",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]

config = ScraperConfig.from_env()
browser_instance: Optional[Browser] = None


class URLValidationError(ValueError):
    pass


class FetchError(Exception):
    pass


def is_private_or_local_host(host: str) -> bool:
    host = (host or "").strip().lower()
    if not host:
        return True
    if host in {"localhost"} or host.endswith(".localhost"):
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast


def validate_url(url: str) -> None:
    parsed = urlparse((url or "").strip())
    if parsed.scheme not in {"http", "https"}:
        raise URLValidationError("unsupported URL scheme")
    if not parsed.hostname:
        raise URLValidationError("invalid URL")
    if not config.allow_private_network and is_private_or_local_host(parsed.hostname):
        raise URLValidationError("private/local network URLs are not allowed")


async def get_browser() -> Browser:
    global browser_instance
    if browser_instance is None or not browser_instance.is_connected():
        from playwright_stealth import Stealth
        pw = await async_playwright().start()
        browser_instance = await pw.chromium.launch(
            headless=True,
            args=[
                "--disable-http2",
                "--disable-features=NetworkService",
                "--disable-blink-features=AutomationControlled"
            ],
        )
    return browser_instance


async def handle_lazy_loading(page: Page) -> None:
    if not config.enable_lazy_load:
        return

    previous_height = await page.evaluate("document.body.scrollHeight")

    for attempt in range(config.max_scroll_attempts):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(0.5)

        current_height = await page.evaluate("document.body.scrollHeight")
        if current_height == previous_height:
            break
        previous_height = current_height


async def wait_for_page_ready(page: Page, url: str) -> None:
    try:
        await page.goto(url, wait_until=WaitStrategy.COMMIT, timeout=config.fetch_timeout_ms)
    except PlaywrightTimeout as e:
        raise FetchError(f"navigation timeout after {config.fetch_timeout_ms}ms") from e
    except Exception as e:
        raise FetchError(f"navigation failed: {str(e)}") from e

    try:
        await page.wait_for_load_state(WaitStrategy.DOMCONTENTLOADED, timeout=3000)
    except PlaywrightTimeout:
        pass

    try:
        await page.wait_for_load_state(WaitStrategy.NETWORKIDLE, timeout=config.network_idle_timeout_ms)
    except PlaywrightTimeout:
        pass


async def fetch_html(url: str) -> str:
    from playwright_stealth import Stealth

    browser = await get_browser()
    user_agent = random.choice(USER_AGENTS)

    context = await browser.new_context(user_agent=user_agent)
    try:
        await context.clear_cookies()
        stealth = Stealth(init_scripts_only=True)
        await stealth.apply_stealth_async(context)

        page = await context.new_page()
        try:
            await wait_for_page_ready(page, url)
            await handle_lazy_loading(page)
            content = await page.content()
            return content
        finally:
            await page.close()
    finally:
        await context.close()


def extract_content(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    body = soup.body or soup

    for element in body(["script", "style"]):
        element.decompose()

    for tag in body.find_all():
        preserved_attrs = {}
        if tag.name == "a" and tag.get("href"):
            preserved_attrs["href"] = tag["href"]
        if tag.get("alt"):
            preserved_attrs["alt"] = tag["alt"]
        if tag.get("title"):
            preserved_attrs["title"] = tag["title"]
        tag.attrs = preserved_attrs

    return str(body)


def html_to_plain_text(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    body = soup.body or soup

    for element in body(["script", "style"]):
        element.decompose()

    text = body.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    global browser_instance
    if browser_instance and browser_instance.is_connected():
        await browser_instance.close()


app = FastAPI(
    title="Research Agent – Scraper",
    description="Microservice to fetch documents from the web.",
    lifespan=lifespan
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "scraper"}


@app.get("/fetch_raw")
async def fetch_raw(url: str = Query(..., description="The URL to scrape")):
    logger.info(f"GET /fetch_raw - URL: {url}")
    try:
        validate_url(url)
        html = await fetch_html(url)
        logger.info(f"Successfully fetched {len(html)} bytes from {url}")
        return Response(content=html, media_type="text/html")
    except URLValidationError as e:
        logger.warning(f"URL validation failed for {url}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except FetchError as e:
        logger.error(f"Fetch error for {url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error for {url}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"unexpected error: {str(e)}")


@app.get("/fetch")
async def fetch(url: str = Query(..., description="The URL to scrape")):
    logger.info(f"GET /fetch - URL: {url}")
    try:
        validate_url(url)
        html = await fetch_html(url)
        logger.info(f"Successfully fetched {len(html)} bytes from {url}")
        return JSONResponse(content={"url": url, "content": html}, status_code=200)
    except URLValidationError as e:
        logger.warning(f"URL validation failed for {url}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except FetchError as e:
        logger.error(f"Fetch error for {url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error for {url}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"unexpected error: {str(e)}")


@app.get("/fetch_content")
async def fetch_content(
    url: str = Query(..., description="The URL to scrape"),
    text_only: bool = Query(False, description="Return plain text only (for LLM consumption)"),
):
    logger.info(f"GET /fetch_content - URL: {url}, text_only: {text_only}")
    try:
        validate_url(url)
        html = await fetch_html(url)
        cleaned = extract_content(html)
        content = html_to_plain_text(cleaned) if text_only else cleaned
        logger.info(f"Successfully processed {len(content)} chars from {url} (format: {'text' if text_only else 'html'})")
        return JSONResponse(
            content={"url": url, "content": content, "format": "text" if text_only else "html"},
            status_code=200,
        )
    except URLValidationError as e:
        logger.warning(f"URL validation failed for {url}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except FetchError as e:
        logger.error(f"Fetch error for {url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error for {url}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"unexpected error: {str(e)}")


async def command_line_scrape(url: str, function: str) -> None:
    if not url:
        print("URL is required.")
        return

    try:
        html = await fetch_html(url)
        if function == "fetch":
            print(html)
        elif function == "fetch_content":
            print(extract_content(html))
        elif function == "fetch_raw":
            print(html)
        else:
            print(f"Unknown function: {function}")
    except Exception as e:
        print(f"Error: {str(e)}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WebScraper API")
    parser.add_argument("url", nargs='?', default=None, help="The URL to scrape")
    parser.add_argument(
        "function",
        nargs='?',
        choices=['fetch', 'fetch_content', 'fetch_raw'],
        default=None,
        help="Function to run when scraping"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    if args.url and args.function:
        asyncio.run(command_line_scrape(args.url, args.function))
    else:
        uvicorn.run(
            "scraper:app",
            host=config.host,
            port=config.port,
            reload=config.reload,
        )


if __name__ == "__main__":
    main()
