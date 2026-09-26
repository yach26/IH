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
- [ ] FastAPI app with `/fields/{id}/twin` and `/fields/{id}/recommend`
- [ ] Pydantic models for TwinState and Recommendation
- [ ] Basic error / abstain responses

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
- [ ] OCR pipeline + farmer confirmation
- [ ] Soil report upload endpoint

## Phase 4 — Frontend
- [ ] Next.js PWA skeleton
- [ ] Farmer dashboard (wireframe match)
- [ ] Why-this-plan expandable view
- [ ] What-If simulator UI
- [ ] Alert display for plan invalidation
- [ ] Agronomist simple dashboard

## Phase 5 — Polish & Demo
- [ ] Visual Growth Simulator (optional wow)
- [ ] Docker Compose
- [ ] End-to-end demo script
- [ ] Documentation update (`00_CONTEXT.md`)
- [ ] Judge pitch alignment

---

**Rule**: Never move to the next phase until the previous phase’s core path is working and tested.
