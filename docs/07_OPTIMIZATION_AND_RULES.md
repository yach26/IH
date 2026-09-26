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

- [ ] Keep current heuristic as default implementation of `Optimizer`.
- [ ] Abstract it behind a clean interface.
- [ ] Add a simple cost model (market prices of Urea/DAP/MOP as config).
- [ ] Rule engine as a list of callable checks that return (pass/fail, reason).
- [ ] Validation Agent runs the rule engine after optimization.
- [ ] Unit tests for each rule and for the heuristic.
