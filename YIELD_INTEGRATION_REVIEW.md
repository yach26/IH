# Yield integration investigation — 2026-09-27

This document records the pre-integration investigation. The user subsequently authorized proceeding ("i want the model working anyhow"). Integration is now complete; see `YIELD_INTEGRATION_RESULT.md`. The proposed external model location below was replaced with a self-contained repository bundle under `agrotwin_api/ml`.

## Baseline

Active FastAPI project: `IH/agrotwin_api`; the workspace-root `agrotwin_api` is an older copy without the current API routes/tests. ML source: `temp/agrotwin_ml`.

Command, run from `IH` before integration:

```text
python -m pytest agrotwin_api/tests backend/tests -q
........................................................................ [ 73%]
..........................                                               [100%]
98 passed, 1 warning in 21.52s
```

Full captured output: `yield_baseline.txt`. Existing warnings concern pytest-asyncio's unset fixture-loop scope and Starlette/httpx deprecation. PowerShell's native stderr redirection reported an error wrapper despite pytest reporting all tests passed.

Standalone check: `python temp/agrotwin_ml/src/inference.py` exited 0. Sugarcane example returned OK, 105293.6 kg/ha, confidence 0.55, with the synthetic-data caveat. RICE returned ABSTAIN with null yield. XGBoost emitted an older-serialization compatibility warning; successful smoke inference does not establish original training versions.

## Files inspected

All Python files under `agrotwin_api/app` were read:

- Root: `__init__.py`, `main.py`, `pipeline.py`, `ledger.py`.
- API: `__init__.py`, `routes.py`, `schemas.py`.
- Agents: `__init__.py`, `crop_agent.py`, `knowledge_agent.py`, `monitoring_agent.py`, `optimizer.py`, `orchestrator.py`, `rag_validation_agent.py`, `report_agent.py`, `soil_agent.py`, `soil_report_agent.py`, `twin_state.py`, `validation_agent.py`, `weather_agent.py`.
- Core: `__init__.py`, `event_bus.py`, `events.py`, `ocr.py`, `optimizer.py`, `proof.py`, `region_config.py`, `rules.py`, `what_if.py`.

Also read the root ledger, SQLite schema, dependency files, test fixture setup, and ML README, inference, features, training, synthetic generator, and metadata. Queried the actual SQLite database read-only.

## Actual API

GET `/health`, `/fields/{field_id}/twin`, `/fields/{field_id}/recommendations/latest`, `/fields/{field_id}/alerts`.

POST `/fields/{field_id}/recommend`, `/events`, `/fields/{field_id}/soil-report/upload`, `/fields/{field_id}/soil-report/confirm`, `/fields/{field_id}/what-if`, `/fields/{field_id}/override`.

Field references accept numeric IDs or field codes. RecommendationOut allows extra fields, but a separate derived-info GET endpoint is a smaller integration boundary.

## Schema and join points

`RecommendationPipeline.run()` calls `app.ledger.run_field_ledger(conn, field_row)`, which delegates to root `ledger.run_field()`. Successful results contain record_id, field_id, crop, recommendation_type, current_stage, status, required, **soil** (not soil_test), gap, plan_kg_ha, confidence, flags, citation, recommendation_notes, and the adapter-added field_code.

`fields` stores district_id and irrigation_type; district strings come from `districts`. Codes are KOLHAPUR/JALGAON; district_name is already Kolhapur/Jalgaon, matching inference exactly. Current crop comes from field_crops/crops through field_active_crop. Soil values, pH, and organic carbon come from the latest soil_tests row, ordered by test_date and soil_test_id descending. Irrigation strings in the database match the model's accepted categories.

The supplied application database has **no field_crops rows**, so its demo fields currently have no active crop. Existing tests seed their own complete fixtures. The actual database also lacks soil_report_uploads, which exists in the schema file. Do not reseed or migrate this existing database implicitly.

The README example incorrectly assigns required RDF nutrient values to applied nutrient values. Applied N/P2O5/K2O must instead be derived from actual plan product kg/ha multiplied by fertilizer_products composition percentages. Exclude the diagnostic n_supplied_by_dap_kg_ha key to avoid double-counting. Preserve required_* from the ledger's RDF lookup. Keep the existing P-proxy caveat visible.

Weather snapshots and WeatherAgent supply rainfall_mm_next_7d, not rainfall_mm_season. There is no seasonal rainfall source in the current integration path. A seven-day forecast cannot substitute for a season total.

## ML contract and limitations

`predict_yield(soil: dict, crop: str, weather: dict, fertilizer_plan: dict) -> dict` takes district, n_kg_ha, p_kg_ha, k_kg_ha, ph, oc_percent; crop; rainfall_mm_season and irrigation_type; and applied/required N, P2O5, K2O kg/ha. It returns status, predicted_yield_kg_ha, yield_band, confidence, model_version, reason, and caveats. ABSTAIN means no supported estimate, not an API failure. Never discard caveats or merge yield confidence into ledger confidence.

Inference imports `features` as a top-level module, so the README's package import needs adapting. Model loading occurs before scope checks and imports ML dependencies eagerly; isolate loading in the new service. The standalone implementation does not comprehensively reject invalid numeric inputs, so the adapter must validate finite, nonnegative values and missing inputs.

All training rows are synthetic. Metrics measure recovery of that synthetic process, not farm accuracy. Jalgaon soil ranges are extrapolated; exact STCR coefficients were unavailable; nutrient uptake efficiencies are approximate; water response omits moisture retention, drainage, and rainfall timing. Coverage is four pilot crops and two districts, with retraining needed on real paired records. The generator samples applied fertilizer at 40–130% of RDF; actual ledger gap plans can fall outside this range, including zero K. Surface this additional extrapolation caveat rather than silently representing every gap plan as within training coverage.

## Dependencies

The API requirements use lower bounds, not exact pins: fastapi>=0.111.0, pydantic>=2.0.0, scipy>=1.12.0, numpy>=1.26.0. The RAG backend uses numpy>=1.24.0. The supplied ML package has no requirements/lock file and metadata records no library versions.

Installed and inspected: FastAPI 0.141.1, Pydantic 2.10.4, NumPy 1.26.4, SciPy 1.17.1, pandas 2.2.3, joblib 1.5.3, scikit-learn 1.8.0, XGBoost 3.2.0, pytest 8.3.4. These are current runtime versions, **not verified training versions**. pandas is also necessary despite being omitted from the requested dependency list.

## Concrete proposed integration, pending approval

1. Add GET `/fields/{field_id}/yield-estimate?rainfall_mm_season=...`. Require an explicit, finite season-total rainfall value for prediction; return a structured ABSTAIN when missing. Never invent rainfall or use a seven-day value as a season total.
2. Compute the existing ledger fresh without persistence and return its unchanged result alongside a separate yield_prediction object. Resolve district_name and latest soil values from existing tables. Missing crop/soil/requirements gives a reasoned abstention. No schema changes or implicit database seeding.
3. Add an isolated service and worker with bounded execution time, lazy ML imports, independent input copies, exception logging, and UNAVAILABLE on missing artifacts, runtime failure, or timeout. Existing recommendation endpoints do not call this service. Mark the one-way Ledger-to-ML boundary explicitly.
4. Use one configured ML root, initially the supplied `temp/agrotwin_ml`, keeping models and metadata together without duplicate artifacts. Document deployment configuration so a checkout of IH alone is not mistaken for containing the external model.
5. If original training pins cannot be supplied, validate and explicitly label exact runtime pins as compatibility-tested rather than training-matched. Preserve existing framework requirements; include pandas. Investigate the XGBoost serialization warning before claiming compatibility is settled.
6. Add integration tests for a real estimate, unsupported scope, missing model, timeout/failure, missing/invalid inputs, confidence/caveat preservation, nutrient conversion, no database writes, and identical fertilizer quantities. Re-run the exact 98-test baseline unchanged, then the new tests. Carry all honest limitations into API documentation.

Proposed capability: AgroTwin will estimate the yield associated with its existing fertilizer plan when soil, crop, irrigation, and seasonal rainfall inputs are available. The estimate will clearly identify its synthetic-data limitations and separate confidence; unsupported inputs or model failures will leave the existing fertilizer recommendation intact.
