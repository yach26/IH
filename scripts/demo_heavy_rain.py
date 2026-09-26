#!/usr/bin/env python3
"""
Demo the closed-loop wow path (doc 08) without a running frontend.

  1. Generate a recommendation (ACTIVE/PROPOSED).
  2. Inject HEAVY_RAIN_ALERT.
  3. Monitoring Agent invalidates the plan.
  4. Orchestrator re-runs only weather + validation + optimizer.
  5. Revised plan defers the application window; kg/ha stay ledger-identical.

Usage (from repo root):

    python scripts/demo_heavy_rain.py

Or against a running API (after `uvicorn app.main:app` in agrotwin_api/):

    python scripts/demo_heavy_rain.py --http http://127.0.0.1:8000 --field SYN-001
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
API = os.path.join(ROOT, "agrotwin_api")
sys.path.insert(0, API)


def _in_memory_demo() -> None:
    from app.agents.monitoring_agent import MonitoringAgent, get_alerts
    from app.core.event_bus import InMemoryEventBus
    from app.core.events import Event, EventType
    from app.pipeline import RecommendationPipeline
    from tests.conftest import make_test_db

    conn, ids = make_test_db()
    field_row = conn.execute(
        "SELECT * FROM field_active_crop WHERE field_id = ?",
        (ids["field_id"],),
    ).fetchone()
    bus = InMemoryEventBus()
    pipe = RecommendationPipeline(bus=bus)
    monitor = MonitoringAgent(bus=bus, conn=conn)

    dry = {
        "rainfall_probability": 10,
        "rainfall_mm_next_7d": 2.0,
        "heavy_rain_alert": False,
        "source": "mock",
    }
    first = pipe.run(conn, field_row, mock_weather=dry)
    print("=== 1. PLAN_CREATED ===")
    print(
        json.dumps(
            {
                "status": first["status"],
                "what": first["what"],
                "how_much": first["how_much"],
                "when": first["when"],
                "confidence": first["confidence"],
                "recommendation_id": first["recommendation_id"],
            },
            indent=2,
        )
    )

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
    print("\n=== 2. Inject HEAVY_RAIN_ALERT ===")
    bus.publish(rain, conn=conn)
    print("event types:", [e.type for e in bus.history])

    latest = conn.execute(
        """SELECT recommendation_id, status, plan_json, invalidated_at
           FROM recommendations WHERE field_id = ?
           ORDER BY recommendation_id DESC LIMIT 1""",
        (ids["field_id"],),
    ).fetchone()
    plan = json.loads(latest["plan_json"])
    print("\n=== 3–5. REVISED PLAN ===")
    print(
        json.dumps(
            {
                "status": plan.get("status"),
                "mode": plan.get("mode"),
                "agents_run": plan.get("agents_run"),
                "what": plan.get("what"),
                "how_much": plan.get("how_much"),
                "when": plan.get("when"),
                "quantities_unchanged": plan.get("how_much") == first.get("how_much"),
                "watched": ids["field_id"] in monitor.watched,
                "alerts": [a["alert_type"] for a in get_alerts(conn, ids["field_id"])],
            },
            indent=2,
        )
    )
    conn.close()


def _http_demo(base: str, field: str) -> None:
    import urllib.error
    import urllib.request

    def _req(method: str, path: str, body: dict | None = None) -> dict:
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(base.rstrip("/") + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise SystemExit(f"{method} {path} failed: {e.read().decode('utf-8', errors='replace')}") from e

    print("=== 1. POST /fields/{field}/recommend ===")
    rec = _req(
        "POST",
        f"/fields/{field}/recommend",
        {
            "mock_weather": {
                "rainfall_probability": 10,
                "rainfall_mm_next_7d": 2.0,
                "heavy_rain_alert": False,
                "source": "mock",
            }
        },
    )
    print(json.dumps({"status": rec.get("status"), "when": rec.get("when"), "how_much": rec.get("how_much")}, indent=2))

    print("\n=== 2. POST /events  HEAVY_RAIN_ALERT ===")
    out = _req(
        "POST",
        "/events",
        {
            "type": "HEAVY_RAIN_ALERT",
            "field_code": field if not field.isdigit() else None,
            "field_id": int(field) if field.isdigit() else None,
            "payload": {
                "heavy_rain_alert": True,
                "rainfall_probability": 90,
                "rainfall_mm_next_7d": 80.0,
            },
            "actor": "demo",
        },
    )
    print(json.dumps(out.get("latest_plan"), indent=2))
    print("alerts:", [a.get("alert_type") for a in out.get("alerts") or []])


def main() -> None:
    parser = argparse.ArgumentParser(description="AgroTwin heavy-rain re-plan demo")
    parser.add_argument("--http", default="", help="Base URL of running API, e.g. http://127.0.0.1:8000")
    parser.add_argument("--field", default="SYN-001", help="field_code or field_id for --http mode")
    args = parser.parse_args()
    if args.http:
        _http_demo(args.http, args.field)
    else:
        _in_memory_demo()


if __name__ == "__main__":
    main()
