"""
agents/ — AgroTwin multi-agent layer (Phase-2).

Each module is a thin, testable layer with a single responsibility:
  soil_agent      — soil data reads, staleness checks
  crop_agent      — crop state + calendar lookups
  weather_agent   — Open-Meteo integration, HEAVY_RAIN_ALERT
  knowledge_agent — BM25 RAG over the Phase-1 data pack documents
  validation_agent— agronomic + weather-conflict plausibility checks
  monitoring_agent— event bus, SUPERSEDED / replan logic
  orchestrator    — thin wrapper around RecommendationPipeline
  optimizer       — optional linprog (NOT the default; default is HeuristicOptimizer)
  twin_state      — shared TwinState TypedDict + confidence helpers

Control-flow glue only lives in orchestrator.py.
All fertilizer *numbers* still originate exclusively from app/ledger.py
(the existing, frozen Nutrient Ledger equations) or the linprog optimizer.

Agent public surfaces
─────────────────────
soil_agent      : get_soil_context(conn, field_id) → dict | None
crop_agent      : get_crop_context(conn, field_row) → dict | None
weather_agent   : get_weather_context(conn, field_id, lat, lon, …) → dict
knowledge_agent : retrieve_evidence(crop_code, region, rec_type, …) → list[dict]
validation_agent: validate_ledger_result(ledger_result, soil_ctx, weather_ctx) → dict
monitoring_agent: fire_event(event_type, **kwargs) | supersede_and_replan(…)
orchestrator    : run_orchestrated_ledger(conn, field_row, mock_weather) → dict
optimizer       : run_optimizer_for_field(conn, gap_n, gap_p2o5, gap_k2o) → OptimizerResult
twin_state      : TwinState, make_empty_twin_state, compute_confidence
"""

from .twin_state import TwinState, make_empty_twin_state, compute_confidence

__all__ = [
    "TwinState",
    "make_empty_twin_state",
    "compute_confidence",
]
