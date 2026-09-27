"""
Kolhapur Soil Context Helper
=============================

Provides real district-level soil nutrient statistics from official
Soil Health Card dashboards. Used by the Knowledge Agent and Report Agent
to ground recommendations in real regional data.
"""

import csv
import logging
import os
from pathlib import Path

LOG = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "real_kolhapur" / "nutrient_dashboard"


def get_kolhapur_soil_context(cycle: str = "2024-25") -> dict:
    """
    Get Kolhapur district soil nutrient statistics for a given SHC cycle.

    Args:
        cycle: SHC cycle year (e.g., "2023-24", "2024-25", "2025-26")

    Returns:
        dict with:
            - cycle: str
            - total_samples: int
            - nitrogen: {"low_pct": float, "medium_pct": float, "high_pct": float}
            - phosphorus: {"low_pct": float, "medium_pct": float, "high_pct": float}
            - potassium: {"low_pct": float, "medium_pct": float, "high_pct": float}
            - organic_carbon: {"low_pct": float, "medium_pct": float, "high_pct": float}
            - ph: {"acidic_pct": float, "neutral_pct": float, "alkaline_pct": float}
            - ec: {"non_saline_pct": float, "saline_pct": float}
            - micronutrients: {"s_deficient_pct": float, "zn_deficient_pct": float, ...}
    """
    filepath = DATA_DIR / f"{cycle}.csv"
    if not filepath.exists():
        LOG.warning("Kolhapur nutrient dashboard not found for cycle %s", cycle)
        return _empty_context(cycle)

    try:
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except Exception as e:
        LOG.error("Failed to read Kolhapur nutrient dashboard: %s", e)
        return _empty_context(cycle)

    if not rows:
        return _empty_context(cycle)

    # Aggregate across all blocks
    total = len(rows)
    totals = {
        "n_low": 0, "n_medium": 0, "n_high": 0,
        "p_low": 0, "p_medium": 0, "p_high": 0,
        "k_low": 0, "k_medium": 0, "k_high": 0,
        "oc_low": 0, "oc_medium": 0, "oc_high": 0,
        "ph_acidic": 0, "ph_neutral": 0, "ph_alkaline": 0,
        "ec_non_saline": 0, "ec_saline": 0,
        "s_deficient": 0, "s_sufficient": 0,
        "zn_deficient": 0, "zn_sufficient": 0,
        "fe_deficient": 0, "fe_sufficient": 0,
        "cu_deficient": 0, "cu_sufficient": 0,
        "b_deficient": 0, "b_sufficient": 0,
        "mn_deficient": 0, "mn_sufficient": 0,
    }

    for row in rows:
        for key in totals:
            col_map = {
                "n_low": "n_Low", "n_medium": "n_Medium", "n_high": "n_High",
                "p_low": "p_Low", "p_medium": "p_Medium", "p_high": "p_High",
                "k_low": "k_Low", "k_medium": "k_Medium", "k_high": "k_High",
                "oc_low": "OC_Low", "oc_medium": "OC_Medium", "oc_high": "OC_High",
                "ph_acidic": "pH_Acidic", "ph_neutral": "pH_Neutral", "ph_alkaline": "pH_Alkaline",
                "ec_non_saline": "EC_NonSaline", "ec_saline": "EC_Saline",
                "s_deficient": "S_Deficient", "s_sufficient": "S_Sufficient",
                "zn_deficient": "Zn_Deficient", "zn_sufficient": "Zn_Sufficient",
                "fe_deficient": "Fe_Deficient", "fe_sufficient": "Fe_Sufficient",
                "cu_deficient": "Cu_Deficient", "cu_sufficient": "Cu_Sufficient",
                "b_deficient": "B_Deficient", "b_sufficient": "B_Sufficient",
                "mn_deficient": "Mn_Deficient", "mn_sufficient": "Mn_Sufficient",
            }
            col = col_map.get(key, key)
            try:
                totals[key] += int(row.get(col, 0) or 0)
            except (ValueError, TypeError):
                pass

    def pct(val, total):
        return round(100 * val / total, 1) if total > 0 else 0.0

    n_total = totals["n_low"] + totals["n_medium"] + totals["n_high"]
    p_total = totals["p_low"] + totals["p_medium"] + totals["p_high"]
    k_total = totals["k_low"] + totals["k_medium"] + totals["k_high"]
    oc_total = totals["oc_low"] + totals["oc_medium"] + totals["oc_high"]
    ph_total = totals["ph_acidic"] + totals["ph_neutral"] + totals["ph_alkaline"]
    ec_total = totals["ec_non_saline"] + totals["ec_saline"]

    return {
        "cycle": cycle,
        "total_samples": n_total,
        "nitrogen": {
            "low_pct": pct(totals["n_low"], n_total),
            "medium_pct": pct(totals["n_medium"], n_total),
            "high_pct": pct(totals["n_high"], n_total),
        },
        "phosphorus": {
            "low_pct": pct(totals["p_low"], p_total),
            "medium_pct": pct(totals["p_medium"], p_total),
            "high_pct": pct(totals["p_high"], p_total),
        },
        "potassium": {
            "low_pct": pct(totals["k_low"], k_total),
            "medium_pct": pct(totals["k_medium"], k_total),
            "high_pct": pct(totals["k_high"], k_total),
        },
        "organic_carbon": {
            "low_pct": pct(totals["oc_low"], oc_total),
            "medium_pct": pct(totals["oc_medium"], oc_total),
            "high_pct": pct(totals["oc_high"], oc_total),
        },
        "ph": {
            "acidic_pct": pct(totals["ph_acidic"], ph_total),
            "neutral_pct": pct(totals["ph_neutral"], ph_total),
            "alkaline_pct": pct(totals["ph_alkaline"], ph_total),
        },
        "ec": {
            "non_saline_pct": pct(totals["ec_non_saline"], ec_total),
            "saline_pct": pct(totals["ec_saline"], ec_total),
        },
        "micronutrients": {
            "s_deficient_pct": pct(totals["s_deficient"], totals["s_deficient"] + totals["s_sufficient"]),
            "zn_deficient_pct": pct(totals["zn_deficient"], totals["zn_deficient"] + totals["zn_sufficient"]),
            "fe_deficient_pct": pct(totals["fe_deficient"], totals["fe_deficient"] + totals["fe_sufficient"]),
            "cu_deficient_pct": pct(totals["cu_deficient"], totals["cu_deficient"] + totals["cu_sufficient"]),
            "b_deficient_pct": pct(totals["b_deficient"], totals["b_deficient"] + totals["b_sufficient"]),
            "mn_deficient_pct": pct(totals["mn_deficient"], totals["mn_deficient"] + totals["mn_sufficient"]),
        },
    }


def _empty_context(cycle: str) -> dict:
    return {
        "cycle": cycle,
        "total_samples": 0,
        "nitrogen": {"low_pct": 0, "medium_pct": 0, "high_pct": 0},
        "phosphorus": {"low_pct": 0, "medium_pct": 0, "high_pct": 0},
        "potassium": {"low_pct": 0, "medium_pct": 0, "high_pct": 0},
        "organic_carbon": {"low_pct": 0, "medium_pct": 0, "high_pct": 0},
        "ph": {"acidic_pct": 0, "neutral_pct": 0, "alkaline_pct": 0},
        "ec": {"non_saline_pct": 0, "saline_pct": 0},
        "micronutrients": {
            "s_deficient_pct": 0, "zn_deficient_pct": 0, "fe_deficient_pct": 0,
            "cu_deficient_pct": 0, "b_deficient_pct": 0, "mn_deficient_pct": 0,
        },
    }


def format_context_for_display(context: dict) -> str:
    """Format the soil context as a human-readable string for the UI."""
    if context["total_samples"] == 0:
        return "No regional soil data available."

    lines = [
        f"Kolhapur District Soil Health (SHC {context['cycle']}):",
        f"  Total samples: {context['total_samples']:,}",
        f"  Nitrogen: {context['nitrogen']['low_pct']}% low, {context['nitrogen']['medium_pct']}% medium, {context['nitrogen']['high_pct']}% high",
        f"  Phosphorus: {context['phosphorus']['low_pct']}% low, {context['phosphorus']['medium_pct']}% medium, {context['phosphorus']['high_pct']}% high",
        f"  Potassium: {context['potassium']['low_pct']}% low, {context['potassium']['medium_pct']}% medium, {context['potassium']['high_pct']}% high",
        f"  Organic Carbon: {context['organic_carbon']['low_pct']}% low, {context['organic_carbon']['medium_pct']}% medium, {context['organic_carbon']['high_pct']}% high",
        f"  pH: {context['ph']['acidic_pct']}% acidic, {context['ph']['neutral_pct']}% neutral, {context['ph']['alkaline_pct']}% alkaline",
    ]
    return "\n".join(lines)
