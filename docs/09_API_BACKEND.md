# 09 — API Backend (FastAPI)

## Goal

Expose the Digital Twin + Ledger + Agents as a clean HTTP API so the frontend (and future mobile clients) can interact without knowing internal details.

---

## Suggested Stack

- FastAPI + Pydantic v2
- SQLAlchemy / asyncpg (or keep SQLite for MVP)
- Redis for events / cache (optional for first demo)
- Uvicorn

---

## Core Endpoints (MVP)

```
POST   /farmers                          # create farmer
POST   /fields                           # create field (with region_id)
GET    /fields/{field_id}/twin           # current Digital Twin state
POST   /fields/{field_id}/soil-report    # upload + OCR trigger
POST   /fields/{field_id}/recommend      # run full recommendation pipeline
GET    /fields/{field_id}/recommendations/latest
POST   /fields/{field_id}/what-if        # sensitivity simulation
POST   /events                           # inject event (demo / weather webhook)
GET    /fields/{field_id}/alerts
POST   /fields/{field_id}/override        # expert override
GET    /health
```

All responses that contain a plan must follow the proof-carrying contract defined in `01_PROJECT_OVERVIEW.md`.

---

## Pydantic Models (minimum)

```python
class SoilTestIn(BaseModel):
    n_kg_ha: float | None
    p_kg_ha: float | None
    k_kg_ha: float | None
    ph: float | None
    test_date: date
    source: Literal["lab", "ocr", "manual"]

class RecommendationOut(BaseModel):
    status: str
    what: str | None
    how_much: dict | None
    when: str | None
    why: dict | None
    based_on: dict | None
    confidence: str
    flags: list[str]
    data_quality: dict

class WhatIfRequest(BaseModel):
    fertilizer_delta_pct: float | None = None
    rainfall_mm: float | None = None
    # ... other levers
```

Never return raw LLM text as the plan.

---

## Implementation Order

1. Lift `ledger.py` + schema into a proper package under `app/core/`.
2. Create FastAPI app with the twin + recommend endpoints (still using the current heuristic).
3. Add simple API-key or no-auth for hackathon.
4. Wire the Orchestrator behind `/recommend`.
5. Add event injection endpoint for the demo wow moment.
6. Add OCR upload endpoint (see `11_OCR_PIPELINE.md`).

---

## Checklist

- [x] `app/main.py` with lifespan (DB connection, event bus).
- [x] Routers split by domain (farmers, fields, recommendations, events). *(MVP: single `app/api/routes.py` with fields + events + health)*
- [x] Dependency injection for DB session and Orchestrator.
- [x] OpenAPI docs automatically generated and useful. (`/docs`)
- [x] Error responses include abstain reasons when applicable. (`status: ABSTAIN` + `required_actions`)
- [x] CORS configured for the frontend.

Remaining (not this slice): farmer CRUD, OCR upload, what-if, agronomist override.
