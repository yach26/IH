"""
Integration tests for RecommendationPipeline (doc 05).

  - Happy path → proof-carrying PLAN_GENERATED
  - Abstain path → missing soil
  - Partial re-plan → weather + validation + optimizer only
"""

from __future__ import annotations

import json

from app.core.event_bus import InMemoryEventBus
from app.pipeline import RecommendationPipeline

DRY = {
    "rainfall_probability": 10,
    "rainfall_mm_next_7d": 2.0,
    "heavy_rain_alert": False,
    "source": "mock",
}
RAIN = {
    "rainfall_probability": 90,
    "rainfall_mm_next_7d": 80.0,
    "heavy_rain_alert": True,
    "source": "mock",
}

PROOF_KEYS = (
    "status",
    "what",
    "how_much",
    "when",
    "why",
    "based_on",
    "confidence",
    "flags",
    "data_quality",
)


class TestPipelineHappyPath:
    def test_full_run_returns_proof_carrying_plan(self, conn, field_row):
        bus = InMemoryEventBus()
        pipe = RecommendationPipeline(bus=bus)
        result = pipe.run(conn, field_row, mock_weather=DRY)
        for key in PROOF_KEYS:
            assert key in result, f"missing proof key {key}"
        assert result["status"] in ("PLAN_GENERATED", "NO_FERTILIZER_NEEDED")
        assert result["how_much"] is not None
        assert "DAP_kg_ha" in result["how_much"] or result["status"] == "NO_FERTILIZER_NEEDED"
        assert result["numeric_source"].startswith("ledger")
        assert result["mode"] == "full"
        assert "soil" in result["agents_run"]
        assert "crop" in result["agents_run"]
        assert "weather" in result["agents_run"]
        assert "ledger" in result["agents_run"]
        assert "optimizer" in result["agents_run"]
        assert "validation" in result["agents_run"]
        assert result["pipeline_audit"]
        assert any(e.type == "PLAN_CREATED" for e in bus.history)

    def test_quantities_match_ledger_heuristic(self, conn, field_row):
        from app.ledger import run_field_ledger, convert_gap_to_products, get_products

        ledger = run_field_ledger(conn, field_row)
        products = get_products(conn)
        expected = convert_gap_to_products(
            ledger["gap"]["N"], ledger["gap"]["P2O5"], ledger["gap"]["K2O"], products
        )
        pipe = RecommendationPipeline(bus=InMemoryEventBus())
        result = pipe.run(conn, field_row, mock_weather=DRY, emit_events=False)
        if result["status"] == "PLAN_GENERATED":
            assert result["how_much"]["DAP_kg_ha"] == expected["DAP_kg_ha"]
            assert result["how_much"]["UREA_kg_ha"] == expected["UREA_kg_ha"]
            assert result["how_much"]["MOP_kg_ha"] == expected["MOP_kg_ha"]

    def test_cost_estimate_is_labelled_engineering_default(self, conn, field_row):
        result = RecommendationPipeline(bus=InMemoryEventBus()).run(
            conn, field_row, mock_weather=DRY, emit_events=False
        )
        cite = (result.get("based_on") or {}).get("cost_citation") or ""
        assert "ENGINEERING_DEFAULT" in cite or "Gap #8" in cite


class TestPipelineAbstain:
    def test_abstain_when_soil_missing(self, conn, ids, field_row):
        conn.execute("DELETE FROM soil_tests WHERE field_id = ?", (ids["field_id"],))
        conn.commit()
        result = RecommendationPipeline(bus=InMemoryEventBus()).run(
            conn, field_row, mock_weather=DRY, emit_events=False
        )
        assert result["status"] == "ABSTAIN"
        assert result["how_much"] is None
        assert result["reason"]
        assert result["required_actions"]
        assert result["confidence"] == "ABSTAIN"

    def test_abstain_when_crop_missing(self, conn, ids):
        conn.execute("UPDATE field_crops SET is_active = 0 WHERE field_id = ?", (ids["field_id"],))
        conn.commit()
        row = conn.execute(
            "SELECT * FROM field_active_crop WHERE field_id = ?", (ids["field_id"],)
        ).fetchone()
        result = RecommendationPipeline(bus=InMemoryEventBus()).run(
            conn, row, mock_weather=DRY, emit_events=False
        )
        assert result["status"] == "ABSTAIN"


class TestPipelinePartialReplan:
    def test_replan_runs_only_requested_agents(self, conn, field_row):
        bus = InMemoryEventBus()
        pipe = RecommendationPipeline(bus=bus)
        first = pipe.run(conn, field_row, mock_weather=DRY, emit_events=False)
        assert first["status"] in ("PLAN_GENERATED", "NO_FERTILIZER_NEEDED")
        second = pipe.run(
            conn,
            field_row,
            agents=["weather", "validation", "optimizer"],
            mock_weather=RAIN,
            emit_events=False,
        )
        assert second["status"] == "PLAN_REVISED"
        assert second["mode"] == "partial_replan"
        assert "weather" in second["agents_run"]
        assert "optimizer" in second["agents_run"]
        assert "validation" in second["agents_run"]
        assert "soil" not in second["agents_run"]
        assert "crop" not in second["agents_run"]
        assert "ledger" not in second["agents_run"]
        # Quantities stay ledger-identical
        if first.get("how_much") and second.get("how_much"):
            assert first["how_much"] == second["how_much"]
        assert second["when_detail"]["code"] == "DEFER_RAIN"
        assert second["validation"]["is_valid"] is False
        assert any("WEATHER_CONFLICT" in b for b in second["validation"]["blocking_issues"])
        # Old plan invalidated
        old = conn.execute(
            "SELECT status, invalidated_at FROM recommendations WHERE recommendation_id = ?",
            (first["recommendation_id"],),
        ).fetchone()
        assert old["status"] == "SUPERSEDED"
        assert old["invalidated_at"] is not None
        stored = conn.execute(
            "SELECT plan_json FROM recommendations WHERE recommendation_id = ?",
            (second["recommendation_id"],),
        ).fetchone()
        blob = json.loads(stored["plan_json"])
        assert blob["status"] == "PLAN_REVISED"
