"""Bright Data SERP API — cross-engine signal discovery.

Endpoint: POST https://api.brightdata.com/request
Zone:     BRIGHT_DATA_SERP_ZONE
Trigger:  brd_json=1 in the Google/Bing URL → returns structured JSON
Response: {"organic": [{"title": "...", "link": "...", "description": "..."}, ...]}
"""

import logging
import urllib.parse

from app.bright_data.base import (
    BrightDataResponse,
    auth_headers,
    elapsed_ms,
    new_client,
    timer,
)
from app.config import settings

_ENDPOINT = "https://api.brightdata.com/request"
log = logging.getLogger("brightdata")


def _classify_serp(resp_status: int, body: str, data: dict, product: str, ms: int, limit: int) -> BrightDataResponse:
    """Classify a SERP response into ok / empty / failed."""
    log.warning(
        "brightdata.raw product=%s status_code=%d latency_ms=%d body_first_500=%r",
        product, resp_status, ms, body[:500],
    )

    # Body-level error field beats HTTP 200.
    if "error" in data:
        return BrightDataResponse(
            status="failed",
            product=product,
            error=f"API error: {data['error']}",
            latency_ms=ms,
        )

    return None  # caller handles ok/empty


async def search(
    query: str,
    country: str = "us",
    engine: str = "google",
    limit: int = 10,
) -> BrightDataResponse:
    """Search for `query` via the SERP API. Returns organic results."""
    encoded = urllib.parse.quote_plus(query)
    if engine == "google":
        search_url = (
            f"https://www.google.com/search"
            f"?q={encoded}&brd_json=1&num={limit}&gl={country}&hl=en"
        )
    else:
        search_url = f"https://www.bing.com/search?q={encoded}&count={limit}"

    start = timer()
    try:
        async with new_client() as client:
            resp = await client.post(
                _ENDPOINT,
                headers=auth_headers(),
                json={
                    "zone": settings.bright_data_serp_zone,
                    "url": search_url,
                    "format": "raw",
                },
            )
            ms = elapsed_ms(start)
            body = resp.text

            log.warning(
                "brightdata.raw product=serp_api tool=serp_search status_code=%d latency_ms=%d body_first_500=%r",
                resp.status_code, ms, body[:500],
            )

            if resp.status_code >= 400:
                return BrightDataResponse(
                    status="failed",
                    product="serp_api",
                    error=f"HTTP {resp.status_code}: {body[:300]}",
                    latency_ms=ms,
                )

            data = resp.json()

            if "error" in data:
                return BrightDataResponse(
                    status="failed",
                    product="serp_api",
                    error=f"API error: {data['error']}",
                    latency_ms=ms,
                )

            organic: list[dict] = data.get("organic", [])
            if not organic:
                return BrightDataResponse(
                    status="empty",
                    product="serp_api",
                    error=f"No organic results. Full body: {body[:300]}",
                    latency_ms=ms,
                )

            return BrightDataResponse(
                status="ok",
                product="serp_api",
                data=organic[:limit],
                latency_ms=ms,
            )
    except Exception as exc:
        import httpx
        err = str(exc)
        if isinstance(exc, httpx.HTTPStatusError):
            err = f"HTTP {exc.response.status_code}: {exc.response.text[:300]}"
        return BrightDataResponse(
            status="failed",
            product="serp_api",
            error=err,
            latency_ms=elapsed_ms(start),
        )


async def search_news(query: str, limit: int = 10) -> BrightDataResponse:
    """Search Google News for recent coverage."""
    encoded = urllib.parse.quote_plus(query)
    news_url = (
        f"https://www.google.com/search"
        f"?q={encoded}&tbm=nws&brd_json=1&num={limit}&hl=en"
    )
    start = timer()
    try:
        async with new_client() as client:
            resp = await client.post(
                _ENDPOINT,
                headers=auth_headers(),
                json={
                    "zone": settings.bright_data_serp_zone,
                    "url": news_url,
                    "format": "raw",
                },
            )
            ms = elapsed_ms(start)
            body = resp.text

            log.warning(
                "brightdata.raw product=serp_api tool=serp_news status_code=%d latency_ms=%d body_first_500=%r",
                resp.status_code, ms, body[:500],
            )

            if resp.status_code >= 400:
                return BrightDataResponse(
                    status="failed",
                    product="serp_api",
                    error=f"HTTP {resp.status_code}: {body[:300]}",
                    latency_ms=ms,
                )

            data = resp.json()

            if "error" in data:
                return BrightDataResponse(
                    status="failed",
                    product="serp_api",
                    error=f"API error: {data['error']}",
                    latency_ms=ms,
                )

            news = data.get("news", data.get("organic", []))
            if not news:
                return BrightDataResponse(
                    status="empty",
                    product="serp_api",
                    error=f"No news results. Full body: {body[:300]}",
                    latency_ms=ms,
                )

            return BrightDataResponse(
                status="ok",
                product="serp_api",
                data=news[:limit],
                latency_ms=ms,
            )
    except Exception as exc:
        return BrightDataResponse(
            status="failed",
            product="serp_api",
            error=str(exc),
            latency_ms=elapsed_ms(start),
        )


# ── Backward compat for /missions/hello ──────────────────────────────────────

async def search_serp(query: str, limit: int = 3) -> list[dict]:
    result = await search(query, limit=limit)
    if result.ok and isinstance(result.data, list):
        return result.data[:limit]
    return []
