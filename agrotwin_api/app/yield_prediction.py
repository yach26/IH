"""Read-only yield annotation. The Ledger remains the fertilizer authority."""
import json
import logging
import math
import os
from pathlib import Path
import subprocess
import sys
import threading

from . import ledger

LOG = logging.getLogger(__name__)
ML_ROOT = Path(__file__).resolve().parents[1] / "ml"
TIMEOUT_SECONDS = 15
_SLOTS = threading.BoundedSemaphore(2)
LIMITATION = "Yield model trained on synthetic data; directional estimate, not validated farm accuracy."


def abstain(reason, status="ABSTAIN"):
    return dict(status=status, predicted_yield_kg_ha=None, yield_band=None,
                confidence=0.0, model_version=None, reason=reason, caveats=[LIMITATION],
                extrapolation=False)


def _predict(payload):
    # A killed/timed-out worker cannot mutate the ledger or hold up recommendations.
    if not _SLOTS.acquire(blocking=False):
        return abstain("Yield workers are busy; retry shortly.", "UNAVAILABLE")
    try:
        root = Path(os.environ.get("AGROTWIN_ML_ROOT", ML_ROOT))
        completed = subprocess.run(
            [sys.executable, str(root / "worker.py")],
            input=json.dumps(payload, allow_nan=False), capture_output=True,
            text=True, timeout=TIMEOUT_SECONDS, check=True,
        )
        if completed.stderr:
            LOG.warning("Yield worker warning: %s", completed.stderr.strip())
        result = json.loads(completed.stdout)
        if result.get("status") not in ("OK", "ABSTAIN") or not isinstance(result.get("caveats"), list):
            raise ValueError("Invalid yield result")
        value = result.get("predicted_yield_kg_ha")
        if result["status"] == "OK" and (value is None or not math.isfinite(value) or value < 0):
            raise ValueError("Invalid predicted yield")
        return result
    except subprocess.TimeoutExpired:
        LOG.exception("Yield inference timed out")
        return abstain("Yield inference timed out.", "UNAVAILABLE")
    except Exception:
        LOG.exception("Yield inference unavailable")
        return abstain("Model unavailable or inference failed; see server logs.", "UNAVAILABLE")
    finally:
        _SLOTS.release()


def estimate(conn, field_row, rainfall_mm_season=None):
    result = ledger.run_field_ledger(conn, field_row)
    response = {"field_code": field_row["field_code"], "ledger": result}
    # ONE-WAY BOUNDARY: Ledger plan -> yield estimate. No ML output is ever
    # passed back into plan_kg_ha, fertilizer computation, or ledger confidence.
    try:
        response["yield_prediction"] = _estimate(conn, field_row, result, rainfall_mm_season)
    except Exception:
        LOG.exception("Yield input adapter failed")
        response["yield_prediction"] = abstain("Yield input preparation failed.", "UNAVAILABLE")
    return response


def _estimate(conn, field_row, result, rainfall):
    district = conn.execute("SELECT district_name FROM districts WHERE district_id = ?",
                            (field_row["district_id"],)).fetchone()
    if result.get("crop") and result["crop"] not in ("BANANA", "SUGARCANE", "COTTON", "SOYBEAN"):
        return abstain("Crop is outside the four trained pilot crops.")
    if not district or district["district_name"] not in ("Kolhapur", "Jalgaon"):
        return abstain("District is outside the trained Kolhapur/Jalgaon scope.")
    if result["status"] == "ABSTAIN":
        return abstain("Ledger abstained: " + result.get("reason", "missing inputs"))
    if rainfall is None:
        return abstain("Supply rainfall_mm_season explicitly; seven-day rainfall is not a seasonal total.")
    soil_row = conn.execute(
        "SELECT n_kg_ha,p_kg_ha,k_kg_ha,ph,oc_percent FROM soil_tests WHERE field_id=? "
        "ORDER BY test_date DESC,soil_test_id DESC LIMIT 1", (field_row["field_id"],)
    ).fetchone()
    soil = dict(soil_row) if soil_row else {}
    values = list(soil.values()) + [rainfall]
    if len(soil) != 5 or any(v is None or not math.isfinite(float(v)) or float(v) < 0 for v in values):
        return abstain("Complete finite nonnegative soil values and seasonal rainfall are required, including pH and organic carbon.")
    if not 3 <= float(soil["ph"]) <= 11:
        return abstain("Soil pH is outside supported physical bounds (3–11).")
    # PostgreSQL NUMERIC values are Decimal; workers receive JSON-native floats.
    soil = {key: float(value) for key, value in soil.items()}
    soil["district"] = district["district_name"]
    products = ledger.get_products(conn)
    applied = dict(N=0.0, P2O5=0.0, K2O=0.0)
    for key, qty in result["plan_kg_ha"].items():
        if key.startswith("n_supplied"):
            continue
        code = key.removesuffix("_kg_ha")
        if code not in products or not math.isfinite(float(qty)) or float(qty) < 0:
            return abstain("Plan contains an unsupported product or invalid quantity.")
        for nutrient in applied:
            applied[nutrient] += float(qty) * float(products[code][nutrient.lower()]) / 100
    plan = {}
    for nutrient, amount in applied.items():
        required = result["required"].get(nutrient)
        if required is None or not math.isfinite(float(required)) or float(required) <= 0:
            return abstain("Ledger RDF must contain positive finite N/P2O5/K2O requirements.")
        plan[f"applied_{nutrient.lower()}_kg_ha"] = amount
        plan[f"required_{nutrient.lower()}_kg_ha"] = required
    prediction = _predict(dict(soil=soil, crop=result["crop"],
        weather=dict(rainfall_mm_season=rainfall, irrigation_type=field_row["irrigation_type"]),
        fertilizer_plan=plan))
    prediction["inputs"] = {"rainfall_mm_season": rainfall, "rainfall_source": "caller_supplied",
                            "fertilizer_plan": plan}
    prediction["caveats"].extend(result.get("flags", []))
    rain_bounds = (900, 1300) if soil["district"] == "Kolhapur" else (550, 850)
    rain_extrapolation = not rain_bounds[0] <= rainfall <= rain_bounds[1]
    if rain_extrapolation:
        prediction["caveats"].append(f"Seasonal rainfall is outside the synthetic training range for {soil['district']} ({rain_bounds[0]}–{rain_bounds[1]} mm).")
    prediction["caveats"].append("The supplied yield model uses the original soil-P proxy features; the current fertilizer ledger converts elemental P to P2O5. Model features are preserved to match training.")
    nutrient_extrapolation = any(not 0.4 <= applied[n] / result["required"][n] <= 1.3 for n in applied)
    if nutrient_extrapolation:
        prediction["caveats"].append("This plan includes nutrient rates outside the synthetic training range (40–130% of RDF); yield is an extrapolation.")
    prediction["extrapolation"] = rain_extrapolation or nutrient_extrapolation
    if prediction["extrapolation"]:
        LOG.warning(
            "Yield model extrapolation: field=%s rain_extrapolation=%s nutrient_extrapolation=%s",
            field_row["field_code"], rain_extrapolation, nutrient_extrapolation,
        )
    return prediction
