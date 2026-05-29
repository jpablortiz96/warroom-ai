"""Supabase service-role client — singleton with typed helpers.

All public functions are sync; async wrappers (prefixed `a`) wrap them in
asyncio.to_thread so LangGraph nodes and FastAPI routes stay non-blocking.
"""

import asyncio
from datetime import datetime, timezone
from uuid import UUID

from supabase import Client, create_client

from app.config import settings

_client: Client | None = None


def get_supabase() -> Client:
    """Return the shared service-role client (created once on first call)."""
    global _client
    if _client is None:
        if not settings.supabase_url or not settings.supabase_service_key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in api/.env"
            )
        _client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _client


# ── Missions ──────────────────────────────────────────────────────────────────

def insert_mission(
    target: str,
    mission_type: str,
    context: str | None = None,
) -> dict:
    row: dict = {"target": target, "mission_type": mission_type.lower(), "status": "queued"}
    if context:
        row["context"] = context
    result = get_supabase().table("missions").insert(row).execute()
    return result.data[0]


def update_mission_status(mission_id: UUID | str, status: str) -> None:
    get_supabase().table("missions").update(
        {
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", str(mission_id)).execute()


def get_mission(mission_id: UUID | str) -> dict | None:
    result = (
        get_supabase()
        .table("missions")
        .select("*")
        .eq("id", str(mission_id))
        .maybe_single()
        .execute()
    )
    return result.data


def list_missions(limit: int = 20, offset: int = 0) -> list[dict]:
    result = (
        get_supabase()
        .table("missions")
        .select("*")
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return result.data or []


# ── Agent events ──────────────────────────────────────────────────────────────

def insert_agent_event(
    mission_id: UUID | str,
    agent: str,
    event_type: str,
    message: str,
    payload: dict | None = None,
    bright_data_product: str | None = None,
) -> dict:
    row: dict = {
        "mission_id": str(mission_id),
        "agent": agent.lower(),
        "event_type": event_type.lower(),
        "message": message,
    }
    if payload is not None:
        row["payload"] = payload
    if bright_data_product is not None:
        row["bright_data_product"] = bright_data_product.lower()
    result = get_supabase().table("agent_events").insert(row).execute()
    return result.data[0]


def list_agent_events(mission_id: UUID | str) -> list[dict]:
    result = (
        get_supabase()
        .table("agent_events")
        .select("*")
        .eq("mission_id", str(mission_id))
        .order("created_at")
        .execute()
    )
    return result.data or []


# ── Briefs ────────────────────────────────────────────────────────────────────

def insert_brief(mission_id: UUID | str, brief: dict) -> dict:
    """Insert an Executive Battle Brief.

    The `brief` dict must contain: market_move_score, recommended_move,
    confidence_score, executive_summary, action_pack, bright_data_calls.
    """
    # Normalise enum fields to lowercase so Postgres never gets a case mismatch.
    safe = {**brief}
    if "recommended_move" in safe and safe["recommended_move"]:
        safe["recommended_move"] = str(safe["recommended_move"]).lower()
    row = {"mission_id": str(mission_id), **safe}
    result = get_supabase().table("briefs").insert(row).execute()
    return result.data[0]


def get_brief_by_mission(mission_id: UUID | str) -> dict | None:
    result = (
        get_supabase()
        .table("briefs")
        .select("*")
        .eq("mission_id", str(mission_id))
        .maybe_single()
        .execute()
    )
    if not result.data:
        return None
    # maybe_single() returns a dict directly; guard against list responses.
    return result.data if isinstance(result.data, dict) else result.data[0]


# ── Scraper cache ─────────────────────────────────────────────────────────────

def get_scraper_cache(target_url: str, dataset_id: str, max_age_hours: int = 24) -> dict | None:
    """Return cached snapshot data if younger than max_age_hours, else None."""
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=max_age_hours)).isoformat()
    result = (
        get_supabase()
        .table("scraper_cache")
        .select("data, snapshot_id, created_at")
        .eq("target_url", target_url)
        .eq("dataset_id", dataset_id)
        .gte("created_at", cutoff)
        .maybe_single()
        .execute()
    )
    return result.data if result.data else None


def set_scraper_cache(target_url: str, dataset_id: str, snapshot_id: str, data: dict | list) -> None:
    """Upsert a successful snapshot into the cache."""
    get_supabase().table("scraper_cache").upsert({
        "target_url": target_url,
        "dataset_id": dataset_id,
        "snapshot_id": snapshot_id,
        "data": data,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()


async def aget_scraper_cache(target_url: str, dataset_id: str) -> dict | None:
    return await asyncio.to_thread(get_scraper_cache, target_url, dataset_id)


async def aset_scraper_cache(target_url: str, dataset_id: str, snapshot_id: str, data: dict | list) -> None:
    await asyncio.to_thread(set_scraper_cache, target_url, dataset_id, snapshot_id, data)


# ── Citations ─────────────────────────────────────────────────────────────────

def insert_citations(citations: list[dict]) -> list[dict]:
    """Bulk-insert citations. Each dict needs: brief_id, mission_id, claim,
    source_url, confidence, agent, and optionally bright_data_product."""
    if not citations:
        return []
    result = get_supabase().table("citations").insert(citations).execute()
    return result.data or []


# ── Async wrappers ────────────────────────────────────────────────────────────

async def ainsert_mission(
    target: str, mission_type: str, context: str | None = None
) -> dict:
    return await asyncio.to_thread(insert_mission, target, mission_type, context)


async def aupdate_mission_status(mission_id: UUID | str, status: str) -> None:
    await asyncio.to_thread(update_mission_status, mission_id, status)


async def ainsert_agent_event(
    mission_id: UUID | str,
    agent: str,
    event_type: str,
    message: str,
    payload: dict | None = None,
    bright_data_product: str | None = None,
) -> dict:
    return await asyncio.to_thread(
        insert_agent_event,
        mission_id,
        agent,
        event_type,
        message,
        payload,
        bright_data_product,
    )


async def ainsert_brief(mission_id: UUID | str, brief: dict) -> dict:
    return await asyncio.to_thread(insert_brief, mission_id, brief)


async def aget_mission(mission_id: UUID | str) -> dict | None:
    return await asyncio.to_thread(get_mission, mission_id)


async def aget_brief_by_mission(mission_id: UUID | str) -> dict | None:
    return await asyncio.to_thread(get_brief_by_mission, mission_id)


async def alist_missions(limit: int = 20, offset: int = 0) -> list[dict]:
    return await asyncio.to_thread(list_missions, limit, offset)


async def alist_agent_events(mission_id: UUID | str) -> list[dict]:
    return await asyncio.to_thread(list_agent_events, mission_id)


def mark_brief_shared(mission_id: UUID | str) -> dict | None:
    """Set shared_at on the brief for this mission. Returns the updated brief."""
    result = (
        get_supabase()
        .table("briefs")
        .update({"shared_at": datetime.now(timezone.utc).isoformat()})
        .eq("mission_id", str(mission_id))
        .execute()
    )
    return result.data[0] if result.data else None


async def amark_brief_shared(mission_id: UUID | str) -> dict | None:
    return await asyncio.to_thread(mark_brief_shared, mission_id)


# ── Mission schedules ─────────────────────────────────────────────────────────

def list_schedules() -> list[dict]:
    result = (
        get_supabase()
        .table("mission_schedules")
        .select("*")
        .order("created_at")
        .execute()
    )
    return result.data or []


def insert_schedule(target: str, mission_type: str, cron: str, label: str | None = None) -> dict:
    row = {"target": target, "mission_type": mission_type.lower(), "cron": cron}
    if label:
        row["label"] = label
    result = get_supabase().table("mission_schedules").insert(row).execute()
    return result.data[0]


def delete_schedule(schedule_id: str) -> None:
    get_supabase().table("mission_schedules").delete().eq("id", schedule_id).execute()


def mark_schedule_ran(schedule_id: str, mission_id: str) -> None:
    get_supabase().table("mission_schedules").update({
        "last_run_at": datetime.now(timezone.utc).isoformat(),
        "last_mission_id": mission_id,
    }).eq("id", schedule_id).execute()


async def alist_schedules() -> list[dict]:
    return await asyncio.to_thread(list_schedules)


async def ainsert_schedule(target: str, mission_type: str, cron: str, label: str | None = None) -> dict:
    return await asyncio.to_thread(insert_schedule, target, mission_type, cron, label)


async def adelete_schedule(schedule_id: str) -> None:
    await asyncio.to_thread(delete_schedule, schedule_id)


async def amark_schedule_ran(schedule_id: str, mission_id: str) -> None:
    await asyncio.to_thread(mark_schedule_ran, schedule_id, mission_id)
