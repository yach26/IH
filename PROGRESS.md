# AgroTwin AI — Progress & Running Audit Log

## Standard of Honesty
Every change, verified run, and stubbed feature is tracked here following the project's strict conventions (flags, citations, `ENGINEERING_DEFAULT` labels for unsourced assumptions).

---

## 1. Repository Cleanup & Canonical Backend
- [x] **Archive Superseded Prototype**: `agrotwin_prototype/` moved to `archive/agrotwin_prototype/` with notes in root `README.md`.
- [x] **Canonical Backend**: `agrotwin_api/` is the single application backend.
- [x] **Dependencies Updated**: Added `python-multipart>=0.0.9` and `psycopg[binary]>=3.1.18` to `agrotwin_api/requirements.txt`.

---

## 2. Database ID-Scheme Architecture Decision
- **Decision**: Keep `SERIAL` integer primary keys in PostgreSQL matching `schema_sqlite.sql`.
- **Rationale**: The entire application layer (`routes.py`'s `_field_row`, `isdigit()` routing, ledger methods, agent state, and queries) was written assuming integer primary keys (`field_id`, `crop_id`, `soil_test_id`, `recommendation_id`). Adopting UUIDs would require disruptive rewrites across dozens of call sites without agronomic benefit.
- **Action Implemented**: Updated `schema_postgres.sql` to use `SERIAL PRIMARY KEY` and integer foreign keys matching `schema_sqlite.sql` exactly 1:1.
- **Drift Guard**: Added synchronized headers to both `schema_sqlite.sql` and `schema_postgres.sql` stating they must remain structurally identical.

---

## 3. Seed Data & Crop Assignment Endpoint
- [x] **Seed Data Fixed**: Updated `seed_data.py` so that all 8 synthetic records (`SYN-001` through `SYN-008`) populate the `field_crops` table with their crop code, variety, sowing date, current stage, and recommendation type (`RECOMMENDATION_TYPE_BY_RECORD`). Fresh seeding no longer ABSTAINs on `/recommend`.
- [x] **New Endpoint**: Added `POST /fields/{id}/crop` to `app/api/routes.py` with `CropAssignRequest` schema. Clients can assign or update a field's active crop, variety, sowing date, and growth stage, emitting a `CROP_STAGE_CHANGED` event on the bus.

---

## 4. Soil Report OCR Wiring
- [x] **Replaced Mock OCR**: Replaced the hardcoded mock in `app/core/ocr.py` with `app/agents/soil_report_agent.py` in `POST /fields/{id}/soil-report/upload`.
- [x] **Real Extraction & Review**: Uploaded reports now extract real NPK, pH, OC, EC values using regex over text/bytes, calculate per-field confidence, and flag fields needing review (<0.85).
- [x] **PDF & EasyOCR Support**: Enhanced `_try_ocr()` in `soil_report_agent.py` with PDF text extraction and tempfile-backed EasyOCR execution when available.
- [x] **Farmer Confirmation**: Wired `POST /fields/{id}/soil-report/confirm` to update the digital twin only after confirmation, and publish `SOIL_REPORT_UPDATED`.

---

## 5. Selectable Optimizer (Heuristic & Linprog)
- [x] **Linprog Optimizer Implemented**: Added `ScipyLinprogOptimizer` to `app/core/optimizer.py` implementing the `Optimizer` protocol and delegating to `app/agents/optimizer.py` (solving LP via SciPy `highs` solver).
- [x] **Selectable in Pipeline & API**: Made optimizer selectable in `RecommendationPipeline.run` and `POST /fields/{id}/recommend` (`optimizer="heuristic"` or `"linprog"`). Default remains the explainable heuristic DAP→Urea→MOP.

---

## 6. Hybrid RAG Integration
- [x] **Merged RAG Engine**: Copied `backend/rag` (ingestion module and markdown doc pack: `mpkv_icar_rdf.md`, `jalgaon_rdf.md`, `fco_fertilizer_spec.md`, `crop_calendars.md`) into `agrotwin_api/rag`.
- [x] **Knowledge Agent Updated**: Refactored `agrotwin_api/app/agents/knowledge_agent.py` to use `HybridIndex` (BM25 + dense fallback) over `rag/docs/`. Queries now return real evidence citations and topically relevant text excerpts for Banana, Sugarcane, Cotton, and Soybean.

---

## 7. Database Abstraction Layer (SQLite & NeonDB Postgres)
- [x] **Unified DB Layer (`app/db.py`)**: Supports both SQLite (local development and fast unit testing) and PostgreSQL / NeonDB (serverless cloud Postgres), switched automatically when `DATABASE_URL` is set.
- [x] **Query & Row Adapter**: Automatically maps query parameters (`?` to `%s`), handles `cur.lastrowid` on Postgres inserts with `RETURNING`, and exposes dictionary row access.
- [x] **Dual-Mode Seed Script**: `seed_data.py` targets SQLite when `DATABASE_URL` is unset, and PostgreSQL when `DATABASE_URL` is provided.

---

## 8. Next.js Frontend Built
- [x] **Design Spec Compliance**: Minimalist light theme (#FAFAFA / #FFFFFF), WCAG AA high-contrast neutrals (#18181B / #52525B), calm agricultural green accent (#15803D), consistent confidence badges (HIGH, MEDIUM, LOW, ABSTAIN).
- [x] **Screens Implemented**:
  1. Main Dashboard: Living farm twin, crop metrics, soil NPK progress bars, active alerts.
  2. Proof-Carrying Recommendation: WHAT / HOW MUCH / WHEN / WHY / BASED ON WHAT / HOW SURE ARE WE.
  3. Evidence Viewer: Real RAG evidence chunks with citation links.
  4. What-If Simulator: Sliders for fertilizer delta % and 7-day rainfall forecast with side-by-side plan comparison.
  5. Soil Report OCR: File upload, per-field confidence preview, and farmer verification form.
  6. Crop Setup: Live assignment form for crop, stage, variety, and RDF recommendation pattern.
  7. Agronomist Oversight: Flagged recommendations and expert override form with audit trail.
- [x] **Tailwind & Tokens**: Custom tokens defined in `tailwind.config.ts` and `globals.css`.

---

## 9. Deployment Wiring
- [x] **Frontend Containerized**: Added `agrotwin_frontend/Dockerfile`.
- [x] **Docker Compose**: Updated `docker-compose.yml` to orchestrate both `api` (port 8000) and `frontend` (port 3000) with optional `DATABASE_URL`.
- [x] **Environment Template**: Created `.env.example` documenting all configuration keys.

---

## Verification & Status
- **Local SQLite Testing**: Ready for run via `seed_data.py` and `pytest`.
- **NeonDB Cloud Postgres**: Awaiting user's `DATABASE_URL` environment variable for real cloud verification.
