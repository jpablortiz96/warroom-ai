"""Mission routes — create, stream, and retrieve War Room missions."""

import asyncio
import json

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.agents import events as ev
from app.agents.graph import mission_graph
from app.agents.state import MissionState
from app.bright_data.mcp_client import search_serp
from app.config import settings
from app.db import client as db
from app.schemas.mission import MissionCreate

router = APIRouter(tags=["missions"])

# Prevent background tasks from being garbage collected before they finish.
_running_tasks: set[asyncio.Task] = set()


async def _run_mission(
    mission_id: str,
    mission_type: str,
    target: str,
    context: str | None,
) -> None:
    """Run the LangGraph graph, persist results, signal SSE done."""
    try:
        await db.aupdate_mission_status(mission_id, "running")

        initial_state: MissionState = {
            "mission_id": mission_id,
            "mission_type": mission_type,
            "target": target,
            "context": context,
            "research_plan": [],
            "raw_findings": "",
            "bright_data_calls": [],
            "challenges": [],
            "verified_findings": "",
            "confidence_score": 0,
            "market_move_score": 0,
            "recommended_move": "MONITOR",
            "executive_summary": "",
            "action_pack": {},
            "events": [],
        }

        final_state = await mission_graph.ainvoke(initial_state)

        # Persist accumulated events
        for evt in final_state.get("events", []):
            try:
                await db.ainsert_agent_event(
                    mission_id=mission_id,
                    agent=evt["agent"],
                    event_type=evt["event_type"],
                    message=evt["message"],
                    payload=evt.get("payload"),
                    bright_data_product=evt.get("bright_data_product"),
                )
            except Exception:
                pass

        # Persist the Battle Brief
        await db.ainsert_brief(mission_id, {
            "market_move_score": final_state.get("market_move_score", 0),
            "recommended_move": final_state.get("recommended_move", "MONITOR"),
            "confidence_score": final_state.get("confidence_score", 0),
            "executive_summary": final_state.get("executive_summary", ""),
            "action_pack": final_state.get("action_pack", {}),
            "bright_data_calls": final_state.get("bright_data_calls", []),
        })
        await db.aupdate_mission_status(mission_id, "completed")

    except Exception as exc:
        await db.aupdate_mission_status(mission_id, "failed")
        await ev.emit(mission_id, "commander", "failed", f"Mission failed: {exc}")

    finally:
        await ev.emit_done(mission_id)


# ── Routes — literal paths MUST come before /{mission_id} ────────────────────

@router.get("/hello")
async def hello_mission() -> dict:
    """Smoke-test: verifies Bright Data reachability."""
    if not settings.bright_data_api_token:
        return {
            "status": "config_needed",
            "message": "Set BRIGHT_DATA_API_TOKEN in api/.env",
        }
    try:
        results = await search_serp("war room AI hackathon", limit=3)
        return {
            "status": "ok",
            "bright_data_reachable": True,
            "sample_titles": [r.get("title", "(no title)") for r in results],
        }
    except Exception as exc:
        return {"status": "error", "bright_data_reachable": False, "error": str(exc)}


@router.post("/", status_code=201)
async def create_mission(body: MissionCreate) -> dict:
    """Create a new mission and launch the 5-agent LangGraph pipeline."""
    mission = await db.ainsert_mission(body.target, body.mission_type.value, body.context)
    mission_id = str(mission["id"])
    ev.create_queue(mission_id)
    task = asyncio.create_task(
        _run_mission(mission_id, body.mission_type.value, body.target, body.context)
    )
    _running_tasks.add(task)
    task.add_done_callback(_running_tasks.discard)
    return {"mission_id": mission_id, "status": "queued"}


@router.get("/")
async def list_missions(limit: int = 20) -> list[dict]:
    return await db.alist_missions(limit=limit)


@router.get("/{mission_id}/stream")
async def stream_mission(mission_id: str):
    """SSE stream for a running mission. Replays history then streams live events."""

    async def event_generator():
        # Replay past events persisted in Supabase (reconnection support)
        past = await db.alist_agent_events(mission_id)
        for evt in past:
            yield {
                "event": "agent_event",
                "data": json.dumps({
                    "agent": evt["agent"],
                    "event_type": evt["event_type"],
                    "message": evt["message"],
                    "bright_data_product": evt.get("bright_data_product"),
                    "payload": evt.get("payload") or {},
                }),
            }

        # Stream live events from the in-memory queue
        q = ev.get_queue(mission_id)
        if q is None:
            # Mission already finished or never started — send done immediately
            yield {"event": "done", "data": json.dumps({"message": "no active stream"})}
            return

        while True:
            item = await q.get()
            if item.get("__done__"):
                yield {"event": "done", "data": json.dumps({"message": "mission complete"})}
                ev.remove_queue(mission_id)
                return
            yield {"event": "agent_event", "data": json.dumps(item)}

    return EventSourceResponse(event_generator())


@router.get("/{mission_id}/diff")
async def get_mission_diff(mission_id: str) -> dict:
    """Compare this mission's brief to the most recent prior run on the same target+type."""
    mission = await db.aget_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    current_brief = await db.aget_brief_by_mission(mission_id)
    if not current_brief:
        return {"has_prior": False}

    prior_mission = await db.afind_prior_mission(
        target=mission["target"],
        mission_type=mission["mission_type"],
        exclude_id=mission_id,
    )
    if not prior_mission:
        return {"has_prior": False}

    prior_brief = await db.aget_brief_by_mission(str(prior_mission["id"]))
    if not prior_brief:
        return {"has_prior": False}

    score_delta = current_brief["market_move_score"] - prior_brief["market_move_score"]
    confidence_delta = current_brief["confidence_score"] - prior_brief["confidence_score"]
    current_move = (current_brief.get("recommended_move") or "").upper()
    prior_move = (prior_brief.get("recommended_move") or "").upper()

    def _actions(b: dict) -> list[str]:
        ap = b.get("action_pack") or {}
        acts = ap.get("actions") or {}
        return (acts.get("immediate") or []) + (acts.get("this_week") or []) + (acts.get("watch") or [])

    def _jaccard(a: str, b: str) -> float:
        ta, tb = set(a.lower().split()), set(b.lower().split())
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / len(ta | tb)

    def _matched(item: str, pool: list[str], thresh: float = 0.4) -> bool:
        return any(_jaccard(item, p) >= thresh for p in pool)

    cur_acts = _actions(current_brief)
    pri_acts = _actions(prior_brief)
    new_findings = [a for a in cur_acts if not _matched(a, pri_acts)][:3]
    resolved_findings = [a for a in pri_acts if not _matched(a, cur_acts)][:3]

    return {
        "has_prior": True,
        "prior_mission_id": str(prior_mission["id"]),
        "prior_date": prior_mission.get("created_at"),
        "score_delta": score_delta,
        "confidence_delta": confidence_delta,
        "move_changed": current_move != prior_move,
        "prior_move": prior_move,
        "current_move": current_move,
        "new_findings": new_findings,
        "resolved_findings": resolved_findings,
        "prior_summary": ((prior_brief.get("action_pack") or {}).get("situation") or ""),
    }


@router.post("/{mission_id}/notify")
async def notify_slack(mission_id: str, body: dict) -> dict:
    """Post a formatted Battle Brief to a Slack webhook (Slack Block Kit)."""
    webhook_url: str = body.get("webhook_url", "").strip()
    share_base: str = body.get("share_base", "http://localhost:3000").rstrip("/")

    if not webhook_url:
        raise HTTPException(status_code=400, detail="webhook_url is required")

    mission = await db.aget_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    brief = await db.aget_brief_by_mission(mission_id)
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not ready yet")

    import httpx

    target = mission.get("target", "")
    mission_type = mission.get("mission_type", "").replace("_", " ").upper()
    score = brief.get("market_move_score", 0)
    move = (brief.get("recommended_move") or "MONITOR").upper()
    confidence = brief.get("confidence_score", 0)
    action_pack = brief.get("action_pack") or {}
    headline = action_pack.get("headline", "")
    situation = action_pack.get("situation", "")
    actions = action_pack.get("actions") or {}
    immediate = actions.get("immediate") or []

    _MOVE_EMOJI = {
        "ATTACK": ":red_circle:", "DEFEND": ":large_yellow_circle:",
        "ESCALATE": ":rotating_light:", "WAIT": ":pause_button:",
        "MONITOR": ":eye:",
    }
    move_emoji = _MOVE_EMOJI.get(move, ":white_circle:")
    share_url = f"{share_base}/share/{mission_id}"

    # Truncate long text for Slack's 3000-char section limit.
    summary = (headline + "\n" + situation).strip()
    if len(summary) > 500:
        summary = summary[:497] + "..."

    immediate_text = "\n".join(f"> :arrow_right: {a}" for a in immediate[:3])

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"War Room AI — {target} | {move_emoji} {move}"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Mission:*\n{mission_type}"},
                {"type": "mrkdwn", "text": f"*Market Move Score:*\n*{score}/100*"},
                {"type": "mrkdwn", "text": f"*Recommended Move:*\n{move_emoji} *{move}*"},
                {"type": "mrkdwn", "text": f"*Confidence:*\n{confidence}/100"},
            ],
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Situation*\n{summary}"},
        },
    ]

    if immediate_text:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Immediate Actions*\n{immediate_text}"},
        })

    blocks += [
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": "Generated by *War Room AI* · Powered by *Bright Data*"},
            ],
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View Full Brief"},
                    "url": share_url,
                    "style": "primary",
                },
            ],
        },
    ]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook_url, json={"blocks": blocks})
        if resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Slack returned {resp.status_code}: {resp.text[:200]}",
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach Slack: {exc}")

    return {"ok": True, "target": target, "move": move, "score": score}


@router.get("/{mission_id}")
async def get_mission(mission_id: str) -> dict:
    mission = await db.aget_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    try:
        brief = await db.aget_brief_by_mission(mission_id)
    except Exception:
        brief = None  # brief may not exist yet — always return 200
    return {"mission": mission, "brief": brief}
