"""
inference.py — the ONLY function the rest of AgroTwin should import from
this ML component.

    from inference import predict_yield

ARCHITECTURE REMINDER: this function receives a fertilizer_plan that the
Nutrient Ledger + Optimizer already computed. It never invents, adjusts,
or second-guesses that plan — it only predicts what yield to expect if
that plan is followed, given the field's soil/weather context. If the
model is asked about a crop it wasn't trained for, or given nonsensical
inputs, it ABSTAINS (predicted_yield_kg_ha=None) rather than guessing,
consistent with the rest of AgroTwin's confidence/abstention design.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd

from features import build_features, CROP_CODES, DISTRICTS, IRRIGATION_TYPES, FEATURE_COLUMNS

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(HERE, "..", "models", "yield_model.joblib")
METADATA_PATH = os.path.join(HERE, "..", "models", "model_metadata.json")

_MODELS = None
_METADATA = None
# v2 models are trained with all features including crop one-hot
_PER_CROP_FEATURES = FEATURE_COLUMNS


def _load():
    global _MODELS, _METADATA
    if _MODELS is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"No trained model found at {MODEL_PATH}. Run "
                f"`python3 train_model.py` first (after "
                f"`python3 generate_training_data.py`)."
            )
        _MODELS = joblib.load(MODEL_PATH)  # dict: {crop_code: XGBRegressor}
        with open(METADATA_PATH) as f:
            _METADATA = json.load(f)
    return _MODELS, _METADATA


def _yield_band(predicted, mean_actual, r2):
    """Bands the prediction relative to this crop's training-set mean —
    NOT relative to the field's own target yield (AgroTwin doesn't have a
    farmer-declared target yield in scope yet; if/when it does, banding
    should switch to be relative to that instead)."""
    if predicted < 0.85 * mean_actual:
        return "low"
    elif predicted > 1.15 * mean_actual:
        return "high"
    return "expected"


def _confidence_from_r2(r2):
    """Confidence is derived from this crop-model's OWN held-out R2 (see
    model_metadata.json), not asserted. A model that explains less of the
    variance on its own test set should report itself as less confident.
    This is intentionally coarse (three bands) rather than a false-precision
    decimal, consistent with the rest of AgroTwin treating confidence as
    a categorical, explained quantity rather than a bare number."""
    if r2 >= 0.75:
        return 0.75
    elif r2 >= 0.5:
        return 0.55
    return 0.35


def predict_yield(
    soil: dict,
    crop: str,
    weather: dict,
    fertilizer_plan: dict,
) -> dict:
    """
    Args:
        soil: {"district": "Kolhapur"|"Jalgaon", "n_kg_ha": float,
               "p_kg_ha": float, "k_kg_ha": float, "ph": float,
               "oc_percent": float}
        crop: one of "BANANA", "SUGARCANE", "COTTON", "SOYBEAN"
        weather: {"rainfall_mm_season": float, "irrigation_type": str}
               irrigation_type must be one of: "Drip", "Furrow + drip",
               "Irrigated", "Rainfed + protective", "Rainfed"
        fertilizer_plan: the ALREADY-COMPUTED plan from AgroTwin's Nutrient
               Ledger/Optimizer — {"applied_n_kg_ha": float,
               "applied_p2o5_kg_ha": float, "applied_k2o_kg_ha": float,
               "required_n_kg_ha": float, "required_p2o5_kg_ha": float,
               "required_k2o_kg_ha": float}
               The required_* values should be copied directly from the
               same fertilizer_recommendations row the Ledger used — this
               function does not look them up itself, to guarantee it is
               always evaluating the exact plan the Ledger produced.

    Returns:
        {
          "predicted_yield_kg_ha": float | None,   # None means ABSTAIN
          "yield_band": "low" | "expected" | "high" | None,
          "confidence": float,                      # 0-1, or 0.0 if ABSTAIN
          "model_version": str,
          "status": "OK" | "ABSTAIN",
          "reason": str | None,                     # populated iff ABSTAIN
          "caveats": [str, ...]                     # always populated, see below
        }
    """
    models, metadata = _load()

    crop = crop.upper()
    if crop not in CROP_CODES:
        return {
            "predicted_yield_kg_ha": None, "yield_band": None, "confidence": 0.0,
            "model_version": metadata["model_version"], "status": "ABSTAIN",
            "reason": f"No trained model exists for crop '{crop}'. "
                      f"This ML component only covers the four pilot crops: {CROP_CODES}.",
            "caveats": [],
        }

    irrigation_type = weather.get("irrigation_type")
    if irrigation_type not in IRRIGATION_TYPES:
        return {
            "predicted_yield_kg_ha": None, "yield_band": None, "confidence": 0.0,
            "model_version": metadata["model_version"], "status": "ABSTAIN",
            "reason": f"irrigation_type '{irrigation_type}' is not one of the "
                      f"types this model was trained on: {IRRIGATION_TYPES}.",
            "caveats": [],
        }

    district = soil.get("district")
    if district not in DISTRICTS:
        return {
            "predicted_yield_kg_ha": None, "yield_band": None, "confidence": 0.0,
            "model_version": metadata["model_version"], "status": "ABSTAIN",
            "reason": f"district '{district}' is outside the current pilot "
                      f"scope {DISTRICTS}. This model must not be used to "
                      f"extrapolate to other regions without new calibration.",
            "caveats": [],
        }

    required = {
        "required_n_kg_ha": fertilizer_plan["required_n_kg_ha"],
        "required_p2o5_kg_ha": fertilizer_plan["required_p2o5_kg_ha"],
        "required_k2o_kg_ha": fertilizer_plan["required_k2o_kg_ha"],
    }
    if any(v is None or v <= 0 for v in required.values()):
        return {
            "predicted_yield_kg_ha": None, "yield_band": None, "confidence": 0.0,
            "model_version": metadata["model_version"], "status": "ABSTAIN",
            "reason": "fertilizer_plan is missing a required_*_kg_ha value "
                      "from the Ledger's own RDF lookup — cannot compute "
                      "sufficiency features without it.",
            "caveats": [],
        }

    row = pd.DataFrame([{
        "district": district,
        "crop_code": crop,
        "irrigation_type": irrigation_type,
        "soil_n_kg_ha": soil["n_kg_ha"],
        "soil_p_kg_ha": soil["p_kg_ha"],
        "soil_k_kg_ha": soil["k_kg_ha"],
        "ph": soil.get("ph", 7.0),
        "oc_percent": soil.get("oc_percent", 0.5),
        "rainfall_mm_season": weather["rainfall_mm_season"],
        "applied_n_kg_ha": fertilizer_plan["applied_n_kg_ha"],
        "applied_p2o5_kg_ha": fertilizer_plan["applied_p2o5_kg_ha"],
        "applied_k2o_kg_ha": fertilizer_plan["applied_k2o_kg_ha"],
        **required,
    }])

    X = build_features(row)[_PER_CROP_FEATURES]
    model = models[crop]
    predicted = float(model.predict(X)[0])

    crop_metrics = metadata["per_crop_metrics"][crop]
    band = _yield_band(predicted, crop_metrics["mean_actual_yield_kg_ha"], crop_metrics["r2"])
    confidence = _confidence_from_r2(crop_metrics["r2"])

    caveats = [
        "This model was trained on SYNTHETIC data calibrated to published "
        "district/state yield averages, not on real paired farm-level "
        "fertilizer-yield records (none were openly available for this "
        "pilot — see README.md). Treat this as a directional estimate, "
        "not a guaranteed outcome.",
    ]
    if district == "Jalgaon" and crop in ("BANANA", "COTTON"):
        caveats.append(
            "Soil-nutrient ranges for Jalgaon in the training data were "
            "extrapolated, not sourced from a Jalgaon-specific Soil Health "
            "Card sample (only Kolhapur-Ajara published samples were "
            "available in the Phase-1 data pack)."
        )

    return {
        "predicted_yield_kg_ha": round(predicted, 1),
        "yield_band": band,
        "confidence": confidence,
        "model_version": metadata["model_version"],
        "status": "OK",
        "reason": None,
        "caveats": caveats,
        "extrapolation": False,
    }


if __name__ == "__main__":
    # Quick manual smoke test using values in the same ballpark as the
    # Phase-1 synthetic record SYN-003 (Sugarcane, Kolhapur, pre-seasonal).
    example = predict_yield(
        soil={"district": "Kolhapur", "n_kg_ha": 210, "p_kg_ha": 35,
              "k_kg_ha": 310, "ph": 7.9, "oc_percent": 0.62},
        crop="SUGARCANE",
        weather={"rainfall_mm_season": 1100, "irrigation_type": "Furrow + drip"},
        fertilizer_plan={
            "applied_n_kg_ha": 340, "applied_p2o5_kg_ha": 170, "applied_k2o_kg_ha": 170,
            "required_n_kg_ha": 340, "required_p2o5_kg_ha": 170, "required_k2o_kg_ha": 170,
        },
    )
    print(json.dumps(example, indent=2))

    # ABSTAIN example: unknown crop
    print(json.dumps(predict_yield(
        soil={"district": "Kolhapur", "n_kg_ha": 200, "p_kg_ha": 30, "k_kg_ha": 300},
        crop="RICE",
        weather={"rainfall_mm_season": 1000, "irrigation_type": "Irrigated"},
        fertilizer_plan={"applied_n_kg_ha": 100, "applied_p2o5_kg_ha": 50, "applied_k2o_kg_ha": 50,
                          "required_n_kg_ha": 100, "required_p2o5_kg_ha": 50, "required_k2o_kg_ha": 50},
    ), indent=2))
