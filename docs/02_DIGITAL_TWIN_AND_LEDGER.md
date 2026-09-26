# 02 — Digital Twin + Nutrient Ledger (Implementation Guide)

> **Status**: Phase-1 core is already implemented and working in `agrotwin_api/` (and `agrotwin_prototype/`).  
> This document describes how to treat it as the foundation and how to extend it safely.

---

## 1. Field Digital Twin Schema (Conceptual)

```
FIELD DIGITAL TWIN
├── Identity
│   ├── field_id
│   ├── farmer_id
│   ├── location / coordinates
│   ├── area_ha
│   ├── soil_type
│   └── region_id                    # kolhapur | jalgaon | ...
├── Crop State
│   ├── crop_code
│   ├── variety
│   ├── sowing_date
│   ├── growth_stage
│   └── target_yield_kg_ha
├── Soil State
│   ├── N, P, K (kg/ha)
│   ├── pH, OC, EC, moisture
│   ├── micronutrients
│   ├── test_date
│   └── source (lab | ocr | manual)
├── Environment
│   ├── temperature, humidity
│   ├── rainfall (recent + forecast)
│   └── irrigation status
├── Historical Memory
│   ├── previous crops
│   ├── soil tests
│   ├── fertilizer applications
│   ├── yields
│   └── previous recommendations
└── Current Plan
    ├── nutrient_requirement
    ├── deficit / gap
    ├── selected_fertilizers
    ├── quantities (kg/ha)
    ├── application_windows
    ├── estimated_cost
    ├── confidence
    ├── flags
    └── evidence_citations
```

In the current SQLite implementation this is already partially realized via tables:
- `fields`, `crops`, `soil_tests`
- `fertilizer_recommendations`, `fertilizer_products`
- `nutrient_ledger_entries`, `recommendations`

---

## 2. Nutrient Ledger Equations (Executable)

**Location**: `ledger.py`

### Core rules already enforced in code

1. Required nutrients come **only** from `fertilizer_recommendations` rows (which cite MPKV/ICAR RDF).
2. Gap = required − available. Losses are currently **not** subtracted (they are unsourced → conservative).
3. Product conversion uses **exact** FCO percentages from `fertilizer_products`.
4. Every calculation carries a list of flags; confidence is derived from flag count.
5. If usable requirement cannot be derived → status = `ABSTAIN`.

### Key functions

```python
def get_recommendation(conn, crop_code, rec_type) -> tuple | None:
    """Lookup RDF requirement. Returns (n, p2o5, k2o, citation, notes) or None."""

def get_products(conn) -> dict:
    """Returns {product_code: {n, p2o5, k2o}} from fertilizer_products."""

def compute_gap(required_n, required_p2o5, required_k2o,
                soil_n, soil_p_proxy, soil_k) -> tuple:
    """
    gap = required - available (no loss subtraction).
    Returns (gap_n, gap_p2o5, gap_k2o). Negative gaps are clamped to 0.
    """

def convert_gap_to_products(gap_n, gap_p2o5, gap_k2o, products) -> dict:
    """
    Prefer DAP for P₂O₅, then Urea for remaining N, MOP for K.
    Exact logic from conversion_notes.md.
    Returns {
      "DAP_kg_ha": ...,
      "UREA_kg_ha": ...,
      "MOP_kg_ha": ...,
      "n_supplied_by_dap_kg_ha": ...
    }
    """

def run_field(conn, field_id, field_meta, rec_type_map) -> dict:
    """
    Full ledger run for one field.
    Returns a result dict with status, required, soil, gap, plan_kg_ha,
    confidence, flags, citation, etc.
    """
```

### Current conversion heuristic (matches source worked example)

1. Calculate DAP needed to meet P₂O₅ gap.
2. Subtract N supplied by that DAP from the N gap.
3. Meet remaining N with Urea.
4. Meet K₂O gap with MOP.
5. All quantities in kg/ha, rounded to 1 decimal place.

**Future**: Replace the fixed heuristic with a real multi-objective optimizer while keeping the same interface so the rest of the system does not break.

---

## 3. Confidence & Flags (Already Implemented)

| Flag | Meaning | Effect on Confidence |
|------|---------|----------------------|
| `P_PROXY` | Soil test stores P, RDF is P₂O₅ (no conversion factor in data pack yet) | Always present → MEDIUM baseline |
| `DERIVED_DENSITY` | Banana kg/ha derived from g/plant × mid-point 2,250 plants/ha | Extra flag → LOW |
| `MIDPOINT_RANGE_RDF` | Source gives a range (e.g. Cotton); mid-point used | Extra flag → LOW |

Rule currently in code:

```python
confidence = "MEDIUM" if len(flags) == 1 else "LOW"
```

When more flags appear or critical data is missing → status becomes `ABSTAIN`.

---

## 4. How to Extend Safely

### Adding a new crop / recommendation type

1. Insert row(s) into `fertilizer_recommendations` with an accurate `source_citation`.
2. If density or unit conversion is required, document it and add a corresponding flag.
3. **Never** hard-code numbers inside `ledger.py`.

### Adding losses (future)

Only when a validated agronomic source provides the loss equation.  
Until then keep `losses = None` and do not subtract.

### Making the Twin “living”

- After any soil report, application, weather update, or expert override → update the relevant tables.
- The Monitoring Agent (see `08_MONITORING_AND_EVENTS.md`) will detect these changes and trigger selective re-planning.

---

## 5. Integration Contract for Other Components

Any agent or API that wants a fertilizer plan **must** call:

```python
result = ledger.run_field(conn, field_id, field_meta, rec_type_map)
```

and then pass the result through the Validation Agent before exposing it to the farmer.

The result already contains everything needed for a proof-carrying recommendation.

### Example result shape

```python
{
  "record_id": "SYN-008",
  "field_id": "...",
  "crop": "RICE",
  "recommendation_type": "tillering",
  "current_stage": "tillering",
  "status": "PLAN_GENERATED",          # or ABSTAIN / NO_FERTILIZER_NEEDED
  "required": {"N": 100.0, "P2O5": 50.0, "K2O": 50.0},
  "soil": {"N": 45.0, "P_proxy": 12.0, "K": 80.0},
  "gap": {"N": 55.0, "P2O5": 38.0, "K2O": 0.0},
  "plan_kg_ha": {
    "DAP_kg_ha": 82.6,
    "UREA_kg_ha": 78.3,
    "MOP_kg_ha": 0.0,
    "n_supplied_by_dap_kg_ha": 14.9
  },
  "confidence": "MEDIUM",
  "flags": ["P_PROXY"],
  "citation": "mpkv_icar_rdf.md#rice-tillering",
  "recommendation_notes": "..."
}
```

---

## 6. Testing Checklist

- [ ] `python run_demo.py` produces results identical to current `output/ledger_results.csv`.
- [ ] Banana recommendations carry `DERIVED_DENSITY` and appropriate confidence.
- [ ] Fields with no matching recommendation → `ABSTAIN` with clear reason.
- [ ] Every kg/ha number is traceable via `citation` + `source_citation` columns.
- [ ] Changing a single soil value correctly changes the gap and plan.
- [ ] No negative quantities appear.

---

## 7. Known Gaps (from 04_remaining_gaps.md)

Still open (except banana density which is resolved):

- Exact P → P₂O₅ conversion factor for soil tests.
- Micronutrient handling.
- Loss equations.
- Stage-specific recommendations for more crops.
- Real field densities for banana (currently mid-point).

**Rule**: Document any new assumption as a flag. Never hide it.
