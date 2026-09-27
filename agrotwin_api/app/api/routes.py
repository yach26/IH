"""API routers — recommend, twin, events, alerts."""

from __future__ import annotations

import json
import os
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
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
from ..core.ocr import save_upload_file, run_ocr_on_file

router = APIRouter()


from ..db import get_db_connection, _json_load


def get_conn():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


def _field_row(conn: sqlite3.Connection, field_ref: str) -> sqlite3.Row:
    if field_ref.isdigit():
        row = conn.execute(
            "SELECT * FROM field_active_crop WHERE field_id = ?",
            (int(field_ref),),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT * FROM field_active_crop WHERE field_code = ?",
            (field_ref,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Field not found: {field_ref}")
    return row


@router.get("/health")
def health():
    return {"status": "ok", "service": "agrotwin"}


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
            plan = {"raw": rec["plan_json"]}
        plan["status_db"] = rec["status"]
        plan["invalidated_at"] = rec["invalidated_at"]
    return {
        "field": dict(row),
        "soil": dict(soil) if soil else None,
        "latest_plan": plan,
    }


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
        "UPDATE field_crops SET is_active = 0 WHERE field_id = ?",
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
    simulated_plan = run_orchestrated_ledger(
        conn,
        row,
        mock_weather=mock_weather if mock_weather else None,
        farmer_input=farmer_input if farmer_input else None,
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

    return {
        "original_plan": original_plan,
        "simulated_plan": simulated_plan
    }


@router.post("/fields/{field_id}/override")
def agronomist_override(
    field_id: str,
    body: OverrideRequest,
    conn: sqlite3.Connection = Depends(get_conn)
):
    """
    Agronomist overrides the plan.

    NOTE (audit §4): doc 09 describes this route as /agronomist/override.
    The actual path is /fields/{field_id}/override (here). The code is correct;
    doc 09 has a path typo. Route kept as-is to avoid breaking existing tests.
    """
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
