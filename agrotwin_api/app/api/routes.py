"""API routers — recommend, twin, events, alerts."""

from __future__ import annotations

import json
import os
import sqlite3

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from datetime import datetime
import io
from gtts import gTTS

from ..agents import soil_report_agent
from ..agents import weather_agent
from ..agents.crop_agent import resolve_dynamic_stage
from ..agents.monitoring_agent import get_alerts, get_monitoring_agent
from ..agents.orchestrator import request_replan, run_orchestrated_ledger
from ..core.event_bus import get_bus
from ..core.events import Event
from .schemas import (
    ApplicationIn,
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
    """Check optional OCR readiness without making ML mandatory."""
    try:
        import torch
    except ImportError:
        return {"status": "degraded", "engine": "unavailable", "cuda_available": False}
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


def _get_rdf_targets(conn: sqlite3.Connection, crop_code: str, rec_type: str):
    """Returns (n_kg_ha, p2o5_kg_ha, k2o_kg_ha) from the same authoritative
    fertilizer_recommendations table the ledger/optimizer use, or None if no
    RDF row exists for this crop/stage. Never invent a universal target."""
    from ..ledger import get_recommendation as _get_recommendation

    rec = _get_recommendation(conn, crop_code, rec_type)
    if rec is None:
        return None
    required_n, required_p2o5, required_k2o = rec[0], rec[1], rec[2]
    return (
        float(required_n) if required_n is not None else None,
        float(required_p2o5) if required_p2o5 is not None else None,
        float(required_k2o) if required_k2o is not None else None,
    )


def _water_stress(irrigation_type: str | None, weather_available: bool, rainfall_mm_next_7d: float | None) -> dict:
    """Coarse dryness signal — see rules.water_stress in region_config.py for
    the threshold and its (lack of a real) evidence base. Never a substitute
    for a soil-moisture/water-balance model this system doesn't have."""
    from ..core.region_config import load_region_config

    irrigation = (irrigation_type or "").strip().lower()
    if irrigation == "irrigated":
        return {"label": "Low", "reason": "Field is irrigated — rainfall shortfall is supplemented."}
    if irrigation != "rainfed":
        return {"label": "Not available", "reason": "Irrigation type not recorded for this field."}
    if not weather_available or rainfall_mm_next_7d is None:
        return {"label": "Not available", "reason": "No current rainfall forecast to assess a rainfed field against."}
    threshold = load_region_config()["rules"]["water_stress"]["dry_threshold_mm"]
    if rainfall_mm_next_7d < threshold:
        return {"label": "Elevated", "reason": f"Rainfed field; forecast rainfall ({rainfall_mm_next_7d} mm/7d) is below the {threshold} mm dryness threshold."}
    return {"label": "Low", "reason": f"Rainfed field; forecast rainfall ({rainfall_mm_next_7d} mm/7d) meets the {threshold} mm dryness threshold."}


def _crop_condition(soil_health_score: float | None, ph: float | None) -> dict:
    """Proxy from real, already-measured soil signals — see rules.crop_condition
    in region_config.py. Never a substitute for a vision/scouting assessment."""
    from ..core.region_config import load_region_config

    if soil_health_score is None:
        return {"label": "Not available", "reason": "No confirmed soil test to derive a nutrient-sufficiency proxy from."}
    cfg = load_region_config()["rules"]
    good_min = cfg["crop_condition"]["good_score_min"]
    poor_max = cfg["crop_condition"]["poor_score_max"]
    ph_min, ph_max = cfg["soil_limits"]["ph_min"], cfg["soil_limits"]["ph_max"]
    ph_ok = ph is None or (ph_min <= ph <= ph_max)
    if soil_health_score < poor_max or not ph_ok:
        reason = f"Soil health score ({soil_health_score}/100) is below {poor_max}" if soil_health_score < poor_max else f"pH ({ph}) is outside the {ph_min}–{ph_max} sufficiency window"
        return {"label": "Needs Attention", "reason": reason + "."}
    if soil_health_score >= good_min and ph_ok:
        return {"label": "Good", "reason": f"Soil health score ({soil_health_score}/100) meets the {good_min} threshold and pH is in range."}
    return {"label": "Fair", "reason": f"Soil health score ({soil_health_score}/100) is between {poor_max} and {good_min}."}


def _pest_disease_risk(weather_available: bool, rainfall_mm_next_7d: float | None) -> dict:
    """Moisture-driven proxy — see rules.pest_disease_risk in region_config.py.
    Never a substitute for a pest-scouting or disease-detection model."""
    from ..core.region_config import load_region_config

    if not weather_available or rainfall_mm_next_7d is None:
        return {"label": "Not available", "reason": "No current rainfall forecast to assess moisture-driven pest/disease pressure."}
    threshold = load_region_config()["rules"]["pest_disease_risk"]["wet_threshold_mm"]
    if rainfall_mm_next_7d >= threshold:
        return {"label": "Elevated", "reason": f"Forecast rainfall ({rainfall_mm_next_7d} mm/7d) is at or above the {threshold} mm wet-conditions threshold."}
    return {"label": "Low", "reason": f"Forecast rainfall ({rainfall_mm_next_7d} mm/7d) is below the {threshold} mm wet-conditions threshold."}


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

    # Derived display/context only: a GET or what-if must not write crop state.
    if row["current_crop_id"] is not None:
        computed = resolve_dynamic_stage(conn, row["current_crop_id"], row["sowing_date"])
        if computed:
            row = {**dict(row), "current_stage": computed["stage_name"]}
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
           ORDER BY test_date DESC, soil_test_id DESC LIMIT 1""",
        (row["field_id"],),
    ).fetchone()
    
    rec = conn.execute(
        """SELECT * FROM recommendations WHERE field_id = ?
           ORDER BY generated_at DESC, recommendation_id DESC LIMIT 1""",
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

    # Only fresh, field-scoped snapshots support a current weather display.
    from datetime import timezone
    weather_status = "COORDINATES_MISSING" if row["lat"] is None or row["lon"] is None else "WEATHER_UNAVAILABLE"
    weather_snapshot = conn.execute("""SELECT * FROM weather_snapshots WHERE field_id = ?
        ORDER BY fetched_at DESC, snapshot_id DESC LIMIT 1""", (row["field_id"],)).fetchone()
    weather_payload = None
    weather_source = None
    if weather_snapshot is not None and weather_status != "COORDINATES_MISSING":
        try:
            fetched = datetime.fromisoformat(str(weather_snapshot["fetched_at"]))
            if fetched.tzinfo is None:
                fetched = fetched.replace(tzinfo=timezone.utc)
            fresh = 0 <= (datetime.now(timezone.utc) - fetched).total_seconds() <= 900
            if fresh:
                weather_source = weather_snapshot["source"]
                weather_status = "WEATHER_AVAILABLE" if weather_source == "open-meteo" else "SIMULATED_WEATHER"
                weather_payload = dict(weather_snapshot)
        except (ValueError, TypeError):
            pass

    # No fresh (<=15 min) cached snapshot — fetch live rather than making the
    # farmer run a full /recommend just to see this week's forecast. A field
    # only needs a weather agent RUN recorded, not a run in the last 15 minutes.
    if weather_payload is None and weather_status != "COORDINATES_MISSING":
        try:
            live = weather_agent.get_weather_context(
                conn, row["field_id"], row["lat"], row["lon"], force_refresh=False
            )
            snap = live.get("snapshot")
            if snap is not None:
                weather_source = snap.get("source")
                weather_status = "WEATHER_AVAILABLE" if weather_source == "open-meteo" else "SIMULATED_WEATHER"
                weather_payload = snap
            else:
                weather_status = live.get("status", weather_status)
        except Exception:
            pass

    # Soil health score / N-P-K sufficiency requires a crop-aware nutrient target.
    # Reuse the SAME authoritative RDF lookup the ledger/optimizer use
    # (fertilizer_recommendations, keyed by crop_code + recommendation_type) —
    # do not invent a universal threshold. A field whose crop/stage has no
    # matching RDF row (or no soil test at all) gets an honest "not available"
    # score, not a sugarcane-shaped number applied to every crop.
    n_val = soil["n_kg_ha"] if soil else None
    p_val = soil["p_kg_ha"] if soil else None
    k_val = soil["k_kg_ha"] if soil else None
    ph_val = soil["ph"] if soil else None
    oc_val = soil["oc_percent"] if soil else None

    from ..core.nutrients import normalize, CONVERSION_SOURCE
    normalized = normalize(n_val, p_val, k_val)
    n_val, p_val, k_val = normalized["N"], normalized["P2O5"], normalized["K2O"]

    crop_code_for_rdf = dict(row).get("crop_code_str")
    rec_type_for_rdf = dict(row).get("recommendation_type")
    rdf_targets = None
    if crop_code_for_rdf and rec_type_for_rdf:
        rdf_targets = _get_rdf_targets(conn, crop_code_for_rdf, rec_type_for_rdf)

    n_score = p_score = k_score = None
    soil_health_score = None
    if soil is not None and rdf_targets is not None:
        target_n, target_p2o5, target_k2o = rdf_targets
        n_score = min(100, round((n_val / target_n) * 100)) if target_n and n_val is not None else None
        p_score = min(100, round((p_val / target_p2o5) * 100)) if target_p2o5 and p_val is not None else None
        k_score = min(100, round((k_val / target_k2o) * 100)) if target_k2o and k_val is not None else None
        if n_score is not None and p_score is not None and k_score is not None:
            soil_health_score = round((n_score * 0.4 + p_score * 0.3 + k_score * 0.3))

    # Parse recommendation plan details
    plan_detail = {}
    if plan:
        how_much = plan.get("how_much")
        if isinstance(how_much, dict) and plan.get("status") != "ABSTAIN":
            plan_detail = {key: value for key, value in how_much.items() if value is not None}

    # Persisted calendar is the shared crop-code/stage source used by onboarding and the Crop Agent.
    calendar = conn.execute("SELECT stage_name FROM crop_calendars WHERE crop_id = ? ORDER BY stage_order", (row["current_crop_id"],)).fetchall()
    stages = [entry["stage_name"].replace("_", " ").title() for entry in calendar]
    current_stage_raw = row["current_stage"] or ""
    current_stage_display = current_stage_raw.replace("_", " ").title()

    # Formatting to match frontend `twin_state.json`
    formatted_response = {
        "fieldId": row["field_code"] or str(row["field_id"]),
        "crop": dict(row).get("crop_name") or dict(row).get("crop_code") or "Unknown",
        "growthStage": current_stage_display,
        "growthStageRaw": current_stage_raw,
        "stageSequence": stages,
        "area_ha": dict(row).get("area_ha") or 0.0,
        "soilType": dict(row).get("soil_type"),
        # No hardcoded Kolhapur/Polgaon coordinate fallback — a field without a
        # real recorded lat/lon must show as "not provided", never a demo location.
        "lat": dict(row).get("lat"),
        "lon": dict(row).get("lon"),
        "location": (
            f"{dict(row).get('lat')}, {dict(row).get('lon')}"
            if dict(row).get("lat") is not None and dict(row).get("lon") is not None
            else None
        ),
        # A field with no soil_tests row has never had a soil report submitted —
        # the frontend must gate the dashboard behind this, not show 0-valued
        # nutrients as if they were a real (deficient) reading.
        "hasSoilTest": soil is not None,
        "soilHealthScore": soil_health_score,
        "soilDetail": {
            "ph": round(ph_val, 2) if ph_val is not None else None,
            "oc_percent": round(oc_val, 3) if oc_val is not None else None,
            "n_score": n_score,
            "p_score": p_score,
            "k_score": k_score,
        },
        "nutrientBasis": "N/P2O5/K2O",
        "conversionSource": CONVERSION_SOURCE,
        "nutrients": {
            "n": {"current": n_val, "target": rdf_targets[0] if rdf_targets else None, "unit": "kg N/ha"},
            "p": {"current": p_val, "target": rdf_targets[1] if rdf_targets else None, "unit": "kg P2O5/ha"},
            "k": {"current": k_val, "target": rdf_targets[2] if rdf_targets else None, "unit": "kg K2O/ha"},
        },
        "proof": plan or None,
        "currentPlan": {
            # `plan` (the persisted proof) sets what/when/why/how_much to an explicit
            # None (not a missing key) when status == ABSTAIN — so `.get(key, default)`
            # does NOT fall back to `default` in that case. Every lookup below must
            # guard with `or {}`/`or default` against that explicit None, not just a
            # missing key, or this 500s on any ABSTAINed field.
            "nextAction": (plan.get("what") if plan else None) or "Awaiting plan",
            "fertilizerBreakdown": plan_detail,
            "quantity": " + ".join(f"{key.removesuffix('_kg_ha')} {value}" for key, value in plan_detail.items()) + " kg/ha" if plan_detail else "N/A",
            "applicationWindow": (plan.get("when") if plan else None) or "N/A",
            # Real cost estimate lives under based_on.cost_estimate (an
            # ENGINEERING_DEFAULT price-table estimate, never the source of
            # kg/ha quantities) — `plan.get("cost")` was never a real key and
            # always fell through to a fake hardcoded 13242.
            "estimatedCost": (plan.get("based_on") or {}).get("cost_estimate") if plan else None,
            "costCitation": (plan.get("based_on") or {}).get("cost_citation") if plan else None,
            "pricesPerKg": (plan.get("based_on") or {}).get("prices_inr_per_kg") if plan else None,
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
            "available": weather_payload is not None,
            "status": weather_status,
            "source": weather_source,
            "rainfall_mm_next_7d": weather_payload.get("rainfall_mm_next_7d") if weather_payload else None,
            "heavy_rain_alert": bool(weather_payload.get("heavy_rain_alert", False)) if weather_payload else False,
            "condition": (
                "Heavy rain expected — fertilizer application deferred"
                if weather_payload and weather_payload.get("heavy_rain_alert")
                else "Forecast available; no heavy-rain alert"
                if weather_payload
                else None
            ),
        },
        "waterStress": _water_stress(
            dict(row).get("irrigation_type"),
            weather_payload is not None,
            weather_payload.get("rainfall_mm_next_7d") if weather_payload else None,
        ),
        "cropCondition": _crop_condition(soil_health_score, ph_val),
        "pestDiseaseRisk": _pest_disease_risk(
            weather_payload is not None,
            weather_payload.get("rainfall_mm_next_7d") if weather_payload else None,
        ),
        "activeAlert": active_alert
    }
    concerning = {"Elevated", "Needs Attention"}
    signals = [
        formatted_response["waterStress"]["label"],
        formatted_response["cropCondition"]["label"],
        formatted_response["pestDiseaseRisk"]["label"],
    ]
    if all(label == "Not available" for label in signals):
        formatted_response["overallStatus"] = "Unknown"
    elif any(label in concerning for label in signals):
        formatted_response["overallStatus"] = "Needs Attention"
    else:
        formatted_response["overallStatus"] = "Healthy"

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
           ORDER BY generated_at DESC, recommendation_id DESC LIMIT 1""",
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


@router.get("/fields/{field_id}/recommendations")
def recommendation_history(
    field_id: str,
    limit: int = Query(20, ge=1, le=100),
    conn: sqlite3.Connection = Depends(get_conn),
):
    """
    Every recommendation ever generated for this field, most recent first —
    the audit trail for the Recommendation History / Oversight panel. Reuses
    the same `recommendations` rows the ledger/monitoring agent already
    write; this is a read-only view over existing data, not a new concept.
    """
    row = _field_row(conn, field_id)
    rows = conn.execute(
        """SELECT recommendation_id, generated_at, status, confidence, confidence_reason,
                  total_cost_estimate, invalidated_at, superseded_by, plan_json
           FROM recommendations WHERE field_id = ?
           ORDER BY generated_at DESC, recommendation_id DESC LIMIT ?""",
        (row["field_id"], limit),
    ).fetchall()

    history = []
    for r in rows:
        try:
            plan = _json_load(r["plan_json"])
        except json.JSONDecodeError:
            plan = {}
        history.append({
            "recommendation_id": r["recommendation_id"],
            "generated_at": r["generated_at"],
            "status": r["status"],
            "confidence": r["confidence"],
            "confidence_reason": r["confidence_reason"],
            "total_cost_estimate": r["total_cost_estimate"],
            "invalidated_at": r["invalidated_at"],
            "superseded_by": r["superseded_by"],
            "what": plan.get("what"),
            "how_much": plan.get("how_much"),
            "when": plan.get("when"),
            "reason": plan.get("reason"),
        })
    return {"field_id": row["field_id"], "history": history}


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
    extension = os.path.splitext(file.filename or "")[1].lower()
    if extension not in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".pdf", ".txt", ".csv", ".md"):
        raise HTTPException(status_code=415, detail="Use PNG, JPG, WEBP, BMP, TIFF, PDF, TXT, CSV or MD")
    contents = file.file.read(10 * 1024 * 1024 + 1)
    if not contents or len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Upload a nonempty soil report of at most 10 MB")
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
    if any(getattr(body.soil_test, key) is None for key in ("n_kg_ha", "p_kg_ha", "k_kg_ha")):
        raise HTTPException(status_code=422, detail="Confirm all three soil nutrients N, P and K")
    if not body.soil_test.test_date and not body.upload_id:
        raise HTTPException(status_code=422, detail="Enter the actual soil sample date")
    from ..core.nutrients import elemental
    body.soil_test.p_kg_ha, body.soil_test.k_kg_ha = elemental(
        body.soil_test.p_kg_ha, body.soil_test.k_kg_ha,
        p_basis=body.soil_test.p_basis, k_basis=body.soil_test.k_basis)
    row = _field_row(conn, field_id)
    if body.upload_id:
        upload = soil_report_agent.get_upload(conn, body.upload_id)
        if upload is None or upload["field_id"] != row["field_id"]:
            raise HTTPException(status_code=404, detail="Soil upload not found for this field")
        if upload["status"] == "CONFIRMED":
            raise HTTPException(status_code=409, detail="This upload has already been confirmed")
        if any(getattr(body.soil_test, key) is None for key in ("n_kg_ha", "p_kg_ha", "k_kg_ha")):
            raise HTTPException(status_code=422, detail="Review and enter nitrogen, phosphorus and potassium before confirming")
        # This singleton may hold a connection closed by an earlier request.
        get_monitoring_agent().bind(conn)
        if not body.soil_test.test_date:
            raise HTTPException(status_code=422, detail="Enter the actual soil sample date")
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
    from ..core.scenario import run_scenario
    return run_scenario(conn, _field_row(conn, field_id),
                        fertilizer_delta_pct=body.fertilizer_delta_pct,
                        rainfall_mm=body.rainfall_mm,
                        product_deltas_pct=body.product_deltas_pct)


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

    # The proof object this overridden plan replaces — reused for its `when`
    # (application window) and `based_on` (citation/cost) fields so overriding
    # the quantities doesn't blank out everything else /twin displays. Only
    # `how_much`, `what`, `status`, `confidence`, and `reason` are agronomist-set.
    original_row = conn.execute(
        "SELECT plan_json FROM recommendations WHERE recommendation_id = ?",
        (body.recommendation_id,),
    ).fetchone()
    try:
        original_plan = _json_load(original_row["plan_json"]) if original_row else {}
    except json.JSONDecodeError:
        original_plan = {}

    what_str = " + ".join(k.removesuffix("_kg_ha").replace("_", " ") for k in body.new_plan)
    override_plan = {
        **original_plan,
        "status": "PLAN_GENERATED",
        "what": what_str or original_plan.get("what"),
        "how_much": body.new_plan,
        "confidence": "HIGH",
        "reason": f"Agronomist override: {body.reason}",
    }

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
        (row["field_id"], json.dumps(override_plan))
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
def list_fields(conn: sqlite3.Connection = Depends(get_conn), demo: bool = False):
    """Return all registered fields with basic metadata."""
    rows = conn.execute(
        """SELECT f.field_id, f.field_code, f.area_ha, f.lat, f.lon, f.soil_type, f.is_synthetic,
                  fa.full_name as farmer_name,
                  c.crop_name as crop_code, fac.current_stage
           FROM fields f
           LEFT JOIN farmers fa ON fa.farmer_id = f.farmer_id
           LEFT JOIN field_active_crop fac ON fac.field_id = f.field_id
           LEFT JOIN crops c ON c.crop_id = fac.current_crop_id
           ORDER BY f.field_code"""
    ).fetchall()
    # REAL-NNN is the reserved namespace generated by seed_data.py. Those
    # imported pilot records have is_synthetic=False, so that flag alone is insufficient.
    fields = []
    for row in rows:
        field = dict(row)
        code = field["field_code"]
        is_demo = bool(field.pop("is_synthetic")) or (code.startswith("REAL-") and code[5:].isdigit())
        if is_demo == demo:
            field["is_demo"] = is_demo
            fields.append(field)
    for field in fields:
        field["soil_health_score"] = get_twin(str(field["field_id"]), conn)["soilHealthScore"]
    return fields


@router.get("/onboarding/options")
def onboarding_options(conn: sqlite3.Connection = Depends(get_conn)):
    """Persisted geography and supported crop contexts for farmer entry."""
    return {
        "districts": [dict(r) for r in conn.execute(
            """SELECT d.district_id, d.region_id, d.district_name, r.region_name
               FROM districts d JOIN regions r ON r.region_id = d.region_id
               ORDER BY r.region_name, d.district_name"""
        ).fetchall()],
        "crops": [dict(r) for r in conn.execute(
            """SELECT DISTINCT c.crop_code, c.crop_name, fr.recommendation_type
               FROM crops c JOIN fertilizer_recommendations fr ON fr.crop_id = c.crop_id
               ORDER BY c.crop_name, fr.recommendation_type"""
        ).fetchall()],
        "stages": [dict(r) for r in conn.execute(
            """SELECT c.crop_code, cc.stage_name, cc.region_id
               FROM crop_calendars cc JOIN crops c ON c.crop_id = cc.crop_id
               ORDER BY c.crop_code, cc.stage_order"""
        ).fetchall()],
    }


@router.get("/fields/{field_id}/applications")
def application_history(field_id: str, conn=Depends(get_conn)):
    row = _field_row(conn, field_id)
    rows = conn.execute("""SELECT a.*, p.product_code FROM applications a
        LEFT JOIN fertilizer_products p ON p.product_id = a.product_id
        WHERE a.field_id = ? ORDER BY a.application_date DESC, a.application_id DESC""", (row["field_id"],)).fetchall()
    return {"status": "RECORDED" if rows else "NO_RECORDED_APPLICATIONS", "applications": [dict(r) for r in rows]}


@router.get("/fertilizer-products")
def fertilizer_products(conn=Depends(get_conn)):
    return [dict(r) for r in conn.execute("SELECT product_code, product_name FROM fertilizer_products ORDER BY product_name").fetchall()]


def _replan_after_application(field_id: int, field_code: str, application_id: int) -> None:
    """Runs the selective replan on its own connection, after the response
    has already gone back to the farmer — recording an application should
    not make them wait on a live weather fetch + optimizer run."""
    bg_conn = get_db_connection()
    try:
        get_monitoring_agent().bind(bg_conn)
        get_bus().publish(Event.create("FERTILIZER_APPLIED", field_id=field_id, field_code=field_code,
            payload={"application_id": application_id}, actor="farmer"), conn=bg_conn)
    finally:
        bg_conn.close()


@router.post("/fields/{field_id}/applications", status_code=201)
def record_application(field_id: str, body: ApplicationIn, background_tasks: BackgroundTasks, conn=Depends(get_conn)):
    row = _field_row(conn, field_id)
    product = conn.execute("SELECT * FROM fertilizer_products WHERE product_code = ?", (body.product_code,)).fetchone()
    if product is None:
        raise HTTPException(status_code=422, detail="Select a registered fertilizer product")
    q = body.quantity_kg_ha
    cur = conn.execute("""INSERT INTO applications
        (field_id, product_id, application_date, quantity_kg_ha, n_supplied_kg_ha, p2o5_supplied_kg_ha, k2o_supplied_kg_ha, notes)
        VALUES (?,?,?,?,?,?,?,?)""", (row["field_id"], product["product_id"], body.application_date, q,
        q * float(product["n_percent"]) / 100, q * float(product["p2o5_percent"]) / 100,
        q * float(product["k2o_percent"]) / 100, body.notes))
    application_id = cur.lastrowid
    conn.commit()
    background_tasks.add_task(_replan_after_application, row["field_id"], row["field_code"], application_id)
    return {"status": "RECORDED", "application_id": application_id}


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

@router.post("/tts")
async def text_to_speech(
    text: str = Query(...),
    lang: str = Query("hi")
):
    """
    Fallback TTS endpoint.
    Accepts raw text and a language code (hi, mr, en).
    Returns an audio/mpeg stream.
    Note: 'mr' (Marathi) is natively supported by gTTS (Google Translate API).
    """
    tts_lang = lang if lang in ["hi", "mr", "en"] else "hi"
    try:
        tts = gTTS(text=text, lang=tts_lang, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return StreamingResponse(fp, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {e}")
