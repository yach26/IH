# 01 — Project Overview & Architecture Principles

## Goal of This Document

Give every implementer a clear mental model of what AgroTwin **is** and **is not**, so design decisions stay coherent across the team and across AI models.

---

## 1. The Closed-Loop Decision System

AgroTwin is **not** a one-shot recommendation model.

```
OBSERVE → UNDERSTAND → PREDICT → OPTIMIZE → VALIDATE
    → RECOMMEND → MONITOR → DETECT CHANGE → RE-PLAN
         ▲__________________________________|
                    continuous loop
```

### What this means in practice

- A recommendation is stored as an **active plan** attached to a field’s Digital Twin.
- After the plan is issued, the Monitoring Agent keeps watching the conditions that produced it.
- When a relevant condition changes (weather, soil test, crop stage, application recorded, etc.), an event is emitted.
- The Orchestrator selectively re-runs only the affected agents and produces a revised plan.
- The old plan is marked `invalidated_at`.
- The farmer is notified — without having to ask the system anything.

This is the core differentiator. Most fertilizer recommenders stop at “here is your recommendation”. AgroTwin answers the question: **“What happens after we give the farmer the first recommendation?”**

---

## 2. The Four Layers of Intelligence (Hybrid)

| Layer | Responsibility | Preferred Technology | LLM Allowed? |
|-------|----------------|----------------------|--------------|
| **Deterministic Rules / Agronomic Models** | Nutrient requirements, hard safety limits, compatibility, conversion factors, stage calendars | Pure Python + data tables | No |
| **Optimization** | Quantity selection, product combination, cost / excess trade-offs | SciPy / OR-Tools or simple heuristic for MVP | No |
| **ML** | Yield / response prediction, anomaly detection, uncertainty estimation (only where data exists) | scikit-learn / XGBoost | No (for numbers) |
| **LLM + Agentic RAG** | Evidence retrieval, explanation generation, agent orchestration, farmer Q&A | LangGraph or pure state machine + hybrid RAG | Yes (explanation & retrieval only) |

**Golden rule**: The LLM never produces a number that ends up in a recommendation.  
All kg/ha values must come from the Ledger / Optimizer / Rules.

---

## 3. Region-Agnostic Core

```
regions/
├── kolhapur/
│   ├── config.yaml
│   ├── crops/
│   ├── agronomic_rules/
│   ├── knowledge_sources/      # fed into RAG
│   ├── soil_datasets/
│   └── geospatial_metadata/
└── jalgaon/
    └── ... (identical structure)
```

### Design rules

- The intelligence layer (agents, ledger, optimizer, RAG engine) is **identical** for every region.
- Region-specific data is loaded at runtime via `region_id` on the field.
- Adding a new region = adding a data folder, **not** rewriting agents or the recommendation engine.
- Specific Kolhapur / Jalgaon crops, soil properties and recommendations are still under research. Treat them as configuration until verified.

### Scalability pitch for judges

> “We are initially validating AgroTwin in Kolhapur and Jalgaon. However, the intelligence layer is region-agnostic. Region-specific crop calendars, agronomic recommendations, soil context, knowledge sources and geospatial configuration are maintained separately. Therefore, expansion to another region means onboarding its regional knowledge and data — not rebuilding the platform.”

---

## 4. Proof-Carrying Recommendation Contract

Every recommendation object **must** contain answers to these six questions:

| Question | Field |
|----------|-------|
| WHAT? | Recommended fertilizer / nutrient strategy |
| HOW MUCH? | Calculated quantity (kg/ha) — only from ledger/optimizer |
| WHEN? | Application window |
| WHY? | Reasoning (soil status, crop stage, weather, history) |
| BASED ON WHAT? | Farm data + retrieved agronomic evidence with citations |
| HOW SURE ARE WE? | Confidence level + flags + data quality checklist |

### Example shape

```json
{
  "status": "PLAN_GENERATED",
  "what": "DAP + Urea + MOP",
  "how_much": {
    "DAP_kg_ha": 54.3,
    "UREA_kg_ha": 78.3,
    "MOP_kg_ha": 33.3
  },
  "when": "28–30 September",
  "why": {
    "soil": "N status LOW",
    "crop": "Rice, Tillering stage",
    "weather": "Suitable application window identified",
    "history": "Previous N application: ..."
  },
  "based_on": {
    "farm_data": ["soil_test_id: ...", "crop_stage: tillering"],
    "evidence": [
      {
        "source": "MPKV/ICAR RDF",
        "excerpt": "...",
        "page": 12,
        "region_applicability": "Maharashtra"
      }
    ]
  },
  "confidence": "MEDIUM",
  "flags": ["P_PROXY"],
  "data_quality": {
    "soil_report_current": true,
    "weather_available": true,
    "crop_stage_known": true,
    "micronutrients_complete": false
  }
}
```

This contract is enforced by the Validation Agent and the database schema, not just by the UI.

---

## 5. What NOT to Build (Hackathon Guardrails)

Avoid turning AgroTwin into feature soup:

- Crop disease detector
- Marketplace / fertilizer ordering
- Weather app as a standalone product
- Generic chatbot that invents advice
- Drone dashboard
- Irrigation controller
- Tractor / IoT hardware integration

**Every major feature must reinforce**: continuous nutrient monitoring and sustainable fertilizer decision support.

### Hackathon MVP priority

Digital Twin + recommendation engine + optimizer (or current heuristic) + weather-aware monitoring + Agentic RAG + evidence + OCR + What-If simulation + farmer dashboard.

### Future scalability modules (only after core is complete)

Satellite / NDVI, IoT hardware, marketplace ordering, drone integration, tractor control.

---

## 6. Success Metric for the Demo

The single “wow” moment judges must see:

1. Farmer gets a recommendation (with full proof-carrying payload).
2. A heavy-rainfall forecast update is injected (demo button or script).
3. **Nobody asks the AI anything**.
4. Monitoring Agent detects that the plan’s assumptions have changed.
5. Orchestrator selectively re-runs Weather + Validation + Optimizer.
6. A revised plan appears with new application window, confidence and evidence.

This story proves the closed-loop architecture better than any slide.

---

## 7. One-Sentence Pitch

> Existing fertilizer recommenders give farmers a one-time answer. AgroTwin maintains a living digital twin of the farm, calculates an optimized fertilizer strategy from soil, crop, weather and history, grounds it in agricultural evidence, and continuously monitors conditions to automatically re-evaluate the plan when the farm changes.
