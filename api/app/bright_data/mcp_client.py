"""Bright Data MCP Server — agentic navigation of the live web.

Transport: stdio via `npx @brightdata/mcp` (same transport Claude Desktop uses).
           This is the officially supported Python approach.

Available tools (from luminati-io/brightdata-mcp):
  search_engine(query, engine)        — SERP results in JSON/Markdown
  scrape_as_markdown(url)             — Any page as clean Markdown (bot-protected)
  scrape_as_html(url)                 — Any page as raw HTML
  search_engine_batch(queries)        — Up to 10 parallel searches
  scrape_batch(urls)                  — Up to 10 parallel page fetches
  web_data_<site>(url)                — 40+ structured extractors (LinkedIn, Crunchbase, etc.)
  scraping_browser_<action>(...)      — Click, type, navigate, screenshot

Prerequisites: Node.js 18+ (user has Node 24 ✓)
               npx fetches @brightdata/mcp on first call (~3s), cached after.

Used by: Researcher agent (multi-step agentic navigation, structured site extraction)
"""

import asyncio
import os

from app.bright_data.base import BrightDataResponse, elapsed_ms, timer
from app.config import settings

# Also re-export search_serp for /missions/hello backward compat.
from app.bright_data.serp import search_serp  # noqa: F401


def _server_params():
    """Build StdioServerParameters for the Bright Data MCP server."""
    from mcp.client.stdio import StdioServerParameters

    env = {
        **os.environ,
        "API_TOKEN": settings.bright_data_api_token,
        "PRO_MODE": "false",
    }
    return StdioServerParameters(
        command="npx",
        args=["-y", "@brightdata/mcp"],
        env=env,
    )


async def call_tool(tool_name: str, arguments: dict) -> BrightDataResponse:
    """Call any Bright Data MCP tool by name via stdio transport.

    Opens a subprocess running `npx @brightdata/mcp`, calls the tool,
    then closes the subprocess. For bulk research, use MCPSession context
    manager below to share one subprocess across many calls.

    Args:
        tool_name: e.g. "search_engine", "scrape_as_markdown", "web_data_linkedin_company_profile"
        arguments: Tool-specific dict, e.g. {"query": "Wix.com funding", "engine": "google"}
    """
    if not settings.bright_data_api_token:
        return BrightDataResponse(
            status="error",
            product="mcp_server",
            error="BRIGHT_DATA_API_TOKEN not set in api/.env",
        )

    try:
        from mcp import ClientSession
        from mcp.client.stdio import stdio_client
    except ImportError:
        return BrightDataResponse(
            status="error",
            product="mcp_server",
            error="mcp package not installed — run: uv add mcp",
        )

    start = timer()
    try:
        async with stdio_client(_server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                ms = elapsed_ms(start)

                text_parts = [
                    c.text
                    for c in (result.content or [])
                    if hasattr(c, "text") and c.text
                ]
                combined = "\n".join(text_parts)

                return BrightDataResponse(
                    status="ok",
                    product="mcp_server",
                    data={"tool": tool_name, "result": combined},
                    latency_ms=ms,
                )
    except Exception as exc:
        return BrightDataResponse(
            status="error",
            product="mcp_server",
            error=str(exc),
            latency_ms=elapsed_ms(start),
        )


class MCPSession:
    """Persistent MCP subprocess — reuse across many tool calls in one mission.

    Usage:
        async with MCPSession() as mcp:
            r1 = await mcp.call("search_engine", {"query": "..."})
            r2 = await mcp.call("scrape_as_markdown", {"url": "..."})
    """

    def __init__(self):
        self._ctx = None
        self._session = None

    async def __aenter__(self):
        from mcp import ClientSession
        from mcp.client.stdio import stdio_client

        self._stdio_ctx = stdio_client(_server_params())
        self._read, self._write = await self._stdio_ctx.__aenter__()
        self._session_ctx = ClientSession(self._read, self._write)
        self._session = await self._session_ctx.__aenter__()
        await self._session.initialize()
        return self

    async def __aexit__(self, *args):
        if self._session_ctx:
            await self._session_ctx.__aexit__(*args)
        if self._stdio_ctx:
            await self._stdio_ctx.__aexit__(*args)

    async def call(self, tool_name: str, arguments: dict) -> BrightDataResponse:
        start = timer()
        try:
            result = await self._session.call_tool(tool_name, arguments)
            ms = elapsed_ms(start)
            text_parts = [
                c.text
                for c in (result.content or [])
                if hasattr(c, "text") and c.text
            ]
            return BrightDataResponse(
                status="ok",
                product="mcp_server",
                data={"tool": tool_name, "result": "\n".join(text_parts)},
                latency_ms=ms,
            )
        except Exception as exc:
            return BrightDataResponse(
                status="error",
                product="mcp_server",
                error=str(exc),
                latency_ms=elapsed_ms(start),
            )


# ── Convenience wrappers ──────────────────────────────────────────────────────

async def search(query: str, engine: str = "google") -> BrightDataResponse:
    return await call_tool("search_engine", {"query": query, "engine": engine})


async def scrape_markdown(url: str) -> BrightDataResponse:
    return await call_tool("scrape_as_markdown", {"url": url})


async def scrape_html(url: str) -> BrightDataResponse:
    return await call_tool("scrape_as_html", {"url": url})


async def web_data(site: str, url: str) -> BrightDataResponse:
    """Call a structured web_data_<site> extractor.

    Args:
        site: e.g. "linkedin_company_profile", "crunchbase_company", "g2_product"
        url:  Target URL for the extractor.
    """
    return await call_tool(f"web_data_{site}", {"url": url})
