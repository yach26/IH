# Yield integration result

Historical pre-Groq validation; see `GROQ_MERGE_VALIDATION.md` for the current
merged ledger conversion, demo results, and additional checks.

Implemented and validated on main. This report accompanies the yield integration commit.

## Changes

Existing files touched:
- `agrotwin_api/app/api/routes.py`: add Query import and one read-only yield-estimate route.
- `agrotwin_api/requirements.txt`: pin NumPy to the existing installed 1.26.4 and add exact compatibility-tested XGBoost/joblib/scikit-learn/pandas versions. Original training pins were unavailable.
- `agrotwin_api/README.md`: endpoint, demo commands, separate confidence, failure behavior, and limitations.

New files:
- `agrotwin_api/app/yield_prediction.py`: ledger-to-model adapter, actual nutrient conversion, validation, separate confidence/caveats, bounded worker slots, timeout and failure isolation.
- `agrotwin_api/ml/worker.py`: disposable inference process, independent of the API's imports and mutable state.
- `agrotwin_api/ml/src/{inference,features}.py`, `ml/models/{yield_model.joblib,model_metadata.json}`: supplied trained bundle copied byte-for-byte into one canonical deployment location. SHA-256 comparisons verified all four match the supplied originals. Original external source files were preserved.
- `agrotwin_api/ml/README_SOURCE.md`, `ml/README.md`: source provenance and complete limitations/runtime notes.
- `agrotwin_api/scripts/demo_yield.py`: real API inference and optional HTTP server on a separate temporary seeded demo DB.
- `agrotwin_api/tests/test_yield_prediction.py`: 12 integration cases.

No ledger equations, original tests, schemas, existing database, or recommendation pipeline were changed.

## Validation

Exact command, run from IH before and after implementation:

```text
python -m pytest agrotwin_api/tests backend/tests -q
Before: 98 passed, 1 warning in 12.89s
After: 110 passed, 1 warning in 17.46s
```

Full output is in `yield_baseline_main.txt` and `yield_after_integration.txt`. All original 98 tests remained unchanged. New tests check real inference, immutable ledger quantities and confidence, zero database writes, product-to-nutrient conversion, unsupported crop/district/irrigation, missing model, timeout/exception, incomplete inputs, invalid rainfall, and unknown fields. `git diff --check` passes.

`python scripts/demo_yield.py` succeeded through FastAPI TestClient with a real model invocation: SYN-003, explicit example rainfall 1100 mm, yield 98993.2 kg/ha, status OK, yield confidence 0.55. Ledger quantities remained DAP 293.5, UREA 167.8, MOP 0.0 kg/ha. Synthetic-data, P-proxy, and fertilizer-rate extrapolation caveats were returned.

## Run

From `IH/agrotwin_api`:

```text
python scripts/demo_yield.py --serve
```

Open `http://127.0.0.1:8000/fields/SYN-003/yield-estimate?rainfall_mm_season=1100` or `/docs`. This prepares crop assignments in its own temporary database, leaving the existing database untouched. For an existing deployment, the same endpoint is available under the normal `app.main:app`; fields need active crops and complete soil data. Seasonal rainfall must be explicitly supplied.

## Capability and limits

AgroTwin now estimates yield for the fertilizer plan produced by its existing Nutrient Ledger. It combines the actual supplied nutrients with soil, crop, irrigation, and caller-supplied seasonal rainfall, then returns predicted kg/ha with separate confidence and visible caveats. Model failures cannot modify the fertilizer plan or break existing recommendation endpoints. This is a synthetic-data demonstration, not validated farm accuracy. The supplied artifact still emits an older-XGBoost serialization warning, recorded in logs; local compatibility tests pass, but original training-version provenance remains unavailable.
