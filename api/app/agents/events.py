"""In-memory asyncio.Queue registry for SSE streaming.

Each running mission gets a queue. Agents call emit() to push events;
the SSE route reads from the queue and forwards to the browser.
"""

import asyncio
from typing import Optional

_queues: dict[str, asyncio.Queue] = {}

# Sentinel that tells the SSE route to close the stream.
STREAM_DONE: dict = {"__done__": True}


def create_queue(mission_id: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _queues[mission_id] = q
    return q


def get_queue(mission_id: str) -> Optional[asyncio.Queue]:
    return _queues.get(mission_id)


def remove_queue(mission_id: str) -> None:
    _queues.pop(mission_id, None)


async def emit(
    mission_id: str,
    agent: str,
    event_type: str,
    message: str,
    product: str | None = None,
    payload: dict | None = None,
) -> None:
    q = _queues.get(mission_id)
    if q:
        await q.put({
            "agent": agent,
            "event_type": event_type,
            "message": message,
            "bright_data_product": product,
            "payload": payload or {},
        })


async def emit_done(mission_id: str) -> None:
    q = _queues.get(mission_id)
    if q:
        await q.put(STREAM_DONE)
