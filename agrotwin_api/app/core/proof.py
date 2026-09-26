"""
Proof-carrying recommendation assembler (doc 01 §4, doc 05 output contract).

Answers WHAT / HOW MUCH / WHEN / WHY / BASED ON WHAT / HOW SURE ARE WE.
HOW MUCH is copied from ledger/optimizer quantities — never generated here.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

PRODUCT_ORDER = ("DAP", "UREA", "MOP")


def _product_qty(plan_kg_ha: dict[str, Any] | None) -> dict[str, float]:
    src = plan_kg_ha or {}
    out: dict[str, float] = {}
    for key, val in src.items():
        if key.endswith("_kg_ha") and not key.startswith("n_supplied") and float(val or 0) != 0:
            out[key] = float(val)
    return out


def _what(how_much: dict[str, float]) -> str:
    names = []
    seen = set()
    for code in PRODUCT_ORDER:
        key = f"{code}_kg_ha"
        if key in how_much:
            names.append(code.title() if code != "DAP" and code != "MOP" else code)
            seen.add(key)
    for key in how_much:
        if key not in seen:
            names.append(key.replace("_kg_ha", ""))
    if not names:
        return "No fertilizer application required"
    return " + ".join(names)


def _when(weather: dict[str, Any], revised: bool) -> dict[str, Any]:
    today = date.today()
    if weather.get("heavy_rain_alert"):
        start = today + timedelta(days=7)
        end = start + timedelta(days=3)
        return {
            "code": "DEFER_RAIN",
            "label": (
                f"{start.isoformat()} – {end.isoformat()} "
                "(deferred until after the heavy-rain window)"
            ),
            "window_start": start.isoformat(),
            "window_end": end.isoformat(),
            "revised": revised,
        }
    start = today + timedelta(days=1)
    end = today + timedelta(days=3)
    return {
        "code": "APPLY_NEXT_DRY_DAYS",
        "label": f"{start.isoformat()} – {end.isoformat()} (next dry application window)",
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "revised": revised,
    }


def assemble_proof(
    *,
    status: str,
    ledger: dict[str, Any],
    twin: dict[str, Any],
    optimizer_plan: dict[str, Any] | None,
    validation: dict[str, Any],
    evidence: list[dict],
    mode: str,
    agents_run: list[str],
    audit: list[dict],
    reason: str | None = None,
    required_actions: list[str] | None = None,
) -> dict[str, Any]:
    how_much = _product_qty(
        (optimizer_plan or {}).get("plan_kg_ha") or ledger.get("plan_kg_ha")
    )
    weather = twin.get("weather") or {}
    soil = twin.get("soil") or {}
    crop = twin.get("crop") or {}
    revised = mode == "partial_replan" or status == "PLAN_REVISED"
    when = _when(weather, revised=revised)

    dq = twin.get("data_quality") or {}
    flags = list(twin.get("flags") or ledger.get("flags") or [])

    proof = {
        "status": status,
        "what": None if status == "ABSTAIN" else _what(how_much),
        "how_much": None if status == "ABSTAIN" else how_much,
        "when": None if status == "ABSTAIN" else when["label"],
        "when_detail": None if status == "ABSTAIN" else when,
        "why": None
        if status == "ABSTAIN"
        else {
            "soil": (
                f"Soil N={soil.get('n_kg_ha')}, P={soil.get('p_kg_ha')}, "
                f"K={soil.get('k_kg_ha')} kg/ha; pH={soil.get('ph')}"
            ),
            "crop": (
                f"{crop.get('crop_name') or crop.get('crop_code')}, "
                f"stage={crop.get('current_stage')}, "
                f"rec_type={crop.get('recommendation_type')}"
            ),
            "weather": weather.get("alert_details")
            or (
                "Heavy rain alert — application deferred"
                if weather.get("heavy_rain_alert")
                else "Suitable application window identified (no heavy-rain alert)"
            ),
            "history": f"{len(twin.get('history') or [])} prior recommendation(s) on file",
            "gap": ledger.get("gap"),
            "required": ledger.get("required"),
        },
        "based_on": {
            "farm_data": [
                f"soil_test_id: {soil.get('soil_test_id')}",
                f"crop_stage: {crop.get('current_stage')}",
                f"field_id: {twin.get('field_id')}",
            ],
            "evidence": evidence,
            "citation": ledger.get("citation"),
            "optimizer": (optimizer_plan or {}).get("optimizer_id"),
            "cost_estimate": (optimizer_plan or {}).get("cost_estimate"),
            "cost_currency": (optimizer_plan or {}).get("cost_currency"),
            "cost_citation": (optimizer_plan or {}).get("cost_citation"),
        },
        "confidence": twin.get("confidence") or ledger.get("confidence") or "LOW",
        "flags": flags,
        "data_quality": {
            "soil_report_current": bool(dq.get("has_soil_test") and dq.get("soil_is_fresh")),
            "weather_available": bool(dq.get("has_weather") and dq.get("weather_ok")),
            "crop_stage_known": bool(dq.get("has_crop") and dq.get("stage_in_calendar")),
            "micronutrients_complete": soil.get("micronutrients") not in (None, "", "{}"),
            "has_soil_test": bool(dq.get("has_soil_test")),
            "soil_is_fresh": bool(dq.get("soil_is_fresh")),
            "has_crop": bool(dq.get("has_crop")),
            "has_rec_type": bool(dq.get("has_rec_type")),
        },
        "validation": {
            "is_valid": validation.get("is_valid", False),
            "warnings": validation.get("warnings", []),
            "blocking_issues": validation.get("blocking_issues", []),
        },
        "mode": mode,
        "agents_run": agents_run,
        "pipeline_audit": audit,
        "field_id": ledger.get("field_id") or twin.get("field_id"),
        "field_code": ledger.get("field_code") or twin.get("field_code"),
        "reason": reason,
        "required_actions": required_actions or [],
        "numeric_source": "ledger.convert_gap_to_products (HeuristicOptimizer)",
    }
    # Keep raw ledger + optimizer for persistence / debugging (not farmer-facing)
    proof["ledger"] = ledger
    proof["optimizer_result"] = optimizer_plan
    proof["soil_context"] = soil or None
    proof["crop_context"] = crop or None
    proof["weather_context"] = {
        "heavy_rain_alert": weather.get("heavy_rain_alert", False),
        "alert_details": weather.get("alert_details", ""),
        "rainfall_mm_next_7d": (weather.get("snapshot") or {}).get("rainfall_mm_next_7d")
        if isinstance(weather.get("snapshot"), dict)
        else weather.get("rainfall_mm_next_7d"),
        "rainfall_probability": (weather.get("snapshot") or {}).get("rainfall_probability")
        if isinstance(weather.get("snapshot"), dict)
        else weather.get("rainfall_probability"),
        "source": weather.get("source") or "open-meteo",
        "flags": weather.get("flags", []),
        "warning": weather.get("warning"),
    }
    return proof
