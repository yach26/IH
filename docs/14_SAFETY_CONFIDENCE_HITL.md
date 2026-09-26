# 14 — Safety, Confidence, Human-in-the-Loop

## Low-Confidence / Abstain Behaviour

The system must know when **not** to recommend.

Example UI message:

```
⚠ LOW CONFIDENCE

A reliable fertilizer plan cannot currently be produced.

Reasons:
  • Soil test is 18 months old
  • Soil moisture unavailable
  • Crop stage uncertain

Required: Upload a recent soil report or confirm current values.
```

Build detection into the actual decision pipeline, not just the UI.

---

## Confidence Framework

- Start from data quality flags (soil age, missing micronutrients, proxy conversions, derived density, etc.).
- Validation Agent can further downgrade based on weather conflict, evidence mismatch, or out-of-distribution inputs.
- Final levels: `HIGH` | `MEDIUM` | `LOW` | `ABSTAIN`

Current rule in ledger (can be extended):

```python
confidence = "MEDIUM" if len(flags) == 1 else "LOW"
# additional rules in Validation Agent can force ABSTAIN
```

---

## Human-in-the-Loop

Two roles:

1. **Farmer**  
   - Confirms OCR values  
   - Records applications  
   - Provides feedback on outcomes

2. **Agronomist**  
   - Separate dashboard to review recommendations  
   - Inspect evidence  
   - Override plans  
   - Flag incorrect recommendations  
   - Validate region-specific guidance

### Feedback loop

```
AI Recommendation → Agronomist Review → Outcome
    → Feedback Dataset → Future Model Improvement
```

Every override is written to the audit log.

---

## Checklist

- [x] Validation Agent implements all abstain rules
- [ ] Frontend clearly surfaces low-confidence and ABSTAIN states
- [x] Agronomist override endpoint + audit trail
- [x] No silent acceptance of low-quality data
- [x] Farmer confirmation required for OCR values
