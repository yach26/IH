# AgroTwin AI — backend_v1 audit update 2

Repo checkout: `IH`, branch `backend_v1` (verified with `git branch --show-current`).

The pasted audit named this file as the report to update, but that file was not present in the checkout. The repo contained `agrotwin_api/AGROTWIN_MAIN_BRANCH_AUDIT.md`, a different main-branch report. This file records the requested update 2 results.

## Phase 0 results

### Test isolation and committed database

- `tests/test_api_onboarding.py` now imports and overrides `get_conn`, the exact dependency used by the routes.
- The override is installed by the per-test fixture. This was necessary because `tests/test_api_events.py` clears `app.dependency_overrides` during the full test run; setting the onboarding override at module import alone still left all nine onboarding tests using the real DB.
- Added `agrotwin_api/agrotwin.db` to `.gitignore` and removed the tracked DB. A clean run was made with no database file present.
- First clean suite run after changing the dependency target: **60 passed, 9 failed**. The failures revealed the cross-module override clearing described above.
- After moving the override into the per-test fixture: `python -m pytest tests/ -v` from `agrotwin_api/` reported **69 passed, 2 warnings, 0 failed**. Warnings were an upstream Starlette/httpx deprecation and pytest cache write permission warnings.

### Fresh seed and API smoke test

Commands run from `agrotwin_api/`:

```text
python seed_data.py
python -m uvicorn app.main:app --port 8010
```

`seed_data.py` reported all eight fields (`SYN-001` through `SYN-008`). Live GET `/fields/SYN-001/twin` returned the banana field and a populated soil test. Live POST `/fields/SYN-001/recommend` returned `PLAN_GENERATED`, with DAP 232.6 kg/ha and Urea 240.4 kg/ha. Its evidence included real excerpts cited from `jalgaon_rdf.md` and `crop_calendars.md`.

The recommendation quantities came from the deterministic optimizer pipeline. No LLM-derived fertilizer quantities were used.

## Phase 1 results

### RAG evidence

The live recommendation returned excerpts and citations from the merged documents, including `jalgaon_rdf.md#para-1`, `jalgaon_rdf.md#para-2`, `jalgaon_rdf.md#para-22`, and `crop_calendars.md#para-12`. The backend log reported: `Loaded 76 chunks from 4 documents` and `BM25 index built over 76 chunks`. These are retrieved source excerpts, not the former static placeholder.

### OCR confirmation and connection bug fix

- Uploaded a text soil report through `POST /fields/SYN-001/soil-report/upload`. It returned `PENDING_CONFIRMATION`, engine `regex_text`, confidence 0.92 for the five extracted values, and flagged missing `ec_ds_m` (confidence 0.0) in `fields_needing_review`.
- Confirmation initially returned HTTP 500 after a prior request left the singleton `MonitoringAgent` holding a closed SQLite connection. The soil row and event had been written before the exception.
- Fixed the upload-confirm route to bind the monitor to the request's live connection before publishing the event.
- Repeated the live flow after reseeding: recommendation returned HTTP 200; soil confirmation returned HTTP 200 and `CONFIRMED`; SQLite then showed two soil rows for field 1 and a persisted `SOIL_REPORT_UPDATED` event.

### SciPy optimizer

`python scripts/verify_phase2.py` reported **20 passed, 0 failed**. Its linprog path returned `PLAN_GENERATED`, optimizer ID `scipy_linprog`, and status `OPTIMAL`. It minimizes total fertilizer weight subject to nutrient gaps; the tested output was 800.3 kg/ha versus 800.2 kg/ha for the heuristic. This is an LP minimizing total weight, not a cost optimization: the reported INR cost is an engineering-default estimate, not the LP objective.

Live POST `/fields/SYN-001/recommend` with `{"optimizer":"linprog"}` also returned HTTP 200, `PLAN_GENERATED`, and `OPTIMAL` (DAP 232.6, Urea 240.5 kg/ha).

### Heavy-rain replan

- `python scripts/demo_heavy_rain.py` emitted `PLAN_CREATED`, `PLAN_INVALIDATED`, and `RECOMMENDATION_RECALCULATED`; its replan deferred application until after the heavy-rain window and retained the same ledger quantities. The demo uses an in-memory DB.
- Separately, a live `POST /events` heavy-rain injection for `SYN-001` returned HTTP 200. SQLite showed `PLAN_INVALIDATED` and `RECOMMENDATION_RECALCULATED` in `events`; the older recommendations were `SUPERSEDED` and a new recommendation was `PROPOSED`.

### Frontend

- `npm.cmd install` completed: 386 packages audited, 0 vulnerabilities.
- Started `npm.cmd run dev` with `NEXT_PUBLIC_API_URL=http://localhost:8010`. GET `http://127.0.0.1:3000/` returned HTTP 200 and HTML containing `AgroTwin`.
- Source inspection shows the fetch calls use `API_BASE` from `NEXT_PUBLIC_API_URL` (with localhost:8000 fallback). The active frontend test server was explicitly configured to use the verified backend on port 8010.
- Source inspection shows a light neutral palette, green accents, a centered page, and no sidebar. It exposes **five navigation tabs**: Dashboard & Plan, What-If Simulator, Soil Report OCR, Crop Assignment, and Agronomist Review. I did not use a browser screenshot, so pixel-level visual review is not verified; the requested seven-screen count was not evident in the navigation.

## Not verified / What I need from Jatin

- Live NeonDB/Postgres path: requires a `DATABASE_URL` and credentials. No value was available, so it was not tested.
- A screenshot-based visual audit, if the seven-screen requirement refers to views beyond the five navigation tabs found in source.

## Files changed in this pass

- `.gitignore`
- `agrotwin_api/tests/test_api_onboarding.py`
- `agrotwin_api/app/api/routes.py`
- Deleted tracked `agrotwin_api/agrotwin.db`
- This report
