"""
Orchestrator — the single coordinator that sequences all agents.

Call order (per architecture brief §9):
  1. soil_agent.get_soil_context()
  2. crop_agent.get_crop_context()
  3. weather_agent.get_weather_context()
  4. ledger.run_field_ledger()          ← existing, unchanged equations
  5. optimizer.run_optimizer_for_field() ← linprog, replaces fixed rule in response
  6. knowledge_agent.retrieve_evidence()
  7. validation_agent.validate_ledger_result()
  8. write_ledger_result() + return enriched response

This is the ONLY module that calls multiple agents in sequence.
GET /fields/{code}/ledger in main.py calls run_orchestrated_ledger().

No fertilizer quantities are computed here — they originate from
app/ledger.py (gap math) and agents/optimizer.py (product allocation).
"""

import sqlite3
import json
from datetime import date

from .. import ledger as ledger_module
from . import soil_agent, crop_agent, weather_agent, knowledge_agent
from . import validation_agent, monitoring_agent
from .optimizer import run_optimizer_for_field


def run_orchestrated_ledger(
    conn: sqlite3.Connection,
    field_row: sqlite3.Row,
    mock_weather: dict | None = None,
) -> dict:
    """
    Full orchestrated run for one field.

    Returns an enriched ledger result dict that includes:
      All original ledger fields (status, gap, plan_kg_ha, flags, confidence …)
      + soil_context    (staleness, soil_test_id, …)
      + crop_context    (stage validity, calendar, …)
      + weather_context (snapshot, heavy_rain_alert, …)
      + optimizer_result (LP plan, comparison with fixed rule)
      + evidence        (BM25 chunks from Knowledge Agent)
      + validation      (is_valid, warnings, blocking_issues)
    """
    field_id = field_row["field_id"]
    field_code = field_row["field_code"]

    # ── Step 1: Soil Agent ──────────────────────────────────────────
    soil_ctx = soil_agent.get_soil_context(conn, field_id)

    # ── Step 2: Crop Agent ──────────────────────────────────────────
    crop_ctx = crop_agent.get_crop_context(conn, field_row)

    # ── Step 3: Weather Agent ───────────────────────────────────────
    lat = field_row["lat"] if "lat" in field_row.keys() else None
    lon = field_row["lon"] if "lon" in field_row.keys() else None
    weather_ctx = weather_agent.get_weather_context(
        conn, field_id, lat, lon,
        mock_snapshot=mock_weather,
    )

    # ── Step 4: Core Nutrient Ledger (unchanged equations) ──────────
    ledger_result = ledger_module.run_field_ledger(conn, field_row)

    # ── Step 5: LP Optimizer ────────────────────────────────────────
    optimizer_result = None
    if ledger_result.get("status") not in ("ABSTAIN",):
        gap = ledger_result.get("gap", {})
        opt = run_optimizer_for_field(
            conn,
            gap_n=gap.get("N", 0),
            gap_p2o5=gap.get("P2O5", 0),
            gap_k2o=gap.get("K2O", 0),
        )
        optimizer_result = {
            "status": opt.status,
            "plan_kg_ha": opt.plan_kg_ha,
            "total_kg_ha": opt.total_kg_ha,
            "fixed_rule_plan_kg_ha": opt.fixed_rule_plan_kg_ha,
            "fixed_rule_total_kg_ha": opt.fixed_rule_total_kg_ha,
            "weight_saving_kg_ha": opt.weight_saving_kg_ha,
            "flag": opt.flag,
            "message": opt.message,
            "objective": (
                "minimize_total_weight_kg_ha "
                "(cost objective pending Gap #8: no price table sourced yet)"
            ),
        }

    # ── Step 6: Knowledge Agent (evidence retrieval) ────────────────
    crop_code = (crop_ctx or {}).get("crop_code")
    rec_type = (crop_ctx or {}).get("recommendation_type")
    district_row = conn.execute(
        "SELECT district_code FROM districts WHERE district_id = ?",
        (field_row["district_id"],),
    ).fetchone()
    region_str = district_row["district_code"] if district_row else None

    evidence = knowledge_agent.retrieve_evidence(
        crop_code=crop_code,
        region=region_str,
        recommendation_type=rec_type,
        top_k=4,
    )

    # ── Step 7: Validation Agent ────────────────────────────────────
    validation = validation_agent.validate_ledger_result(
        ledger_result, soil_ctx, weather_ctx
    )

    # ── Step 8: Merge flags, write back, return ─────────────────────
    # Merge new flags from agents into the ledger_result flags list
    all_flags = list(ledger_result.get("flags", []))
    if soil_ctx:
        all_flags.extend(soil_ctx.get("flags", []))
    if crop_ctx:
        all_flags.extend(crop_ctx.get("flags", []))
    if weather_ctx:
        all_flags.extend(weather_ctx.get("flags", []))
    all_flags.extend(validation.get("flags_added", []))
    if optimizer_result and optimizer_result.get("flag"):
        all_flags.append(optimizer_result["flag"])

    ledger_result["flags"] = all_flags

    # Recompute confidence: MEDIUM=1 flag, LOW=2+, HIGH=0 (only base flags count)
    base_flags = [f for f in all_flags if not f.startswith("OPTIMIZER_") and
                  not f.startswith("WEATHER_FETCH_ERROR") and
                  not f.startswith("NO_COORDINATES")]
    if len(base_flags) == 0:
        ledger_result["confidence"] = "HIGH"
    elif len(base_flags) == 1:
        ledger_result["confidence"] = "MEDIUM"
    else:
        ledger_result["confidence"] = "LOW"

    # Write back to twin
    ledger_module.write_ledger_result(conn, ledger_result)

    # Build enriched response
    enriched = {
        **ledger_result,
        "soil_context": soil_ctx,
        "crop_context": crop_ctx,
        "weather_context": {
            "heavy_rain_alert": weather_ctx.get("heavy_rain_alert", False),
            "alert_details": weather_ctx.get("alert_details", ""),
            "rainfall_mm_next_7d": (
                (weather_ctx.get("snapshot") or {}).get("rainfall_mm_next_7d")
            ),
            "rainfall_probability": (
                (weather_ctx.get("snapshot") or {}).get("rainfall_probability")
            ),
            "source": "open-meteo",
            "flags": weather_ctx.get("flags", []),
            "warning": weather_ctx.get("warning"),
        },
        "optimizer_result": optimizer_result,
        "evidence": evidence,
        "validation": {
            "is_valid": validation["is_valid"],
            "warnings": validation["warnings"],
            "blocking_issues": validation["blocking_issues"],
        },
    }

    return enriched
