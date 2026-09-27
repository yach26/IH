"""Live HTTP coverage for the two endpoints Phase 1 flagged as unverified:
/fields/{id}/override, and the ABSTAIN path when a crop+stage has no RDF row.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.routes import get_conn
from app.main import app


def test_agronomist_override_live(db):
    conn, ids = db

    def _override_conn():
        yield conn

    app.dependency_overrides[get_conn] = _override_conn
    try:
        client = TestClient(app)

        rec = client.post(f"/fields/{ids['field_id']}/recommend", json={})
        assert rec.status_code == 200, rec.text

        latest = client.get(f"/fields/{ids['field_id']}/recommendations/latest")
        assert latest.status_code == 200, latest.text
        recommendation_id = latest.json()["recommendation_id"]

        override = client.post(
            f"/fields/{ids['field_id']}/override",
            json={
                "recommendation_id": recommendation_id,
                "new_plan": {"DAP_kg_ha": 100.0, "UREA_kg_ha": 50.0, "MOP_kg_ha": 0.0},
                "reason": "Agronomist field visit adjustment",
                "agronomist_id": "agronomist-test",
            },
        )
        assert override.status_code == 200, override.text
        body = override.json()
        assert body["status"] == "success"
        assert isinstance(body["new_recommendation_id"], int)

        old_row = conn.execute(
            "SELECT status FROM recommendations WHERE recommendation_id = ?",
            (recommendation_id,),
        ).fetchone()
        assert old_row["status"] == "SUPERSEDED"

        new_row = conn.execute(
            "SELECT status, confidence_reason FROM recommendations WHERE recommendation_id = ?",
            (body["new_recommendation_id"],),
        ).fetchone()
        assert new_row["status"] == "PROPOSED"
        assert new_row["confidence_reason"] == "Agronomist Override"

        audit = conn.execute(
            "SELECT action FROM audit_log WHERE entity_type = 'recommendation' "
            "ORDER BY audit_id DESC LIMIT 1"
        ).fetchone()
        assert audit["action"] == "OVERRIDE"
    finally:
        app.dependency_overrides.clear()


def test_recommend_abstains_on_missing_rdf_row(db):
    conn, ids = db

    def _override_conn():
        yield conn

    conn.execute(
        "UPDATE field_crops SET recommendation_type = 'NONEXISTENT_STAGE' WHERE field_id = ?",
        (ids["field_id"],),
    )
    conn.commit()

    app.dependency_overrides[get_conn] = _override_conn
    try:
        client = TestClient(app)
        rec = client.post(f"/fields/{ids['field_id']}/recommend", json={})
        assert rec.status_code == 200, rec.text
        body = rec.json()
        assert body["status"] == "ABSTAIN"
        assert body.get("reason")

        # Phase 5.1: /twin must not 500 on a field whose latest recommendation is
        # ABSTAIN — assemble_proof sets what/when/why/how_much to an *explicit* None
        # (not a missing key) when status == ABSTAIN, and the frontend needs status/
        # reason/requiredActions to render the "⚠ LOW CONFIDENCE" warning block.
        twin = client.get(f"/fields/{ids['field_id']}/twin")
        assert twin.status_code == 200, twin.text
        plan = twin.json()["currentPlan"]
        assert plan["status"] == "ABSTAIN"
        assert plan["soilGap"] == {}
        assert plan["applicationWindow"] == "N/A"
    finally:
        app.dependency_overrides.clear()
