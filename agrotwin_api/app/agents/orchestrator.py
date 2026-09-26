"""
Orchestrator — thin coordinator around RecommendationPipeline.

Domain sequencing lives in `app.pipeline.RecommendationPipeline`.
This module keeps the historical `run_orchestrated_ledger()` entry point
used by tests and FastAPI, plus `request_replan()` for Monitoring Agent.
"""

from __future__ import annotations

import sqlite3
from typing import Iterable

from ..pipeline import EVENT_AGENT_MAP, RecommendationPipeline


_PIPELINE: RecommendationPipeline | None = None


def get_pipeline() -> RecommendationPipeline:
    global _PIPELINE
    if _PIPELINE is None:
        _PIPELINE = RecommendationPipeline()
    return _PIPELINE


def run_orchestrated_ledger(
    conn: sqlite3.Connection,
    field_row: sqlite3.Row,
    mock_weather: dict | None = None,
    farmer_input: dict | None = None,
) -> dict:
    """Full pipeline run (Soil → Crop → Weather → Ledger → Optimizer → Validation)."""
    return get_pipeline().run(
        conn, field_row, mock_weather=mock_weather, farmer_input=farmer_input
    )


def request_replan(
    conn: sqlite3.Connection,
    field_row: sqlite3.Row,
    agents: Iterable[str],
    mock_weather: dict | None = None,
    previous_plan: dict | None = None,
) -> dict:
    """Selective re-plan: re-run only `agents` plus knowledge/confidence/persist."""
    return get_pipeline().run(
        conn,
        field_row,
        agents=list(agents),
        mock_weather=mock_weather,
        previous_plan=previous_plan,
    )


def agents_for_event(event_type: str) -> tuple[str, ...]:
    return EVENT_AGENT_MAP.get(event_type, ("weather", "validation", "optimizer"))
