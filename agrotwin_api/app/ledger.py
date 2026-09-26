"""
app/ledger.py — thin adapter layer around the root-level ledger.py.

The Orchestrator (and any FastAPI endpoint) imports from here so that all
code under app/ uses a consistent import path (``from app import ledger``).

The root ledger.py contains the FROZEN Nutrient Ledger equations and is the
single source of truth for fertilizer quantities. This module does NOT
re-implement any equations — it imports and re-exports the root module's
functions and adds the small write_ledger_result() helper that the
Orchestrator needs.

CRITICAL: No quantities may be altered here. Calculation lives in ledger.py.
"""

import sqlite3
import json
import sys
import os

# Make root agrotwin_api/ importable when app/ is the cwd or when running
# from a sub-package (e.g. uvicorn agrotwin_api.app.main:app).
_api_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _api_root not in sys.path:
    sys.path.insert(0, _api_root)

from ledger import (  # noqa: E402  (import after sys.path manipulation)
    get_recommendation,
    get_products,
    compute_gap,
    convert_gap_to_products,
    run_field as _run_field_raw,
)

__all__ = [
    "get_recommendation",
    "get_products",
    "compute_gap",
    "convert_gap_to_products",
    "run_field_ledger",
    "write_ledger_result",
]


# ──────────────────────────────────────────────────────────────────────────────
# Public helper: run the ledger for a field_row fetched via the app DB layer.
# ──────────────────────────────────────────────────────────────────────────────

def run_field_ledger(conn: sqlite3.Connection, field_row: sqlite3.Row) -> dict:
    """
    Runs the Nutrient Ledger for a single field.

    ``field_row`` must expose the columns from the ``field_active_crop`` view
    (i.e. field_code, current_crop_id, current_stage, recommendation_type, plus
    the soil test values populated by seed_data / soil_agent).

    The inner ``_run_field_raw`` is the original ledger.run_field() function
    which takes (conn, field_id, field_meta, rec_type_map). We reconstruct the
    field_meta dict from the richer Row object here.
    """
    field_id = field_row["field_id"]
    crop_code = _get_crop_code(conn, field_row)

    if not crop_code:
        return {
            "field_id": field_id,
            "field_code": field_row["field_code"],
            "status": "ABSTAIN",
            "reason": "No active crop assigned to this field.",
            "flags": [],
        }

    rec_type = field_row["recommendation_type"]
    if not rec_type:
        return {
            "field_id": field_id,
            "field_code": field_row["field_code"],
            "status": "ABSTAIN",
            "reason": "No recommendation_type set on active field_crop.",
            "flags": [],
        }

    # Fetch latest soil test row
    soil_row = conn.execute(
        """SELECT n_kg_ha, p_kg_ha, k_kg_ha, ph, oc_percent
           FROM soil_tests WHERE field_id = ?
           ORDER BY test_date DESC, soil_test_id DESC LIMIT 1""",
        (field_id,),
    ).fetchone()

    if soil_row is None:
        return {
            "field_id": field_id,
            "field_code": field_row["field_code"],
            "status": "ABSTAIN",
            "reason": "No soil test found for this field (required for gap calculation).",
            "flags": [],
        }

    # Build the field_meta dict expected by the root ledger
    # (it mimics the CSV row format used by seed_data)
    record_id = field_row["field_code"] or str(field_id)
    field_meta = {
        "field_id": field_id,
        "crop_code": crop_code,
        "current_stage": field_row["current_stage"] or "UNKNOWN",
        "row": {
            "record_id": record_id,
            "N_kg_ha": soil_row["n_kg_ha"] or 0.0,
            "P_kg_ha": soil_row["p_kg_ha"] or 0.0,
            "K_kg_ha": soil_row["k_kg_ha"] or 0.0,
        },
    }
    rec_type_map = {record_id: rec_type}

    result = _run_field_raw(conn, field_id, field_meta, rec_type_map)

    # Enrich with field_code for traceability
    result["field_code"] = field_row["field_code"]
    return result


def _get_crop_code(conn: sqlite3.Connection, field_row: sqlite3.Row) -> str | None:
    """Resolve crop_code from the active crop id on the field row."""
    crop_id = field_row["current_crop_id"] if "current_crop_id" in field_row.keys() else None
    if crop_id is None:
        return None
    row = conn.execute(
        "SELECT crop_code FROM crops WHERE crop_id = ?", (crop_id,)
    ).fetchone()
    return row["crop_code"] if row else None


# ──────────────────────────────────────────────────────────────────────────────
# Write-back helper (called by Orchestrator after validation)
# ──────────────────────────────────────────────────────────────────────────────

def write_ledger_result(conn: sqlite3.Connection, result: dict) -> int | None:
    """
    Persists the enriched ledger result into nutrient_ledger_entries +
    recommendations.  Returns the new recommendation_id or None on ABSTAIN.

    This is the only place a recommendation row is written to the DB; keeping
    it here (not in the Orchestrator) preserves the clean separation where the
    Orchestrator sequences agents but does not contain DB logic.
    """
    field_id = result.get("field_id")
    if field_id is None:
        return None

    cur = conn.cursor()

    if result.get("status") == "ABSTAIN":
        cur.execute(
            """INSERT INTO recommendations
               (field_id, plan_json, confidence, confidence_reason,
                evidence_citations, flags, is_synthetic, status)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                field_id,
                json.dumps({}),
                "ABSTAIN",
                result.get("reason", ""),
                json.dumps([]),
                json.dumps(result.get("flags", [])),
                0,
                "ABSTAINED",
            ),
        )
        conn.commit()
        return None

    # Write nutrient_ledger_entries row
    crop_code = result.get("crop")
    cur.execute(
        """INSERT INTO nutrient_ledger_entries
           (field_id, crop_id, current_stage,
            required_n_kg_ha, required_p2o5_kg_ha, required_k2o_kg_ha,
            required_source,
            soil_n_kg_ha, soil_p_kg_ha, soil_k_kg_ha,
            gap_n_kg_ha, gap_p2o5_kg_ha, gap_k2o_kg_ha,
            calculation_notes, flags, confidence, is_synthetic)
           VALUES (?,
                   (SELECT crop_id FROM crops WHERE crop_code = ?),
                   ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            field_id,
            crop_code,
            result.get("current_stage", "UNKNOWN"),
            result.get("required", {}).get("N"),
            result.get("required", {}).get("P2O5"),
            result.get("required", {}).get("K2O"),
            result.get("citation", ""),
            result.get("soil", {}).get("N"),
            result.get("soil", {}).get("P_proxy"),
            result.get("soil", {}).get("K"),
            result.get("gap", {}).get("N"),
            result.get("gap", {}).get("P2O5"),
            result.get("gap", {}).get("K2O"),
            "; ".join(result.get("flags", [])),
            json.dumps(result.get("flags", [])),
            result.get("confidence", "MEDIUM"),
            0,
        ),
    )
    ledger_id = cur.lastrowid

    plan_json = {
        **result.get("plan_kg_ha", {}),
        "optimizer": result.get("optimizer_result"),
    }

    cur.execute(
        """INSERT INTO recommendations
           (field_id, ledger_id, plan_json, confidence, confidence_reason,
            evidence_citations, flags, is_synthetic, status)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            field_id,
            ledger_id,
            json.dumps(plan_json),
            result.get("confidence", "MEDIUM"),
            "; ".join(result.get("flags", [])),
            json.dumps([result.get("citation", "")]),
            json.dumps(result.get("flags", [])),
            0,
            "PROPOSED",
        ),
    )
    rec_id = cur.lastrowid
    conn.commit()
    return rec_id
