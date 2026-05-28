import operator
from typing import Annotated, TypedDict


class ResearchStep(TypedDict):
    step: int
    goal: str
    tool: str  # serp_search | serp_news | mcp_search | mcp_scrape | unlocker_fetch | scraper_linkedin | browser_render
    query_or_url: str
    result: str | None
    ok: bool | None


class BDCall(TypedDict):
    product: str  # matches bright_data_product DB enum
    tool: str
    query_or_url: str
    latency_ms: int
    ok: bool


class AgentEvent(TypedDict):
    agent: str
    event_type: str
    message: str
    bright_data_product: str | None
    payload: dict | None


class MissionState(TypedDict):
    # Inputs
    mission_id: str
    mission_type: str  # account_pulse | supplier_watch | threat_surface
    target: str
    context: str | None

    # Planner → Research plan
    research_plan: list[ResearchStep]

    # Researcher → Raw intelligence
    raw_findings: str
    bright_data_calls: list[BDCall]

    # Skeptic → Challenges
    challenges: list[str]

    # Verifier → Verified intelligence
    verified_findings: str
    confidence_score: int

    # Commander → Battle Brief
    market_move_score: int
    recommended_move: str  # ATTACK | DEFEND | WAIT | ESCALATE | MONITOR
    executive_summary: str
    action_pack: dict  # full brief structure persisted as JSONB

    # SSE streaming — operator.add accumulates across nodes
    events: Annotated[list[AgentEvent], operator.add]
