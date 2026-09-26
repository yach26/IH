# AgroTwin AI — Shared Context Document

> **Purpose**: This is the single source of truth for every teammate and every AI model (Claude, GPT, Gemini, Grok, Cursor, etc.).  
> Copy-paste this file (or relevant sections) into any new chat so the model instantly understands the project state, constraints, and priorities.

---

## 1. Project Identity

| Item | Value |
|------|-------|
| **Name** | AgroTwin AI |
| **Tagline** | An Agentic, Evidence-Grounded Digital Twin for Continuous Farm Nutrient Monitoring and Sustainable Fertilizer Optimization |
| **Problem** | PSAI01 — Sustainable Fertilizer Usage Optimizer for Higher Yield |
| **Pilot Regions** | Kolhapur & Jalgaon (Maharashtra, India) |
| **Core Principle** | A fertilizer recommendation must **not** remain static when the farm conditions that produced it have changed. |

### The Three Primary USPs (never dilute these)

1. **Living Farm Digital Twin + Nutrient Ledger**  
   Persistent, continuously updated digital representation of every field + conceptual nutrient balance equations.  
   Equations and thresholds come **only** from validated agronomic sources (MPKV / ICAR / FCO), never invented by an LLM.

2. **Agentic Continuous Monitoring + Event-Driven Replanning**  
   After the first recommendation is issued, a Monitoring Agent continuously watches weather, soil, crop stage, applications and farmer feedback.  
   When conditions change, the system proactively invalidates the old plan and triggers selective re-planning.  
   **No one has to ask the AI anything** — the system reacts.

3. **Evidence-Grounded Multi-Objective Fertilizer Optimizer**  
   Quantities (kg/ha) come **only** from deterministic rules + optimizer.  
   LLM is never allowed to invent numbers.  
   Every recommendation must answer six questions:  
   **WHAT / HOW MUCH / WHEN / WHY / BASED ON WHAT / HOW SURE ARE WE**.

### Critical Constraints (non-negotiable)

- LLM must **never** generate fertilizer quantities (kg/ha, bags, etc.).
- Do **not** fabricate agronomic equations or thresholds.
- Every numerical recommendation must be traceable to data / model / rule / optimizer.
- RAG provides evidence and contextual reasoning only — never numeric prescriptions.
- System must **gracefully abstain** when required inputs are missing or confidence is inadequate.
- Preserve human / agronomist oversight.
- Keep architecture feasible for a student hackathon team while showing a credible production-scale path.
- Avoid feature soup (disease detector, marketplace, drones, tractor control = Phase 3+).

---

## 2. Current Repository Status (as of 2026-09-26)

**GitHub**: https://github.com/yach26/IH

### What exists today

```
agrotwin_api/          (and almost identical agrotwin_prototype/)
├── schema_sqlite.sql          # SQLite port of the frozen Digital Twin schema
├── seed_data.py               # Loads real Phase-1 data (8 synthetic farms, MPKV/ICAR RDF, FCO %)
├── ledger.py                  # Executable Nutrient Ledger (gap calc + product conversion)
├── run_demo.py                # End-to-end runner → writes results + CSV
├── agrotwin.db                # Generated SQLite Digital Twin
├── data/                      # synthetic_records.csv, npk_composition.csv
├── output/ledger_results.csv
└── app/agents/                # Placeholder (next step)
```

**What is already working and trusted**:
- Digital Twin schema + Nutrient Ledger are executable.
- Full traceability is enforced in code (citations + flags + confidence rules).
- Banana density issue resolved (mid-point 2250 plants/ha + `DERIVED_DENSITY` flag).
- Rounding errors from previous hand-worked tables are fixed by code.
- Confidence is computed from flags, not asserted by hand.

**What is NOT yet implemented**:
- FastAPI service
- Multi-agent orchestration
- Multi-objective optimizer (still using fixed DAP→Urea→MOP heuristic)
- Agentic RAG
- Weather event monitoring
- Frontend / PWA
- Soil report OCR

This Phase-1 core is solid. All future work must build on top of `ledger.py` and the schema without breaking the traceability guarantee.

---

## 3. Recommended Repository Structure Going Forward

```
AgroTwin/
├── docs/                              # ← All implementation MDs live here
│   ├── 00_CONTEXT.md                  # This file
│   ├── 01_PROJECT_OVERVIEW.md
│   ├── 02_DIGITAL_TWIN_AND_LEDGER.md
│   ├── 03_DATABASE_SCHEMA.md
│   ├── 04_MULTI_AGENT_ARCHITECTURE.md
│   ├── 05_RECOMMENDATION_PIPELINE.md
│   ├── 06_AGENTIC_RAG.md
│   ├── 07_OPTIMIZATION_AND_RULES.md
│   ├── 08_MONITORING_AND_EVENTS.md
│   ├── 09_API_BACKEND.md
│   ├── 10_FRONTEND_AND_UX.md
│   ├── 11_OCR_PIPELINE.md
│   ├── 12_WEATHER_INTEGRATION.md
│   ├── 13_WHAT_IF_AND_VISUALIZER.md
│   ├── 14_SAFETY_CONFIDENCE_HITL.md
│   ├── 15_DEPLOYMENT_MVP_ORDER.md
│   └── IMPLEMENTATION_ORDER.md
├── backend/
│   ├── app/
│   │   ├── agents/                    # Soil, Crop, Weather, Knowledge, Validation, Monitoring, Orchestrator
│   │   ├── core/                      # Digital Twin, Ledger, Optimizer, Rules
│   │   ├── rag/                       # Ingestion + retrieval
│   │   ├── api/                       # FastAPI routers
│   │   └── main.py
│   ├── data/
│   ├── tests/
│   └── requirements.txt
├── frontend/                          # Next.js PWA
├── regions/                           # Region-agnostic config pattern
│   ├── kolhapur/
│   └── jalgaon/
├── scripts/
└── docker/
```

---

## 4. How to Use This Context with Any Model

### Prompt template for a new chat

```
You are helping implement AgroTwin AI — a closed-loop agricultural digital twin for sustainable fertilizer optimization.

Read and strictly follow the constraints in this CONTEXT.md:

[paste entire 00_CONTEXT.md here]

Current task: [e.g. "Implement the Weather Agent and event emission for HEAVY_RAIN_ALERT"]

Relevant implementation guide: [paste the specific numbered MD]

Existing code status: The Nutrient Ledger + SQLite Digital Twin already works (see GitHub yach26/IH). 
Do not reinvent quantities or equations. Build on top of ledger.py and the schema.
Never let the LLM generate fertilizer kg/ha numbers.
```

### Rules for every model / teammate

1. Never invent kg/ha numbers.
2. Always surface confidence + flags.
3. Prefer deterministic code for calculations; LLM only for explanation / orchestration / RAG.
4. When data is missing → ABSTAIN with clear reason.
5. Keep the three USPs front-and-center in every design decision.
6. Prefer simple, testable Python over complex frameworks unless justified.

---

## 5. Immediate Next Steps (Hackathon Priority)

1. Harden & document the existing ledger (done).
2. Turn the script into a FastAPI service that exposes the Digital Twin + Ledger.
3. Add the six agents (narrow responsibilities) + simple Orchestrator.
4. Wire weather API + event bus for the "wow" moment (plan invalidation on heavy rain).
5. Basic farmer dashboard that shows proof-carrying recommendation.
6. OCR for soil reports.
7. What-If simulator (reuse ledger + simple sensitivity).
8. Minimal RAG over a small trusted document set.

See `15_DEPLOYMENT_MVP_ORDER.md` and `IMPLEMENTATION_ORDER.md` for the exact ordered backlog.

---

## 6. Key Source Documents (Phase-1 Data Pack)

The architecture references a data pack that is **not** fully in the public GitHub yet (assumed internal or to be added):

- `05_Crop_Calendars/four_pilot_crops.md`
- `06_Fertilizer_Recommendations/mpkv_icar_rdf.md`
- `07_Fertilizer_Composition/npk_composition.csv` + `conversion_notes.md`
- `11_Digital_Twin_Schema/`
- `04_remaining_gaps.md`

All numbers currently flowing through `ledger.py` are already sourced from these.

---

**Last updated**: 2026-09-27  
**Maintainer**: Team AgroTwin (yach26/IH)  
**Rule**: Update this CONTEXT.md whenever the repository status or priorities change.
