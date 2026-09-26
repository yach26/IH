"""
Integration test for the demo wow path (doc 08):

  PLAN_CREATED → HEAVY_RAIN_ALERT → PLAN_INVALIDATED
  → selective re-plan (weather, validation, optimizer)
  → RECOMMENDATION_RECALCULATED
"""

from app.agents.monitoring_agent import MonitoringAgent, get_alerts, weather_conflicts
from app.core.event_bus import InMemoryEventBus
from app.core.events import Event, EventType
from app.pipeline import RecommendationPipeline

DRY = {
    "rainfall_probability": 10,
    "rainfall_mm_next_7d": 2.0,
    "heavy_rain_alert": False,
    "source": "mock",
}


class TestHeavyRainWowPath:
    def test_full_wow_path(self, conn, ids, field_row):
        bus = InMemoryEventBus()
        pipe = RecommendationPipeline(bus=bus)
        monitor = MonitoringAgent(bus=bus, conn=conn)

        first = pipe.run(conn, field_row, mock_weather=DRY)
        assert first["status"] in ("PLAN_GENERATED", "NO_FERTILIZER_NEEDED")
        assert first["when_detail"]["code"] != "DEFER_RAIN"
        assert any(e.type == EventType.PLAN_CREATED.value for e in bus.history)

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
        assert weather_conflicts(first, rain) is True
        bus.publish(rain, conn=conn)

        types = [e.type for e in bus.history]
        assert EventType.HEAVY_RAIN_ALERT.value in types
        assert EventType.PLAN_INVALIDATED.value in types
        assert EventType.RECOMMENDATION_RECALCULATED.value in types

        old = conn.execute(
            "SELECT status, invalidated_at, superseded_by FROM recommendations WHERE recommendation_id = ?",
            (first["recommendation_id"],),
        ).fetchone()
        assert old["status"] == "SUPERSEDED"
        assert old["invalidated_at"] is not None

        latest = conn.execute(
            """SELECT recommendation_id, status, plan_json FROM recommendations
               WHERE field_id = ? AND status = 'PROPOSED'
               ORDER BY recommendation_id DESC LIMIT 1""",
            (ids["field_id"],),
        ).fetchone()
        assert latest is not None
        import json

        plan = json.loads(latest["plan_json"])
        assert plan["status"] == "PLAN_REVISED"
        assert plan["mode"] == "partial_replan"
        assert "weather" in plan["agents_run"]
        assert "soil" not in plan["agents_run"]
        assert plan["when_detail"]["code"] == "DEFER_RAIN"
        if first.get("how_much") and plan.get("how_much"):
            assert plan["how_much"] == first["how_much"]

        alerts = get_alerts(conn, ids["field_id"])
        assert any(a["alert_type"] == "HEAVY_RAIN_ALERT" for a in alerts)
        audit = conn.execute(
            "SELECT action FROM audit_log WHERE entity_id = ?", (ids["field_id"],)
        ).fetchall()
        actions = {r["action"] for r in audit}
        assert "PLAN_INVALIDATED" in actions
        assert ids["field_id"] in monitor.watched

    def test_no_conflict_when_already_deferred(self):
        plan = {"when_detail": {"code": "DEFER_RAIN"}, "how_much": {"UREA_kg_ha": 50}}
        rain = Event.create("HEAVY_RAIN_ALERT", field_id=1, payload={"heavy_rain_alert": True})
        assert weather_conflicts(plan, rain) is False
