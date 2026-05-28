"""Smoke test: real Supabase round-trip (requires SUPABASE_URL + SUPABASE_SERVICE_KEY in api/.env).

Run from api/ directory:
    uv run pytest tests/test_db.py -v
"""

import pytest

from app.db.client import (
    get_supabase,
    insert_mission,
    update_mission_status,
    get_mission,
    insert_agent_event,
    list_agent_events,
    insert_brief,
    get_brief_by_mission,
)


@pytest.fixture(autouse=True)
def cleanup_missions():
    """Track and delete all missions created during the test."""
    created_ids: list[str] = []
    yield created_ids
    for mid in created_ids:
        # Cascade deletes agent_events, briefs, citations
        get_supabase().table("missions").delete().eq("id", mid).execute()


def test_mission_insert_and_fetch(cleanup_missions):
    mission = insert_mission("smoke-test.example.com", "account_pulse")
    cleanup_missions.append(mission["id"])

    assert mission["target"] == "smoke-test.example.com"
    assert mission["mission_type"] == "account_pulse"
    assert mission["status"] == "queued"
    assert "id" in mission

    fetched = get_mission(mission["id"])
    assert fetched is not None
    assert fetched["id"] == mission["id"]


def test_update_mission_status(cleanup_missions):
    mission = insert_mission("status-test.example.com", "supplier_watch")
    cleanup_missions.append(mission["id"])

    update_mission_status(mission["id"], "running")
    updated = get_mission(mission["id"])
    assert updated["status"] == "running"

    update_mission_status(mission["id"], "completed")
    final = get_mission(mission["id"])
    assert final["status"] == "completed"


def test_agent_events_round_trip(cleanup_missions):
    mission = insert_mission("events-test.example.com", "threat_surface")
    mid = mission["id"]
    cleanup_missions.append(mid)

    e1 = insert_agent_event(
        mid, "planner", "started",
        message="Generating research plan",
        payload={"steps": 4},
    )
    e2 = insert_agent_event(
        mid, "researcher", "tool_call",
        message="Calling SERP API",
        bright_data_product="serp_api",
        payload={"query": "smoke test query"},
    )

    events = list_agent_events(mid)
    assert len(events) == 2
    assert events[0]["agent"] == "planner"
    assert events[0]["event_type"] == "started"
    assert events[1]["agent"] == "researcher"
    assert events[1]["bright_data_product"] == "serp_api"
    assert events[1]["payload"]["query"] == "smoke test query"


def test_brief_insert_and_fetch(cleanup_missions):
    mission = insert_mission("brief-test.example.com", "account_pulse")
    mid = mission["id"]
    cleanup_missions.append(mid)

    update_mission_status(mid, "completed")

    brief_data = {
        "market_move_score": 72,
        "recommended_move": "attack",
        "confidence_score": 85,
        "executive_summary": "Smoke test brief — target shows clear opportunity.",
        "action_pack": {
            "landing_angle": "Test angle",
            "email_copy": "Test email",
            "crm_payload": "Test CRM",
            "risk_warning": "Test warning",
        },
        "bright_data_calls": [
            {"product": "serp_api", "calls": 3},
            {"product": "web_unlocker", "calls": 1},
        ],
    }
    brief = insert_brief(mid, brief_data)

    assert brief["market_move_score"] == 72
    assert brief["recommended_move"] == "attack"
    assert brief["confidence_score"] == 85

    fetched = get_brief_by_mission(mid)
    assert fetched is not None
    assert fetched["mission_id"] == mid
    assert fetched["market_move_score"] == 72


def test_get_nonexistent_mission():
    import uuid
    result = get_mission(uuid.uuid4())
    assert result is None
