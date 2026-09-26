# 15 — Deployment, MVP Scope & Implementation Order

## Tech Stack Summary (Hackathon)

| Layer | Choice |
|-------|--------|
| Frontend | Next.js + Tailwind + PWA |
| Backend | Python, FastAPI, Pydantic |
| Agent Orchestration | Pure state machine first, LangGraph later if needed |
| ML | scikit-learn / XGBoost (only if data supports it) |
| Optimization | Current heuristic → SciPy / OR-Tools later |
| RAG | sentence-transformers + BM25 + FAISS/Chroma |
| Database | SQLite (dev) → PostgreSQL |
| Queue / Events | Redis or in-process for demo |
| OCR | PaddleOCR / EasyOCR |
| Weather | Any reliable API + synthetic injection |
| Deployment | Docker Compose |

---

## MVP Scope (Hackathon Priority)

**Must have**
- Digital Twin + Nutrient Ledger (already done)
- FastAPI exposing twin + recommend
- Six agents + Orchestrator (narrow responsibilities)
- Event-driven monitoring (at least the heavy-rain path)
- Proof-carrying recommendations
- Basic farmer dashboard
- Soil report OCR + confirmation
- What-If simulator
- Minimal RAG over trusted docs
- Agronomist simple review view

**Explicitly out of scope for MVP**
- Full multi-objective optimizer
- Satellite / NDVI pipeline
- IoT hardware
- Marketplace / ordering
- Disease detection
- Production-grade auth / multi-tenancy

---

## Exact Implementation Order

1. Harden existing ledger (already mostly done)
2. Package the core (`app/core/ledger.py`, schema, seed)
3. FastAPI skeleton with `/twin` and `/recommend` using current ledger
4. Soil + Crop + Weather agents (read-only first)
5. Orchestrator that sequences them + calls ledger
6. Validation Agent + confidence rules
7. Event bus + Monitoring Agent + heavy-rain demo path
8. Knowledge Agent + minimal RAG
9. OCR pipeline + confirmation flow
10. Farmer dashboard (Next.js)
11. What-If endpoint + UI
12. Visual growth simulator (nice-to-have wow)
13. Agronomist dashboard
14. Docker Compose for one-command demo
15. Polish demo script that walks the complete story

---

## Demo Data Strategy

- Keep the 8 synthetic records as the core demo set.
- For weather: live API when possible + synthetic injection button.
- For RAG: small curated set of MPKV/ICAR markdown/PDF chunks.
- For OCR: 2–3 sample soil report images with known ground truth.
- Clearly label any simulated data in the UI.

---

## Testing Strategy

- Unit tests for ledger (already partially covered by `run_demo.py`)
- Unit tests for each agent
- Integration test: full recommend → rain event → re-plan
- Manual demo checklist matching the Complete Demo Story in the master brief

---

## Likely Bottlenecks & Mitigations

| Bottleneck | Mitigation |
|------------|------------|
| Agronomic data gaps | Flag + abstain; never invent |
| OCR accuracy | Always require farmer confirmation |
| Weather API reliability | Synthetic injection for demo |
| LLM cost / latency | Use only for explanation & RAG; keep calculation deterministic |
| Team coordination | Strict use of `00_CONTEXT.md` + these implementation docs |

---

## Final Judge-Facing Justification

Every major architectural decision must answer:

> “What happens after we give the farmer the first recommendation?”

Answer:  
**We remember. We monitor. We detect. We re-evaluate. We explain. We validate.**
