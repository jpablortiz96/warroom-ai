"""Planner — parses mission + target into a structured Bright Data research plan."""

import json
import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents import events as ev
from app.agents.state import AgentEvent, MissionState, ResearchStep
from app.config import settings

log = logging.getLogger(__name__)

_SYSTEM = """You are the Planner agent in War Room AI, a market intelligence platform.
Your job: design a precise research plan for the given mission and target.

Available Bright Data tools:
- serp_search      Google organic search. Best for: general intel, market data, company overview.
- serp_news        Google News search. Best for: recent events, press releases, announcements.
- mcp_search       MCP Server structured search. Best for: tech company data, product info.
- mcp_scrape       MCP Server page scrape (returns clean Markdown). Best for: specific pages.
- unlocker_fetch   Web Unlocker (bypasses bot protection). Best for: paywalled/protected pages.
- scraper_linkedin Web Scraper API — LinkedIn PERSON profile only (URL must be linkedin.com/in/...).
- browser_render   Scraping Browser (full JS rendering). Best for: SPAs, dynamic pricing pages.

Mission types:
- account_pulse   GTM intel: competitor moves, funding rounds, leadership changes, product launches
- supplier_watch  Supply chain: financial health, risk signals, market position, contract risk
- threat_surface  Security: breach history, CVEs, threat intel, dark web exposure, domain risk

Rules:
1. Produce exactly 5 steps.
2. Use ALL 5 Bright Data products: serp_api (serp_search/serp_news), mcp_server (mcp_search/mcp_scrape),
   web_unlocker (unlocker_fetch), web_scraper_api (scraper_linkedin), scraping_browser (browser_render).
3. For scraper_linkedin: target the company CEO or a key executive's profile URL (linkedin.com/in/...).
4. For browser_render: target a dynamic page (pricing, careers, app dashboard).
5. For unlocker_fetch: target a page that is likely behind bot protection (press/news page, paywalled).
6. Queries and URLs must be specific to the actual target — no placeholders.

Output ONLY a JSON array — no markdown fences, no explanation:
[
  {"step": 1, "goal": "...", "tool": "serp_search", "query_or_url": "...", "result": null, "ok": null},
  ...
]"""


# Products that must appear in every plan, mapped to which tools cover them.
_REQUIRED_PRODUCTS: dict[str, set[str]] = {
    "serp_api": {"serp_search", "serp_news"},
    "mcp_server": {"mcp_search", "mcp_scrape"},
    "web_unlocker": {"unlocker_fetch"},
    "web_scraper_api": {"scraper_linkedin"},
    "scraping_browser": {"browser_render"},
}


def _target_domain(target: str) -> str:
    """Best-effort domain extraction — 'Wix.com' → 'wix.com', 'Shopify' → 'shopify.com'."""
    raw = target.lower().strip().replace("https://", "").replace("http://", "").replace("www.", "")
    domain = raw.split("/")[0]
    if "." not in domain:
        domain = f"{domain}.com"
    return domain


def _ensure_all_products(
    plan: list[ResearchStep], mission_type: str, target: str
) -> list[ResearchStep]:
    """Append one step per missing Bright Data product — ensures full coverage."""
    used_tools = {s["tool"] for s in plan}
    missing = [
        product
        for product, tools in _REQUIRED_PRODUCTS.items()
        if not (tools & used_tools)
    ]
    if not missing:
        return plan

    domain = _target_domain(target)
    base_url = f"https://www.{domain}"
    name_slug = domain.replace(".com", "").replace(".", "-")
    step_num = len(plan) + 1

    default_steps: dict[str, ResearchStep] = {
        "serp_api": {
            "step": step_num,
            "goal": f"Search for recent {target} news and market developments",
            "tool": "serp_news",
            "query_or_url": f"{target} news 2025",
            "result": None,
            "ok": None,
        },
        "mcp_server": {
            "step": step_num,
            "goal": f"MCP structured search: {target} company technology overview",
            "tool": "mcp_search",
            "query_or_url": f"{target} company products technology stack 2025",
            "result": None,
            "ok": None,
        },
        "web_unlocker": {
            "step": step_num,
            "goal": f"Fetch {target} press/news page bypassing bot protection",
            "tool": "unlocker_fetch",
            "query_or_url": (
                f"{base_url}/press"
                if mission_type == "account_pulse"
                else f"{base_url}/investors"
                if mission_type == "supplier_watch"
                else f"https://haveibeenpwned.com/DomainSearch/{domain}"
            ),
            "result": None,
            "ok": None,
        },
        "web_scraper_api": {
            "step": step_num,
            "goal": f"Get LinkedIn profile of {target} key executive for leadership intel",
            "tool": "scraper_linkedin",
            "query_or_url": f"https://www.linkedin.com/in/{name_slug}-ceo/",
            "result": None,
            "ok": None,
        },
        "scraping_browser": {
            "step": step_num,
            "goal": f"Render {target} dynamic page for JS-rendered competitive data",
            "tool": "browser_render",
            "query_or_url": (
                f"{base_url}/pricing"
                if mission_type in ("account_pulse", "supplier_watch")
                else f"{base_url}/security"
            ),
            "result": None,
            "ok": None,
        },
    }

    additions: list[ResearchStep] = []
    for product in missing:
        step = {**default_steps[product], "step": step_num}
        additions.append(step)  # type: ignore[arg-type]
        step_num += 1

    log.info("Planner appended %d default steps for missing products: %s", len(additions), missing)
    return plan + additions


def _human(mission_type: str, target: str, context: str | None) -> str:
    ctx = f"\nContext: {context}" if context else ""
    return f"Mission type: {mission_type}\nTarget: {target}{ctx}\n\nCreate the research plan."


async def run_planner(state: MissionState) -> dict:
    mission_id = state["mission_id"]
    mission_type = state["mission_type"]
    target = state["target"]
    context = state.get("context")

    await ev.emit(mission_id, "planner", "started", f"Analyzing {mission_type} on: {target}")
    await ev.emit(mission_id, "planner", "thinking", "Building research plan…")

    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=settings.anthropic_api_key,
        max_tokens=2048,
    )

    response = await llm.ainvoke([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=_human(mission_type, target, context)),
    ])

    raw = response.content.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1].lstrip("json").strip() if len(parts) > 1 else raw

    plan: list[ResearchStep] = json.loads(raw)

    # Post-processing guarantee: every plan must cover all 5 Bright Data products.
    plan = _ensure_all_products(plan, mission_type, target)

    tools_used = {s["tool"] for s in plan}
    products_covered = {
        p for p, tools in _REQUIRED_PRODUCTS.items() if tools & tools_used
    }

    await ev.emit(
        mission_id, "planner", "completed",
        f"Plan ready: {len(plan)} steps, {len(products_covered)}/5 Bright Data products",
        payload={"plan": plan},
    )

    event: AgentEvent = {
        "agent": "planner",
        "event_type": "completed",
        "message": f"Plan: {len(plan)} steps, {len(products_covered)}/5 products",
        "bright_data_product": None,
        "payload": {"plan": plan},
    }
    return {"research_plan": plan, "events": [event]}
