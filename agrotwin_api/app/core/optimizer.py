"""
Optimizer interface (doc 07).

Default implementation is the existing DAP→Urea→MOP heuristic in
`ledger.convert_gap_to_products`. The rest of the system talks only to
this Protocol so a later MIP solver can be swapped in without touching
the pipeline.

CRITICAL: this module must never invent nutrient gaps or product
compositions. Gaps come from the ledger; compositions from fertilizer_products.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from .. import ledger as ledger_module
from .region_config import load_region_config


@dataclass
class OptimizerPlan:
    """Quantities + cost estimate. Quantities are ledger-derived."""

    plan_kg_ha: dict[str, float]
    total_kg_ha: float
    cost_estimate: float | None
    cost_currency: str
    cost_citation: str
    optimizer_id: str
    message: str
    constraint_violations: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def product_quantities(self) -> dict[str, float]:
        """kg/ha keys only (excludes diagnostic fields like n_supplied_by_dap)."""
        return {
            k: v
            for k, v in self.plan_kg_ha.items()
            if k.endswith("_kg_ha") and not k.startswith("n_supplied")
        }


class Optimizer(Protocol):
    def optimize(self, twin: dict[str, Any], candidates: list[dict] | None = None) -> OptimizerPlan:
        """
        Returns a Plan with quantities, cost estimate, and any constraint notes.
        Must never invent numbers outside the supplied requirements and
        product compositions.
        """
        ...


def estimate_cost(plan_kg_ha: dict[str, float], region_id: str | None = None) -> tuple[float, str, str]:
    cfg = load_region_config(region_id)
    prices = cfg["cost_model"]["prices_inr_per_kg"]
    citation = cfg["cost_model"]["citation"]
    currency = cfg["cost_model"]["currency"]
    total = 0.0
    for key, qty in plan_kg_ha.items():
        if not key.endswith("_kg_ha") or key.startswith("n_supplied"):
            continue
        product = key.replace("_kg_ha", "")
        price = prices.get(product)
        if price is None:
            continue
        total += float(qty) * float(price)
    return round(total, 2), currency, citation


class HeuristicOptimizer:
    """
    Default optimizer: DAP for P₂O₅, remaining N from Urea, MOP for K₂O.

    Delegates arithmetic to `ledger.convert_gap_to_products` so the
    numeric source of truth does not fork.
    """

    optimizer_id = "heuristic_dap_urea_mop"

    def optimize(self, twin: dict[str, Any], candidates: list[dict] | None = None) -> OptimizerPlan:
        gap = (twin.get("current_plan") or {}).get("gap") or twin.get("gap") or {}
        gap_n = float(gap.get("N") or 0)
        gap_p = float(gap.get("P2O5") or 0)
        gap_k = float(gap.get("K2O") or 0)

        products = twin.get("products")
        if not products:
            raise ValueError(
                "HeuristicOptimizer requires twin['products'] from fertilizer_products "
                "(FCO %). Refusing to invent compositions."
            )

        plan = ledger_module.convert_gap_to_products(gap_n, gap_p, gap_k, products)
        qty = {
            k: float(v)
            for k, v in plan.items()
            if k.endswith("_kg_ha")
        }
        total = round(
            sum(v for k, v in qty.items() if not k.startswith("n_supplied")),
            1,
        )
        cost, currency, citation = estimate_cost(qty, twin.get("region_id"))
        return OptimizerPlan(
            plan_kg_ha=plan,
            total_kg_ha=total,
            cost_estimate=cost,
            cost_currency=currency,
            cost_citation=citation,
            optimizer_id=self.optimizer_id,
            message=(
                "DAP→Urea→MOP heuristic from conversion_notes.md "
                "(ledger.convert_gap_to_products). Not a multi-objective solver."
            ),
            meta={"gap": {"N": gap_n, "P2O5": gap_p, "K2O": gap_k}},
        )


class ScipyLinprogOptimizer:
    """
    Linprog multi-objective optimizer (solves LP to minimize fertilizer mass
    subject to N, P2O5, K2O constraints using available FCO products).
    """

    optimizer_id = "scipy_linprog"

    def optimize(self, twin: dict[str, Any], candidates: list[dict] | None = None) -> OptimizerPlan:
        from ..agents.optimizer import solve_optimizer

        gap = (twin.get("current_plan") or {}).get("gap") or twin.get("gap") or {}
        gap_n = float(gap.get("N") or 0)
        gap_p = float(gap.get("P2O5") or 0)
        gap_k = float(gap.get("K2O") or 0)

        products = twin.get("products")
        if not products:
            raise ValueError(
                "ScipyLinprogOptimizer requires twin['products'] from fertilizer_products. "
                "Refusing to invent compositions."
            )

        res = solve_optimizer(gap_n, gap_p, gap_k, products)
        plan_qty = {
            k: float(v)
            for k, v in res.plan_kg_ha.items()
            if k.endswith("_kg_ha")
        }
        cost, currency, citation = estimate_cost(plan_qty, twin.get("region_id"))

        return OptimizerPlan(
            plan_kg_ha=res.plan_kg_ha,
            total_kg_ha=res.total_kg_ha,
            cost_estimate=cost,
            cost_currency=currency,
            cost_citation=citation,
            optimizer_id=self.optimizer_id,
            message=res.message,
            constraint_violations=[],
            meta={
                "gap": {"N": gap_n, "P2O5": gap_p, "K2O": gap_k},
                "status": res.status,
                "weight_saving_kg_ha": res.weight_saving_kg_ha,
                "flag": res.flag,
            },
        )


def get_default_optimizer() -> HeuristicOptimizer:
    return HeuristicOptimizer()


def get_optimizer(name: str | None = None) -> Optimizer:
    if name and name.lower() in ("linprog", "scipy", "scipy_linprog"):
        return ScipyLinprogOptimizer()
    return HeuristicOptimizer()
