# 13 — What-If Simulator + Visual Growth Simulator

## What-If Simulator

Supports simulating:

- more / less fertilizer (± %)
- rainfall / irrigation changes
- fertilizer substitution
- delayed application
- target yield changes

**Rule**: Only display outcome numbers actually supported by models/data.  
Do not fabricate impressive percentages for the hackathon.

### Implementation

Re-run the ledger / optimizer with modified inputs and return the delta plan + new confidence.

```python
POST /fields/{id}/what-if
{
  "fertilizer_delta_pct": -20,
  "rainfall_mm": 30
}
```

Response contains both the original plan and the simulated plan side-by-side.

---

## Visual Growth Simulator

A farmer-facing companion that shows plant appearance over growth stages.

- Fixed library of SVG / Lottie states per crop per stage (stressed, below-average, healthy, thriving).
- Driven by:
  - Nutrient Ledger sufficiency trajectory
  - Yield-prediction band (if available)
  - Weather risk flags
- Side-by-side: Current Plan vs What-If Plan
- Scrubber or auto-play for demo

### Guardrails

- Never generate photorealistic “predictions”.
- Label as “Illustrative projection based on current data”.
- Degrade to “not enough data to project growth” state when confidence is low.
- This is a **UI/communication layer**, not a fourth core USP.

---

## Checklist

- [ ] `/what-if` endpoint that accepts delta parameters
- [ ] Frontend controls that call it and show delta
- [ ] SVG asset set for pilot crops (4–5 states each)
- [ ] Mapping from model outputs → visual states
- [ ] Graceful low-confidence visual state
