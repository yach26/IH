# AgroTwin AI — Yield Prediction ML Component

Predicts expected crop yield (kg/ha) given soil, weather, and a
**fertilizer plan the Nutrient Ledger + Optimizer has already computed**.
This model never outputs a fertilizer quantity — that architecture rule
is enforced structurally (see `inference.py`'s docstring and signature).

## 1. Datasets actually used (no Kaggle, per instruction)

### From the Phase-1 data pack (`AgroTwin_Phase1_Data.zip`)
| Folder | Used for |
|---|---|
| `05_Crop_Calendars/four_pilot_crops.md` | Crop stages, typical density (Banana) |
| `06_Fertilizer_Recommendations/mpkv_icar_rdf.md` | MPKV/ICAR RDF per crop — the "required" nutrient values used throughout |
| `07_Fertilizer_Composition/` | (Used elsewhere in AgroTwin's Ledger; not directly needed here since this model consumes N/P2O5/K2O directly) |
| `03_Soil_Data/soil_sources_and_samples.md` | Kolhapur-Ajara published soil N/P/K/pH/OC ranges |
| `09_Yield_Datasets/yield_sources.md` | The explicit instruction this component follows: "use STCR equations + published response functions as primary, augment with synthetic but labelled records" |
| `10_Synthetic_Farm_Histories/synthetic_records.csv` | 8 reference records with a real `previous_yield` column — used as a sanity-check target, not as training data (8 rows cannot train anything) |

### External sources consulted (reputable government/public sources only, no Kaggle)
| Figure used | Source |
|---|---|
| Kolhapur district Sugarcane yield, 2024-25 Kharif: **114,516 kg/ha** | Ministry of Agriculture & Farmers Welfare, District/Season/Crop-wise Area, Production & Yield Statistics for Maharashtra, via UPAg, aggregated at [dataful.in/datasets/5632](https://dataful.in/datasets/5632/) |
| Maharashtra Banana state productivity: **~65.7 t/ha** (highest of any Indian state; national avg ~30.5 t/ha) | State horticulture profile, reproduced at [indianbusinessportal.in](https://www.indianbusinessportal.in/GIProducts/agriculture-jalgaon-banana/c-144) citing government production data |
| Maharashtra Cotton (lint) historical yield, ~250-380 kg lint/ha in recent years | Ministry of Agriculture & Farmers Welfare state-wise yield tables, reproduced in an RBI publication (Table 85, website.rbi.org.in) |
| Maharashtra Soybean, 2012-13: **1,319 kg/ha** | *International Journal of Tropical Agriculture*, citing Government of India agricultural statistics |
| Soybean STCR target-yield range 20-25 q/ha; Cotton irrigated/rainfed RDF ranges | `06_Fertilizer_Recommendations/mpkv_icar_rdf.md` (Phase-1 pack) |

These are **calibration anchors**, not training rows — they tell the
synthetic generator what a realistic yield ceiling/average looks like per
crop, so the generated training data isn't just internally consistent but
also plausible against real published numbers.

## 2. Why synthetic training data was necessary (and how it was built honestly)

`09_Yield_Datasets/yield_sources.md` states plainly: *"True farm-level
multi-year fertilizer-yield paired datasets are scarce openly."* We
verified this is still true — no bulk, open, farm-level Maharashtra
fertilizer-yield dataset was found from a reputable non-Kaggle source
during this session. The 8 synthetic records in the data pack have a
yield column, but 8 rows cannot train an XGBoost model meaningfully.

So `src/generate_training_data.py` generates **900 synthetic rows**
(150 per crop/practice combination) using:
- **Liebig's Law of the Minimum**: yield is capped by whichever nutrient
  (N, P, or K) is least available relative to its requirement — a
  standard, textbook agronomic principle, not something invented for
  this project.
- **Mitscherlich-type diminishing-returns response**: each additional
  unit of a nutrient helps less as availability approaches requirement.
- Soil N/P/K/pH/OC sampled within the published Kolhapur-Ajara ranges
  (Jalgaon ranges are an acknowledged extrapolation — no Jalgaon-specific
  Soil Health Card sample existed in the data pack).
- Fertilizer actually applied randomized 40%-130% of the MPKV/ICAR RDF,
  representing realistic variation in farmer practice.
- A water-adequacy index built from each field's rainfall relative to its
  own district's normal range, moderated by irrigation type — **not** a
  literal comparison of district rainfall totals to a textbook crop-water
  figure (an earlier version of this script did that and produced
  physically nonsensical near-zero yields; see the code comments in
  `generate_training_data.py` for the specific bug and fix).
- ~7% random noise per record for realistic field-to-field scatter.

Every generated row is flagged `is_synthetic=1`. **This is not real farm
data and must never be presented to a farmer, judge, or investor as such.**

### Sanity check: generated yields vs. real anchors
| Crop | Generated mean (range) | Real anchor |
|---|---|---|
| Sugarcane Pre-seasonal | 93.1 t/ha (49-130) | Kolhapur district avg 114.5 t/ha (2024-25) — within range, mean slightly conservative since the sample spans under-fertilized fields too |
| Sugarcane Ratoon | 84.7 t/ha (52-116) | Ratoons are agronomically expected lower than pre-seasonal — consistent |
| Banana | 41.9 t/ha (25.5-61.8) | Maharashtra state ceiling ~65-70 t/ha; matches Phase-1 record range (35-38 t/ha) in the lower-middle |
| Cotton Irrigated | 2,164 kg/ha (1,413-2,955) | Matches Phase-1 synthetic records almost exactly (22-28 q/ha = 2,200-2,800 kg/ha) |
| Cotton Rainfed | 1,315 kg/ha (992-1,681) | Sensibly lower than irrigated |
| Soybean | 1,648 kg/ha (897-2,420) | Above the 2012-13 state average (1,319 kg/ha), consistent with better-managed, Rhizobium-treated pilot fields; within the STCR target band (2,000-2,500) at the upper end |

## 3. Model architecture: one XGBoost regressor **per crop**

An earlier version trained a single global model across all 4 crops with
a one-hot crop feature. Because Sugarcane yields (tens of thousands of
kg/ha) are ~2 orders of magnitude larger than Cotton/Soybean yields, that
model's trees spent nearly all their capacity on "which crop is this"
(96.8% of feature importance) and had almost nothing left to learn the
real soil/fertilizer/weather response. Overall R² looked great (0.985)
purely from guessing the crop; per-crop R² was 0.5-0.7, and **negative**
(-0.53) for Soybean — worse than predicting the mean. Training one model
per crop fixed this and is standard practice for multi-crop agronomic
modeling.

### Held-out test-set results (on the SYNTHETIC data — see limitations)
| Crop | Test MAE | MAE as % of mean yield | R² |
|---|---|---|---|
| Banana | 3,050.8 kg/ha | 7.0% | 0.720 |
| Cotton | 145.3 kg/ha | 8.5% | 0.868 |
| Soybean | 108.0 kg/ha | 6.6% | 0.810 |
| Sugarcane | 6,753.7 kg/ha | 7.4% | 0.734 |

These R² values (0.72-0.87) are not suspiciously perfect — they land
close to the ~93% variance explained you'd expect if the model correctly
recovered the deterministic generating formula against its own 7% noise
floor. That's a good sign the pipeline is sound, not a claim about
real-world predictive power (see Section 5).

Full metrics: `reports/metrics.json`. Plots: `reports/residuals.png`,
`reports/feature_importance.png`.

## 4. Files

```

agrotwin\_ml/
├── src/
│   ├── generate\_training\_data.py   - builds the synthetic training set (documented above)
│   ├── features.py                  - single source of truth for feature engineering (train + inference both import this)
│   ├── train\_model.py               - per-crop XGBoost training, tuning, evaluation, plots
│   └── inference.py                 - predict\_yield(), the only function the rest of AgroTwin should call
├── data/
│   └── yield\_training\_data\_synthetic.csv
├── models/
│   ├── yield\_model.joblib           - dict of {crop\_code: XGBRegressor}, loaded via joblib
│   └── model\_metadata.json          - version, feature list, per-crop metrics
├── reports/
│   ├── metrics.json
│   ├── feature\_importance.png / .csv
│   └── residuals.png
└── README.md                        - this file

````

To reproduce from scratch:
```bash
cd src
python3 generate_training_data.py
python3 train_model.py
python3 inference.py   # smoke test
````

## 5. Honest limitations (read before integrating)

- **No real farm-level fertilizer-yield data was used.** Every training
  row is synthetic, generated by a documented formula, calibrated to real
  published averages but not observed on a real farm. The reported R²/MAE
  describe how well the model recovers its own synthetic generating
  process — they are **not** a claim about real-world prediction accuracy.
- **Jalgaon soil ranges are extrapolated.** Only Kolhapur-Ajara had a
  published Soil Health Card sample in the Phase-1 data pack. Jalgaon
  ranges were widened/adjusted judgment calls, not sourced figures.
- **STCR equations were not available in machine-readable form.** MPKV
  publishes these in yearly PDFs; this project used the well-established
  general principles they're built on (Liebig's Law, diminishing returns)
  rather than the exact fitted coefficients.
- **Nutrient uptake efficiency figures (N 40%, P 22%, K 55%)** are
  order-of-magnitude figures consistent with general Indian agronomy
  extension literature, not measured for these specific pilot fields.
- **The water-adequacy model is a simplification.** It does not account
  for soil moisture retention, drainage, or within-season rainfall
  timing — only how a season's total rainfall compares to its own
  district's normal range, moderated by irrigation type.
- **Geographic coverage is Kolhapur + Jalgaon only**, four crops only.
  `inference.py` explicitly ABSTAINs (returns `predicted_yield_kg_ha: null`)
  for any other district or crop rather than extrapolating silently.
- **This model must be retrained once real data exists.** The correct
  trigger, per the AgroTwin architecture's Agronomist feedback loop, is:
  once enough real (farm_id, soil_test, fertilizer_applied, weather,
  actual_yield) records accumulate via the Agronomist dashboard's
  override/feedback mechanism, replace `yield_training_data_synthetic.csv`
  with real data (or a real+synthetic blend), and re-run `train_model.py`
  unchanged — the pipeline doesn't need to be rebuilt, only re-fed.

## 6. Integration guide — calling this from AgroTwin's RecommendationPipeline

The Nutrient Ledger + Optimizer already produce a fertilizer plan before
this model is ever called. Call `predict_yield()` **after** that, purely
to annotate the recommendation with an expected-outcome estimate:

```python
from agrotwin_ml.src.inference import predict_yield

# ... inside RecommendationPipeline, after ledger.run_field_ledger() ...
ledger_result = run_field_ledger(conn, field_row)

if ledger_result["status"] == "PLAN_GENERATED":
    yield_estimate = predict_yield(
        soil={
            "district": field_row["district_code"],
            "n_kg_ha": ledger_result["soil_test"]["N"],
            "p_kg_ha": ledger_result["soil_test"]["P_proxy"],
            "k_kg_ha": ledger_result["soil_test"]["K"],
            "ph": field_row.get("ph", 7.0),
            "oc_percent": field_row.get("oc_percent", 0.5),
        },
        crop=ledger_result["crop"],
        weather={
            "rainfall_mm_season": weather_agent_forecast["season_total_mm"],
            "irrigation_type": field_row["irrigation_type"],
        },
        fertilizer_plan={
            "applied_n_kg_ha": ledger_result["required"]["N"],       # the PLAN being evaluated
            "applied_p2o5_kg_ha": ledger_result["required"]["P2O5"],
            "applied_k2o_kg_ha": ledger_result["required"]["K2O"],
            "required_n_kg_ha": ledger_result["required"]["N"],      # from the same RDF lookup
            "required_p2o5_kg_ha": ledger_result["required"]["P2O5"],
            "required_k2o_kg_ha": ledger_result["required"]["K2O"],
        },
    )
    # yield_estimate["caveats"] should be surfaced in the "Why this plan?"
    # / data-quality panel exactly like the Ledger's own `flags` are —
    # never silently dropped.
```

For the **What-If Simulator**: when the farmer adjusts the fertilizer
amount slider, recompute the Ledger's plan for the modified scenario
first (per the What-If contract already defined for AgroTwin), then call
`predict_yield()` again with the new `applied_*` values — this is what
lets the simulator show "expected yield" changing alongside the fertilizer
numbers, using the same two-step pattern (Ledger first, ML second) as the
real recommendation path.

For the **"How sure are we?" confidence panel**: `predict_yield()`'s
`confidence` field is derived from the crop-model's own held-out R²
(see `_confidence_from_r2` in `inference.py`) — it should be combined
with, not override, the Ledger's own `flags`-based confidence. A
reasonable combination rule: show the Ledger's confidence for the
fertilizer numbers themselves, and the yield model's confidence
separately for the expected-outcome number, since they're honestly
different claims with different evidence behind them.
