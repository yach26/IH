"""
Monitoring Agent — event-driven (doc 08). Not an LLM poller.

Listens on the in-process EventBus. The demo wow path is:

  PLAN_CREATED (ACTIVE/PROPOSED)
    → inject HEAVY_RAIN_ALERT
    → weather conflicts with application window
    → PLAN_INVALIDATED
    → selective re-plan [weather, validation, optimizer]
    → RECOMMENDATION_RECALCULATED
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Callable

from ..core.event_bus import get_bus
from ..core.events import Event, EventType

# Legacy in-process registry (kept for existing unit tests)
_handlers: list[tuple[str, Callable]] = []


def register_handler(event_type: str, handler: Callable) -> None:
    _handlers.append((event_type, handler))


def fire_event(event_type: str, **kwargs) -> None:
    """
    Legacy kwargs API. Preferred path is EventBus.publish(Event).
    kwargs: field_id, field_code, detail, db_path, conn, payload, ...
    """
    for registered_type, handler in list(_handlers):
        if registered_type == event_type:
            try:
                handler(**kwargs)
            except Exception as e:
                print(f"Monitoring Agent ERROR: Handler for {event_type} failed: {e}")

    conn = kwargs.get("conn")
    field_id = kwargs.get("field_id")
    if field_id is not None:
        event = Event.create(
            event_type,
            field_id=int(field_id),
            field_code=kwargs.get("field_code"),
            payload=kwargs.get("payload")
            or {"detail": kwargs.get("detail"), "db_path": kwargs.get("db_path")},
        )
        get_bus().publish(event, conn=conn)


def supersede_and_replan(
    conn: sqlite3.Connection,
    field_id: int,
    field_code: str,
    event_type: str,
    event_detail: str,
    orchestrator_fn: Callable,
) -> Any:
    """
    Legacy full-replan transaction (used by older tests).
    Prefer MonitoringAgent.on_event for selective re-plan.
    """
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """UPDATE recommendations
           SET status = 'SUPERSEDED', invalidated_at = ?
           WHERE field_id = ? AND status = 'PROPOSED'""",
        (now, field_id),
    )
    conn.commit()

    field_row = conn.execute(
        "SELECT * FROM field_active_crop WHERE field_id = ?", (field_id,)
    ).fetchone()
    if field_row is None:
        field_row = conn.execute(
            "SELECT * FROM fields WHERE field_id = ?", (field_id,)
        ).fetchone()

    new_result = None
    new_rec_id = None
    if field_row is not None:
        new_result = orchestrator_fn(conn, field_row)
        new_rec = conn.execute(
            """SELECT recommendation_id FROM recommendations
               WHERE field_id = ? AND status IN ('PROPOSED','ABSTAINED','NO_FERTILIZER_NEEDED')
               ORDER BY generated_at DESC LIMIT 1""",
            (field_id,),
        ).fetchone()
        new_rec_id = new_rec["recommendation_id"] if new_rec else None

    message = (
        f"Event '{event_type}' triggered automatic replanning for field {field_code}. "
        f"Previous PROPOSED recommendation(s) marked SUPERSEDED. "
        f"New recommendation generated. Detail: {event_detail}"
    )
    conn.execute(
        """INSERT INTO alerts
           (field_id, alert_type, severity, message, triggered_at, related_recommendation_id)
           VALUES (?,?,?,?,?,?)""",
        (
            field_id,
            event_type,
            "HIGH" if event_type == "HEAVY_RAIN_ALERT" else "MEDIUM",
            message,
            now,
            new_rec_id,
        ),
    )
    conn.commit()
    return new_result


def get_alerts(conn: sqlite3.Connection, field_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM alerts WHERE field_id = ? ORDER BY triggered_at DESC",
        (field_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_active_plan(conn: sqlite3.Connection, field_id: int) -> dict | None:
    row = conn.execute(
        """SELECT * FROM recommendations
           WHERE field_id = ? AND status = 'PROPOSED'
           ORDER BY generated_at DESC LIMIT 1""",
        (field_id,),
    ).fetchone()
    if row is None:
        return None
    try:
        plan = json.loads(row["plan_json"] or "{}")
    except json.JSONDecodeError:
        plan = {}
    plan["recommendation_id"] = row["recommendation_id"]
    plan["status_db"] = row["status"]
    return plan


def weather_conflicts(plan: dict | None, event: Event) -> bool:
    """
    Conflict if an application is still scheduled inside the rain window
    (when_detail.code != DEFER_RAIN) and the event is a heavy-rain alert,
    or if the plan itself still shows APPLY_NEXT_DRY_DAYS.
    """
    if not plan:
        return False
    payload = event.payload or {}
    if not payload.get("heavy_rain_alert", True):
        return False
    when = plan.get("when_detail") or {}
    if when.get("code") == "DEFER_RAIN":
        return False
    how_much = plan.get("how_much") or plan.get("plan_kg_ha") or {}
    urea = float(how_much.get("UREA_kg_ha") or 0)
    gap_n = float(((plan.get("why") or {}).get("gap") or {}).get("N") or 0)
    if urea <= 0 and gap_n <= 0:
        return False
    return True


class MonitoringAgent:
    def __init__(self, bus=None, conn: sqlite3.Connection | None = None) -> None:
        self.bus = bus or get_bus()
        self.conn = conn
        self.watched: set[int] = set()
        self.bus.subscribe(EventType.PLAN_CREATED.value, self._on_plan_created)
        self.bus.subscribe(EventType.HEAVY_RAIN_ALERT.value, self.on_event)
        self.bus.subscribe(EventType.SOIL_REPORT_UPDATED.value, self.on_event)
        self.bus.subscribe(EventType.WEATHER_FORECAST_CHANGED.value, self.on_event)
        self.bus.subscribe(EventType.CROP_STAGE_CHANGED.value, self.on_event)
        self.bus.subscribe(EventType.FERTILIZER_APPLIED.value, self.on_event)

    def bind(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def start_watching(self, field_id: int, plan: dict | None = None) -> None:
        self.watched.add(int(field_id))

    def _on_plan_created(self, event: Event) -> None:
        if event.payload.get("status") != "ABSTAIN":
            self.start_watching(event.field_id)

    def on_event(self, event: Event) -> None:
        conn = self.conn
        if conn is None:
            return
        self._audit(conn, event, "RECEIVED")

        if event.type == EventType.HEAVY_RAIN_ALERT.value:
            self._handle_heavy_rain(conn, event)
            return

        # Other events: selective re-plan without the weather-conflict gate
        from ..pipeline import EVENT_AGENT_MAP, RecommendationPipeline

        field_row = conn.execute(
            "SELECT * FROM field_active_crop WHERE field_id = ?",
            (event.field_id,),
        ).fetchone()
        if field_row is None:
            return
        agents = EVENT_AGENT_MAP.get(event.type, ("weather", "validation", "optimizer"))
        RecommendationPipeline(bus=self.bus).run(conn, field_row, agents=list(agents))

    def _handle_heavy_rain(self, conn: sqlite3.Connection, event: Event) -> None:
        from ..pipeline import RecommendationPipeline

        plan = get_active_plan(conn, event.field_id)
        if plan and weather_conflicts(plan, event):
            now = datetime.now(timezone.utc).isoformat()
            reason = (
                "HEAVY_RAIN_ALERT conflicts with the current application window "
                f"({plan.get('when')})."
            )
            self.bus.publish(
                Event.create(
                    EventType.PLAN_INVALIDATED,
                    field_id=event.field_id,
                    field_code=event.field_code,
                    payload={
                        "reason": reason,
                        "invalidated_recommendation_id": plan.get("recommendation_id"),
                    },
                ),
                conn=conn,
            )
            conn.execute(
                """UPDATE recommendations
                   SET status = 'SUPERSEDED', invalidated_at = ?
                   WHERE recommendation_id = ?""",
                (now, plan["recommendation_id"]),
            )
            conn.execute(
                """INSERT INTO alerts
                   (field_id, alert_type, severity, message, triggered_at,
                    related_recommendation_id)
                   VALUES (?,?,?,?,?,?)""",
                (
                    event.field_id,
                    EventType.HEAVY_RAIN_ALERT.value,
                    "HIGH",
                    reason,
                    now,
                    plan.get("recommendation_id"),
                ),
            )
            conn.commit()
            self._audit(conn, event, "PLAN_INVALIDATED")

            field_row = conn.execute(
                "SELECT * FROM field_active_crop WHERE field_id = ?",
                (event.field_id,),
            ).fetchone()
            mock_weather = {
                "rainfall_probability": (event.payload or {}).get("rainfall_probability", 90),
                "rainfall_mm_next_7d": (event.payload or {}).get("rainfall_mm_next_7d", 80),
                "heavy_rain_alert": True,
                "source": "event_injection",
            }
            if field_row is not None:
                RecommendationPipeline(bus=self.bus).run(
                    conn,
                    field_row,
                    agents=["weather", "validation", "optimizer"],
                    mock_weather=mock_weather,
                    previous_plan=plan,
                )
        else:
            self._audit(conn, event, "NO_CONFLICT")

    def _audit(self, conn: sqlite3.Connection, event: Event, action: str) -> None:
        conn.execute(
            """INSERT INTO audit_log (entity_type, entity_id, action, actor, new_value)
               VALUES (?,?,?,?,?)""",
            (
                "event",
                event.field_id,
                action,
                event.actor,
                json.dumps({"type": event.type, "payload": event.payload}),
            ),
        )
        conn.commit()


_MONITOR: MonitoringAgent | None = None


def get_monitoring_agent() -> MonitoringAgent:
    global _MONITOR
    if _MONITOR is None:
        _MONITOR = MonitoringAgent()
    return _MONITOR


def make_replan_handler(event_type: str):
    """Legacy handler factory — routes through fire_event / MonitoringAgent."""

    def handler(field_id: int, field_code: str, detail: str, db_path: str, **kwargs):
        import sqlite3 as _sqlite3
        from .orchestrator import run_orchestrated_ledger

        conn = _sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = _sqlite3.Row
        try:
            supersede_and_replan(
                conn=conn,
                field_id=field_id,
                field_code=field_code,
                event_type=event_type,
                event_detail=detail,
                orchestrator_fn=run_orchestrated_ledger,
            )
        finally:
            conn.close()

    return handler


def register_all_handlers() -> None:
    """Idempotent: ensure MonitoringAgent is attached to the process bus."""
    get_monitoring_agent()


register_all_handlers()
