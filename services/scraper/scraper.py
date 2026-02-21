"""
Scraper microservice for the research agent.

Fetches documents from the web via Playwright (JS support + stealth), exposes:
- GET /health       – health check
- GET /fetch        – raw HTML as JSON
- GET /fetch_raw    – raw HTML as text/html
- GET /fetch_content?url=...&text_only=false – cleaned HTML or plain text

Config: SCRAPER_HOST, SCRAPER_PORT, SCRAPER_FETCH_TIMEOUT_MS, SCRAPER_RELOAD
"""
import argparse
import asyncio
import ipaddress
import os
import random
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, Response
import uvicorn
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.2478.67",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]

# Config (env overrides for container/deployment)
SCRAPER_HOST = os.environ.get("SCRAPER_HOST", "127.0.0.1")
SCRAPER_PORT = int(os.environ.get("SCRAPER_PORT", "8000"))
FETCH_TIMEOUT_MS = int(os.environ.get("SCRAPER_FETCH_TIMEOUT_MS", "15000"))
ALLOW_PRIVATE_NETWORK = os.environ.get("SCRAPER_ALLOW_PRIVATE_NETWORK", "").strip().lower() in ("1", "true", "yes", "on")

app = FastAPI(title="Research Agent – Scraper", description="Microservice to fetch documents from the web.")


def _is_private_or_local_host(host: str) -> bool:
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


def _validate_url(url: str) -> None:
    parsed = urlparse((url or "").strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("unsupported URL scheme")
    if not parsed.hostname:
        raise ValueError("invalid URL")
    if not ALLOW_PRIVATE_NETWORK and _is_private_or_local_host(parsed.hostname):
        raise ValueError("private/local network URLs are not allowed")

async def _fetch(url: str) -> str:
    stealth = Stealth( init_scripts_only=True  )
    pw = await async_playwright().start()
    try:
        browser = await pw.chromium.launch(
            headless=True,  # set False if you want to see the browser
            args=["--disable-http2", "--disable-features=NetworkService", "--disable‑blink-features=AutomationControlled"],
        )

        user_agent = random.choice(USER_AGENTS)
        context = await browser.new_context(user_agent=user_agent)
        await context.clear_cookies()
        await stealth.apply_stealth_async(context)

        page = await context.new_page()
        #response = await page.goto(url, timeout=FETCH_TIMEOUT_MS, wait_until="domcontentloaded")

        try:
            await page.goto(url, wait_until="commit", timeout=FETCH_TIMEOUT_MS)
        except:
            pass

        try:
            await page.wait_for_load_state("domcontentloaded", timeout=3000)
        except:
            pass

        """
        if response is None:
            raise ValueError("navigation failed: empty response")
        """
        content = await page.content()
        await browser.close()
        return content
    finally:
        await pw.stop()

def _extract_content(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")

    # Prefer to work with <body> if it exists; otherwise, use the whole soup
    body = soup.body or soup

    # Remove all <script> and <style> elements
    for element in body(["script", "style", "svg"]):
        element.decompose()

    # Strip attributes except 'href'
    for tag in body.find_all():
        tag.attrs = {}

    cleaned_html = str(body)
    return cleaned_html


def _html_to_plain_text(html_content: str) -> str:
    """Extract readable plain text from HTML for LLM consumption."""
    soup = BeautifulSoup(html_content, "html.parser")
    body = soup.body or soup
    for element in body(["script", "style", "svg"]):
        element.decompose()
    text = body.get_text(separator="\n", strip=True)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


@app.get("/health")
async def health():
    """Health check for orchestration and load balancers."""
    return {"status": "ok", "service": "scraper"}


@app.get("/fetch_raw")
async def fetch_raw(url: str = Query(..., description="The URL to scrape")):
    try:
        _validate_url(url)
        html = await _fetch(url)
        return Response(content=html, media_type="text/html")
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/fetch")
async def fetch(url: str = Query(..., description="The URL to scrape")):
    try:
        _validate_url(url)
        html = await _fetch(url)
        return JSONResponse(content={"url": url, "content": html}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/fetch_content")
async def fetch_content(
    url: str = Query(..., description="The URL to scrape"),
    text_only: bool = Query(False, description="Return plain text only (for LLM consumption)"),
):
    try:
        _validate_url(url)
        html = await _fetch(url)
        cleaned = _extract_content(html)
        content = _html_to_plain_text(cleaned) if text_only else cleaned
        return JSONResponse(
            content={"url": url, "content": content, "format": "text" if text_only else "html"},
            status_code=200,
        )
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


async def command_line_scrape(url: str, function: str):
    if not url:
        print("URL is required.")
        return

    html = await _fetch(url)
    if function == "fetch":
        print(html)
    elif function == "fetch_content":
        print(_extract_content(html))
    elif function == "fetch_raw":
        print(html)
    else:
        print(f"Unknown function: {function}")

def parse_arguments():
    parser = argparse.ArgumentParser(description="WebScraper API")
    parser.add_argument("url", nargs='?', default=None, help="The URL to scrape")
    parser.add_argument("function", nargs='?', choices=['fetch', 'fetch_content', 'fetch_raw'], default=None, help="Function to run when scraping")

    return parser.parse_args()

def main():
    args = parse_arguments()

    if args.url and args.function:
        asyncio.run(command_line_scrape(args.url, args.function))
    else:
        uvicorn.run(
            "scraper:app",
            host=SCRAPER_HOST,
            port=SCRAPER_PORT,
            reload=os.environ.get("SCRAPER_RELOAD", "").lower() in ("1", "true", "yes"),
        )

if __name__ == "__main__":
    main()
