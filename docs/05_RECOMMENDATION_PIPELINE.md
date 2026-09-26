# 05 — Recommendation Pipeline

## Exact Ordered Steps

```
Farmer Input
    ↓ Validation (basic schema + required fields)
    ↓ Digital Twin Update
    ↓ Crop Nutrient Requirement          ← Crop Agent + RDF look-up
    ↓ Available Nutrient Estimate         ← Soil Agent
    ↓ Nutrient Gap                        ← Ledger (the only place numbers are born)
    ↓ Candidate Fertilizer Generation
    ↓ Weather Feasibility                 ← Weather Agent
    ↓ Cost / Availability Constraints
    ↓ Multi-Objective Optimization        ← Optimizer (or current heuristic)
    ↓ Candidate Plans
    ↓ Agronomic Constraint Validation     ← Validation Agent + Rules
    ↓ Evidence Retrieval                  ← Knowledge Agent (RAG)
    ↓ Confidence / Uncertainty assembly
    ↓ Final Decision-Support Plan
```

---

## Detailed Step Notes

### 1. Farmer Input + Validation
- Accept soil report, crop selection, sowing date, target yield, etc.
- Reject incomplete required fields early.

### 2. Digital Twin Update
- Write confirmed values into the twin tables.
- This is the single source of truth for all subsequent steps.

### 3–5. Requirement → Available → Gap
- Crop Agent looks up the RDF requirement (never invents it).
- Soil Agent reads the latest soil test.
- Ledger computes gap = required − available (see `02_DIGITAL_TWIN_AND_LEDGER.md`).

### 6–9. Candidate generation + constraints + optimization
- Generate possible product combinations.
- Weather Agent can reject or shift application windows.
- Cost model (simple market prices) and availability filters.
- Optimizer (or current DAP→Urea→MOP heuristic) selects the final quantities.

### 10. Agronomic Constraint Validation
- Hard limits, compatibility, stage restrictions, soil pH/EC limits.
- Any violation → ABSTAIN or force a safer plan.

### 11. Evidence Retrieval
- Runs **after** a candidate plan exists so the RAG query can be precise (crop + stage + nutrient + region).
- Knowledge Agent returns citations only.

### 12–13. Confidence assembly + final plan
- Flags + data quality checklist → confidence level.
- Persist the full proof-carrying object.
- Emit `PLAN_CREATED` event so Monitoring Agent starts watching.

---

## Selective Re-planning Path

When Monitoring Agent emits an event:

```
Event → Orchestrator
      → decide affected agents (e.g. only Weather + Validation + Optimizer)
      → re-run only those steps
      → produce REVISED plan
      → invalidate old plan (set invalidated_at)
      → notify farmer / agronomist
```

This is the core of USP 2 and the demo “wow” moment.

---

## Output Contract

The pipeline must return a full proof-carrying object (see `01_PROJECT_OVERVIEW.md`).  
If any critical step fails → return `status: "ABSTAIN"` with reasons and required actions for the farmer.

---

## Implementation Checklist

- [x] Implement the pipeline as a pure function / class that takes `field_id` and returns a Recommendation. (`agrotwin_api/app/pipeline.py` → `RecommendationPipeline`)
- [x] Log every intermediate state for audit. (`pipeline_audit` on the proof object)
- [x] Support both “full run” and “partial re-plan” modes. (`agents=[...]`)
- [x] Ensure ledger is the single source of numeric truth. (`HeuristicOptimizer` → `ledger.convert_gap_to_products`)
- [x] Unit test each step in isolation; integration test the full happy path + abstain path + re-plan path. (`tests/test_pipeline.py`)

### Done (2026-09-27)

| Item | Where |
|------|--------|
| Ordered Soil → Crop → Weather → Ledger → Optimizer → Validation → Knowledge | `app/pipeline.py` |
| Proof-carrying object (WHAT / HOW MUCH / WHEN / WHY / BASED ON WHAT / HOW SURE) | `app/core/proof.py` |
| ABSTAIN + required_actions | pipeline `_abstain()` |
| Selective re-plan | `Orchestrator.request_replan()` |
| Persist + invalidate old plan (`invalidated_at`, `SUPERSEDED`) | pipeline `_persist()` |
