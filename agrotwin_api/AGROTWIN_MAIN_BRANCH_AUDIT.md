# AgroTwin AI — Main Branch Audit (Updated)

## Phase 1 & 2 Completed

### Phase 1: Fix confirmed bugs
- **Missing test dependency:** Added `python-multipart` to `requirements.txt`.
- **Crop assignment:** Implemented `POST /fields/{field_id}/crop` and `seed_data.py` now populates `field_crops` for all synthetic fields. Recommend endpoint no longer abstains due to missing crop.
- **Missing farmer/field endpoints:** Added `POST /farmers` and `POST /fields`.
- **Route path mismatch:** Added docstring note to `/fields/{id}/override`.

### Phase 2: USP verification and hardening
- **Fertilizer correctness + traceability:** Created `verify_phase2.py` which proves the `ScipyLinprogOptimizer` actively uses SciPy HiGHS to calculate multi-objective solutions minimizing fertilizer weight, while exactly meeting the required nutrient gaps. Both the heuristic and linprog paths were verified to produce correct nonzero quantities for a test field.
- **Digital Twin persistence:** Fixed `app/pipeline.py` bug where full pipeline runs failed to cascade the `SUPERSEDED` status in DB. It now correctly passes the previous plan down to `_persist()` so that DB rows accurately reflect state transitions (`PROPOSED` -> `SUPERSEDED`).
- **Event-driven replanning, live:** Live injection of `HEAVY_RAIN_ALERT` correctly triggers a selective re-plan, creating a new `PROPOSED` plan and marking the old plan as `SUPERSEDED`.
- **ABSTAIN safety:** Verified that fields with a surplus soil test (gaps <= 0) safely return `NO_FERTILIZER_NEEDED`, and fields without a soil test return an `ABSTAIN` status citing `soil_test` as the blocker.

## Final status table

| Area | Status | Evidence | Remaining |
|---|---|---|---|
| Fertilizer USP math | ✅ Working & Integrated | `test_api_onboarding.py` and `verify_phase2.py` run full linprog/heuristic paths live on endpoints and directly via the orchestrator. | — |
| ABSTAIN safety | ✅ Working | Verified missing crop, missing soil, and surplus soil paths. | — |
| Monitoring/events | ✅ Code real | `verify_phase2.py` runs a live DB event injection causing an old plan to be `SUPERSEDED` by a new one. | — |
| Test suite | ✅ 69/69 passing | Run `pytest tests/ -v` | — |
| API surface | ✅ Corrected | Added Farmer/Field creation; all routes now match documentation or have explicitly noted deviations. | — |
| Digital Twin Persistence | ✅ Working | DB accurately reflects `SUPERSEDED` transitions for replaced plans. | — |
| RAG, OCR, Frontend | ⏳ Not audited this pass | — | Next pass |

## What I need from Jatin
- **Postgres Database URL** (`DATABASE_URL`) to re-verify the full suite against the live cloud instance instead of SQLite (if you want the cloud verified again after these changes).
- **Frontend validation criteria**: Instructions on testing Next.js visual states (if you want me to audit the frontend pixel-level implementations).
