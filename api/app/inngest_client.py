"""Inngest client and scheduled mission functions for War Room AI.

Dev server:  npx inngest-cli@latest dev -u http://localhost:8000/api/inngest
Docs:        https://www.inngest.com/docs/sdk/serve
"""

import logging

import inngest

log = logging.getLogger(__name__)

client = inngest.Inngest(app_id="warroom-ai", is_production=False)


@client.create_function(
    fn_id="missions-run",
    trigger=inngest.TriggerEvent(event="warroom/missions.run"),
)
async def run_mission_fn(ctx: inngest.Context, step: inngest.Step) -> dict:
    """Event-triggered: run any mission from a schedule or ad-hoc trigger."""
    target: str = ctx.event.data.get("target", "")
    mission_type: str = ctx.event.data.get("mission_type", "account_pulse")
    schedule_id: str | None = ctx.event.data.get("schedule_id")

    if not target:
        return {"error": "target is required"}

    log.info("Inngest: running mission target=%s type=%s", target, mission_type)

    from app.db import client as db
    from app.agents import events as ev
    from app.agents.graph import mission_graph
    from app.agents.state import MissionState
    import asyncio

    mission = await db.ainsert_mission(target, mission_type)
    mission_id = str(mission["id"])
    ev.create_queue(mission_id)

    initial_state: MissionState = {
        "mission_id": mission_id,
        "mission_type": mission_type,
        "target": target,
        "context": f"Recurring schedule (id={schedule_id})" if schedule_id else None,
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

    try:
        await db.aupdate_mission_status(mission_id, "running")
        final_state = await mission_graph.ainvoke(initial_state)

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

        await db.ainsert_brief(mission_id, {
            "market_move_score": final_state.get("market_move_score", 0),
            "recommended_move": final_state.get("recommended_move", "MONITOR"),
            "confidence_score": final_state.get("confidence_score", 0),
            "executive_summary": final_state.get("executive_summary", ""),
            "action_pack": final_state.get("action_pack", {}),
            "bright_data_calls": final_state.get("bright_data_calls", []),
        })
        await db.aupdate_mission_status(mission_id, "completed")

        if schedule_id:
            try:
                await db.amark_schedule_ran(schedule_id, mission_id)
            except Exception:
                pass

    except Exception as exc:
        log.error("Inngest mission failed: %s", exc)
        try:
            await db.aupdate_mission_status(mission_id, "failed")
        except Exception:
            pass
    finally:
        try:
            await ev.emit_done(mission_id)
        except Exception:
            pass

    return {"mission_id": mission_id, "status": "completed"}


@client.create_function(
    fn_id="missions-weekly-anthropic",
    trigger=inngest.TriggerCron(cron="0 9 * * 1"),  # Monday 9am UTC
)
async def weekly_anthropic_fn(ctx: inngest.Context, step: inngest.Step) -> dict:
    """Pre-loaded schedule: Anthropic account_pulse every Monday 9am UTC."""
    await step.send_event(
        "trigger-anthropic",
        inngest.Event(
            name="warroom/missions.run",
            data={
                "target": "anthropic.com",
                "mission_type": "account_pulse",
                "schedule_id": "preset-anthropic",
            },
        ),
    )
    return {"triggered": True}


FUNCTIONS = [run_mission_fn, weekly_anthropic_fn]
