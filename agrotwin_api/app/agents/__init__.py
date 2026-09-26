"""
agents/ — AgroTwin multi-agent layer (Phase-2 extension).

Each module is a thin, testable layer with a single responsibility:
  soil_agent      — soil data reads, staleness checks
  crop_agent      — crop state + calendar lookups
  weather_agent   — Open-Meteo integration, HEAVY_RAIN_ALERT
  knowledge_agent — BM25 RAG over the Phase-1 data pack documents
  validation_agent— agronomic + weather-conflict plausibility checks
  monitoring_agent— event bus, SUPERSEDED / replan logic
  orchestrator    — sequence the agents, called by GET /ledger

Control-flow glue only lives here.
All fertilizer *numbers* still originate exclusively from app/ledger.py
(the existing, frozen Nutrient Ledger equations) or the linprog optimizer.
"""
