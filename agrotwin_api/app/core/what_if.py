"""
What-If simulator (doc 13) — backend only.

Re-runs the ledger / optimizer with modified inputs and returns the
baseline plan beside the simulated plan. Never persists the simulation
as the active recommendation. Never fabricates yield percentages.
"""

from __future__ import annotations

import sqlite3
from copy import deepcopy
from typing import Any

from ..pipeline import RecommendationPipeline
from .event_bus import InMemoryEventBus
from .optimizer import HeuristicOptimizer, estimate_cost
from .rules import RuleEngine


def run_what_if(
    conn: sqlite3.Connection,
    field_row: sqlite3.Row,
    *,
    fertilizer_delta_pct: float | None = None,
    rainfall_mm: float | None = None,
    substitute: dict[str, str] | None = None,
    delay_days: int | None = None,
    mock_weather: dict | None = None,
) -> dict[str, Any]:
    """
    fertilizer_delta_pct: scale the *plan quantities* after the ledger
        (e.g. -20 means apply 20% less of each product). Re-validates.
    rainfall_mm: inject a synthetic 7-day rainfall total (and alert if
        it crosses the region threshold).
    substitute: {"from": "DAP", "to": "SSP"} using FCO compositions from
        fertilizer_products — remaining N topped up with Urea.
    delay_days: shift the application window label only (no new kg/ha).
    """
    dry = mock_weather or {
        "rainfall_probability": 10,
        "rainfall_mm_next_7d": 2.0,
        "heavy_rain_alert": False,
        "source": "what_if_baseline",
    }
    if rainfall_mm is not None:
        from .region_config import load_region_config

        cfg = load_region_config()["rules"]["weather_windows"]
        sim_weather = {
            "rainfall_probability": 80 if rainfall_mm >= cfg["rainfall_mm_next_7d"] else 20,
            "rainfall_mm_next_7d": float(rainfall_mm),
            "heavy_rain_alert": float(rainfall_mm) >= float(cfg["rainfall_mm_next_7d"]),
            "source": "what_if",
        }
    else:
        sim_weather = dry

    bus = InMemoryEventBus()
    pipe = RecommendationPipeline(bus=bus, optimizer=HeuristicOptimizer(), rule_engine=RuleEngine())
    baseline = pipe.run(
        conn, field_row, mock_weather=dry, emit_events=False, persist=False
    )
    simulated = pipe.run(
        conn, field_row, mock_weather=sim_weather, emit_events=False, persist=False
    )

    notes: list[str] = []
    how = deepcopy(simulated.get("how_much") or {})

    if fertilizer_delta_pct is not None:
        factor = 1.0 + (float(fertilizer_delta_pct) / 100.0)
        if factor < 0:
            factor = 0.0
        how = {k: round(float(v) * factor, 1) for k, v in how.items()}
        simulated["how_much"] = how
        simulated["what"] = " + ".join(
            k.replace("_kg_ha", "") for k, v in how.items() if float(v or 0) > 0
        ) or simulated.get("what")
        notes.append(
            f"SIMULATED fertilizer_delta_pct={fertilizer_delta_pct}. "
            "Quantities are scaled from the ledger plan; not a new RDF."
        )

    if substitute:
        src = (substitute.get("from") or "").upper()
        dst = (substitute.get("to") or "").upper()
        products = simulated.get("ledger") and None
        from .. import ledger as ledger_module

        products = ledger_module.get_products(conn)
        how = _substitute_product(how or deepcopy(baseline.get("how_much") or {}), src, dst, products)
        simulated["how_much"] = how
        notes.append(
            f"SIMULATED substitution {src}→{dst} using FCO % from fertilizer_products."
        )

    if delay_days:
        when = simulated.get("when_detail") or {}
        notes.append(f"SIMULATED delay_days={delay_days} (window shift only).")
        simulated["when"] = f"{when.get('label', simulated.get('when'))} [+{delay_days} days simulated]"

    cost, currency, cite = estimate_cost(simulated.get("how_much") or {})
    simulated_cost = {
        "cost_estimate": cost,
        "cost_currency": currency,
        "cost_citation": cite,
    }

    return {
        "status": "SIMULATION",
        "baseline": _slim(baseline),
        "simulated": {**_slim(simulated), **simulated_cost},
        "delta_how_much": _delta(baseline.get("how_much"), simulated.get("how_much")),
        "notes": notes
        + [
            "This is a simulation. It was not saved as the active plan.",
            "No yield % is reported — the data pack has no calibrated yield model.",
        ],
        "numeric_source": "ledger.convert_gap_to_products (scaled/substituted in what-if only)",
    }


def _slim(proof: dict) -> dict:
    return {
        "status": proof.get("status"),
        "what": proof.get("what"),
        "how_much": proof.get("how_much"),
        "when": proof.get("when"),
        "confidence": proof.get("confidence"),
        "flags": proof.get("flags"),
        "validation": proof.get("validation"),
    }


def _delta(a: dict | None, b: dict | None) -> dict[str, float]:
    keys = set((a or {}) | (b or {}))
    out = {}
    for k in keys:
        out[k] = round(float((b or {}).get(k) or 0) - float((a or {}).get(k) or 0), 1)
    return out


def _substitute_product(
    how: dict[str, float], src: str, dst: str, products: dict
) -> dict[str, float]:
    """
    Replace src kg with dst kg that supplies the same P2O5 (or N/K),
    then top up remaining N with Urea. All % from fertilizer_products.
    """
    src_key = f"{src}_kg_ha"
    dst_key = f"{dst}_kg_ha"
    src_kg = float(how.get(src_key) or 0)
    if src_kg <= 0:
        return how
    src_comp = products.get(src) or products.get(src.upper())
    dst_comp = products.get(dst) or products.get(dst.upper())
    if not src_comp or not dst_comp:
        return how

    p_need = src_kg * float(src_comp.get("p2o5") or 0) / 100.0
    n_from_src = src_kg * float(src_comp.get("n") or 0) / 100.0
    k_from_src = src_kg * float(src_comp.get("k2o") or 0) / 100.0

    out = dict(how)
    out[src_key] = 0.0
    dst_p = float(dst_comp.get("p2o5") or 0) / 100.0
    dst_n = float(dst_comp.get("n") or 0) / 100.0
    dst_k = float(dst_comp.get("k2o") or 0) / 100.0
    if dst_p > 0 and p_need > 0:
        dst_kg = round(p_need / dst_p, 1)
    elif dst_k > 0 and k_from_src > 0:
        dst_kg = round(k_from_src / dst_k, 1)
    elif dst_n > 0 and n_from_src > 0:
        dst_kg = round(n_from_src / dst_n, 1)
    else:
        return how
    out[dst_key] = round(float(out.get(dst_key) or 0) + dst_kg, 1)

    n_from_dst = dst_kg * dst_n
    n_short = max(0.0, round(n_from_src - n_from_dst, 1))
    urea = products.get("UREA") or {"n": 46.0}
    if n_short > 0:
        extra_urea = round(n_short / (float(urea["n"]) / 100.0), 1)
        out["UREA_kg_ha"] = round(float(out.get("UREA_kg_ha") or 0) + extra_urea, 1)
    return {k: v for k, v in out.items() if float(v or 0) != 0 or k in how}
