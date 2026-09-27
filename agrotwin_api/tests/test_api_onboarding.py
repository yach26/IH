"""
Tests for Phase 1 audit fixes:
  1. POST /fields/{id}/crop — crop assignment via live API (TestClient)
  2. POST /farmers — farmer creation
  3. POST /fields  — field creation
  4. Confirm recommend does NOT abstain after crop assignment (§3 requirement)

These tests use the FastAPI TestClient with an in-memory SQLite DB injected
via dependency override — the same pattern used by the existing test suite.
"""

from __future__ import annotations

import sys
import os

import pytest
from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.main import app
from app.api.routes import get_conn
from tests.conftest import make_test_db


# ── Dependency override: inject in-memory DB for all TestClient calls ─────────

_test_conn = None
_test_ids = None


def override_get_db():
    """Yield the shared in-memory connection for the duration of each request."""
    yield _test_conn


@pytest.fixture(autouse=True)
def _fresh_db():
    """Recreate a clean in-memory DB before each test in this module."""
    global _test_conn, _test_ids
    _test_conn, _test_ids = make_test_db()
    # Other API test modules clear this shared app mapping; reapply it per test.
    app.dependency_overrides[get_conn] = override_get_db
    yield
    app.dependency_overrides.pop(get_conn, None)
    _test_conn.close()


client = TestClient(app, raise_server_exceptions=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _field_id() -> int:
    return _test_ids["field_id"]


def _region_id() -> int:
    return _test_ids["region_id"]


def _district_id() -> int:
    return _test_ids["district_id"]


# ── Phase 1 §2: crop assignment endpoint ─────────────────────────────────────

class TestCropAssignment:
    def test_assign_crop_returns_success(self):
        """POST /fields/{id}/crop with a valid crop_code must return status=success."""
        fid = _field_id()
        resp = client.post(
            f"/fields/{fid}/crop",
            json={
                "crop_code": "SUGARCANE",
                "recommendation_type": "PRE_SEASONAL",
                "current_stage": "GRAND_GROWTH",
                "sowing_date": "2026-06-01",
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "success"
        assert body["crop_code"] == "SUGARCANE"

    def test_assign_crop_unknown_code_returns_400(self):
        fid = _field_id()
        resp = client.post(
            f"/fields/{fid}/crop",
            json={"crop_code": "UNICORN_CROP"},
        )
        assert resp.status_code == 400

    def test_recommend_after_crop_assign_not_abstain_on_missing_fields(self):
        """
        Audit §3 requirement: after a valid crop assignment the recommend endpoint
        must NOT return ABSTAIN with reason 'Incomplete required fields: crop,
        recommendation_type'. It may still ABSTAIN for OTHER legitimate reasons
        (e.g. missing soil test would produce a different ABSTAIN reason), but the
        'no active crop' blocker must be gone.

        conftest.py already inserts a field_crop row (SUGARCANE, PRE_SEASONAL) AND
        a soil_test row, so the full pipeline should run and produce PLAN_GENERATED.
        """
        fid = _field_id()
        resp = client.post(f"/fields/{fid}/recommend", json={})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        # Must not be the "no crop assigned" abstain
        if body["status"] == "ABSTAIN":
            reason = body.get("reason", "")
            assert "crop" not in reason.lower() and "recommendation_type" not in reason.lower(), (
                f"Got ABSTAIN for crop-missing reason after crop was assigned: {reason}"
            )
        else:
            assert body["status"] in ("PLAN_GENERATED", "NO_FERTILIZER_NEEDED")

    def test_assign_then_reassign_deactivates_previous(self):
        """Assigning a second crop must deactivate the first (is_active=0 on old row)."""
        fid = _field_id()
        # First assignment (already done by conftest) — add a second one
        resp = client.post(
            f"/fields/{fid}/crop",
            json={
                "crop_code": "SUGARCANE",
                "recommendation_type": "RATOON",
                "current_stage": "RATOON",
                "sowing_date": "2026-09-01",
            },
        )
        assert resp.status_code == 200
        # Only one active row should exist
        rows = _test_conn.execute(
            "SELECT * FROM field_crops WHERE field_id = ? AND is_active = 1", (fid,)
        ).fetchall()
        assert len(rows) == 1, f"Expected 1 active crop, got {len(rows)}"


# ── Phase 1 §3: farmer creation endpoint ─────────────────────────────────────

class TestFarmerCreation:
    def test_create_farmer_returns_201(self):
        rid = _region_id()
        resp = client.post(
            "/farmers",
            json={"region_id": rid, "full_name": "Ramesh Patil", "mobile": "9876543210"},
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["status"] == "created"
        assert isinstance(body["farmer_id"], int)

    def test_create_farmer_bad_region_returns_400(self):
        resp = client.post("/farmers", json={"region_id": 99999})
        assert resp.status_code == 400


# ── Phase 1 §3: field creation endpoint ──────────────────────────────────────

class TestFieldCreation:
    def test_create_field_returns_201(self):
        rid = _region_id()
        did = _district_id()
        resp = client.post(
            "/fields",
            json={
                "region_id": rid,
                "district_id": did,
                "field_code": "REAL-001",
                "area_ha": 1.5,
                "irrigation_type": "Rainfed",
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["status"] == "created"
        assert isinstance(body["field_id"], int)
        assert "next_steps" in body

    def test_create_field_bad_district_returns_400(self):
        rid = _region_id()
        resp = client.post(
            "/fields",
            json={"region_id": rid, "district_id": 99999, "area_ha": 1.0},
        )
        assert resp.status_code == 400

    def test_create_field_then_assign_crop_and_recommend(self):
        """
        Full onboarding flow for a real (non-synthetic) farmer:
        1. Create field  2. Add soil test  3. Assign crop  4. Recommend
        This is the integration test the audit required in §2.
        """
        rid = _region_id()
        did = _district_id()

        # 1. Create field
        resp = client.post(
            "/fields",
            json={"region_id": rid, "district_id": did, "area_ha": 2.0,
                  "field_code": "ONBOARD-001", "irrigation_type": "Irrigated"},
        )
        assert resp.status_code == 201
        fid = resp.json()["field_id"]

        # 2. Add soil test via confirm endpoint (no upload needed)
        resp = client.post(
            f"/fields/{fid}/soil-report/confirm",
            json={
                "soil_test": {
                    "n_kg_ha": 120.0, "p_kg_ha": 40.0, "k_kg_ha": 80.0,
                    "ph": 7.2, "oc_percent": 0.65, "test_date": "2026-09-01",
                    "source": "manual"
                }
            },
        )
        assert resp.status_code == 200

        # 3. Assign crop
        resp = client.post(
            f"/fields/{fid}/crop",
            json={
                "crop_code": "SUGARCANE",
                "recommendation_type": "PRE_SEASONAL",
                "current_stage": "GRAND_GROWTH",
                "sowing_date": "2026-06-01",
            },
        )
        assert resp.status_code == 200

        # 4. Recommend — must not be "no crop" ABSTAIN
        resp = client.post(f"/fields/{fid}/recommend", json={})
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] in ("PLAN_GENERATED", "NO_FERTILIZER_NEEDED", "ABSTAIN")
        if body["status"] == "ABSTAIN":
            assert "crop" not in body.get("reason", "").lower()
