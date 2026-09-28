"""
STEP 1 (P0) backend test:
  POST /fields/{id}/soil-report/confirm
    → publishes SOIL_REPORT_UPDATED
    → MonitoringAgent supersedes the previous PROPOSED recommendation.
"""
from __future__ import annotations

import json
from datetime import date

import pytest

from tests.conftest import make_test_db
from agrotwin_api.app.agents import monitoring_agent as _ma
from agrotwin_api.app.agents import soil_report_agent
from agrotwin_api.app.core.event_bus import get_bus
from agrotwin_api.app.core.events import EventType
from agrotwin_api.app.pipeline import RecommendationPipeline


def _seed_plan(conn, field_id: int) -> int:
    """Insert a PROPOSED recommendation and return its id."""
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO recommendations
           (field_id, plan_json, status, confidence, confidence_reason, is_synthetic)
           VALUES (?, ?, 'PROPOSED', 'HIGH', 'seeded for test', 0)""",
        (field_id, json.dumps({"status": "PLAN_GENERATED", "what": "Apply fertilizer"})),
    )
    conn.commit()
    return cur.lastrowid


def _seed_upload(conn, field_id: int) -> int:
    """Insert a PENDING_CONFIRMATION soil_report_uploads row and return upload_id."""
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO soil_report_uploads
           (field_id, original_file_path, extracted_json, status)
           VALUES (?, ?, ?, 'PENDING_CONFIRMATION')""",
        (field_id, "/tmp/test.txt", json.dumps({})),
    )
    conn.commit()
    return cur.lastrowid


class TestSoilConfirmInvalidatesPlan:
    def test_confirm_publishes_event_and_supersedes_plan(self):
        """
        Confirming a soil report:
          1. publishes SOIL_REPORT_UPDATED via the event bus
          2. the monitoring agent supersedes the previous PROPOSED plan.
        """
        conn, ids = make_test_db()
        field_id = ids["field_id"]

        # Seed a PROPOSED plan that should become SUPERSEDED.
        old_rec_id = _seed_plan(conn, field_id)
        status_before = conn.execute(
            "SELECT status FROM recommendations WHERE recommendation_id = ?",
            (old_rec_id,),
        ).fetchone()["status"]
        assert status_before == "PROPOSED"

        # Set up monitoring agent (listens to SOIL_REPORT_UPDATED).
        monitor = _ma.MonitoringAgent(bus=get_bus(), conn=conn)
        monitor.bind(conn)

        # Seed an upload row.
        upload_id = _seed_upload(conn, field_id)

        confirmed_values = {
            "n_kg_ha": 120.0,
            "p_kg_ha": 40.0,
            "k_kg_ha": 80.0,
            "ph": 7.2,
            "test_date": date.today().isoformat(),
        }

        # Act: confirm triggers SOIL_REPORT_UPDATED → monitoring agent → replan.
        result = soil_report_agent.confirm_and_write(
            conn, upload_id, confirmed_values, actor="farmer", emit_event=True
        )
        assert result["status"] == "CONFIRMED"

        # The monitoring agent runs a partial replan which supersedes the old plan.
        old_status = conn.execute(
            "SELECT status FROM recommendations WHERE recommendation_id = ?",
            (old_rec_id,),
        ).fetchone()["status"]
        assert old_status == "SUPERSEDED", (
            f"Expected old plan to be SUPERSEDED after soil confirm, got {old_status!r}"
        )

        # A new recommendation must have been generated.
        new_rec = conn.execute(
            """SELECT recommendation_id, status FROM recommendations
               WHERE field_id = ? AND recommendation_id != ?
               ORDER BY recommendation_id DESC LIMIT 1""",
            (field_id, old_rec_id),
        ).fetchone()
        assert new_rec is not None, "No new recommendation was created after soil confirm"
        assert new_rec["status"] in ("PROPOSED", "ABSTAINED", "NO_FERTILIZER_NEEDED"), (
            f"Unexpected new recommendation status: {new_rec['status']!r}"
        )

    def test_confirm_without_prior_plan_does_not_crash(self):
        """Confirming soil with no prior plan should not raise — a new plan is created."""
        conn, ids = make_test_db()
        field_id = ids["field_id"]

        # No plan exists yet.
        upload_id = _seed_upload(conn, field_id)
        monitor = _ma.MonitoringAgent(bus=get_bus(), conn=conn)
        monitor.bind(conn)

        result = soil_report_agent.confirm_and_write(
            conn,
            upload_id,
            {"n_kg_ha": 100.0, "p_kg_ha": 30.0, "k_kg_ha": 60.0, "test_date": date.today().isoformat()},
            actor="farmer",
            emit_event=True,
        )
        assert result["status"] == "CONFIRMED"
        rec = conn.execute(
            "SELECT recommendation_id FROM recommendations WHERE field_id = ? LIMIT 1",
            (field_id,),
        ).fetchone()
        assert rec is not None, "A recommendation should be created even without a prior plan"
