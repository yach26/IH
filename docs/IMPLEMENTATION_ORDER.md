# AgroTwin AI — Exact Hackathon Implementation Order

Use this as the living backlog. Check items off as they are completed.

## Phase 0 — Foundation (Done)
- [x] Digital Twin schema (SQLite)
- [x] Nutrient Ledger executable (`ledger.py`)
- [x] Seed data + 8 synthetic farms
- [x] Traceability + flags + confidence rules
- [x] Banana density resolution

## Phase 1 — Core Service
- [x] Package ledger + schema into clean Python package
- [x] FastAPI app with `/fields/{id}/twin` and `/fields/{id}/recommend`
- [x] Pydantic models for TwinState and Recommendation
- [x] Basic error / abstain responses

## Phase 2 — Agents
- [x] Soil Agent
- [x] Crop Agent
- [x] Weather Agent (with synthetic injection)
- [x] Orchestrator (pure Python state machine)
- [x] Validation Agent
- [x] Monitoring Agent + event bus
- [x] Heavy-rain → re-plan path (demo wow)

## Phase 3 — Evidence & OCR
- [x] Minimal RAG ingestion + hybrid retrieval
- [x] Knowledge Agent
- [x] OCR pipeline + farmer confirmation
- [x] Soil report upload endpoint

## Phase 4 — Frontend
- [ ] Next.js PWA skeleton
- [ ] Farmer dashboard (wireframe match)
- [ ] Why-this-plan expandable view
- [ ] What-If simulator UI
- [ ] Alert display for plan invalidation
- [ ] Agronomist simple dashboard

## Phase 5 — Polish & Demo
- [ ] Visual Growth Simulator (optional wow)
- [x] Docker Compose
- [x] End-to-end demo script (`scripts/demo_heavy_rain.py` + `POST /events`)
- [x] Documentation update (`00_CONTEXT.md`) — pipeline / optimizer / events slice
- [ ] Judge pitch alignment

---

**Rule**: Never move to the next phase until the previous phase’s core path is working and tested.
