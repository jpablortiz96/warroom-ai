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

CONFIDENCE CALCULATION RULE — READ CAREFULLY:
Confidence measures the QUALITY of what you found, NOT the percentage of steps that succeeded.
A step that returned empty or timed out is a COLLECTION GAP, not negative evidence.
It means "we don't know" for that dimension — it does NOT reduce confidence in what you DID find.

Calibration:
- If 2 sources independently confirm the same specific event (e.g., a named breach, a named acquisition,
  a named financial figure), that is STRONG corroboration → base confidence 75–85, regardless of how
  many other steps returned empty.
- If 3+ sources corroborate and data is recent → 80–95.
- If only 1 source found data but that data is specific and detailed → 55–70.
- Empty/failed steps do not lower confidence — they just limit SCOPE of what you can speak to.

Apply penalties ONLY for timeouts (status: timeout): subtract 5 per timed-out step, max -15.
DO NOT apply any penalty for empty or failed steps.

CONCRETE EXAMPLES:
  Bad:  2 ok steps (both at 80% quality) + 4 empty steps → confidence 32 ← WRONG
  Good: 2 ok steps (both at 80% quality) + 4 empty steps → confidence 78 - 0 = 78 ← CORRECT
  Good: 2 ok steps (80%) + 1 timeout + 3 empty → confidence 78 - 5 = 73 ← CORRECT
  Good: 1 ok step (specific named event) + 5 empty → confidence 62 ← CORRECT

Confidence scale (apply to what you DID find):
- 80–100: Strong corroboration of specific facts across ≥2 independent sources
- 60–79: Solid — 1–2 sources with specific, named, verifiable findings
- 40–59: Partial — directional signals but no specific verifiable facts
- Below 40: Genuinely insufficient — only speculation or hearsay found (NOT same as "few sources")

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
