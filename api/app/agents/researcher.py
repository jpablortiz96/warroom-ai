"""Researcher — executes the research plan via Bright Data tools."""

import logging

from app.agents import events as ev
from app.agents.state import AgentEvent, BDCall, MissionState, ResearchStep
from app.bright_data import browser, mcp_client, scraper_api, serp, unlocker

log = logging.getLogger(__name__)
from app.config import settings

_PRODUCT_MAP: dict[str, str] = {
    "serp_search": "serp_api",
    "serp_news": "serp_api",
    "mcp_search": "mcp_server",
    "mcp_scrape": "mcp_server",
    "unlocker_fetch": "web_unlocker",
    "scraper_linkedin": "web_scraper_api",
    "browser_render": "scraping_browser",
}


def _fmt_serp(results: list[dict]) -> str:
    lines = []
    for x in results[:5]:
        title = x.get("title", "")
        desc = x.get("description", "") or x.get("snippet", "")
        url = x.get("url", "") or x.get("link", "")
        lines.append(f"**{title}**\n{desc}\n{url}")
    return "\n\n".join(lines)


async def _execute(step: ResearchStep) -> tuple[str, BDCall]:
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
    bd_call: BDCall = {
        "product": _PRODUCT_MAP.get(tool, "unknown"),
        "tool": tool,
        "query_or_url": q,
        "latency_ms": latency_ms,
        "ok": ok,
    }
    return result_text or f"[No data retrieved for: {q}]", bd_call


async def run_researcher(state: MissionState) -> dict:
    mission_id = state["mission_id"]
    plan = state["research_plan"]

    await ev.emit(mission_id, "researcher", "started", f"Executing {len(plan)} research steps…")

    findings: list[str] = []
    bd_calls: list[BDCall] = []
    state_events: list[AgentEvent] = []

    for step in plan:
        product = _PRODUCT_MAP.get(step["tool"], "unknown")
        await ev.emit(
            mission_id, "researcher", "tool_call",
            f"Step {step['step']}: {step['goal']}",
            product=product,
        )

        text, bd_call = await _execute(step)
        bd_calls.append(bd_call)
        findings.append(f"### Step {step['step']}: {step['goal']}\n\n{text}")

        await ev.emit(
            mission_id, "researcher", "tool_result",
            f"Step {step['step']} done — {bd_call['latency_ms']}ms, {len(text)} chars",
            product=product,
            payload={"latency_ms": bd_call["latency_ms"], "ok": bd_call["ok"]},
        )
        state_events.append({
            "agent": "researcher",
            "event_type": "tool_call",
            "message": f"Step {step['step']}: {step['goal']}",
            "bright_data_product": product,
            "payload": {"bd_call": bd_call},
        })

    products_used = {c["product"] for c in bd_calls}
    if len(products_used) < 5:
        missing = {"serp_api", "mcp_server", "web_unlocker", "web_scraper_api", "scraping_browser"} - products_used
        log.warning("Researcher: only %d/5 products used — missing: %s", len(products_used), missing)
    await ev.emit(
        mission_id, "researcher", "completed",
        f"Research complete — {len(bd_calls)} BD calls across {len(products_used)}/5 products",
    )

    return {
        "raw_findings": "\n\n---\n\n".join(findings),
        "bright_data_calls": bd_calls,
        "events": state_events,
    }
