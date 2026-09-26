"""
Region-agnostic default configuration for cost model and agronomic rules.

Every numeric threshold carries a citation. Magic numbers without a source
are labelled ENGINEERING_DEFAULT (see 04_remaining_gaps.md).
"""

from copy import deepcopy

# Default region pack used when a field has no overlay.
# Kolhapur / Jalgaon overlays can replace keys later without changing agents.
DEFAULT_REGION_CONFIG: dict = {
    "region_id": "default",
    "cost_model": {
        "currency": "INR",
        "unit": "per_kg",
        # Gap #8: no sourced fertilizer price table exists in the data pack.
        "citation": (
            "ENGINEERING_DEFAULT market prices pending Gap #8 "
            "(04_remaining_gaps.md — no fertilizer price table sourced). "
            "Used only for a cost *estimate* on the proof object; never as "
            "the source of kg/ha quantities."
        ),
        "prices_inr_per_kg": {
            "UREA": 6.0,
            "DAP": 27.0,
            "MOP": 20.0,
            "SSP": 8.0,
            "SOP": 45.0,
            "AMMONIUM_SULPHATE": 12.0,
            "19_19_19": 30.0,
            "12_32_16": 28.0,
            "10_26_26": 29.0,
        },
    },
    "rules": {
        "max_rates": {
            "rule_id": "MAX_RATES_RDF",
            # Hard cap: product mix must not supply more than RDF required +
            # a small rounding tolerance. RDF comes from fertilizer_recommendations
            # (mpkv_icar_rdf.md) — never invented here.
            "citation": (
                "MPKV/ICAR RDF row in fertilizer_recommendations "
                "(source_citation on the twin). Product conversion must not "
                "exceed required N/P2O5/K2O by more than rounding_tol_kg_ha."
            ),
            "rounding_tol_kg_ha": 2.0,
        },
        "compatibility": {
            "rule_id": "PRODUCT_COMPATIBILITY",
            "citation": (
                "FCO fertilizer spec / conversion_notes.md common practice: "
                "do not tank-mix urea with single super phosphate (SSP) in "
                "the same application (ammonia loss / incompatibility)."
            ),
            "incompatible_pairs": [["UREA", "SSP"]],
        },
        "weather_windows": {
            "rule_id": "WEATHER_WINDOW_HEAVY_RAIN",
            "citation": (
                "ENGINEERING_DEFAULT — 04_Weather/weather_sources.md + "
                "weather_agent.py. Soluble N leaches under heavy rain. "
                "Trigger: rainfall_probability >= 70% AND rainfall_mm_next_7d >= 50 mm."
            ),
            "no_application_if_heavy_rain": True,
            "rainfall_probability_pct": 70,
            "rainfall_mm_next_7d": 50.0,
        },
        "soil_limits": {
            "rule_id": "SOIL_PH_WINDOW",
            "citation": (
                "ENGINEERING_DEFAULT agronomic pH window used by Validation Agent "
                "(typical 5.5–8.0 for NPK availability). Not a statutory FCO limit."
            ),
            "ph_min": 5.5,
            "ph_max": 8.0,
        },
        "data_freshness": {
            "rule_id": "SOIL_DATA_FRESHNESS",
            "citation": (
                "ENGINEERING_DEFAULT STALE_SOIL_DAYS=180 pending MoA/NHM "
                "re-testing frequency guidance (Gap #2 in 04_remaining_gaps.md)."
            ),
            "soil_max_age_days": 180,
            "stale_action": "lower_confidence",  # not hard-abstain
        },
        "ec_limits": {
            "rule_id": "SOIL_EC_WINDOW",
            "citation": (
                "ENGINEERING_DEFAULT: EC > 4 dS/m is commonly treated as saline "
                "for field crops (FAO irrigation water/soil salinity guidance, "
                "used here as a warning only)."
            ),
            "ec_ds_m_max": 4.0,
        },
    },
}


def load_region_config(region_id: str | None = None) -> dict:
    """
    Return a deep copy of the config for `region_id`.

    Overlays can later live in regions/<id>/config — for MVP every region
    shares the default pack so agents stay region-agnostic.
    """
    cfg = deepcopy(DEFAULT_REGION_CONFIG)
    if region_id:
        cfg["region_id"] = str(region_id)
    return cfg
