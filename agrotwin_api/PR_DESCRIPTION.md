# feat: optimizer abstraction + event-driven monitoring

## Summary

Implements docs **05** (recommendation pipeline), **07** (optimizer + rules), and **08** (event-driven monitoring) on top of the existing schema, agents, and Nutrient Ledger.

- Ordered pipeline: Soil → Crop → Weather → Ledger → HeuristicOptimizer → RuleEngine → Knowledge → proof-carrying plan
- Selective re-plan (`agents=["weather","validation","optimizer"]`)
- Default optimizer is still DAP→Urea→MOP via `ledger.convert_gap_to_products` (no kg/ha invented by an LLM or a forked formula)
- In-process event bus + Monitoring Agent
- Demo wow path: `HEAVY_RAIN_ALERT` → `PLAN_INVALIDATED` → revised window, same quantities

## Testing

```bash
cd agrotwin_api
pip install -r requirements.txt
python -m pytest tests/ -v
```

Expected: all tests pass. Weather is mocked (no network). No LLM calls.

```bash
# Closed-loop demo (in-memory)
python ../scripts/demo_heavy_rain.py

# HTTP demo
python run_demo.py
uvicorn app.main:app --reload
python ../scripts/demo_heavy_rain.py --http http://127.0.0.1:8000 --field SYN-001
```

### Heavy-rain checklist

1. `POST /fields/{id}/recommend` returns `PLAN_GENERATED` with a dry `when` window
2. `POST /events` with `HEAVY_RAIN_ALERT` for that field
3. Previous row is `SUPERSEDED` + `invalidated_at` set
4. Latest plan is `PLAN_REVISED`, `mode=partial_replan`, `when` deferred, `how_much` unchanged
5. `GET /fields/{id}/alerts` shows `HEAVY_RAIN_ALERT`

## Non-goals (out of this PR)

- Real RAG / multi-objective MIP / event broker / frontend
