"""Bright Data Web Unlocker — bypass bot detection, CAPTCHAs, and geo-blocks.

Endpoint: POST https://api.brightdata.com/request
Zone:     BRIGHT_DATA_UNLOCKER_ZONE
Returns:  raw HTML of the target page with bot protection bypassed.

Used by: Researcher agent
When:    Target URL blocks datacenter IPs, shows CAPTCHAs, or is geo-restricted.
"""

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
            resp.raise_for_status()
            html = resp.text
            return BrightDataResponse(
                status="ok",
                product="web_unlocker",
                data={"html": html, "length": len(html), "url": url},
                latency_ms=ms,
            )
    except Exception as exc:
        import httpx
        err = str(exc)
        if isinstance(exc, httpx.HTTPStatusError):
            err = f"HTTP {exc.response.status_code}: {exc.response.text[:300]}"
        return BrightDataResponse(
            status="error",
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
    # Collapse excessive whitespace
    md = "\n".join(line for line in md.splitlines() if line.strip())
    return BrightDataResponse(
        status="ok",
        product="web_unlocker",
        data={"markdown": md, "length": len(md), "url": url},
        latency_ms=result.latency_ms,
    )
