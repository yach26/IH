"""
features.py — single source of truth for feature engineering.

Used by BOTH train_model.py and inference.py so that training-time and
inference-time features can never silently drift apart (a common source
of production ML bugs). Every feature here is either a raw input or a
transparent, explainable derived quantity — no black-box embeddings.
"""

import pandas as pd

CROP_CODES = ["BANANA", "SUGARCANE", "COTTON", "SOYBEAN"]
DISTRICTS = ["Kolhapur", "Jalgaon"]
IRRIGATION_TYPES = ["Drip", "Furrow + drip", "Irrigated",
                     "Rainfed + protective", "Rainfed"]

FEATURE_COLUMNS = [
    # raw soil
    "soil_n_kg_ha", "soil_p_kg_ha", "soil_k_kg_ha", "ph", "oc_percent",
    # raw weather
    "rainfall_mm_season",
    # the fertilizer plan actually being evaluated (from the Ledger/Optimizer)
    "applied_n_kg_ha", "applied_p2o5_kg_ha", "applied_k2o_kg_ha",
    # engineered: how the applied plan compares to the MPKV/ICAR requirement
    "n_pct_of_rdf", "p2o5_pct_of_rdf", "k2o_pct_of_rdf",
    # engineered: crude total-nutrient sufficiency proxies (soil + plan vs RDF)
    "n_sufficiency_proxy", "p2o5_sufficiency_proxy", "k2o_sufficiency_proxy",
    # one-hot categoricals
    *[f"crop__{c}" for c in CROP_CODES],
    *[f"district__{d}" for d in DISTRICTS],
    *[f"irrigation__{i}" for i in IRRIGATION_TYPES],
]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """df must have columns: district, crop_code, irrigation_type,
    soil_n_kg_ha, soil_p_kg_ha, soil_k_kg_ha, ph, oc_percent,
    rainfall_mm_season, applied_n_kg_ha, applied_p2o5_kg_ha,
    applied_k2o_kg_ha, required_n_kg_ha, required_p2o5_kg_ha,
    required_k2o_kg_ha (the last three come from the Ledger's own
    fertilizer_recommendations lookup, NOT invented here)."""
    out = df.copy()

    out["n_pct_of_rdf"] = (out["applied_n_kg_ha"] / out["required_n_kg_ha"].replace(0, pd.NA)).fillna(0) * 100
    out["p2o5_pct_of_rdf"] = (out["applied_p2o5_kg_ha"] / out["required_p2o5_kg_ha"].replace(0, pd.NA)).fillna(0) * 100
    out["k2o_pct_of_rdf"] = (out["applied_k2o_kg_ha"] / out["required_k2o_kg_ha"].replace(0, pd.NA)).fillna(0) * 100

    # Simple, explainable sufficiency proxy: (soil + applied) / required,
    # capped at 2.0 so extreme over-application doesn't dominate the scale.
    out["n_sufficiency_proxy"] = ((out["soil_n_kg_ha"] + out["applied_n_kg_ha"])
                                   / out["required_n_kg_ha"].replace(0, pd.NA)).fillna(0).clip(upper=2.0)
    out["p2o5_sufficiency_proxy"] = ((out["soil_p_kg_ha"] + out["applied_p2o5_kg_ha"])
                                      / out["required_p2o5_kg_ha"].replace(0, pd.NA)).fillna(0).clip(upper=2.0)
    out["k2o_sufficiency_proxy"] = ((out["soil_k_kg_ha"] + out["applied_k2o_kg_ha"])
                                     / out["required_k2o_kg_ha"].replace(0, pd.NA)).fillna(0).clip(upper=2.0)

    for c in CROP_CODES:
        out[f"crop__{c}"] = (out["crop_code"] == c).astype(int)
    for d in DISTRICTS:
        out[f"district__{d}"] = (out["district"] == d).astype(int)
    for i in IRRIGATION_TYPES:
        out[f"irrigation__{i}"] = (out["irrigation_type"] == i).astype(int)

    missing = [c for c in FEATURE_COLUMNS if c not in out.columns]
    if missing:
        raise ValueError(f"build_features did not produce expected columns: {missing}")

    return out[FEATURE_COLUMNS]
