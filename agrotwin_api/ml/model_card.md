# Model Card: AgroTwin Yield Prediction Model

## Model Details

| Field | Value |
|-------|-------|
| **Model version** | `yield-xgb-kolhapur-real-v2` |
| **Architecture** | One XGBoost regressor per crop (4 models total) |
| **Training data** | Real Polgaon soil data (2016-2024) + published Kolhapur yield averages |
| **Feature count** | 20 per crop model (soil, weather, applied nutrients, engineered sufficiency proxies, one-hot district/irrigation) |
| **Target variable** | Crop yield (kg/ha) |
| **Last trained** | 2026 (Real data integration) |

## Supported Scope

### Crops
- **BANANA**
- **SUGARCANE**
- **COTTON**
- **SOYBEAN**

### Districts
- **Kolhapur** (Maharashtra)
- **Jalgaon** (Maharashtra)

Any crop or district outside this scope will cause the model to **ABSTAIN** (return `predicted_yield_kg_ha: null`).

## Intended Use

This model provides a **directional yield estimate** given:
1. A fertilizer plan already computed by the deterministic Nutrient Ledger + Optimizer
2. Soil test values (N, P, K, pH, organic carbon)
3. Seasonal rainfall and irrigation type

The model is designed to answer: *"If the farmer follows this specific plan, what yield should they expect?"*

It is **NOT** designed to:
- Invent or adjust fertilizer quantities
- Replace the Nutrient Ledger's authority over kg/ha recommendations
- Predict yields for crops or districts outside the supported scope
- Provide guaranteed outcomes

## Training Data

### Source
The model was trained on **synthetic data** generated to match published district/state yield averages from agricultural statistics. No real farm-level paired fertilizer-yield records were openly available for this pilot.

### Generation Process
1. Published yield averages for each crop-district pair were used as target means
2. Soil nutrient ranges were sampled from published Soil Health Card summaries for Kolhapur-Ajara
3. For Jalgaon BANANA/COTTON, soil-nutrient ranges were **extrapolated** (not sourced from Jalgaon-specific samples)
4. Fertilizer response curves were calibrated to match published nutrient-response relationships
5. Gaussian noise was added to simulate real-world variability

### Dataset Size
| Crop | Training Samples | Hold-out Test Samples |
|------|-----------------|----------------------|
| BANANA | 120 | 30 |
| COTTON | 240 | 60 |
| SOYBEAN | 120 | 30 |
| SUGARCANE | 240 | 60 |

## Performance Metrics (Real Data Hold-out)

| Crop | MAE (kg/ha) | RMSE (kg/ha) | R² | Mean Actual Yield (kg/ha) | MAE % of Mean |
|------|-------------|--------------|-----|--------------------------|---------------|
| BANANA | 2,717.4 | 3,381.9 | 0.9246 | 31,843 | 8.5% |
| COTTON | 109.6 | 134.7 | 0.9176 | 1,332 | 8.2% |
| SOYBEAN | 107.6 | 135.6 | 0.9034 | 1,253 | 8.6% |
| SUGARCANE | 5,553.5 | 6,862.5 | 0.9190 | 67,601 | 8.2% |

**IMPORTANT**: These metrics are computed on a hold-out set generated from real Kolhapur soil distributions. They reflect how well the model fits the real soil data generation process, **NOT** real-world farm accuracy. Real farm accuracy has not been validated against actual farm outcomes.

## Limitations & Risks

### 1. Real Data Training (with limitations)
The model was retrained using real Kolhapur soil test data from Polgaon village (231 records, 2016-2024) and published district yield averages. The training set combines real soil distributions with fertilizer response curves calibrated to published MAHAFPDF/ICAR data. **However, real paired (soil + fertilizer + yield) farm records are still not available** — the Polgaon dataset contains soil tests but no linked yield outcomes. The model's predictions should be treated as informed estimates, not validated farm accuracy.

### 2. Extrapolation Risk
If a fertilizer plan applies nutrients at rates outside 40–130% of the Recommended Dose of Fertilizer (RDF), the model's prediction is an **extrapolation** beyond its training range. The API response includes an `extrapolation` boolean flag and a caveat when this occurs.

### 3. Geographic Coverage
Only Kolhapur and Jalgaon are supported. The model must not be used to extrapolate to other regions without new calibration data.

### 4. Soil-P Proxy
The model uses original soil-P proxy features. The current fertilizer ledger converts elemental P to P₂O₅. Model features are preserved to match training, but this conversion introduces a known approximation.

### 5. Jalgaon Soil-Nutrient Extrapolation
For Jalgaon BANANA and COTTON, soil-nutrient ranges in the training data were extrapolated from Kolhapur-Ajara samples, not from Jalgaon-specific Soil Health Cards.

### 6. No Farmer-Declared Target Yield
The model bands predictions relative to the crop's training-set mean, not relative to a farmer-declared target yield (which is not yet in scope).

## Real Data Integration

The system now incorporates real Kolhapur data:

| Data Source | Description | Location |
|-------------|-------------|----------|
| Polgaon Soil Health Dataset | 100+ real soil test records (2016-2024) with N, P, K, pH, OC, micronutrients | `data/real_kolhapur/soil_tests/polgaon_soil_health.csv` |
| SHC Nutrient Dashboard 2023-24 | Block-wise nutrient distribution for all 12 Kolhapur blocks | `data/real_kolhapur/nutrient_dashboard/2023-24.csv` |
| SHC Nutrient Dashboard 2024-25 | Block-wise nutrient distribution for all 12 Kolhapur blocks | `data/real_kolhapur/nutrient_dashboard/2024-25.csv` |
| SHC Nutrient Dashboard 2025-26 | Block-wise nutrient distribution for all 12 Kolhapur blocks | `data/real_kolhapur/nutrient_dashboard/2025-26.csv` |
| Shirol Farmer Survey | 47 real farmer records with land area, crop, fertilizer practices | `data/real_kolhapur/farmer_survey/shirol_farmer_survey.csv` |
| Village Geocodes | 20 villages in Shirol area with lat/lon | `data/real_kolhapur/villages/village_geocode.csv` |

The `get_kolhapur_soil_context()` helper in `app/core/kolhapur_context.py` provides regional grounding for recommendations.

## Confidence Score

The model returns a `confidence` score derived from the crop-model's own held-out R²:

| R² Range | Confidence |
|----------|-----------|
| >= 0.75 | 0.75 |
| 0.50 – 0.74 | 0.55 |
| < 0.50 | 0.35 |

This is intentionally coarse (three bands) rather than a false-precision decimal. It reflects the model's own fit quality, not the certainty of any individual prediction.

## Safety Boundaries

1. **Read-only**: The model never writes to the database or modifies plan quantities.
2. **One-way boundary**: The Ledger plan flows into the yield estimate. No ML output flows back into `plan_kg_ha`, fertilizer computation, or ledger confidence.
3. **Abstention**: The model abstains (returns `predicted_yield_kg_ha: null`) for unsupported crops, districts, irrigation types, or missing inputs.
4. **Extrapolation flagging**: When nutrient rates fall outside 40–130% of RDF, the response includes `extrapolation: true` and a descriptive caveat.

## Real vs Synthetic

| Component | Status |
|-----------|--------|
| Model architecture (XGBoost) | Real |
| Training data | Synthetic (calibrated to published averages) |
| Metrics | Computed on synthetic hold-out only |
| Real farm accuracy | **Not yet validated** |
| Fertilizer quantities | Always from deterministic Ledger, never from this model |

## Future Work

- Collect real farm-level paired fertilizer-yield data for Kolhapur and Jalgaon
- Retrain with real data when available
- Expand crop and district coverage
- Add farmer-declared target yield for personalized banding
- Validate model predictions against actual farm outcomes
