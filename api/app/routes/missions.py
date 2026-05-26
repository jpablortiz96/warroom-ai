import asyncio

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.bright_data.mcp_client import search_serp
from app.config import settings

router = APIRouter(tags=["missions"])


@router.get("/hello")
async def hello_mission() -> dict:
    """Smoke-test endpoint: verifies Bright Data reachability on Day 1."""
    if not settings.bright_data_api_token:
        return {
            "status": "config_needed",
            "message": "Set BRIGHT_DATA_API_TOKEN in api/.env",
            "next_steps": [
                "Copy api/.env.example to api/.env",
                "Set BRIGHT_DATA_API_TOKEN=<your token from app.brightdata.com>",
                "Set BRIGHT_DATA_SERP_ZONE=<zone name from Bright Data dashboard>",
                "Restart the server: uv run uvicorn main:app --reload --port 8000",
            ],
        }

    try:
        results = await search_serp("war room AI hackathon", limit=3)
        return {
            "status": "ok",
            "bright_data_reachable": True,
            "sample_titles": [r.get("title", "(no title)") for r in results],
        }
    except Exception as exc:
        return {
            "status": "error",
            "bright_data_reachable": False,
            "error": str(exc),
            "next_steps": [
                "401 → BRIGHT_DATA_API_TOKEN is invalid; regenerate at app.brightdata.com/account",
                "403 → SERP API zone not enabled; enable it in your Bright Data dashboard",
                "407 → BRIGHT_DATA_SERP_ZONE value is wrong; check zone name in dashboard",
                "Timeout → increase httpx timeout or check network/firewall",
            ],
        }


@router.get("/{mission_id}/stream")
async def stream_mission(mission_id: str):
    """SSE stream for a running mission. Day 2: wire up LangGraph graph here."""

    async def event_generator():
        for i, agent in enumerate(["planner", "researcher", "skeptic", "verifier", "commander"]):
            yield {
                "event": "agent_event",
                "data": f'{{"agent": "{agent}", "status": "pending", "mission_id": "{mission_id}"}}',
            }
            await asyncio.sleep(0.5)
        yield {"event": "done", "data": '{"message": "Day 2 — real graph not yet wired"}'}

    return EventSourceResponse(event_generator())
