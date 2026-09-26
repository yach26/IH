# 08 — Monitoring & Event-Driven Architecture

## Principle

Do **not** implement monitoring as a cron job that polls an LLM every five minutes.  
Use events.

---

## Event Bus Flow

```
External APIs / User Events
        ↓
    Event Bus (Redis / simple in-memory queue / Celery)
        ↓
 Monitoring Engine
        ↓
  Rules / Thresholds
        ↓
 Relevant Agent(s)
        ↓
   Recalculation (selective)
```

---

## Core Events

| Event | Trigger | Typical Action |
|-------|---------|----------------|
| `SOIL_REPORT_UPDATED` | OCR or manual upload confirmed | Re-run Soil Agent + full or partial plan |
| `WEATHER_FORECAST_CHANGED` | Weather API push / poll | Weather Agent risk assessment |
| `HEAVY_RAIN_ALERT` | Forecast threshold crossed | Invalidate current plan if application window conflicts |
| `CROP_STAGE_CHANGED` | Calendar or farmer input | Crop Agent + possible requirement change |
| `FERTILIZER_APPLIED` | Farmer records application | Update Nutrient Ledger history |
| `IRRIGATION_RECORDED` | Farmer input | Update moisture / environment |
| `PLAN_CREATED` | Successful recommendation | Start monitoring for that plan |
| `PLAN_INVALIDATED` | Monitoring decision | Notify farmer, mark old plan |
| `RECOMMENDATION_RECALCULATED` | Re-plan finished | New plan available |
| `EXPERT_OVERRIDE` | Agronomist action | Audit + possible model feedback |

---

## Monitoring Agent Logic (MVP)

```python
class MonitoringAgent:
    def on_event(self, event: Event):
        if event.type == "HEAVY_RAIN_ALERT":
            plan = self.get_active_plan(event.field_id)
            if plan and self.weather_conflicts(plan, event.payload):
                self.emit("PLAN_INVALIDATED", field_id=event.field_id, reason=...)
                self.orchestrator.request_replan(
                    event.field_id,
                    agents=["weather", "validation", "optimizer"]
                )
```

For the demo, a simple in-memory or Redis list is enough.  
Later move to a proper message broker.

---

## The Demo “Wow” Path (must work)

1. Recommendation is generated and stored as ACTIVE.
2. Demo script (or admin button) injects a `HEAVY_RAIN_ALERT` for the field.
3. Monitoring Agent detects conflict with the application window.
4. Orchestrator re-runs only Weather + Validation + Optimizer.
5. New plan appears with updated window / confidence / evidence.
6. Farmer dashboard shows the alert + revised plan **without any user query**.

This single path communicates the closed-loop architecture better than any slide.

---

## Checklist

- [ ] Define Event model (type, field_id, payload, timestamp).
- [ ] Simple event bus (Redis pub/sub or in-process queue).
- [ ] Monitoring Agent registers handlers.
- [ ] Orchestrator supports partial re-plan.
- [ ] Demo script / admin endpoint that injects the rain event.
- [ ] Audit log of every event and resulting action.
- [ ] Integration test covering the full wow path.
