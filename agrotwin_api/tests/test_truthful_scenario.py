import json
from app.core.scenario import run_scenario


def test_missing_baseline_has_no_invented_values_or_writes(conn, field_row):
    before = conn.total_changes
    result = run_scenario(conn, field_row, fertilizer_delta_pct=-20)
    assert result["status"] == "NO_DATA"
    assert result["original"] is None
    assert result["simulated"] is None
    assert result["deltaYield"] is None
    assert conn.total_changes == before


def test_invalid_rainfall_rejected(conn, field_row):
    import pytest
    with pytest.raises(ValueError):
        run_scenario(conn, field_row, rainfall_mm=-1)


def test_incomplete_week_is_not_a_valid_forecast(conn, ids, monkeypatch):
    from app.agents import weather_agent as weather
    class Response:
        def raise_for_status(self): pass
        def json(self):
            return {"daily": {"precipitation_sum": [0, 0], "precipitation_probability_max": [0, 0]}}
    monkeypatch.setattr(weather.requests, "get", lambda *a, **kw: Response())
    result = weather.get_weather_context(conn, ids["field_id"], 16.7, 74.2)
    assert result["snapshot"] is None
    assert result["status"] == "PROVIDER_ERROR"


def test_saved_scenario_scales_cost_without_writes(conn, field_row, monkeypatch):
    from app.agents import knowledge_agent
    from app.pipeline import RecommendationPipeline
    from app.core.event_bus import InMemoryEventBus
    monkeypatch.setattr(knowledge_agent, "retrieve_evidence", lambda **kwargs: [])
    proof = RecommendationPipeline(bus=InMemoryEventBus()).run(
        conn, field_row, mock_weather={"rainfall_probability": 0, "rainfall_mm_next_7d": 0, "heavy_rain_alert": False},
        emit_events=False)
    assert proof["validation"]["is_valid"]
    before = conn.total_changes
    result = run_scenario(conn, field_row, fertilizer_delta_pct=-20, rainfall_mm=0)
    assert result["status"] == "SIMULATION", result["reason"]
    assert result["original"]["quantities"] == proof["how_much"]
    for product, quantity in proof["how_much"].items():
        assert result["simulated"]["quantities"][product] == round(quantity * .8, 2)
    assert result["deltaCost"] < 0
    assert result["deltaYield"] is None
    assert result["simulated"]["rainfallMm"] == 0
    assert conn.total_changes == before
