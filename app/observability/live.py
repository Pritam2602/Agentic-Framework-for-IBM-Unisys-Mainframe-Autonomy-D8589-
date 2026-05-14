"""In-process live observability event stream."""

from __future__ import annotations

import asyncio
import json
from collections import deque
from typing import Any, AsyncIterator, Deque, Dict, Set


MAX_RECENT_EVENTS = 200
_recent_events: Deque[Dict[str, Any]] = deque(maxlen=MAX_RECENT_EVENTS)
_subscribers: Set[asyncio.Queue[Dict[str, Any]]] = set()


def publish_event(event: Dict[str, Any]) -> None:
    _recent_events.appendleft(event)
    dead: list[asyncio.Queue[Dict[str, Any]]] = []
    for queue in _subscribers:
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            dead.append(queue)
    for queue in dead:
        _subscribers.discard(queue)


def recent_events(limit: int = 50) -> list[Dict[str, Any]]:
    return list(_recent_events)[:limit]


async def event_stream() -> AsyncIterator[str]:
    queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=100)
    _subscribers.add(queue)
    try:
        for event in reversed(recent_events(limit=20)):
            yield f"data: {json.dumps(event, default=str)}\n\n"
        while True:
            event = await queue.get()
            yield f"data: {json.dumps(event, default=str)}\n\n"
    finally:
        _subscribers.discard(queue)
