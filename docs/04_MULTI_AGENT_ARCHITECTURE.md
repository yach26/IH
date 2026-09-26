# 04 — Multi-Agent Architecture

## Design Principle

Use **narrow, specialized agents**. Do not create fifteen agents just to claim “multi-agent”.

```
                 ┌───────────────────┐
                 │   ORCHESTRATOR    │
                 └─────────┬─────────┘
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
   SOIL AGENT         CROP AGENT         WEATHER AGENT
       └───────────────────┼───────────────────┘
                           ▼
                  FARM DIGITAL TWIN
                           ▼
                 RECOMMENDATION ENGINE
                    ┌──────┴──────┐
                    ▼             ▼
               ML ENGINE      OPTIMIZER
                    └──────┬──────┘
                           ▼
                    KNOWLEDGE AGENT (Agentic RAG)
                           ▼
                   VALIDATION AGENT
                           ▼
                   FARMER / EXPERT
                           ▼
                   MONITORING AGENT
                           │  (event detected)
                           └──────→ back to ORCHESTRATOR
```

---

## Agent Responsibilities (Exact)

| Agent | Responsibilities | Must NOT do |
|-------|------------------|-------------|
| **Soil Agent** | Read soil data; validate NPK/pH/etc.; soil-health assessment; detect missing/stale tests; detect deficiencies/excess; update Digital Twin | Calculate fertilizer quantities |
| **Crop Agent** | Crop identification; growth stage; nutrient requirements (look-up only); target yield; crop calendar; previous-crop context | Invent requirements |
| **Weather Agent** | Forecast, rainfall, temperature, humidity; application-condition suitability; weather-risk assessment; detect forecast changes → emit events | Decide quantities |
| **Knowledge Agent** | Agentic RAG — retrieve, hybrid search, rerank, determine applicability, return citations | Calculate any numbers |
| **Validation Agent** | Check agronomic limits, incompatible inputs, missing critical data, low confidence, stale soil, weather conflicts, recommendation/evidence consistency | Override numbers |
| **Monitoring Agent** | After a plan exists: watch weather changes, crop-stage transitions, new soil measurements, applications, farmer feedback, irrigation, drift. Generate events and trigger selective re-planning | Run full optimization itself |
| **Orchestrator** | Route tasks, maintain state, decide which agents to call, handle re-plan loops | Contain domain logic |

---

## Shared State Object

```python
from typing import TypedDict, Optional, List, Dict, Any

class TwinState(TypedDict):
    field_id: str
    region_id: str
    soil: Dict[str, Any]
    crop: Dict[str, Any]
    weather: Dict[str, Any]
    history: List[Dict]
    current_plan: Optional[Dict]
    flags: List[str]
    confidence: str
    events: List[Dict]
    evidence: List[Dict]
    data_quality: Dict[str, bool]
```

All agents receive and return (or mutate) this state. The Orchestrator owns the lifecycle.

---

## Implementation Recommendation (Hackathon)

### Option A — Pure Python State Machine (recommended first)

```python
class Orchestrator:
    def __init__(self, soil, crop, weather, knowledge, validation, monitoring, ledger, optimizer):
        self.soil = soil
        self.crop = crop
        self.weather = weather
        self.knowledge = knowledge
        self.validation = validation
        self.monitoring = monitoring
        self.ledger = ledger
        self.optimizer = optimizer

    def run_recommendation(self, field_id: str) -> dict:
        twin = self.load_twin(field_id)

        twin = self.soil.assess(twin)
        twin = self.crop.assess(twin)
        twin = self.weather.assess(twin)

        # Ledger is the only place quantities are calculated
        plan = self.ledger.run_field(...)          # or self.optimizer.optimize(twin)

        evidence = self.knowledge.retrieve(plan, twin)
        validated = self.validation.check(plan, evidence, twin)

        if validated["status"] != "ABSTAIN":
            self.save_plan(field_id, validated)
            self.monitoring.start_watching(field_id, validated)

        return validated

    def handle_event(self, event: dict):
        """Selective re-plan path used by Monitoring Agent."""
        if event["type"] == "HEAVY_RAIN_ALERT":
            twin = self.load_twin(event["field_id"])
            twin = self.weather.assess(twin)          # only weather
            # re-validate existing plan against new weather
            # if conflict → re-run optimizer with new constraints
            ...
```

### Option B — LangGraph (only after Option A works)

Use LangGraph when the flow becomes complex (many conditional branches, human-in-the-loop interrupts, etc.). Nodes = agents, edges = conditional routing based on events / confidence.

---

## Event Types the Monitoring Agent Emits

```
SOIL_REPORT_UPDATED
WEATHER_FORECAST_CHANGED
HEAVY_RAIN_ALERT
CROP_STAGE_CHANGED
FERTILIZER_APPLIED
IRRIGATION_RECORDED
PLAN_CREATED
PLAN_INVALIDATED
RECOMMENDATION_RECALCULATED
EXPERT_OVERRIDE
```

On any of these the Orchestrator decides **which subset of agents** to re-run (selective, not full pipeline).

---

## Implementation Checklist

- [x] Create `app/agents/` package with one module per agent.
- [x] Each agent exposes a single public method (`assess`, `retrieve`, `validate`, `monitor`, `handle_event`).
- [x] Orchestrator is the only place that sequences agents. (delegates to `RecommendationPipeline`)
- [x] Monitoring Agent registers listeners on the event bus (or simple queue).
- [x] Unit tests for each agent in isolation (mock the twin).
- [x] Integration test: full recommendation + weather-change → re-plan path.
- [x] Never let an agent call the LLM to produce a kg/ha number.
