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
