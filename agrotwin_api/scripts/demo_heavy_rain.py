"""
In-process demo of the heavy-rain wow path (doc 08).

Does not require a running HTTP server. Uses an in-memory SQLite twin.

Run from agrotwin_api/:
    python scripts/demo_heavy_rain.py
"""

from __future__ import annotations

import os
import sqlite3
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tests.conftest import make_test_db  # noqa: E402
from app.core.event_bus import InMemoryEventBus  # noqa: E402
from app.core.events import Event, EventType  # noqa: E402
from app.pipeline import RecommendationPipeline  # noqa: E402
from app.agents.monitoring_agent import MonitoringAgent  # noqa: E402


def main() -> None:
    conn, ids = make_test_db()
    field_row = conn.execute(
        "SELECT * FROM field_active_crop WHERE field_id = ?",
        (ids["field_id"],),
    ).fetchone()
    bus = InMemoryEventBus()
    pipeline = RecommendationPipeline(bus=bus)
    monitor = MonitoringAgent(bus=bus, conn=conn)

    dry = {
        "rainfall_probability": 10,
        "rainfall_mm_next_7d": 2.0,
        "heavy_rain_alert": False,
        "source": "mock",
    }
    first = pipeline.run(conn, field_row, mock_weather=dry)
    print("=== 1. Initial plan ===")
    print(f"  status     : {first['status']}")
    print(f"  what       : {first['what']}")
    print(f"  how_much   : {first['how_much']}")
    print(f"  when       : {first['when']}")
    print(f"  confidence : {first['confidence']}")
    print(f"  rec_id     : {first.get('recommendation_id')}")

    rain = Event.create(
        EventType.HEAVY_RAIN_ALERT,
        field_id=ids["field_id"],
        field_code="TEST-001",
        payload={
            "heavy_rain_alert": True,
            "rainfall_probability": 90,
            "rainfall_mm_next_7d": 80.0,
        },
        actor="demo",
    )
    bus.publish(rain, conn=conn)

    latest = conn.execute(
        """SELECT recommendation_id, status, plan_json, invalidated_at
           FROM recommendations WHERE field_id = ?
           ORDER BY recommendation_id DESC LIMIT 1""",
        (ids["field_id"],),
    ).fetchone()
    import json

    plan = json.loads(latest["plan_json"])
    print("\n=== 2. After HEAVY_RAIN_ALERT ===")
    print(f"  status     : {plan.get('status')}")
    print(f"  mode       : {plan.get('mode')}")
    print(f"  agents_run : {plan.get('agents_run')}")
    print(f"  when       : {plan.get('when')}")
    print(f"  how_much   : {plan.get('how_much')}")
    print(f"  old rec    : invalidated_at={latest['invalidated_at']}")
    print(f"  event types: {[e.type for e in bus.history]}")
    print("\nQuantities unchanged (ledger is numeric truth):",
          first.get("how_much") == plan.get("how_much"))
    conn.close()
    _ = monitor  # keep watching for the script lifetime


if __name__ == "__main__":
    main()
