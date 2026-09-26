"""
tests/test_agents.py — unit tests for all six agents + orchestrator.

Each agent is tested in ISOLATION via an in-memory SQLite database that
mirrors the production schema (schema_sqlite.sql). No network calls are
made (weather_agent uses mock_snapshot). No LLM is invoked.

Run:
    cd agrotwin_api
    python -m pytest tests/test_agents.py -v

Requires:
    pip install pytest scipy rank-bm25 requests
"""

import json
import os
import sqlite3
import sys
import pytest

# ── Make root importable ───────────────────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

SCHEMA_PATH = os.path.join(ROOT, "schema_sqlite.sql")


# ── Shared fixture: in-memory DB seeded with minimal data ────────────────────

@pytest.fixture
def db():
    """
    Returns (conn, ids) where:
      conn — in-memory sqlite3.Connection with row_factory set
      ids  — dict with field_id, crop_id, soil_test_id, region_id, district_id

    Seeded with:
     - 1 region, 1 district, 1 field
     - 1 crop (SUGARCANE), 1 fertilizer_recommendation (PRE_SEASONAL)
     - 3 fertilizer_products (UREA, DAP, MOP)
     - 1 soil_test (dated today -> fresh)
     - 1 field_crop (active, SUGARCANE, PRE_SEASONAL)
    """
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")

    with open(SCHEMA_PATH) as f:
        c.executescript(f.read())

    # Region + District
    c.execute("INSERT INTO regions (region_code, region_name) VALUES ('MH','Maharashtra')")
    region_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    c.execute(
        "INSERT INTO districts (region_id, district_code, district_name) VALUES (?,?,?)",
        (region_id, "KOLHAPUR", "Kolhapur"),
    )
    district_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Field
    c.execute(
        """INSERT INTO fields
           (region_id, district_id, field_code, area_ha, irrigation_type, lat, lon)
           VALUES (?,?,?,?,?,?,?)""",
        (region_id, district_id, "TEST-001", 2.0, "Irrigated", 16.7, 74.2),
    )
    field_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Crop
    c.execute("INSERT INTO crops (crop_code, crop_name) VALUES ('SUGARCANE','Sugarcane')")
    crop_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Fertilizer products
    for code, name, n, p, k in [
        ("UREA", "Urea", 46.0, 0.0, 0.0),
        ("DAP",  "DAP",  18.0, 46.0, 0.0),
        ("MOP",  "MOP",   0.0,  0.0, 60.0),
    ]:
        c.execute(
            "INSERT INTO fertilizer_products "
            "(product_code, product_name, n_percent, p2o5_percent, k2o_percent) "
            "VALUES (?,?,?,?,?)",
            (code, name, n, p, k),
        )

    # Fertilizer recommendation
    c.execute(
        """INSERT INTO fertilizer_recommendations
           (crop_id, recommendation_type, n_kg_ha, p2o5_kg_ha, k2o_kg_ha, source_citation)
           VALUES (?,?,?,?,?,?)""",
        (crop_id, "PRE_SEASONAL", 340, 170, 170, "mpkv_icar_rdf.md, Sugarcane pre-seasonal"),
    )

    # Soil test (fresh -- today)
    from datetime import date
    c.execute(
        """INSERT INTO soil_tests
           (field_id, test_date, n_kg_ha, p_kg_ha, k_kg_ha, ph, oc_percent, source)
           VALUES (?,?,?,?,?,?,?,?)""",
        (field_id, date.today().isoformat(), 120.0, 40.0, 80.0, 7.2, 0.65, "lab"),
    )
    soil_test_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Active field_crop
    c.execute(
        """INSERT INTO field_crops
           (field_id, crop_id, sowing_date, current_stage, recommendation_type, is_active)
           VALUES (?,?,?,?,?,?)""",
        (field_id, crop_id, "2026-06-01", "GRAND_GROWTH", "PRE_SEASONAL", 1),
    )

    c.commit()

    ids = {
        "field_id": field_id,
        "crop_id": crop_id,
        "soil_test_id": soil_test_id,
        "region_id": region_id,
        "district_id": district_id,
    }
    return c, ids


@pytest.fixture
def conn(db):
    """Just the connection."""
    return db[0]


@pytest.fixture
def ids(db):
    """Just the IDs dict."""
    return db[1]


@pytest.fixture
def field_row(db):
    """Returns the field_active_crop view row for the test field."""
    c, i = db
    return c.execute(
        "SELECT * FROM field_active_crop WHERE field_id = ?",
        (i["field_id"],),
    ).fetchone()


# ==============================================================================
# 1. SOIL AGENT
# ==============================================================================

class TestSoilAgent:
    def test_returns_soil_context_when_test_exists(self, conn, ids):
        from app.agents.soil_agent import get_soil_context
        ctx = get_soil_context(conn, ids["field_id"])
        assert ctx is not None
        assert ctx["n_kg_ha"] == pytest.approx(120.0)
        assert ctx["ph"] == pytest.approx(7.2)
        assert isinstance(ctx["flags"], list)

    def test_fresh_soil_is_not_stale(self, conn, ids):
        from app.agents.soil_agent import get_soil_context
        ctx = get_soil_context(conn, ids["field_id"])
        assert ctx["is_stale"] is False
        assert ctx["days_since_test"] == 0

    def test_abstains_when_no_soil_test(self, conn, ids):
        from app.agents.soil_agent import get_soil_context
        conn.execute("DELETE FROM soil_tests WHERE field_id = ?", (ids["field_id"],))
        ctx = get_soil_context(conn, ids["field_id"])
        assert ctx is None

    def test_stale_flag_on_old_test(self, conn, ids):
        from app.agents.soil_agent import get_soil_context
        conn.execute(
            "UPDATE soil_tests SET test_date = '2020-01-01' WHERE field_id = ?",
            (ids["field_id"],),
        )
        ctx = get_soil_context(conn, ids["field_id"])
        assert ctx["is_stale"] is True
        stale_flags = [f for f in ctx["flags"] if "STALE_SOIL_DATA" in f]
        assert len(stale_flags) == 1

    def test_write_soil_test_returns_id(self, conn, ids):
        from app.agents.soil_agent import write_soil_test
        from datetime import date
        new_id = write_soil_test(
            conn, ids["field_id"], date.today().isoformat(),
            n_kg_ha=130.0, p_kg_ha=45.0, k_kg_ha=90.0,
            ph=6.8, source="API",
        )
        assert isinstance(new_id, int) and new_id > 0

    def test_does_not_calculate_fertilizer_quantity(self):
        import inspect
        import app.agents.soil_agent as m
        src = inspect.getsource(m)
        assert "DAP_kg_ha" not in src
        assert "UREA_kg_ha" not in src
        assert "MOP_kg_ha" not in src


# ==============================================================================
# 2. CROP AGENT
# ==============================================================================

class TestCropAgent:
    def test_returns_crop_context(self, conn, field_row):
        from app.agents.crop_agent import get_crop_context
        ctx = get_crop_context(conn, field_row)
        assert ctx is not None
        assert ctx["crop_code"] == "SUGARCANE"
        assert ctx["recommendation_type"] == "PRE_SEASONAL"

    def test_abstains_when_no_crop(self, conn):
        from app.agents.crop_agent import get_crop_context

        class FakeRow:
            def __getitem__(self, key):
                return {"current_crop_id": None, "recommendation_type": None}.get(key)
            def keys(self):
                return ["current_crop_id", "recommendation_type"]

        assert get_crop_context(conn, FakeRow()) is None

    def test_stage_not_in_calendar_flag_when_calendar_empty(self, conn, field_row):
        from app.agents.crop_agent import get_crop_context
        ctx = get_crop_context(conn, field_row)
        assert ctx["stage_valid"] is True  # no calendar -> skip check

    def test_stage_flag_raised_when_stage_unknown(self, conn, ids, field_row):
        from app.agents.crop_agent import get_crop_context
        conn.execute(
            """INSERT INTO crop_calendars (crop_id, stage_name, stage_order)
               VALUES (?, ?, ?)""",
            (ids["crop_id"], "GERMINATION", 1),
        )
        ctx = get_crop_context(conn, field_row)
        assert ctx["stage_valid"] is False
        assert any("STAGE_NOT_IN_CALENDAR" in f for f in ctx["flags"])

    def test_get_days_after_planting(self):
        from app.agents.crop_agent import get_days_after_planting
        from datetime import date, timedelta
        sow = (date.today() - timedelta(days=45)).isoformat()
        dap = get_days_after_planting(sow)
        assert 44 <= dap <= 46

    def test_does_not_calculate_fertilizer_quantity(self):
        import inspect
        import app.agents.crop_agent as m
        src = inspect.getsource(m)
        assert "DAP_kg_ha" not in src
        assert "UREA_kg_ha" not in src


# ==============================================================================
# 3. WEATHER AGENT
# ==============================================================================

class TestWeatherAgent:
    def _mock_no_rain(self):
        return {"rainfall_probability": 20, "rainfall_mm_next_7d": 5.0,
                "heavy_rain_alert": False, "source": "mock"}

    def _mock_heavy_rain(self):
        return {"rainfall_probability": 85, "rainfall_mm_next_7d": 80.0,
                "heavy_rain_alert": True, "source": "mock"}

    def test_no_coordinates_returns_no_alert(self, conn, ids):
        from app.agents.weather_agent import get_weather_context
        ctx = get_weather_context(conn, ids["field_id"], lat=None, lon=None)
        assert ctx["heavy_rain_alert"] is False
        assert any("NO_COORDINATES" in f for f in ctx["flags"])

    def test_mock_no_rain_no_alert(self, conn, ids):
        from app.agents.weather_agent import get_weather_context
        ctx = get_weather_context(conn, ids["field_id"], lat=16.7, lon=74.2,
                                  mock_snapshot=self._mock_no_rain())
        assert ctx["heavy_rain_alert"] is False
        assert ctx["snapshot"] is not None

    def test_mock_heavy_rain_triggers_alert(self, conn, ids):
        from app.agents.weather_agent import get_weather_context
        ctx = get_weather_context(conn, ids["field_id"], lat=16.7, lon=74.2,
                                  mock_snapshot=self._mock_heavy_rain())
        assert ctx["heavy_rain_alert"] is True
        assert "alert_details" in ctx

    def test_snapshot_stored_in_db(self, conn, ids):
        from app.agents.weather_agent import get_weather_context
        get_weather_context(conn, ids["field_id"], lat=16.7, lon=74.2,
                            mock_snapshot=self._mock_no_rain())
        row = conn.execute(
            "SELECT * FROM weather_snapshots WHERE field_id = ?", (ids["field_id"],)
        ).fetchone()
        assert row is not None
        assert row["rainfall_probability"] == 20

    def test_does_not_calculate_quantities(self):
        import inspect
        import app.agents.weather_agent as m
        src = inspect.getsource(m)
        assert "DAP_kg_ha" not in src
        assert "gap_n" not in src


# ==============================================================================
# 4. KNOWLEDGE AGENT (stub -- no data pack needed)
# ==============================================================================

class TestKnowledgeAgent:
    def test_returns_list(self):
        from app.agents.knowledge_agent import retrieve_evidence, reset_index
        reset_index()
        evidence = retrieve_evidence("SUGARCANE", "KOLHAPUR", "PRE_SEASONAL")
        assert isinstance(evidence, list)
        assert len(evidence) >= 1

    def test_empty_query_returns_placeholder(self):
        from app.agents.knowledge_agent import retrieve_evidence, reset_index
        reset_index()
        result = retrieve_evidence(None, None, None)
        assert result[0]["score"] == 0.0

    def test_never_returns_kg_ha_numbers_as_new_prescription(self):
        from app.agents.knowledge_agent import retrieve_evidence, reset_index
        reset_index()
        result = retrieve_evidence("SUGARCANE", "KOLHAPUR", "PRE_SEASONAL")
        for chunk in result:
            assert "excerpt" in chunk
            assert "source_file" in chunk
            assert "n_kg_ha" not in chunk
            assert "plan_kg_ha" not in chunk


# ==============================================================================
# 5. VALIDATION AGENT
# ==============================================================================

class TestValidationAgent:
    def _good_ledger(self):
        return {"status": "PLAN_GENERATED", "gap": {"N": 220.0, "P2O5": 130.0, "K2O": 90.0}}

    def _abstain_ledger(self):
        return {"status": "ABSTAIN", "reason": "No soil test", "gap": {}}

    def test_valid_when_no_issues(self):
        from app.agents.validation_agent import validate_ledger_result
        result = validate_ledger_result(self._good_ledger(), None, None)
        assert result["is_valid"] is True
        assert result["blocking_issues"] == []

    def test_abstain_ledger_propagates(self):
        from app.agents.validation_agent import validate_ledger_result
        result = validate_ledger_result(self._abstain_ledger(), None, None)
        assert result["is_valid"] is False
        assert any("LEDGER_ABSTAIN" in b for b in result["blocking_issues"])

    def test_weather_conflict_blocks_n_application(self):
        from app.agents.validation_agent import validate_ledger_result
        weather = {"heavy_rain_alert": True, "alert_details": "80mm expected in 7 days"}
        result = validate_ledger_result(self._good_ledger(), None, weather)
        assert result["is_valid"] is False
        assert any("WEATHER_CONFLICT" in b for b in result["blocking_issues"])
        assert "WEATHER_CONFLICT" in result["flags_added"]

    def test_high_ph_warning(self):
        from app.agents.validation_agent import validate_ledger_result
        result = validate_ledger_result(self._good_ledger(), {"ph": 8.5}, None)
        assert result["is_valid"] is True
        assert any("HIGH_PH_WARNING" in w for w in result["warnings"])

    def test_low_ph_warning(self):
        from app.agents.validation_agent import validate_ledger_result
        result = validate_ledger_result(self._good_ledger(), {"ph": 5.0}, None)
        assert any("LOW_PH_WARNING" in w for w in result["warnings"])

    def test_no_conflict_when_n_gap_zero(self):
        from app.agents.validation_agent import validate_ledger_result
        weather = {"heavy_rain_alert": True, "alert_details": "heavy rain"}
        ledger = {"status": "NO_FERTILIZER_NEEDED", "gap": {"N": 0, "P2O5": 0, "K2O": 0}}
        result = validate_ledger_result(ledger, None, weather)
        assert result["is_valid"] is True


# ==============================================================================
# 6. MONITORING AGENT
# ==============================================================================

class TestMonitoringAgent:
    def test_fire_event_calls_handler(self):
        from app.agents import monitoring_agent
        called = []
        monitoring_agent._handlers.clear()
        monitoring_agent.register_handler("TEST_EVENT", lambda **kw: called.append(kw))
        monitoring_agent.fire_event(
            "TEST_EVENT", field_id=1, field_code="T-001", detail="test", db_path=":memory:"
        )
        assert len(called) == 1
        monitoring_agent._handlers.clear()

    def test_get_alerts_returns_list(self, conn, ids):
        from app.agents.monitoring_agent import get_alerts
        alerts = get_alerts(conn, ids["field_id"])
        assert isinstance(alerts, list)

    def test_supersede_marks_old_rec(self, conn, ids, field_row):
        from app.agents.monitoring_agent import supersede_and_replan
        conn.execute(
            "INSERT INTO recommendations (field_id, plan_json, confidence, status) VALUES (?,?,?,?)",
            (ids["field_id"], '{}', 'MEDIUM', 'PROPOSED'),
        )
        conn.commit()

        def dummy_orch(c, fr):
            return {"status": "PLAN_GENERATED", "field_id": ids["field_id"]}

        supersede_and_replan(
            conn=conn,
            field_id=ids["field_id"],
            field_code="TEST-001",
            event_type="SOIL_REPORT_UPDATED",
            event_detail="New soil test uploaded",
            orchestrator_fn=dummy_orch,
        )
        superseded = conn.execute(
            "SELECT COUNT(*) FROM recommendations WHERE field_id = ? AND status = 'SUPERSEDED'",
            (ids["field_id"],),
        ).fetchone()[0]
        assert superseded >= 1


# ==============================================================================
# 7. TWIN STATE
# ==============================================================================

class TestTwinState:
    def test_make_empty_twin_state_structure(self):
        from app.agents.twin_state import make_empty_twin_state
        ts = make_empty_twin_state("TEST-001", "MH")
        assert ts["field_id"] == "TEST-001"
        assert ts["confidence"] == "HIGH"
        assert ts["flags"] == []
        assert ts["current_plan"] is None
        assert isinstance(ts["data_quality"], dict)

    def test_compute_confidence_zero_flags_is_high(self):
        from app.agents.twin_state import compute_confidence
        assert compute_confidence([]) == "HIGH"

    def test_compute_confidence_one_flag_is_medium(self):
        from app.agents.twin_state import compute_confidence
        assert compute_confidence(["STALE_SOIL_DATA (180 days)"]) == "MEDIUM"

    def test_compute_confidence_two_flags_is_low(self):
        from app.agents.twin_state import compute_confidence
        assert compute_confidence(["P_PROXY (note)", "DERIVED_DENSITY (note)"]) == "LOW"

    def test_compute_confidence_abstain_flag_short_circuits(self):
        from app.agents.twin_state import compute_confidence
        assert compute_confidence(["ABSTAIN: missing data"]) == "ABSTAIN"

    def test_optimizer_flags_not_downgrading(self):
        from app.agents.twin_state import compute_confidence
        flags = ["OPTIMIZER_SAVES_WEIGHT: 10 kg/ha less", "NO_COORDINATES"]
        assert compute_confidence(flags) == "HIGH"


# ==============================================================================
# 8. APP LEDGER ADAPTER
# ==============================================================================

class TestAppLedger:
    def test_run_field_ledger_produces_plan(self, conn, field_row):
        from app.ledger import run_field_ledger
        result = run_field_ledger(conn, field_row)
        assert result["status"] in ("PLAN_GENERATED", "NO_FERTILIZER_NEEDED", "ABSTAIN")
        if result["status"] == "PLAN_GENERATED":
            assert "plan_kg_ha" in result
            assert "gap" in result

    def test_abstains_when_no_active_crop(self, conn, ids):
        from app.ledger import run_field_ledger
        conn.execute("UPDATE field_crops SET is_active = 0 WHERE field_id = ?", (ids["field_id"],))
        row = conn.execute(
            "SELECT * FROM field_active_crop WHERE field_id = ?", (ids["field_id"],)
        ).fetchone()
        result = run_field_ledger(conn, row)
        assert result["status"] == "ABSTAIN"

    def test_write_ledger_result_creates_recommendation_row(self, conn, field_row):
        from app.ledger import run_field_ledger, write_ledger_result
        result = run_field_ledger(conn, field_row)
        rec_id = write_ledger_result(conn, result)
        assert isinstance(rec_id, int)
        row = conn.execute(
            "SELECT * FROM recommendations WHERE recommendation_id = ?", (rec_id,)
        ).fetchone()
        assert row is not None

    def test_llm_never_produces_quantities(self):
        import inspect
        import app.ledger as m
        src = inspect.getsource(m)
        assert "_run_field_raw" in src
        assert "gap_n = max" not in src
        assert "gap_p2o5 = max" not in src


# ==============================================================================
# 9. INTEGRATION: orchestrator smoke test (mock weather, no network)
# ==============================================================================

class TestOrchestratorIntegration:
    def test_full_run_no_rain(self, conn, field_row):
        from app.agents.orchestrator import run_orchestrated_ledger
        mock_weather = {"rainfall_probability": 10, "rainfall_mm_next_7d": 2.0,
                        "heavy_rain_alert": False, "source": "mock"}
        result = run_orchestrated_ledger(conn, field_row, mock_weather=mock_weather)
        assert "status" in result
        assert "soil_context" in result
        assert "weather_context" in result
        assert "validation" in result

    def test_heavy_rain_triggers_blocking_issue(self, conn, field_row):
        from app.agents.orchestrator import run_orchestrated_ledger
        mock_weather = {"rainfall_probability": 90, "rainfall_mm_next_7d": 100.0,
                        "heavy_rain_alert": True, "source": "mock"}
        result = run_orchestrated_ledger(conn, field_row, mock_weather=mock_weather)
        val = result.get("validation", {})
        gap_n = (result.get("gap") or {}).get("N", 0)
        if gap_n and gap_n > 0:
            assert not val["is_valid"]
            assert any("WEATHER_CONFLICT" in b for b in val["blocking_issues"])

    def test_no_fertilizer_needed_path(self, conn, ids, field_row):
        from app.agents.orchestrator import run_orchestrated_ledger
        conn.execute(
            "UPDATE soil_tests SET n_kg_ha=9999, p_kg_ha=9999, k_kg_ha=9999 WHERE field_id=?",
            (ids["field_id"],),
        )
        mock_weather = {"rainfall_probability": 0, "rainfall_mm_next_7d": 0,
                        "heavy_rain_alert": False, "source": "mock"}
        result = run_orchestrated_ledger(conn, field_row, mock_weather=mock_weather)
        assert result["status"] in ("NO_FERTILIZER_NEEDED", "PLAN_GENERATED", "ABSTAIN")
