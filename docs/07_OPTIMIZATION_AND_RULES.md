# 07 — Multi-Objective Optimization + Rule Engine

## Current State

The prototype uses a fixed heuristic inside `ledger.py`:

- DAP for P₂O₅ need
- remaining N from Urea
- MOP for K₂O

This matches the source worked example and is fully traceable.  
It is **not** yet a multi-objective optimizer.

---

## Target Optimization Formulation (Conceptual)

```
maximize:   predicted agronomic benefit
minimize:   fertilizer quantity,
            fertilizer cost,
            nutrient excess,
            estimated nutrient loss,
            environmental risk

subject to:
  crop nutrient requirements,
  soil constraints,
  application constraints,
  weather constraints,
  validated agronomic limits
```

---

## Implementation Path

### MVP (Hackathon)

Keep the current DAP→Urea→MOP heuristic inside `ledger.py`.  
Expose it behind an `Optimizer` interface so the rest of the system does not change when we later swap the implementation.

```python
class Optimizer(Protocol):
    def optimize(self, twin: TwinState, candidates: list[Product]) -> Plan:
        """
        Returns a Plan with quantities, cost estimate, and any constraint violations.
        Must never invent numbers outside the supplied requirements and product compositions.
        """
```

### Phase 2

- Formulate as a linear / mixed-integer program with SciPy or OR-Tools.
- Decision variables: kg of each available product.
- Constraints come from the Rule Engine.
- Objectives can be weighted or returned as a Pareto set for the What-If simulator.

---

## Rule / Constraint Engine

Hard rules that the Validation Agent and Optimizer must respect:

| Rule Category | Examples |
|---------------|----------|
| Maximum rates | Max N/P/K per crop per stage from RDF or local guidelines |
| Compatibility | Do not mix certain products in the same application |
| Weather windows | No application if heavy rain expected within X hours |
| Soil limits | Restrict certain fertilizers when pH or EC is outside range |
| Data freshness | Soil test older than N months → force lower confidence or abstain |

All rules must be data-driven (loaded from region config or tables).  
Never hard-code magic numbers without a citation.

```python
class RuleEngine:
    def check(self, plan: Plan, twin: TwinState) -> list[Violation]:
        """Return list of (rule_id, severity, message)."""
```

---

## Checklist

- [x] Keep current heuristic as default implementation of `Optimizer`. (`HeuristicOptimizer` → `ledger.convert_gap_to_products`)
- [x] Abstract it behind a clean interface. (`app/core/optimizer.py` `Optimizer` Protocol)
- [x] Add a simple cost model (market prices of Urea/DAP/MOP as config). (`region_config.cost_model`, labelled ENGINEERING_DEFAULT / Gap #8)
- [x] Rule engine as a list of callable checks that return (pass/fail, reason). (`app/core/rules.py`)
- [x] Validation Agent runs the rule engine after optimization.
- [x] Unit tests for each rule and for the heuristic. (`tests/test_optimizer_rules.py`)

### Done (2026-09-27)

| Item | Where |
|------|--------|
| `Optimizer` Protocol + `OptimizerPlan` | `app/core/optimizer.py` |
| Default DAP→Urea→MOP heuristic (no quantity fork) | `HeuristicOptimizer` |
| Optional linprog kept but **not** wired as default | `app/agents/optimizer.py` |
| Cost estimate (INR/kg config, never used as kg/ha source) | `estimate_cost()` |
| Rules: max RDF rates, Urea+SSP compatibility, weather window, pH, EC, soil freshness | `app/core/rules.py` + `region_config.py` |

### Optimizer invocation semantics (verified 2026-09-27, Phase 2.2)

- The `"optimizer"` step **always runs** on the default `/recommend` path (it is one of
  `FULL_STEPS` in `app/pipeline.py`, not opt-in) — but the *implementation* it runs is
  `HeuristicOptimizer` by default (`app/pipeline.py::RecommendationPipeline.__init__`).
- `POST /fields/{id}/recommend` accepts an optional body field `"optimizer"` (see
  `RecommendRequest.optimizer` in `app/api/schemas.py`). Passing
  `{"optimizer": "scipy_linprog"}` (aliases: `"linprog"`, `"scipy"`) switches to
  `ScipyLinprogOptimizer` for that call via `get_optimizer()` in `app/core/optimizer.py`.
  Omitting it, or any other value, uses `HeuristicOptimizer`.
- **Disagreement handling**: when the active optimizer is `HeuristicOptimizer`
  (`optimizer_id == "heuristic_dap_urea_mop"`) and its `plan_kg_ha` differs from the
  ledger's own `how_much` quantities for the same product, `pipeline.py` **overwrites the
  optimizer's numbers with the ledger's** and appends an `OPTIMIZER_OVERRIDDEN_BY_LEDGER`-style
  flag — i.e. the ledger is the numeric source of truth; the heuristic optimizer's role in the
  default path is to select which products to use, not to have the final say on quantity.
  `ScipyLinprogOptimizer` is not reconciled against the ledger this way (it is
  invitation-only, not on the default path), so calling it directly can legitimately return
  slightly different splits than the ledger heuristic (confirmed live: for field REAL-001,
  default heuristic gave `UREA_kg_ha=36.7` vs `36.6` from `scipy_linprog` — same DAP/MOP,
  rounding-level LP difference, not a disagreement in requirement).
- **Framing note**: describing the system as running "multi-objective optimization" by
  default is not accurate — the default path is a deterministic heuristic split with a
  ledger-enforced numeric guarantee. `ScipyLinprogOptimizer` (true LP, minimizes total
  fertilizer weight) exists and is fully wired, but is opt-in via the `optimizer` field, not
  the default demo path. Prefer describing the default as "evidence-grounded rule-based
  allocation with an optional LP optimizer for weight minimization."
