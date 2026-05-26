"""Bright Data primary client: SERP API (Day 1 working) + MCP Server utilities (Day 2).

TODO(verify-endpoint): Before running, confirm your SERP zone name in the Bright Data
dashboard → Proxies & Scraping → SERP API → zone name. Common values: "serp_api",
"serp_api1". Set BRIGHT_DATA_SERP_ZONE in api/.env to match.

TODO(verify-response): Bright Data returns organic results under the "organic" key with
fields "title", "link", and "description". Verified against the API on 2026-05-25; re-check
if the response shape changes in a future Bright Data release.
"""

import httpx

from app.config import settings

_SERP_ENDPOINT = "https://api.brightdata.com/request"


async def search_serp(query: str, limit: int = 3) -> list[dict]:
    """Query Bright Data SERP API and return top organic search results.

    Args:
        query: Natural-language search query.
        limit: Maximum number of organic results to return.

    Returns:
        List of dicts with at minimum a "title" key. May also include "link" and
        "description" depending on Bright Data response version.

    Raises:
        httpx.HTTPStatusError: On 4xx/5xx from the API (401, 403, 407 are common).
        httpx.TimeoutException: If the request exceeds 30 seconds.
    """
    encoded = query.replace(" ", "+")
    # brd_json=1 instructs Bright Data to parse and return structured JSON instead of raw HTML
    search_url = f"https://www.google.com/search?q={encoded}&brd_json=1&num={limit}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            _SERP_ENDPOINT,
            headers={
                "Authorization": f"Bearer {settings.bright_data_api_token}",
                "Content-Type": "application/json",
            },
            json={
                "zone": settings.bright_data_serp_zone,
                "url": search_url,
                "format": "raw",
            },
        )
        response.raise_for_status()
        data = response.json()

    organic: list[dict] = data.get("organic", [])
    return organic[:limit]


async def mcp_health() -> dict:
    """Ping the Bright Data MCP Server to verify connectivity.

    MCP Server URL: https://mcp.brightdata.com/mcp?token=<API_TOKEN>
    Day 2: Replace with full MCP tool-call client using the MCP protocol.
    """
    mcp_url = f"{settings.bright_data_mcp_url}?token={settings.bright_data_api_token}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(mcp_url)
        return {"reachable": response.status_code < 500, "status_code": response.status_code}
