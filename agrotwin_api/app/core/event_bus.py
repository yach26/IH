"""
In-process event bus (hackathon MVP).

Production would swap this for Redis pub/sub or Celery without changing
publish/subscribe call sites. Handlers run synchronously and in order.
Every published event is optionally persisted to the `events` table.
"""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from typing import Callable, Protocol

from .events import Event

Handler = Callable[[Event], None]


class EventBus(Protocol):
    def subscribe(self, event_type: str, handler: Handler) -> None: ...
    def unsubscribe(self, event_type: str, handler: Handler) -> None: ...
    def publish(self, event: Event, conn: sqlite3.Connection | None = None) -> Event: ...


class InMemoryEventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)
        self._log: list[Event] = []

    def subscribe(self, event_type: str, handler: Handler) -> None:
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Handler) -> None:
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    def publish(self, event: Event, conn: sqlite3.Connection | None = None) -> Event:
        self._log.append(event)
        if conn is not None:
            persist_event(conn, event)
        for handler in list(self._handlers.get(event.type, [])):
            handler(event)
        # wildcard subscribers
        for handler in list(self._handlers.get("*", [])):
            handler(event)
        return event

    @property
    def history(self) -> list[Event]:
        return list(self._log)

    def clear(self) -> None:
        self._log.clear()
        self._handlers.clear()


def persist_event(conn: sqlite3.Connection, event: Event) -> int:
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO events (event_type, field_id, payload, actor, created_at)
           VALUES (?,?,?,?,?)""",
        (
            event.type,
            event.field_id,
            json.dumps(event.payload),
            event.actor,
            event.timestamp,
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


_BUS: InMemoryEventBus | None = None


def get_bus() -> InMemoryEventBus:
    global _BUS
    if _BUS is None:
        _BUS = InMemoryEventBus()
    return _BUS


def reset_bus() -> InMemoryEventBus:
    global _BUS
    _BUS = InMemoryEventBus()
    return _BUS
