# feat: database schema + multi-agent foundation

## Overview

This PR implements Phase 1 (Core Service foundations) + Phase 2 (Agents) of the AgroTwin AI development plan, strictly following docs `03_DATABASE_SCHEMA.md` and `04_MULTI_AGENT_ARCHITECTURE.md`.

## What's Changed

### 1. Database Schema (`schema_sqlite.sql`)

**Upgraded** with full Phase-2 tables while keeping all existing tables and columns unchanged (backward compatible with existing `agrotwin.db`):

| New Table | Purpose |
|-----------|---------|
| `field_crops` | One active crop-season per field — enables Crop Agent reads |
| `weather_snapshots` | Cached Open-Meteo forecasts with alert flags |
| `events` | Typed event bus records (`HEAVY_RAIN_ALERT`, `SOIL_REPORT_UPDATED`, …) |
| `audit_log` | Extended with `actor`, `old_value`, `new_value` for full traceability |

**Enhancements to existing tables:**
- `recommendations`: added `invalidated_at` + `superseded_by` (Monitoring Agent lifecycle)
- `soil_tests`: added `moisture_percent`, `micronutrients`, `ocr_confidence`, `original_file_path`
- `fields`: added `lat`, `lon` columns (needed by Weather Agent)
- `nutrient_ledger_entries`: added `flags` + `confidence` JSON columns
- Added `CHECK` constraints on pH, NPK values
- Added indexes on `(field_id, created_at DESC)` for "latest plan" lookups

**New file:** `schema_postgres.sql` — production-ready PostgreSQL DDL with UUID PKs, JSONB, TIMESTAMPTZ, and PostGIS hook (matches SQLite 1:1).

### 2. App Package Structure (`app/`)

```
agrotwin_api/app/
├── __init__.py           ← NEW: package marker
├── ledger.py             ← NEW: thin adapter around root ledger.py
└── agents/
    ├── __init__.py       ← UPDATED: exports TwinState
    ├── twin_state.py     ← NEW: shared TwinState TypedDict + compute_confidence()
    ├── soil_agent.py     (existing, unchanged)
    ├── crop_agent.py     (existing, unchanged)
    ├── weather_agent.py  (existing, unchanged)
    ├── knowledge_agent.py (existing, unchanged)
    ├── validation_agent.py (existing, unchanged)
    ├── monitoring_agent.py (existing, unchanged)
    ├── orchestrator.py   (existing, unchanged)
    └── optimizer.py      (existing, unchanged)
```

### 3. Shared TwinState (`app/agents/twin_state.py`)

Implements the TypedDict from doc 04:
```python
class TwinState(TypedDict):
    field_id, region_id, soil, crop, weather, history,
    current_plan, flags, confidence, events, evidence, data_quality
```
Includes `make_empty_twin_state()` factory and `compute_confidence()` helper that downgrades `HIGH → MEDIUM → LOW` based on material flags, correctly ignoring informational-only flags (`OPTIMIZER_*`, `NO_COORDINATES`).

### 4. App Ledger Adapter (`app/ledger.py`)

A thin bridge so `from app import ledger` works consistently across all app code. Key functions:
- `run_field_ledger(conn, field_row)` — wraps root `ledger.run_field()`, reads from `field_active_crop` view
- `write_ledger_result(conn, result)` — persists `nutrient_ledger_entries` + `recommendations` rows

**Critical:** No new fertilizer equations. All quantities still originate from `ledger.py` (root).

### 5. Unit Tests (`tests/test_agents.py`)

**40 tests** covering all six agents, TwinState, ledger adapter, and orchestrator integration:

| Class | Tests |
|-------|-------|
| `TestSoilAgent` | context fetch, fresh/stale detection, ABSTAIN on missing test, write_soil_test |
| `TestCropAgent` | context fetch, ABSTAIN on no crop, stage calendar validation, days_after_planting |
| `TestWeatherAgent` | no-coords → no alert, mock no-rain, mock heavy rain → alert, DB storage |
| `TestKnowledgeAgent` | list return, empty query, never returns kg/ha prescription keys |
| `TestValidationAgent` | valid plan, ABSTAIN propagation, WEATHER_CONFLICT blocking, pH warnings |
| `TestMonitoringAgent` | event bus, get_alerts, supersede_and_replan marks SUPERSEDED |
| `TestTwinState` | structure, confidence logic, flag downgrade rules |
| `TestAppLedger` | plan production, ABSTAIN on missing crop, write_ledger_result DB row |
| `TestOrchestratorIntegration` | full run (no rain), heavy rain → blocking validation, NO_FERTILIZER_NEEDED path |

**No network calls** — weather uses `mock_snapshot`. **No LLM** invocations anywhere.

### 6. Requirements (`requirements.txt`)

```
fastapi>=0.111.0 | uvicorn | pydantic>=2.0.0
requests>=2.31.0
scipy>=1.12.0 | numpy>=1.26.0
rank-bm25>=0.2.2
pytest>=7.4.0 | httpx>=0.27.0
```

---

## Testing Instructions

```bash
cd agrotwin_api
pip install -r requirements.txt
python -m pytest tests/test_agents.py -v
```

Expected: **all tests pass**. Zero network calls. Zero LLM invocations.

To also verify the existing ledger still works:
```bash
python run_demo.py
```

---

## Global Constraints Honoured

| Constraint | How enforced |
|------------|-------------|
| LLM never generates kg/ha numbers | `app/ledger.py` delegates to root `ledger.py` equations only |
| Every number traceable | `source_citation` required in DB; flags on every derived value |
| Existing schema/ledger not broken | Only additive schema changes; `run_demo.py` still works |
| Agents have narrow responsibilities | Each agent tested in isolation; structural source-inspection tests assert agents don't contain fertilizer math |
| Graceful ABSTAIN | Every agent returns `None` or `{"status": "ABSTAIN"}` when inputs missing |

---

## Non-Goals (Not in this PR)

- Full recommendation pipeline endpoint (Phase 2 → FastAPI routes)
- Real RAG retrieval (Knowledge Agent is BM25 stub)
- Event bus persistence / async queue (MonitoringAgent is synchronous in-process)
- Frontend / OCR / Optimizer UI
