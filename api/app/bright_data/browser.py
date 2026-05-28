"""Bright Data Scraping Browser — full JS rendering via Playwright CDP.

Connection: wss://{BRIGHT_DATA_BROWSER_USER}:{BRIGHT_DATA_BROWSER_PASS}@brd.superproxy.io:9222

Expected .env values (from dashboard → Browser API zone → Access Parameters):
  BRIGHT_DATA_BROWSER_USER=brd-customer-<customer_id>-zone-<zone_name>
  BRIGHT_DATA_BROWSER_PASS=<zone_password>

Uses SYNCHRONOUS Playwright wrapped in asyncio.to_thread — this avoids the
Windows uvicorn loop-policy NotImplementedError that breaks async Playwright.
"""

import asyncio

from app.bright_data.base import BrightDataResponse, elapsed_ms, timer
from app.config import settings

_CDP_HOST = "brd.superproxy.io"
_CDP_PORT = 9222


def _cdp_url() -> str:
    return (
        f"wss://{settings.bright_data_browser_user}"
        f":{settings.bright_data_browser_pass}"
        f"@{_CDP_HOST}:{_CDP_PORT}"
    )


def _fetch_blocking(
    cdp_url: str,
    url: str,
    wait_for_selector: str | None,
    timeout_ms: int,
    screenshot_path: str | None,
) -> dict:
    """Synchronous Playwright fetch — runs in a thread via asyncio.to_thread."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(cdp_url, timeout=60_000)
        try:
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            if wait_for_selector:
                try:
                    page.wait_for_selector(wait_for_selector, timeout=min(timeout_ms, 15_000))
                except Exception:
                    pass
            content = page.content()
            if screenshot_path:
                page.screenshot(path=screenshot_path, full_page=True)
            return {"html": content, "length": len(content), "url": url}
        finally:
            browser.close()


async def fetch_rendered(
    url: str,
    wait_for_selector: str | None = None,
    screenshot_path: str | None = None,
    timeout_ms: int = 60_000,
) -> BrightDataResponse:
    """Navigate to `url` in the Scraping Browser and return the rendered HTML.

    Uses sync Playwright in a thread — safe on Windows uvicorn event loops.
    """
    if not settings.bright_data_browser_user or not settings.bright_data_browser_pass:
        return BrightDataResponse(
            status="error",
            product="scraping_browser",
            error=(
                "BRIGHT_DATA_BROWSER_USER and BRIGHT_DATA_BROWSER_PASS must be set. "
                "Find them in: Bright Data dashboard → Browser API zone → Access Parameters."
            ),
        )

    try:
        from playwright.sync_api import sync_playwright as _  # noqa: F401  # verify import
    except ImportError:
        return BrightDataResponse(
            status="error",
            product="scraping_browser",
            error="playwright not installed — run: uv add playwright && uv run playwright install chromium",
        )

    start = timer()
    try:
        data = await asyncio.to_thread(
            _fetch_blocking,
            _cdp_url(),
            url,
            wait_for_selector,
            timeout_ms,
            screenshot_path,
        )
        return BrightDataResponse(
            status="ok",
            product="scraping_browser",
            data=data,
            latency_ms=elapsed_ms(start),
        )
    except Exception as exc:
        return BrightDataResponse(
            status="error",
            product="scraping_browser",
            error=str(exc),
            latency_ms=elapsed_ms(start),
        )


async def screenshot(url: str, output_path: str) -> BrightDataResponse:
    """Take a full-page screenshot of `url`."""
    return await fetch_rendered(url, screenshot_path=output_path)
