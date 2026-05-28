"""Skeptic — challenges research findings and surfaces verification gaps."""

import json

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents import events as ev
from app.agents.state import AgentEvent, MissionState
from app.config import settings

_SYSTEM = """You are the Skeptic agent in War Room AI.
Critically review the research findings and raise 3-5 pointed challenges.

Focus on:
- Data gaps: What important information is missing?
- Recency: Is the data fresh enough to act on?
- Source quality: Are sources credible and independent?
- Contradictions: Do any findings conflict with each other?
- Bias or incompleteness: Is any claim likely skewed?

Output ONLY a JSON array of challenge strings — no markdown, no explanation:
["Challenge 1...", "Challenge 2...", ...]"""


async def run_skeptic(state: MissionState) -> dict:
    mission_id = state["mission_id"]
    target = state["target"]
    findings = state["raw_findings"]

    await ev.emit(mission_id, "skeptic", "started", "Reviewing research for weaknesses…")
    await ev.emit(mission_id, "skeptic", "thinking", "Probing data quality and gaps…")

    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=settings.anthropic_api_key,
        max_tokens=1024,
    )

    response = await llm.ainvoke([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=f"Target: {target}\n\nFindings:\n{findings[:6000]}"),
    ])

    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()

    challenges: list[str] = json.loads(raw)

    await ev.emit(
        mission_id, "skeptic", "completed",
        f"Raised {len(challenges)} challenges",
        payload={"challenges": challenges},
    )

    event: AgentEvent = {
        "agent": "skeptic",
        "event_type": "completed",
        "message": f"{len(challenges)} challenges raised",
        "bright_data_product": None,
        "payload": {"challenges": challenges},
    }
    return {"challenges": challenges, "events": [event]}
