"""HTTP demo path: POST /recommend then POST /events HEAVY_RAIN_ALERT."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.routes import get_conn
from app.main import app


def test_recommend_and_inject_heavy_rain(db):
    conn, ids = db

    def _override():
        yield conn

    app.dependency_overrides[get_conn] = _override
    try:
        client = TestClient(app)
        rec = client.post(
            f"/fields/{ids['field_id']}/recommend",
            json={
                "mock_weather": {
                    "rainfall_probability": 10,
                    "rainfall_mm_next_7d": 2.0,
                    "heavy_rain_alert": False,
                    "source": "mock",
                }
            },
        )
        assert rec.status_code == 200, rec.text
        body = rec.json()
        assert body["status"] in ("PLAN_GENERATED", "NO_FERTILIZER_NEEDED", "ABSTAIN")
        assert "confidence" in body

        injected = client.post(
            "/events",
            json={
                "type": "HEAVY_RAIN_ALERT",
                "field_id": ids["field_id"],
                "field_code": "TEST-001",
                "payload": {
                    "heavy_rain_alert": True,
                    "rainfall_probability": 90,
                    "rainfall_mm_next_7d": 80.0,
                },
                "actor": "demo",
            },
        )
        assert injected.status_code == 200, injected.text
        payload = injected.json()
        latest = payload["latest_plan"]
        if body["status"] != "ABSTAIN" and body.get("how_much"):
            assert latest["status"] == "PLAN_REVISED"
            assert latest["mode"] == "partial_replan"
            assert latest["how_much"] == body["how_much"]
        alerts = client.get(f"/fields/{ids['field_id']}/alerts")
        assert alerts.status_code == 200
        health = client.get("/health")
        assert health.json()["status"] == "ok"

        # Phase 3.2: /twin must reflect the just-injected heavy-rain event for the
        # frontend dashboard to show it — not a hardcoded stub, and activeAlert.title
        # must be the real alert_type (previously read a non-existent "type" key).
        twin = client.get(f"/fields/{ids['field_id']}/twin")
        assert twin.status_code == 200, twin.text
        twin_body = twin.json()
        assert twin_body["weather"]["heavy_rain_alert"] is True
        assert twin_body["weather"]["rainfall_mm_next_7d"] == 80.0
        assert twin_body["activeAlert"] is not None
        assert twin_body["activeAlert"]["title"] == "HEAVY_RAIN_ALERT"
        assert twin_body["activeAlert"]["description"]
    finally:
        app.dependency_overrides.clear()
