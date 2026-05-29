"""Bright Data Web Unlocker — bypass bot detection, CAPTCHAs, and geo-blocks.

Endpoint: POST https://api.brightdata.com/request
Zone:     BRIGHT_DATA_UNLOCKER_ZONE
Returns:  raw HTML of the target page with bot protection bypassed.

Used by: Researcher agent
When:    Target URL blocks datacenter IPs, shows CAPTCHAs, or is geo-restricted.
"""

import logging

from markdownify import markdownify

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


async def unlock(url: str, country: str = "us") -> BrightDataResponse:
    """Fetch `url` through Web Unlocker. Returns HTML and character count."""
    start = timer()
    try:
        async with new_client(timeout=90.0) as client:
            resp = await client.post(
                _ENDPOINT,
                headers=auth_headers(),
                json={
                    "zone": settings.bright_data_unlocker_zone,
                    "url": url,
                    "format": "raw",
                    "country": country,
                },
            )
            ms = elapsed_ms(start)
            body = resp.text

            log.warning(
                "brightdata.raw product=web_unlocker tool=unlocker_fetch status_code=%d latency_ms=%d body_first_500=%r",
                resp.status_code, ms, body[:500],
            )

            if resp.status_code >= 400:
                return BrightDataResponse(
                    status="failed",
                    product="web_unlocker",
                    error=f"HTTP {resp.status_code}: {body[:300]}",
                    latency_ms=ms,
                )

            # Check for JSON error envelope (HTTP 200 with error body).
            if body.lstrip().startswith("{"):
                try:
                    import json
                    parsed = json.loads(body)
                    if "error" in parsed:
                        return BrightDataResponse(
                            status="failed",
                            product="web_unlocker",
                            error=f"API error: {parsed['error']}",
                            latency_ms=ms,
                        )
                except Exception:
                    pass  # not JSON — treat as HTML

            if len(body) < 200:
                return BrightDataResponse(
                    status="empty",
                    product="web_unlocker",
                    error=f"Response too short ({len(body)} chars): {body[:300]}",
                    latency_ms=ms,
                )

            return BrightDataResponse(
                status="ok",
                product="web_unlocker",
                data={"html": body, "length": len(body), "url": url},
                latency_ms=ms,
            )
    except Exception as exc:
        import httpx
        err = str(exc)
        if isinstance(exc, httpx.HTTPStatusError):
            err = f"HTTP {exc.response.status_code}: {exc.response.text[:300]}"
        return BrightDataResponse(
            status="failed",
            product="web_unlocker",
            error=err,
            latency_ms=elapsed_ms(start),
        )


async def unlock_as_markdown(url: str, country: str = "us") -> BrightDataResponse:
    """Unlock and convert HTML to clean Markdown — ideal for LLM consumption."""
    result = await unlock(url, country=country)
    if not result.ok or not isinstance(result.data, dict):
        return result
    html = result.data.get("html", "")
    md = markdownify(html, heading_style="ATX", strip=["script", "style"])
    md = "\n".join(line for line in md.splitlines() if line.strip())
    return BrightDataResponse(
        status="ok",
        product="web_unlocker",
        data={"markdown": md, "length": len(md), "url": url},
        latency_ms=result.latency_ms,
    )
