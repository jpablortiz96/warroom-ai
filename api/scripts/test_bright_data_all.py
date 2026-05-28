"""Validate all 5 Bright Data products are reachable.

Run from api/ directory:
    uv run python scripts/test_bright_data_all.py

Expected output:
    SERP API ............ ✓ 1240ms  (10 results)
    Web Unlocker ........ ✓  890ms  (12480 chars)
    Web Scraper API ..... ✓ 4500ms  (snapshot ready, N rows)
    Scraping Browser .... ✓ 2100ms  (rendered, 28450 chars)
    MCP Server .......... ✓  650ms  (tool: search_engine)
"""

import asyncio
import sys
import os

# Allow running from api/ directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main():
    from app.bright_data import serp, unlocker, scraper_api, browser, mcp_client
    from app.config import settings

    LINE = 60
    TICK = "✓"
    CROSS = "✗"

    def row(name: str, ok: bool, detail: str, ms: int) -> str:
        icon = TICK if ok else CROSS
        color = "\033[32m" if ok else "\033[31m"
        reset = "\033[0m"
        label = f"{name} ".ljust(24, ".")
        return f"  {color}{icon}{reset} {label} {ms:>5}ms  {detail}"

    print("\n  War Room AI — Bright Data Integration Check")
    print("  " + "─" * LINE)

    # ── 1. SERP API ───────────────────────────────────────────────────────────
    result = await serp.search("War Room AI hackathon 2026", limit=5)
    n = len(result.data) if isinstance(result.data, list) else 0
    detail = f"{n} results" if result.ok else f"ERR: {result.error}"
    print(row("SERP API", result.ok, detail, result.latency_ms))

    # ── 2. Web Unlocker ───────────────────────────────────────────────────────
    result = await unlocker.unlock("https://example.com", country="us")
    chars = result.data.get("length", 0) if result.ok else 0
    detail = f"{chars:,} chars" if result.ok else f"ERR: {result.error}"
    print(row("Web Unlocker", result.ok, detail, result.latency_ms))

    # ── 3. Web Scraper API ────────────────────────────────────────────────────
    dataset_id = settings.bright_data_scraper_dataset_id
    if not dataset_id:
        print(row("Web Scraper API", False, "SKIP: BRIGHT_DATA_SCRAPER_DATASET_ID not set", 0))
    else:
        result = await scraper_api.collect_and_wait(
            dataset_id,
            [{"url": "https://www.linkedin.com/in/satya-nadella/"}],
            max_wait_seconds=90,
        )
        if result.ok:
            n_rows = len(result.data) if isinstance(result.data, list) else 1
            detail = f"snapshot ready, {n_rows} row(s)"
        else:
            detail = f"ERR: {result.error}"
        print(row("Web Scraper API", result.ok, detail, result.latency_ms))

    # ── 4. Scraping Browser ───────────────────────────────────────────────────
    if not settings.bright_data_browser_user or not settings.bright_data_browser_pass:
        print(row("Scraping Browser", False, "SKIP: BROWSER_USER / BROWSER_PASS not set", 0))
    else:
        result = await browser.fetch_rendered("https://example.com")
        chars = result.data.get("length", 0) if result.ok else 0
        detail = f"rendered, {chars:,} chars" if result.ok else f"ERR: {result.error}"
        print(row("Scraping Browser", result.ok, detail, result.latency_ms))

    # ── 5. MCP Server ─────────────────────────────────────────────────────────
    result = await mcp_client.search("Bright Data web scraping 2026")
    if result.ok:
        tool = result.data.get("tool", "search_engine")
        chars = len(result.data.get("result", ""))
        detail = f"tool: {tool}, {chars} chars"
    else:
        detail = f"ERR: {result.error}"
    print(row("MCP Server", result.ok, detail, result.latency_ms))

    print("  " + "─" * LINE)
    print()


if __name__ == "__main__":
    asyncio.run(main())
