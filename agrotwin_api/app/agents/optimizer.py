"""
Multi-objective Fertilizer Optimizer — linprog-based.

Replaces the fixed DAP→Urea→MOP rule with a small linear program.

Objective (current, honest version):
  Minimize total fertilizer weight (kg/ha) subject to meeting the N/P2O5/K2O
  gap exactly, given the available product set.

Why this objective and not cost minimization?
  Gap #8 in 04_remaining_gaps.md: no fertilizer price table has been sourced.
  Inventing prices would produce a numerically plausible but agronomically
  unverifiable optimizer output. The weight-minimization objective is real and
  meaningful: fewer kg/ha applied means less logistics cost, less risk of over-
  application, and less environmental load — all three are in the architecture's
  stated objectives. This is the honest partial version until prices are sourced.

Cost objective hook:
  When a price table is available, replace the `c` vector in solve_optimizer()
  with price_per_kg[product] values. The constraint matrix (A_eq, b_eq) and
  variable structure remain identical — it's a config change, not a rewrite.
  See the TODO comment in solve_optimizer().

Products included (from FCO NPK table, fertilizer_products table):
  UREA, DAP, MOP, SSP, 19_19_19, 12_32_16, 10_26_26, AMMONIUM_SULPHATE, SOP

scipy.optimize.linprog is used (no external solver required).
Method: 'highs' (default in scipy >= 1.7, mature open-source LP solver).
"""

import sqlite3
from dataclasses import dataclass

try:
    from scipy.optimize import linprog
    import numpy as np
except ImportError as e:
    raise ImportError(
        "scipy and numpy are required for the optimizer. "
        "Install with: pip install scipy"
    ) from e


@dataclass
class OptimizerResult:
    """Structured result from the LP optimizer."""
    status: str                  # 'OPTIMAL' | 'INFEASIBLE' | 'ERROR' | 'NO_ACTION'
    plan_kg_ha: dict             # product_code -> kg/ha allocated
    total_kg_ha: float           # sum of all product quantities
    gap_met: dict                # N|P2O5|K2O -> gap actually covered (should match input)
    message: str
    # Comparison to the fixed DAP→Urea→MOP rule
    fixed_rule_plan_kg_ha: dict  # what the old rule would have produced
    fixed_rule_total_kg_ha: float
    weight_saving_kg_ha: float   # optimizer_total - fixed_rule_total (negative = optimizer wins)
    flag: str                    # any optimizer-specific flag


def get_products_from_db(conn: sqlite3.Connection) -> dict:
    """Fetches all fertilizer products as {code: {n, p2o5, k2o}} dict."""
    rows = conn.execute(
        "SELECT product_code, n_percent, p2o5_percent, k2o_percent FROM fertilizer_products"
    ).fetchall()
    return {
        r["product_code"]: {
            "n": float(r["n_percent"]),
            "p2o5": float(r["p2o5_percent"]),
            "k2o": float(r["k2o_percent"]),
        }
        for r in rows
    }


def _fixed_rule_plan(gap_n: float, gap_p2o5: float, gap_k2o: float,
                     products: dict) -> dict:
    """
    Replicates the original fixed DAP→Urea→MOP rule from app/ledger.py.
    Used ONLY for comparison — the actual ledger output still uses ledger.py.
    """
    dap = products.get("DAP", {"n": 18.0, "p2o5": 46.0, "k2o": 0.0})
    urea = products.get("UREA", {"n": 46.0, "p2o5": 0.0, "k2o": 0.0})
    mop = products.get("MOP", {"n": 0.0, "p2o5": 0.0, "k2o": 60.0})

    dap_kg = round(gap_p2o5 / (dap["p2o5"] / 100), 1) if gap_p2o5 > 0 else 0.0
    n_from_dap = round(dap_kg * (dap["n"] / 100), 1)
    remaining_n = max(0.0, round(gap_n - n_from_dap, 1))
    urea_kg = round(remaining_n / (urea["n"] / 100), 1) if remaining_n > 0 else 0.0
    mop_kg = round(gap_k2o / (mop["k2o"] / 100), 1) if gap_k2o > 0 else 0.0

    total = round(dap_kg + urea_kg + mop_kg, 1)
    return {"plan": {"DAP_kg_ha": dap_kg, "UREA_kg_ha": urea_kg, "MOP_kg_ha": mop_kg},
            "total": total}


def solve_optimizer(
    gap_n: float,
    gap_p2o5: float,
    gap_k2o: float,
    products: dict,
) -> OptimizerResult:
    """
    Solves: minimize sum(x_i) [total kg/ha]
            subject to:
              sum(x_i * n_i)    >= gap_n
              sum(x_i * p2o5_i) >= gap_p2o5
              sum(x_i * k2o_i)  >= gap_k2o
              x_i >= 0  for all i

    Note: using >= (not ==) because we cannot always hit the exact gap with
    the discrete product set — we allow slight over-supply, which is
    agronomically acceptable (the gap is already conservative since losses
    are not subtracted, Gap #6).

    Cost objective TODO (Gap #8):
      When fertilizer prices are sourced, replace:
          c = [1.0] * n_products          (weight minimization)
      with:
          c = [price_per_kg[p] for p in product_list]
      The constraint matrix A_ub, b_ub below does not change.
    """
    if gap_n <= 0 and gap_p2o5 <= 0 and gap_k2o <= 0:
        fixed = _fixed_rule_plan(0, 0, 0, products)
        return OptimizerResult(
            status="NO_ACTION",
            plan_kg_ha={},
            total_kg_ha=0.0,
            gap_met={"N": 0.0, "P2O5": 0.0, "K2O": 0.0},
            message="All gaps are zero or negative — no fertilizer needed.",
            fixed_rule_plan_kg_ha=fixed["plan"],
            fixed_rule_total_kg_ha=0.0,
            weight_saving_kg_ha=0.0,
            flag="",
        )

    product_list = sorted(products.keys())  # deterministic ordering
    n_prod = len(product_list)

    # Objective: minimize total weight (kg/ha).
    # TODO (Gap #8): replace with cost vector when price table is available.
    c = [1.0] * n_prod

    # Inequality constraints: -A_ub @ x <= -b_ub  (i.e. A_ub @ x >= b_ub)
    # One row per nutrient with a nonzero gap.
    A_ub: list[list[float]] = []
    b_ub: list[float] = []

    nutrients_to_cover = []
    if gap_n > 0:
        row = [-(products[p]["n"] / 100.0) for p in product_list]
        A_ub.append(row)
        b_ub.append(-gap_n)
        nutrients_to_cover.append(("N", gap_n))
    if gap_p2o5 > 0:
        row = [-(products[p]["p2o5"] / 100.0) for p in product_list]
        A_ub.append(row)
        b_ub.append(-gap_p2o5)
        nutrients_to_cover.append(("P2O5", gap_p2o5))
    if gap_k2o > 0:
        row = [-(products[p]["k2o"] / 100.0) for p in product_list]
        A_ub.append(row)
        b_ub.append(-gap_k2o)
        nutrients_to_cover.append(("K2O", gap_k2o))

    bounds = [(0, None)] * n_prod

    result = linprog(
        c,
        A_ub=A_ub if A_ub else None,
        b_ub=b_ub if b_ub else None,
        bounds=bounds,
        method="highs",
    )

    # Compare with fixed rule
    fixed = _fixed_rule_plan(gap_n, gap_p2o5, gap_k2o, products)

    if result.status != 0:
        # LP infeasible or error — fall back to fixed rule with a flag
        flag = (
            f"OPTIMIZER_FALLBACK (linprog status={result.status}: {result.message}; "
            f"reverting to fixed DAP→Urea→MOP rule)"
        )
        return OptimizerResult(
            status="ERROR",
            plan_kg_ha=fixed["plan"],
            total_kg_ha=fixed["total"],
            gap_met={"N": gap_n, "P2O5": gap_p2o5, "K2O": gap_k2o},
            message=f"LP solver failed ({result.message}); fixed rule used as fallback.",
            fixed_rule_plan_kg_ha=fixed["plan"],
            fixed_rule_total_kg_ha=fixed["total"],
            weight_saving_kg_ha=0.0,
            flag=flag,
        )

    # Extract solution
    xs = result.x
    plan: dict[str, float] = {}
    for p, qty in zip(product_list, xs):
        kg = round(float(qty), 1)
        if kg > 0.05:  # suppress effectively-zero allocations
            plan[f"{p}_kg_ha"] = kg

    total_optimizer = round(float(sum(xs)), 1)
    weight_saving = round(total_optimizer - fixed["total"], 1)

    # Verify nutrients covered
    gap_met: dict[str, float] = {}
    for nutrient, gap_val in nutrients_to_cover:
        nt_key = nutrient.lower()
        covered = sum(
            float(xs[i]) * products[product_list[i]].get(
                "p2o5" if "p2o5" in nt_key else nt_key, 0
            ) / 100.0
            for i in range(n_prod)
        )
        gap_met[nutrient] = round(covered, 1)

    flag = ""
    if weight_saving < 0:
        flag = (
            f"OPTIMIZER_SAVES_WEIGHT: optimizer uses {abs(weight_saving)} kg/ha less "
            f"than fixed DAP→Urea→MOP rule"
        )
    elif weight_saving > 0:
        flag = (
            f"OPTIMIZER_HEAVIER: optimizer uses {weight_saving} kg/ha MORE than fixed rule "
            f"(may indicate product-mix trade-off; review plan)"
        )
    else:
        flag = "OPTIMIZER_MATCHES_FIXED_RULE"

    return OptimizerResult(
        status="OPTIMAL",
        plan_kg_ha=plan,
        total_kg_ha=total_optimizer,
        gap_met=gap_met,
        message="LP optimizer solved successfully (minimize total weight).",
        fixed_rule_plan_kg_ha=fixed["plan"],
        fixed_rule_total_kg_ha=fixed["total"],
        weight_saving_kg_ha=weight_saving,
        flag=flag,
    )


def run_optimizer_for_field(
    conn: sqlite3.Connection,
    gap_n: float,
    gap_p2o5: float,
    gap_k2o: float,
) -> OptimizerResult:
    """Convenience wrapper: fetches products from DB then runs the LP."""
    products = get_products_from_db(conn)
    return solve_optimizer(gap_n, gap_p2o5, gap_k2o, products)


def compare_all_demo_fields(conn: sqlite3.Connection) -> list[dict]:
    """
    Runs the optimizer vs fixed-rule comparison for all 8 demo fields.
    Returns a list of comparison dicts — used by the ablation endpoint.
    Calls run_field_ledger to get gap values, then optimizes.
    This is the 'prove complexity helps' ablation per architecture Section 18.
    """
    from .. import ledger as ledger_module

    fields = conn.execute(
        "SELECT * FROM field_active_crop WHERE is_synthetic = TRUE"
    ).fetchall()

    results = []
    for field_row in fields:
        ledger_result = ledger_module.run_field_ledger(conn, field_row)
        if ledger_result.get("status") == "ABSTAIN":
            results.append({
                "field_code": field_row["field_code"],
                "status": "ABSTAIN",
                "reason": ledger_result.get("reason", ""),
            })
            continue

        gap = ledger_result.get("gap", {})
        opt = run_optimizer_for_field(
            conn,
            gap_n=gap.get("N", 0),
            gap_p2o5=gap.get("P2O5", 0),
            gap_k2o=gap.get("K2O", 0),
        )

        results.append({
            "field_code": field_row["field_code"],
            "crop": ledger_result.get("crop"),
            "recommendation_type": ledger_result.get("recommendation_type"),
            "gap_N": gap.get("N", 0),
            "gap_P2O5": gap.get("P2O5", 0),
            "gap_K2O": gap.get("K2O", 0),
            "optimizer_plan_kg_ha": opt.plan_kg_ha,
            "optimizer_total_kg_ha": opt.total_kg_ha,
            "fixed_rule_plan_kg_ha": opt.fixed_rule_plan_kg_ha,
            "fixed_rule_total_kg_ha": opt.fixed_rule_total_kg_ha,
            "weight_saving_kg_ha": opt.weight_saving_kg_ha,
            "optimizer_flag": opt.flag,
            "optimizer_status": opt.status,
            "optimizer_message": opt.message,
        })

    return results
