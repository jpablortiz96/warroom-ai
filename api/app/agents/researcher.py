"""Researcher — executes research plan via Bright Data tools, all steps in parallel."""

import asyncio
import logging
import time

from app.agents import events as ev
from app.agents.state import AgentEvent, BDCall, MissionState, ResearchStep
from app.bright_data import browser, mcp_client, scraper_api, serp, unlocker
from app.config import settings

log = logging.getLogger(__name__)

_PRODUCT_MAP: dict[str, str] = {
    "serp_search": "serp_api",
    "serp_news": "serp_api",
    "mcp_search": "mcp_server",
    "mcp_scrape": "mcp_server",
    "unlocker_fetch": "web_unlocker",
    "scraper_linkedin": "web_scraper_api",
    "browser_render": "scraping_browser",
}

# Per-product timeout budgets (seconds).
_PRODUCT_TIMEOUT: dict[str, float] = {
    "serp_api": 15.0,
    "mcp_server": 15.0,
    "web_unlocker": 30.0,
    "web_scraper_api": 45.0,
    "scraping_browser": 35.0,
}

# Products that get one retry on timeout (60% of original budget, after 1s pause).
_RETRY_PRODUCTS = {"web_unlocker", "scraping_browser"}
_RETRY_DELAY = 1.0
_RETRY_TIMEOUT_FACTOR = 0.6


def _fmt_serp(results: list[dict]) -> str:
    lines = []
    for x in results[:5]:
        title = x.get("title", "")
        desc = x.get("description", "") or x.get("snippet", "")
        url = x.get("url", "") or x.get("link", "")
        lines.append(f"**{title}**\n{desc}\n{url}")
    return "\n\n".join(lines)


async def _execute(step: ResearchStep) -> tuple[str, BDCall]:
    """Execute one Bright Data step; handles all errors internally."""
    tool = step["tool"]
    q = step["query_or_url"]
    latency_ms = 0
    result_text: str | None = None

    try:
        if tool == "serp_search":
            r = await serp.search(q)
            latency_ms = r.latency_ms
            if r.ok and isinstance(r.data, list):
                result_text = _fmt_serp(r.data)

        elif tool == "serp_news":
            r = await serp.search_news(q)
            latency_ms = r.latency_ms
            if r.ok and isinstance(r.data, list):
                result_text = _fmt_serp(r.data)

        elif tool == "mcp_search":
            r = await mcp_client.search(q)
            latency_ms = r.latency_ms
            if r.ok:
                result_text = r.data.get("result", "")

        elif tool == "mcp_scrape":
            r = await mcp_client.scrape_markdown(q)
            latency_ms = r.latency_ms
            if r.ok:
                result_text = r.data.get("result", "")[:4000]

        elif tool == "unlocker_fetch":
            r = await unlocker.unlock_as_markdown(q)
            latency_ms = r.latency_ms
            if r.ok:
                result_text = r.data.get("markdown", "")[:4000]

        elif tool == "scraper_linkedin":
            dataset_id = settings.bright_data_scraper_dataset_id
            if not dataset_id:
                result_text = "[LinkedIn scraper skipped: BRIGHT_DATA_SCRAPER_DATASET_ID not set]"
            else:
                r = await scraper_api.collect_and_wait(dataset_id, [{"url": q}])
                latency_ms = r.latency_ms
                if r.ok:
                    result_text = str(r.data)[:3000]

        elif tool == "browser_render":
            r = await browser.fetch_rendered(q)
            latency_ms = r.latency_ms
            if r.ok:
                from markdownify import markdownify as _md
                html = r.data.get("html", "")
                md = _md(html, heading_style="ATX", strip=["script", "style"])
                result_text = "\n".join(ln for ln in md.splitlines() if ln.strip())[:4000]

        else:
            result_text = f"[Unknown tool: {tool}]"

    except Exception as exc:
        result_text = f"[Error in {tool}: {exc}]"

    ok = bool(result_text and len(result_text.strip()) > 10)
    product = _PRODUCT_MAP.get(tool, "unknown")

    if not result_text or len(result_text.strip()) <= 10:
        bd_status = "empty"
    elif ok:
        bd_status = "ok"
    else:
        bd_status = "failed"

    bd_call: BDCall = {
        "product": product,
        "tool": tool,
        "query_or_url": q,
        "latency_ms": latency_ms,
        "ok": ok,
        "status": bd_status,
    }
    return result_text or f"[No data retrieved for: {q}]", bd_call


async def _attempt_with_retry(
    step: ResearchStep, product: str, base_timeout: float
) -> tuple[str, BDCall]:
    """Try once; retry eligible products once more at 60% timeout on TimeoutError."""
    async def _once(timeout: float) -> tuple[str, BDCall] | None:
        try:
            return await asyncio.wait_for(_execute(step), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    result = await _once(base_timeout)
    if result is not None:
        return result

    # First attempt timed out — retry eligible products.
    if product in _RETRY_PRODUCTS:
        log.warning(
            "Step %d (%s) timed out after %.0fs — retrying at %.0fs",
            step["step"], step["tool"], base_timeout, base_timeout * _RETRY_TIMEOUT_FACTOR,
        )
        await asyncio.sleep(_RETRY_DELAY)
        result = await _once(base_timeout * _RETRY_TIMEOUT_FACTOR)
        if result is not None:
            return result

    # Definitive timeout — build a timeout BDCall.
    timeout_bd_call: BDCall = {
        "product": product,
        "tool": step["tool"],
        "query_or_url": step["query_or_url"],
        "latency_ms": int(base_timeout * 1000),
        "ok": False,
        "status": "timeout",
    }
    return f"[{step['tool']} timed out after {base_timeout:.0f}s — skipped]", timeout_bd_call


async def _run_step(step: ResearchStep, mission_id: str) -> tuple[int, str, BDCall]:
    """Emit tool_call, execute with per-product timeout + retry, emit tool_result."""
    product = _PRODUCT_MAP.get(step["tool"], "unknown")
    base_timeout = _PRODUCT_TIMEOUT.get(product, 20.0)

    await ev.emit(
        mission_id, "researcher", "tool_call",
        f"Step {step['step']}: {step['goal']}",
        product=product,
    )

    text, bd_call = await _attempt_with_retry(step, product, base_timeout)

    await ev.emit(
        mission_id, "researcher", "tool_result",
        f"Step {step['step']} {bd_call['status']} — {bd_call['latency_ms']}ms, {len(text)} chars",
        product=product,
        payload={"latency_ms": bd_call["latency_ms"], "ok": bd_call["ok"], "status": bd_call["status"]},
    )

    return step["step"], text, bd_call


async def run_researcher(state: MissionState) -> dict:
    mission_id = state["mission_id"]
    plan = state["research_plan"]

    await ev.emit(mission_id, "researcher", "started",
                  f"Firing {len(plan)} steps in parallel…")

    wall_start = time.monotonic()

    # All steps fire concurrently — tool_call/tool_result events interleave in the live feed.
    raw_results: list[tuple[int, str, BDCall]] = await asyncio.gather(
        *[_run_step(step, mission_id) for step in plan]
    )

    wall_ms = int((time.monotonic() - wall_start) * 1000)

    # Re-sort by step number for coherent findings narrative.
    raw_results.sort(key=lambda x: x[0])

    findings: list[str] = []
    bd_calls: list[BDCall] = []
    state_events: list[AgentEvent] = []

    step_map = {s["step"]: s for s in plan}
    for step_num, text, bd_call in raw_results:
        step = step_map[step_num]
        findings.append(f"### Step {step_num}: {step['goal']}\n\n{text}")
        bd_calls.append(bd_call)
        state_events.append({
            "agent": "researcher",
            "event_type": "tool_call",
            "message": f"Step {step_num}: {step['goal']}",
            "bright_data_product": bd_call["product"],
            "payload": {"bd_call": bd_call},
        })

    status_counts = {}
    for c in bd_calls:
        s = c.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1

    products_used = {c["product"] for c in bd_calls if c.get("status") == "ok"}
    products_attempted = {c["product"] for c in bd_calls}

    if len(products_attempted) < 5:
        missing = (
            {"serp_api", "mcp_server", "web_unlocker", "web_scraper_api", "scraping_browser"}
            - products_attempted
        )
        log.warning("Researcher: only %d/5 products attempted — missing: %s", len(products_attempted), missing)

    await ev.emit(
        mission_id, "researcher", "completed",
        f"Research done — {len(bd_calls)} calls, {len(products_used)}/5 ok, {wall_ms}ms wall",
        payload={
            "wall_time_ms": wall_ms,
            "products_covered": len(products_used),
            "status_counts": status_counts,
        },
    )

    return {
        "raw_findings": "\n\n---\n\n".join(findings),
        "bright_data_calls": bd_calls,
        "events": state_events,
    }
