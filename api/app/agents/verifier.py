"""Verifier — resolves Skeptic challenges and assigns a confidence score."""

import json

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents import events as ev
from app.agents.state import AgentEvent, MissionState
from app.config import settings

_SYSTEM = """You are the Verifier agent in War Room AI.
Address the Skeptic's challenges against the research data.

For each challenge:
- CONFIRMED: Challenge is valid — the data is limited here
- REFUTED: Challenge is unfounded — the data adequately covers this
- PARTIAL: Partially valid — note the nuance

Then produce verified_findings: a crisp Markdown summary of what we KNOW with high confidence.

CONFIDENCE CALCULATION RULE:
Compute confidence using ONLY successful data sources (status: ok).
Apply penalties: subtract 5 points per timed-out step (status: timeout), max -15 total.
Do NOT penalize successful steps because other steps timed out — that is a tool failure, not a data quality issue.
Example: 4 ok steps base 78 + 1 timeout → final: 73.

Confidence scale (before penalties):
- 80–100: Strong multi-source corroboration, recent data
- 60–79: Solid but single-source or aging data
- 40–59: Partial data, notable gaps remain
- Below 40: Insufficient to act — recommend re-research

Output ONLY valid JSON — no markdown fences, no explanation:
{
  "verified_findings": "## Verified Intelligence\\n...",
  "confidence_score": 72,
  "resolutions": [{"challenge": "...", "verdict": "CONFIRMED|REFUTED|PARTIAL", "note": "..."}]
}"""


async def run_verifier(state: MissionState) -> dict:
    mission_id = state["mission_id"]
    target = state["target"]
    findings = state["raw_findings"]
    challenges = state["challenges"]
    bd_calls = state["bright_data_calls"]

    await ev.emit(mission_id, "verifier", "started", "Resolving challenges and verifying facts…")
    await ev.emit(mission_id, "verifier", "thinking", "Cross-referencing data sources…")

    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=settings.anthropic_api_key,
        max_tokens=2048,
    )

    coverage_lines = [
        f"- {c['product']} ({c['tool']}): {c.get('status', 'unknown')}, {c['latency_ms']}ms"
        for c in bd_calls
    ]
    timeout_count = sum(1 for c in bd_calls if c.get("status") == "timeout")
    penalty = min(timeout_count * 5, 15)

    human = (
        f"Target: {target}\n\n"
        f"Research coverage ({len(bd_calls)} Bright Data calls):\n"
        + "\n".join(coverage_lines)
        + f"\n\nTimed-out steps: {timeout_count} → apply -{penalty} confidence penalty (max -15)\n\n"
        f"Research Findings:\n{findings[:4500]}\n\n"
        f"Skeptic Challenges:\n{json.dumps(challenges, indent=2)}"
    )

    response = await llm.ainvoke([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=human),
    ])

    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()

    data = json.loads(raw)
    verified_findings = data.get("verified_findings", findings[:2000])
    confidence_score = max(0, min(100, int(data.get("confidence_score", 60))))

    await ev.emit(
        mission_id, "verifier", "completed",
        f"Confidence: {confidence_score}/100",
        payload={"confidence_score": confidence_score},
    )

    event: AgentEvent = {
        "agent": "verifier",
        "event_type": "completed",
        "message": f"Confidence: {confidence_score}/100",
        "bright_data_product": None,
        "payload": {"confidence_score": confidence_score},
    }
    return {
        "verified_findings": verified_findings,
        "confidence_score": confidence_score,
        "events": [event],
    }
