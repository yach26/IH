"""API routers — recommend, twin, events, alerts."""

from __future__ import annotations

import json
import os
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from datetime import datetime

from ..agents import soil_report_agent
from ..agents.monitoring_agent import get_alerts, get_monitoring_agent
from ..agents.orchestrator import request_replan, run_orchestrated_ledger
from ..core.event_bus import get_bus
from ..core.events import Event
from .schemas import (
    CropAssignRequest,
    EventIn,
    FarmerCreateRequest,
    FieldCreateRequest,
    RecommendRequest,
    RecommendationOut,
    SoilReportConfirmRequest,
    WhatIfRequest,
    OverrideRequest,
)
from ..core.ocr import save_upload_file, run_ocr_on_file, run_ocr_pipeline, get_ocr_reader

router = APIRouter()


@router.get("/ocr/health")
def ocr_health():
    """Check status and readiness of the EasyOCR machine learning engine."""
    import torch
    reader = get_ocr_reader()
    return {
        "status": "ready" if reader is not None else "degraded",
        "engine": "EasyOCR (PyTorch)",
        "cuda_available": torch.cuda.is_available(),
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "supported_extensions": [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".pdf", ".txt", ".csv"],
        "version": "1.7.2",
    }


@router.post("/ocr/extract")
@router.post("/api/ocr/extract")
async def extract_ocr_standalone(
    file: UploadFile = File(...),
):
    """
    Direct, standalone Real OCR API.
    Upload any soil test report (image / scanned PDF / digital PDF / text) to receive
    actual extracted nutrient values, confidence scores, and raw detected blocks.
    No prior field registration required.
    """
    contents = await file.read()
    filename = file.filename or "report.png"
    return run_ocr_pipeline(contents, filename)


from ..db import get_db_connection, _json_load


def get_conn():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


def _field_row(conn: sqlite3.Connection, field_ref: str) -> sqlite3.Row:
    base_query = """
        SELECT fac.*, c.crop_name, c.crop_code as crop_code_str
        FROM field_active_crop fac
        LEFT JOIN crops c ON c.crop_id = fac.current_crop_id
        WHERE fac.{col} = ?
    """
    if field_ref.isdigit():
        row = conn.execute(base_query.format(col="field_id"), (int(field_ref),)).fetchone()
    else:
        row = conn.execute(base_query.format(col="field_code"), (field_ref,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Field not found: {field_ref}")
    return row


@router.get("/health")
def health():
    return {"status": "ok", "service": "agrotwin"}


@router.get("/fields/{field_id}/yield-estimate")
def yield_estimate(
    field_id: str,
    rainfall_mm_season: float | None = Query(default=None, ge=0, allow_inf_nan=False),
    conn: sqlite3.Connection = Depends(get_conn),
):
    from ..yield_prediction import estimate

    return estimate(conn, _field_row(conn, field_id), rainfall_mm_season)


@router.get("/fields/{field_id}/twin")
def get_twin(field_id: str, conn: sqlite3.Connection = Depends(get_conn)):
    row = _field_row(conn, field_id)
    soil = conn.execute(
        """SELECT * FROM soil_tests WHERE field_id = ?
           ORDER BY test_date DESC LIMIT 1""",
        (row["field_id"],),
    ).fetchone()
    
    rec = conn.execute(
        """SELECT * FROM recommendations WHERE field_id = ?
           ORDER BY generated_at DESC LIMIT 1""",
        (row["field_id"],),
    ).fetchone()
    
    plan = None
    if rec:
        try:
            plan = _json_load(rec["plan_json"])
        except json.JSONDecodeError:
            plan = {}

    alerts_list = get_alerts(conn, row["field_id"])
    active_alert = None
    if alerts_list:
        first_alert = alerts_list[0]
        active_alert = {
            "title": first_alert.get("alert_type", "Alert"),
            "description": first_alert.get("message", ""),
        }

    # Latest weather-related event for this field (real payload, not a stub),
    # so the weather widget reflects an injected/real HEAVY_RAIN_ALERT / WEATHER_FORECAST_CHANGED.
    weather_event = conn.execute(
        """SELECT payload FROM events WHERE field_id = ?
           AND event_type IN ('HEAVY_RAIN_ALERT', 'WEATHER_FORECAST_CHANGED')
           ORDER BY created_at DESC LIMIT 1""",
        (row["field_id"],),
    ).fetchone()
    weather_payload = {}
    if weather_event and weather_event["payload"]:
        try:
            weather_payload = json.loads(weather_event["payload"])
        except json.JSONDecodeError:
            weather_payload = {}

    # Derive soil health score: weighted average of N/P/K sufficiency vs typical sugarcane needs
    n_val = soil["n_kg_ha"] if soil else 0
    p_val = soil["p_kg_ha"] if soil else 0
    k_val = soil["k_kg_ha"] if soil else 0
    ph_val = soil["ph"] if soil else 6.5
    oc_val = soil["oc_percent"] if soil else 0.8
    # Scale to 0-100: N need 200-340, P need 15-30, K need 100-170 for sugarcane
    n_score = min(100, round((n_val / 340) * 100))
    p_score = min(100, round((p_val / 30) * 100))
    k_score = min(100, round((k_val / 170) * 100))
    soil_health_score = round((n_score * 0.4 + p_score * 0.3 + k_score * 0.3))

    # Parse recommendation plan details
    plan_detail = {}
    if plan:
        how_much = plan.get("how_much", {})
        plan_detail = {
            "DAP_kg_ha": how_much.get("DAP_kg_ha", 0) if isinstance(how_much, dict) else 0,
            "Urea_kg_ha": how_much.get("UREA_kg_ha", 0) if isinstance(how_much, dict) else 0,
            "MOP_kg_ha": how_much.get("MOP_kg_ha", 0) if isinstance(how_much, dict) else 0,
        }

    # Crop stage sequence for timeline
    stage_sequence = {
        "SUGARCANE": ["Land Prep", "Germination", "Tillering", "Grand Growth", "Ripening", "Harvest"],
        "RICE":      ["Nursery", "Transplanting", "Tillering", "Panicle Init", "Flowering", "Maturity"],
        "SOYBEAN":   ["Emergence", "Vegetative", "Flowering", "Pod Fill", "Maturity", "Harvest"],
    }
    crop_code_upper = (dict(row).get("crop_name") or "").upper()
    stages = stage_sequence.get(crop_code_upper, stage_sequence["SUGARCANE"])
    current_stage_raw = dict(row).get("current_stage") or "GRAND_GROWTH"
    stage_display_map = {
        "GRAND_GROWTH": "Grand Growth", "TILLERING": "Tillering",
        "GERMINATION": "Germination", "RIPENING": "Ripening", "HARVEST": "Harvest",
        "NURSERY": "Nursery", "TRANSPLANTING": "Transplanting",
        "PANICLE_INIT": "Panicle Init", "FLOWERING": "Flowering", "MATURITY": "Maturity",
        "EMERGENCE": "Emergence", "VEGETATIVE": "Vegetative", "POD_FILL": "Pod Fill",
    }
    current_stage_display = stage_display_map.get(current_stage_raw, current_stage_raw.replace("_", " ").title())

    # Formatting to match frontend `twin_state.json`
    formatted_response = {
        "fieldId": row["field_code"] or str(row["field_id"]),
        "crop": dict(row).get("crop_name") or dict(row).get("crop_code") or "Unknown",
        "growthStage": current_stage_display,
        "growthStageRaw": current_stage_raw,
        "stageSequence": stages,
        "area_ha": dict(row).get("area_ha") or 0.0,
        "soilType": dict(row).get("soil_type"),
        "lat": dict(row).get("lat") or 16.705,
        "lon": dict(row).get("lon") or 74.2433,
        "location": f"{dict(row).get('lat', 16.705)}, {dict(row).get('lon', 74.2433)}",
        # A field with no soil_tests row has never had a soil report submitted —
        # the frontend must gate the dashboard behind this, not show 0-valued
        # nutrients as if they were a real (deficient) reading.
        "hasSoilTest": soil is not None,
        "soilHealthScore": soil_health_score,
        "soilDetail": {
            "ph": round(ph_val, 2) if ph_val else None,
            "oc_percent": round(oc_val, 3) if oc_val else None,
            "n_score": n_score,
            "p_score": p_score,
            "k_score": k_score,
        },
        "nutrients": {
            "n": { "current": n_val, "target": 340, "unit": "kg/ha" },
            "p": { "current": p_val, "target": 30, "unit": "kg/ha" },
            "k": { "current": k_val, "target": 170, "unit": "kg/ha" }
        },
        "currentPlan": {
            # `plan` (the persisted proof) sets what/when/why/how_much to an explicit
            # None (not a missing key) when status == ABSTAIN — so `.get(key, default)`
            # does NOT fall back to `default` in that case. Every lookup below must
            # guard with `or {}`/`or default` against that explicit None, not just a
            # missing key, or this 500s on any ABSTAINed field.
            "nextAction": (plan.get("what") if plan else None) or "Awaiting plan",
            "fertilizerBreakdown": plan_detail,
            "quantity": f"DAP {plan_detail.get('DAP_kg_ha',0)} + Urea {plan_detail.get('Urea_kg_ha',0)} + MOP {plan_detail.get('MOP_kg_ha',0)} kg/ha" if plan_detail else "N/A",
            "applicationWindow": (plan.get("when") if plan else None) or "N/A",
            # Real cost estimate lives under based_on.cost_estimate (an
            # ENGINEERING_DEFAULT price-table estimate, never the source of
            # kg/ha quantities) — `plan.get("cost")` was never a real key and
            # always fell through to a fake hardcoded 13242.
            "estimatedCost": (plan.get("based_on") or {}).get("cost_estimate") if plan else None,
            "costCitation": (plan.get("based_on") or {}).get("cost_citation") if plan else None,
            "confidence": (plan.get("confidence") if plan else None) or (rec["confidence"] if rec else "N/A"),
            "citation": (plan.get("based_on") or {}).get("citation", "") if plan else "",
            "soilGap": (plan.get("why") or {}).get("gap", {}) if plan else {},
            # Doc 14 Safety/HITL: ABSTAIN/LOW-CONFIDENCE must be surfaced with itemized reasons.
            "status": (plan.get("status") if plan else None) or "NO_DATA",
            "reason": plan.get("reason") if plan else None,
            "requiredActions": (plan.get("required_actions") if plan else None) or [],
            "flags": (plan.get("flags") if plan else None) or [],
        },
        "weather": {
            "rainfall_mm_next_7d": weather_payload.get("rainfall_mm_next_7d", 17),
            "heavy_rain_alert": weather_payload.get("heavy_rain_alert", False),
            "condition": (
                "Heavy rain expected — fertilizer application deferred"
                if weather_payload.get("heavy_rain_alert")
                else "Clear — suitable for fertilizer application"
            ),
        },
        "activeAlert": active_alert
    }
    
    return formatted_response



@router.post("/fields/{field_id}/recommend", response_model=RecommendationOut)
def recommend(
    field_id: str,
    body: RecommendRequest | None = None,
    conn: sqlite3.Connection = Depends(get_conn),
):
    body = body or RecommendRequest()
    row = _field_row(conn, field_id)
    get_monitoring_agent().bind(conn)
    if body.agents:
        result = request_replan(
            conn,
            row,
            agents=body.agents,
            mock_weather=body.mock_weather,
            optimizer=body.optimizer,
        )
    else:
        result = run_orchestrated_ledger(
            conn,
            row,
            mock_weather=body.mock_weather,
            farmer_input=body.farmer_input,
            optimizer=body.optimizer,
        )
    return result


@router.get("/fields/{field_id}/recommendations/latest")
def latest_recommendation(field_id: str, conn: sqlite3.Connection = Depends(get_conn)):
    row = _field_row(conn, field_id)
    rec = conn.execute(
        """SELECT * FROM recommendations WHERE field_id = ?
           ORDER BY generated_at DESC LIMIT 1""",
        (row["field_id"],),
    ).fetchone()
    if rec is None:
        raise HTTPException(status_code=404, detail="No recommendation yet")
    try:
        plan = _json_load(rec["plan_json"])
    except json.JSONDecodeError:
        plan = {}
    plan["status_db"] = rec["status"]
    plan["invalidated_at"] = rec["invalidated_at"]
    plan["superseded_by"] = rec["superseded_by"]
    plan["recommendation_id"] = rec["recommendation_id"]
    return plan


@router.get("/fields/{field_id}/alerts")
def alerts(field_id: str, conn: sqlite3.Connection = Depends(get_conn)):
    row = _field_row(conn, field_id)
    return {"alerts": get_alerts(conn, row["field_id"])}


@router.post("/events")
def inject_event(body: EventIn, conn: sqlite3.Connection = Depends(get_conn)):
    """
    Demo / webhook entry: inject HEAVY_RAIN_ALERT (or any EventType).

    Example:
      POST /events
      {"type":"HEAVY_RAIN_ALERT","field_code":"SYN-001",
       "payload":{"heavy_rain_alert":true,"rainfall_probability":90,"rainfall_mm_next_7d":80}}
    """
    field_id = body.field_id
    field_code = body.field_code
    if field_id is None and field_code:
        row = conn.execute(
            "SELECT field_id, field_code FROM fields WHERE field_code = ?",
            (field_code,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Field not found")
        field_id = row["field_id"]
        field_code = row["field_code"]
    if field_id is None:
        raise HTTPException(status_code=400, detail="field_id or field_code required")

    monitor = get_monitoring_agent()
    monitor.bind(conn)
    event = Event.create(
        body.type,
        field_id=int(field_id),
        field_code=field_code,
        payload=body.payload,
        actor=body.actor,
    )
    get_bus().publish(event, conn=conn)

    latest = conn.execute(
        """SELECT recommendation_id, status, plan_json, invalidated_at, superseded_by
           FROM recommendations WHERE field_id = ?
           ORDER BY recommendation_id DESC LIMIT 1""",
        (field_id,),
    ).fetchone()
    plan: dict = {}
    if latest:
        try:
            plan = _json_load(latest["plan_json"])
        except json.JSONDecodeError:
            plan = {}
        plan["status_db"] = latest["status"]
        plan["invalidated_at"] = latest["invalidated_at"]
        plan["recommendation_id"] = latest["recommendation_id"]
    return {
        "injected": event.to_dict(),
        "latest_plan": {
            "status": plan.get("status"),
            "when": plan.get("when"),
            "what": plan.get("what"),
            "how_much": plan.get("how_much"),
            "mode": plan.get("mode"),
            "agents_run": plan.get("agents_run"),
            "confidence": plan.get("confidence"),
            "status_db": plan.get("status_db"),
            "recommendation_id": plan.get("recommendation_id"),
        },
        "alerts": get_alerts(conn, int(field_id)),
    }


@router.post("/fields/{field_id}/crop")
def assign_crop(
    field_id: str,
    body: CropAssignRequest,
    conn: sqlite3.Connection = Depends(get_conn),
):
    """
    Assign or update a field's active crop, sowing date, stage, and recommendation type.
    """
    row = _field_row(conn, field_id)
    crop = conn.execute(
        "SELECT crop_id FROM crops WHERE UPPER(crop_code) = ?",
        (body.crop_code.upper().strip(),),
    ).fetchone()
    if crop is None:
        raise HTTPException(status_code=400, detail=f"Unknown crop_code: {body.crop_code}")
    crop_id = crop["crop_id"]

    # Deactivate previous active crop
    conn.execute(
        "UPDATE field_crops SET is_active = FALSE WHERE field_id = ?",
        (row["field_id"],),
    )

    cur = conn.cursor()
    cur.execute(
        """INSERT INTO field_crops
           (field_id, crop_id, variety, sowing_date, current_stage,
            recommendation_type, target_yield_kg_ha, is_active)
           VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
        (
            row["field_id"],
            crop_id,
            body.variety,
            body.sowing_date,
            body.current_stage,
            body.recommendation_type,
            body.target_yield_kg_ha,
        ),
    )
    conn.commit()

    monitor = get_monitoring_agent()
    monitor.bind(conn)
    event = Event.create(
        "CROP_STAGE_CHANGED",
        field_id=row["field_id"],
        field_code=row["field_code"],
        payload=body.model_dump(),
        actor="farmer",
    )
    get_bus().publish(event, conn=conn)

    return {
        "status": "success",
        "field_id": row["field_id"],
        "crop_id": crop_id,
        "crop_code": body.crop_code.upper().strip(),
        "current_stage": body.current_stage,
        "recommendation_type": body.recommendation_type,
    }


@router.post("/fields/{field_id}/soil-report/upload")
def upload_soil_report(
    field_id: str,
    file: UploadFile = File(...),
    conn: sqlite3.Connection = Depends(get_conn)
):
    """
    Step 1: Upload a soil report, run real extraction via soil_report_agent,
    and return extracted fields with per-field confidence.
    """
    row = _field_row(conn, field_id)
    contents = file.file.read()
    res = soil_report_agent.process_upload(
        conn,
        row["field_id"],
        file.filename or "report.txt",
        contents,
    )
    return {
        "status": res["status"],
        "upload_id": res["upload_id"],
        "file_path": res["original_file_path"],
        "extracted_data": res["extracted"],
        "fields_needing_review": res["fields_needing_review"],
        "engine": res["engine"],
        "message": res["message"],
    }


@router.post("/fields/{field_id}/soil-report/confirm")
def confirm_soil_report(
    field_id: str,
    body: SoilReportConfirmRequest,
    conn: sqlite3.Connection = Depends(get_conn)
):
    """
    Step 2: Farmer confirms the OCR values. Save to twin and trigger event.
    """
    row = _field_row(conn, field_id)
    if body.upload_id:
        # This singleton may hold a connection closed by an earlier request.
        get_monitoring_agent().bind(conn)
        confirmed = {
            "n_kg_ha": body.soil_test.n_kg_ha,
            "p_kg_ha": body.soil_test.p_kg_ha,
            "k_kg_ha": body.soil_test.k_kg_ha,
            "ph": body.soil_test.ph,
            "oc_percent": body.soil_test.oc_percent,
            "ec_ds_m": body.soil_test.ec_ds_m,
            "test_date": body.soil_test.test_date,
        }
        res = soil_report_agent.confirm_and_write(conn, body.upload_id, confirmed, actor="farmer")
        return {"status": "success", "message": "Soil report confirmed and Twin updated.", "details": res}

    test_date = body.soil_test.test_date or datetime.utcnow().strftime("%Y-%m-%d")
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO soil_tests 
           (field_id, test_date, n_kg_ha, p_kg_ha, k_kg_ha, ph, oc_percent, ec_ds_m, 
            source, ocr_confidence, original_file_path)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (
            row["field_id"],
            test_date,
            body.soil_test.n_kg_ha,
            body.soil_test.p_kg_ha,
            body.soil_test.k_kg_ha,
            body.soil_test.ph,
            body.soil_test.oc_percent,
            body.soil_test.ec_ds_m,
            body.soil_test.source,
            body.soil_test.ocr_confidence,
            body.soil_test.original_file_path
        )
    )
    conn.commit()

    monitor = get_monitoring_agent()
    monitor.bind(conn)
    event = Event.create(
        "SOIL_REPORT_UPDATED",
        field_id=row["field_id"],
        field_code=row["field_code"],
        payload=body.soil_test.model_dump(),
        actor="farmer"
    )
    get_bus().publish(event, conn=conn)

    return {"status": "success", "message": "Soil report confirmed and Twin updated."}


@router.post("/fields/{field_id}/what-if")
def what_if_simulator(
    field_id: str,
    body: WhatIfRequest,
    conn: sqlite3.Connection = Depends(get_conn)
):
    """
    Run the what-if simulator and return current plan vs new plan side-by-side.
    """
    row = _field_row(conn, field_id)
    
    # Get current plan
    current_rec = conn.execute(
        """SELECT plan_json FROM recommendations WHERE field_id = ? AND status = 'PROPOSED'
           ORDER BY generated_at DESC LIMIT 1""",
        (row["field_id"],)
    ).fetchone()
    
    original_plan = {}
    if current_rec:
        try:
            original_plan = _json_load(current_rec["plan_json"])
        except:
            pass

    mock_weather = {}
    if body.rainfall_mm is not None:
        mock_weather["rainfall_mm_next_7d"] = body.rainfall_mm

    farmer_input = {}
    if body.fertilizer_delta_pct is not None:
        farmer_input["fertilizer_delta_pct"] = body.fertilizer_delta_pct

    # Re-run pipeline for simulated plan
    from ..agents.orchestrator import get_pipeline
    simulated_plan = get_pipeline().run(
        conn,
        row,
        mock_weather=mock_weather if mock_weather else None,
        farmer_input=farmer_input if farmer_input else None,
        persist=False,
        emit_events=False,
    )
    
    # We do NOT save the simulated plan to DB. It's just for frontend rendering.
    # A real implementation might save it with is_synthetic=1 but for MVP just return.
    if body.fertilizer_delta_pct is not None and simulated_plan.get("how_much"):
        multiplier = 1.0 + (body.fertilizer_delta_pct / 100.0)
        for k, v in simulated_plan["how_much"].items():
            if isinstance(v, (int, float)):
                simulated_plan["how_much"][k] = round(v * multiplier, 2)
        if simulated_plan.get("plan_kg_ha"):
            for k, v in simulated_plan["plan_kg_ha"].items():
                if isinstance(v, (int, float)):
                    simulated_plan["plan_kg_ha"][k] = round(v * multiplier, 2)
        # The pre-scaling narrative describes different quantities.
        simulated_plan["narrative"] = ""

    # Formatting to match frontend `what_if.json`
    def format_plan(plan: dict, is_simulated: bool = False):
        if not plan:
            return {
                "fertilizer": "N/A", "rainfall": "N/A", "yieldBand": "N/A",
                "confidence": "N/A", "cost": 0,
                "modelSignals": { "growthStage": dict(row).get("current_stage") or "Initial", "vigor": "N/A", "nutrientSufficiency": "N/A", "waterStress": "N/A" }
            }
        # fertilizer formatted string
        how_much = plan.get("how_much", {})
        fert_str = ", ".join([f"{v} {k}" for k,v in how_much.items()]) if how_much else "N/A"
        
        # Rainfall condition
        rainfall = "Normal"
        if is_simulated and mock_weather.get("rainfall_mm_next_7d"):
            if mock_weather["rainfall_mm_next_7d"] > 50: rainfall = "Heavy"
            elif mock_weather["rainfall_mm_next_7d"] < 10: rainfall = "Low"

        # Yield band
        yield_val = dict(row).get("target_yield_kg_ha") or 4000
        yield_t = float(yield_val) / 1000
        if is_simulated and body.fertilizer_delta_pct and body.fertilizer_delta_pct < 0:
            yield_t *= 0.95 # Mock reduction for visualization
        yield_band = f"{round(yield_t * 0.95, 1)}-{round(yield_t * 1.05, 1)} t/ha"

        # Vigor and stress
        vigor = "thriving"
        water_stress = "none"
        if rainfall == "Heavy": water_stress = "high"
        elif rainfall == "Low": water_stress = "moderate"
        if is_simulated and body.fertilizer_delta_pct and body.fertilizer_delta_pct < 0:
            vigor = "below-average"

        return {
            "fertilizer": fert_str,
            "rainfall": rainfall,
            "yieldBand": yield_band,
            "confidence": plan.get("confidence", "HIGH"),
            "cost": plan.get("cost", 1200) if not is_simulated else (plan.get("cost", 1200) * (1 + (body.fertilizer_delta_pct or 0)/100.0)),
            "modelSignals": {
                "growthStage": dict(row).get("current_stage") or "Initial",
                "vigor": vigor,
                "nutrientSufficiency": "suboptimal" if (is_simulated and body.fertilizer_delta_pct and body.fertilizer_delta_pct < 0) else "optimal",
                "waterStress": water_stress
            }
        }

    formatted_response = {
        "crop": dict(row).get("crop_name") or dict(row).get("crop_code") or "Unknown",
        "original": format_plan(original_plan, is_simulated=False),
        "simulated": format_plan(simulated_plan, is_simulated=True)
    }

    return formatted_response


@router.post("/fields/{field_id}/override")
def agronomist_override(
    field_id: str,
    body: OverrideRequest,
    conn: sqlite3.Connection = Depends(get_conn)
):
    """Agronomist overrides the plan."""
    row = _field_row(conn, field_id)
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

    cur = conn.cursor()
    # Mark old as superseded
    cur.execute(
        """UPDATE recommendations SET status = 'SUPERSEDED', invalidated_at = ?
           WHERE recommendation_id = ?""",
        (now, body.recommendation_id)
    )

    # Insert new
    cur.execute(
        """INSERT INTO recommendations 
           (field_id, plan_json, status, confidence, confidence_reason, is_synthetic)
           VALUES (?, ?, 'PROPOSED', 'HIGH', 'Agronomist Override', false)""",
        (row["field_id"], json.dumps(body.new_plan))
    )
    new_rec_id = cur.lastrowid
    
    # Audit trail
    import logging
    LOG = logging.getLogger(__name__)
    LOG.info(
        "Agronomist override: recommendation_id=%d agronomist=%s reason=%s new_rec_id=%d",
        body.recommendation_id, body.agronomist_id, body.reason, new_rec_id,
    )
    cur.execute(
        """INSERT INTO audit_log (entity_type, entity_id, action, actor, old_value, new_value)
           VALUES ('recommendation', ?, 'OVERRIDE', ?, ?, ?)""",
        (
            body.recommendation_id,
            body.agronomist_id,
            json.dumps({"recommendation_id": body.recommendation_id}),
            json.dumps({"new_recommendation_id": new_rec_id, "reason": body.reason})
        )
    )
    
    # Event
    event = Event.create(
        "EXPERT_OVERRIDE",
        field_id=row["field_id"],
        payload={"reason": body.reason, "new_rec_id": new_rec_id},
        actor=body.agronomist_id
    )
    conn.commit()
    
    get_bus().publish(event, conn=conn)

    return {"status": "success", "new_recommendation_id": new_rec_id}


@router.post("/farmers", status_code=201)
def create_farmer(
    body: FarmerCreateRequest,
    conn=Depends(get_conn),
):
    """
    Create a new farmer record.
    region_id must reference an existing row in the regions table.
    """
    region = conn.execute(
        "SELECT region_id FROM regions WHERE region_id = ?", (body.region_id,)
    ).fetchone()
    if region is None:
        raise HTTPException(status_code=400, detail=f"region_id {body.region_id} not found")

    cur = conn.cursor()
    cur.execute(
        """INSERT INTO farmers (region_id, full_name, mobile, preferred_lang)
           VALUES (?, ?, ?, ?)""",
        (body.region_id, body.full_name, body.mobile, body.preferred_lang),
    )
    conn.commit()
    farmer_id = cur.lastrowid
    return {"status": "created", "farmer_id": farmer_id}


@router.post("/fields", status_code=201)
def create_field(
    body: FieldCreateRequest,
    conn=Depends(get_conn),
):
    """
    Create a new field.
    region_id and district_id must reference existing rows.
    field_code must be unique if supplied.
    After creation use POST /fields/{id}/crop to assign a crop,
    and POST /fields/{id}/soil-report/confirm to add a soil test,
    before calling POST /fields/{id}/recommend.
    """
    if conn.execute(
        "SELECT 1 FROM regions WHERE region_id = ?", (body.region_id,)
    ).fetchone() is None:
        raise HTTPException(status_code=400, detail=f"region_id {body.region_id} not found")
    if conn.execute(
        "SELECT 1 FROM districts WHERE district_id = ?", (body.district_id,)
    ).fetchone() is None:
        raise HTTPException(status_code=400, detail=f"district_id {body.district_id} not found")

    cur = conn.cursor()
    cur.execute(
        """INSERT INTO fields
           (region_id, district_id, taluka_id, farmer_id, field_code,
            area_ha, soil_type, irrigation_type, lat, lon, is_synthetic)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            body.region_id,
            body.district_id,
            body.taluka_id,
            body.farmer_id,
            body.field_code,
            body.area_ha,
            body.soil_type,
            body.irrigation_type,
            body.lat,
            body.lon,
            False,   # is_synthetic: real farmer-created field
        ),
    )
    conn.commit()
    field_id = cur.lastrowid
    return {
        "status": "created",
        "field_id": field_id,
        "field_code": body.field_code,
        "next_steps": [
            f"POST /fields/{field_id}/crop   — assign active crop",
            f"POST /fields/{field_id}/soil-report/confirm — add soil test",
            f"POST /fields/{field_id}/recommend — generate recommendation",
        ],
    }


# ─── Convenience / Alias Routes ───────────────────────────────────────────────

@router.get("/fields")
def list_fields(conn: sqlite3.Connection = Depends(get_conn)):
    """Return all registered fields with basic metadata."""
    rows = conn.execute(
        """SELECT f.field_code, f.area_ha, f.lat, f.lon, f.soil_type,
                  fa.full_name as farmer_name,
                  c.crop_name as crop_code, fac.current_stage
           FROM fields f
           LEFT JOIN farmers fa ON fa.farmer_id = f.farmer_id
           LEFT JOIN field_active_crop fac ON fac.field_id = f.field_id
           LEFT JOIN crops c ON c.crop_id = fac.current_crop_id
           ORDER BY f.field_code"""
    ).fetchall()
    return [dict(r) for r in rows]


@router.post("/upload-soil-report")
async def upload_soil_report_global(
    file: UploadFile = File(...),
    conn: sqlite3.Connection = Depends(get_conn),
):
    """
    Global OCR upload endpoint (field-agnostic).
    Extracts soil nutrient values from an uploaded file (PDF / image / text).
    """
    from ..core.ocr import run_ocr_pipeline

    contents = await file.read()
    filename = file.filename or "upload.txt"

    try:
        result = run_ocr_pipeline(contents, filename)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OCR pipeline error: {exc}") from exc

    extracted = result.get("extracted", result)

    def _val(key):
        v = extracted.get(key)
        return v.get("value") if isinstance(v, dict) else v

    return {
        "status":     result.get("status", "extracted"),
        "engine":     result.get("engine", "text_direct"),
        "n_kg_ha":    _val("n_kg_ha"),
        "p_kg_ha":    _val("p_kg_ha"),
        "k_kg_ha":    _val("k_kg_ha"),
        "ph":         _val("ph"),
        "oc_percent": _val("oc_percent"),
        "ec_ds_m":    _val("ec_ds_m"),
        "raw":        extracted,
    }


@router.get("/recommend/{field_id}", response_model=RecommendationOut)
def recommend_get(
    field_id: str,
    conn: sqlite3.Connection = Depends(get_conn),
):
    """
    GET alias for /fields/{field_id}/recommend.
    Runs the full proof-carrying multi-agent recommendation pipeline.
    """
    row = _field_row(conn, field_id)
    get_monitoring_agent().bind(conn)
    result = run_orchestrated_ledger(conn, row)
    return result


@router.get("/alerts")
def list_all_alerts(
    limit: int = Query(50, ge=1, le=500),
    conn: sqlite3.Connection = Depends(get_conn),
):
    """Return the most recent alerts across ALL fields."""
    rows = conn.execute(
        """SELECT a.*, f.field_code
           FROM alerts a
           LEFT JOIN fields f ON f.field_id = a.field_id
           ORDER BY a.triggered_at DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]
