"""Commander — synthesizes the Executive Battle Brief from verified intelligence."""

import json

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents import events as ev
from app.agents.state import AgentEvent, MissionState
from app.config import settings

_SYSTEM = """You are Commander — the synthesis and decision agent in War Room AI.
Produce the Executive Battle Brief from verified intelligence.

Recommended moves:
- ATTACK    Clear opportunity — move aggressively now
- DEFEND    Threat detected — protect position immediately
- WAIT      Signal too weak — gather more data before acting
- ESCALATE  Critical signal — senior leadership must act within 24h
- MONITOR   Low signal — maintain watch, no action needed now

Market Move Score (0–100):
- 81–100  Critical — act within 24–48h
- 61–80   Strong — act this week
- 41–60   Moderate — plan a response
- 21–40   Low — situational awareness only
- 0–20    Noise — no action needed

Output ONLY valid JSON — no markdown fences, no explanation:
{
  "market_move_score": 72,
  "recommended_move": "ATTACK",
  "headline": "One sentence, under 20 words, for the C-suite",
  "situation": "2-3 sentence situation assessment",
  "key_findings": [
    {"agent": "researcher", "headline": "Key finding in one line", "detail": "Supporting detail", "confidence": 80}
  ],
  "action_pack": {
    "immediate": ["Do this today"],
    "this_week": ["Do this week"],
    "watch": ["Monitor this signal"]
  },
  "commander_rationale": "Why this move was chosen over alternatives"
}"""


async def run_commander(state: MissionState) -> dict:
    mission_id = state["mission_id"]
    mission_type = state["mission_type"]
    target = state["target"]
    verified_findings = state["verified_findings"]
    confidence_score = state["confidence_score"]
    challenges = state["challenges"]
    bd_calls = state["bright_data_calls"]

    await ev.emit(mission_id, "commander", "started", "Synthesizing intelligence into Battle Brief…")
    await ev.emit(mission_id, "commander", "thinking", "Evaluating move options…")

    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=settings.anthropic_api_key,
        max_tokens=2048,
    )

    products_used = list({c["product"] for c in bd_calls})
    bd_summary = f"{len(bd_calls)} calls across: {', '.join(products_used)}"

    human = (
        f"Mission: {mission_type}\nTarget: {target}\n"
        f"Intelligence confidence: {confidence_score}/100\n"
        f"Bright Data coverage: {bd_summary}\n\n"
        f"Verified Intelligence:\n{verified_findings}\n\n"
        f"Open Challenges:\n{json.dumps(challenges, indent=2)}"
    )

    response = await llm.ainvoke([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=human),
    ])

    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()

    data = json.loads(raw)
    market_move_score = max(0, min(100, int(data.get("market_move_score", 50))))
    recommended_move = data.get("recommended_move", "MONITOR")
    executive_summary = f"{data.get('headline', '')} {data.get('situation', '')}".strip()
    action_pack = {
        "headline": data.get("headline", ""),
        "situation": data.get("situation", ""),
        "key_findings": data.get("key_findings", []),
        "actions": data.get("action_pack", {}),
        "commander_rationale": data.get("commander_rationale", ""),
    }

    await ev.emit(
        mission_id, "commander", "completed",
        f"Battle Brief: {recommended_move} — Score {market_move_score}/100",
        payload={"market_move_score": market_move_score, "recommended_move": recommended_move},
    )

    event: AgentEvent = {
        "agent": "commander",
        "event_type": "completed",
        "message": f"{recommended_move} — Score {market_move_score}/100",
        "bright_data_product": None,
        "payload": {"market_move_score": market_move_score, "recommended_move": recommended_move},
    }
    return {
        "market_move_score": market_move_score,
        "recommended_move": recommended_move,
        "executive_summary": executive_summary,
        "action_pack": action_pack,
        "events": [event],
    }
