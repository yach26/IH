"""
Monitoring Agent — event bus and automatic replanning.

Responsibility:
  - Listen for state-change events (e.g., SOIL_REPORT_UPDATED,
    HEAVY_RAIN_ALERT, FERTILIZER_APPLIED).
  - Supersede the current PROPOSED recommendation for a field.
  - Trigger the Orchestrator to generate a fresh recommendation.
  - Write an audit trail (Alerts) explaining *why* the replan occurred.

Architecture note:
  This is implemented as a synchronous, in-process event bus for the prototype.
  In production, this would be an async message queue (Redis/Celery) as
  specified in the architecture brief.
"""

import sqlite3
from datetime import datetime, timezone
from typing import Callable, Any

# Simple in-process registry: list of (event_type, handler_callable)
_handlers: list[tuple[str, Callable]] = []


def register_handler(event_type: str, handler: Callable):
    """Registers a callback for an event type."""
    _handlers.append((event_type, handler))


def fire_event(event_type: str, **kwargs):
    """
    Fires an event synchronously.
    kwargs must include at least: field_id, field_code, detail, db_path
    """
    for registered_type, handler in _handlers:
        if registered_type == event_type:
            try:
                handler(**kwargs)
            except Exception as e:
                print(f"Monitoring Agent ERROR: Handler for {event_type} failed: {e}")


def supersede_and_replan(
    conn: sqlite3.Connection,
    field_id: int,
    field_code: str,
    event_type: str,
    event_detail: str,
    orchestrator_fn: Callable,
) -> Any:
    """
    The core replan transaction:
      1. Marks any 'PROPOSED' recommendations for this field as 'SUPERSEDED'.
      2. Calls the orchestrator to generate a new plan (which writes a new PROPOSED rec).
      3. Writes an alert explaining the replan.
    """
    # Step 1: supersede existing PROPOSED recs
    conn.execute(
        """UPDATE recommendations SET status = 'SUPERSEDED'
           WHERE field_id = ? AND status = 'PROPOSED'""",
        (field_id,),
    )
    conn.commit()

    # Step 2: replan
    field_row = conn.execute(
        "SELECT * FROM fields WHERE field_id = ?", (field_id,)
    ).fetchone()

    new_result = None
    new_rec_id = None
    if field_row is not None:
        new_result = orchestrator_fn(conn, field_row)
        # The orchestrator already writes the new rec via write_ledger_result.
        # Fetch its ID.
        new_rec = conn.execute(
            """SELECT recommendation_id FROM recommendations
               WHERE field_id = ? AND status IN ('PROPOSED','ABSTAINED','NO_FERTILIZER_NEEDED')
               ORDER BY generated_at DESC LIMIT 1""",
            (field_id,),
        ).fetchone()
        new_rec_id = new_rec["recommendation_id"] if new_rec else None

    # Step 3: write alert
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
            datetime.now(timezone.utc).isoformat(),
            new_rec_id,
        ),
    )
    conn.commit()
    return new_result


def get_alerts(conn: sqlite3.Connection, field_id: int) -> list[dict]:
    """Returns all alerts for a field, newest first."""
    rows = conn.execute(
        "SELECT * FROM alerts WHERE field_id = ? ORDER BY triggered_at DESC",
        (field_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Handler factory — creates replan handlers for each event type.
# The orchestrator_fn is imported lazily inside the handler to avoid the
# circular-import: monitoring_agent → orchestrator → monitoring_agent.
# ---------------------------------------------------------------------------

def make_replan_handler(event_type: str):
    """
    Returns a handler callable that, when fired for a field, runs
    supersede_and_replan() using the orchestrator as the replan function.
    The db_path kwarg is required so the handler opens its own connection
    (synchronous, in-process; no thread safety issue at single-request scale).
    """
    def handler(field_id: int, field_code: str, detail: str, db_path: str, **_kwargs):
        # Lazy import to avoid circular dependency
        from ..agents.orchestrator import run_orchestrated_ledger
        import sqlite3 as _sqlite3

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


def register_all_handlers():
    """
    Registers replan handlers for all three supported events.
    Call this once at app startup (from main.py's lifespan or startup event).
    Idempotent: duplicate registrations are prevented by checking existing list.
    """
    registered_types = {etype for etype, _ in _handlers}
    for etype in ("HEAVY_RAIN_ALERT", "SOIL_REPORT_UPDATED", "FERTILIZER_APPLIED"):
        if etype not in registered_types:
            register_handler(etype, make_replan_handler(etype))


# Auto-register handlers when this module is imported.
# This ensures handlers are present regardless of whether the FastAPI
# startup event has fired (important for test clients and direct imports).
register_all_handlers()
