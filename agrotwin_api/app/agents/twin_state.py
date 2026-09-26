"""
app/agents/twin_state.py — shared TwinState TypedDict.

All agents receive and return (or mutate) this state.
The Orchestrator owns the lifecycle.

Design rules (from 04_MULTI_AGENT_ARCHITECTURE.md):
  - TwinState is the single object passed between agents.
  - Each agent is responsible for exactly one sub-dict (soil, crop, weather, etc.).
  - Agents MUST NOT write into another agent's sub-dict.
  - Flags are accumulated in the top-level `flags` list; each agent appends its own.
  - Confidence degrades from HIGH → MEDIUM → LOW as flags accumulate.
  - LLMs must NEVER write into `current_plan` quantities.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class TwinState(TypedDict):
    """
    Shared Digital Twin state object — mutated in-place as agents run.

    Fields
    ------
    field_id : str
        Unique field identifier (matches ``fields.field_code`` or ``fields.field_id``).
    region_id : str
        Region code (e.g. 'MH', 'kolhapur') — used to inject region config.
    soil : Dict[str, Any]
        Populated by SoilAgent.assess().  Keys: n_kg_ha, p_kg_ha, k_kg_ha, ph,
        oc_percent, ec_ds_m, is_stale, days_since_test, soil_test_id, flags.
    crop : Dict[str, Any]
        Populated by CropAgent.assess().  Keys: crop_id, crop_code, crop_name,
        recommendation_type, current_stage, calendar_entries, stage_valid, flags.
    weather : Dict[str, Any]
        Populated by WeatherAgent.assess().  Keys: heavy_rain_alert, alert_details,
        rainfall_mm_next_7d, rainfall_probability, snapshot, flags.
    history : List[Dict]
        Previous recommendations / ledger runs for this field (for context only).
    current_plan : Optional[Dict]
        The latest recommendation dict written by the Orchestrator after the
        Ledger + Optimizer + Validation pipeline.  NEVER written by an LLM.
    flags : List[str]
        Accumulated across all agents.  Each flag string carries its source tag,
        e.g. "STALE_SOIL_DATA (…)", "WEATHER_CONFLICT (…)".
    confidence : str
        Overall confidence computed by Orchestrator: "HIGH" | "MEDIUM" | "LOW" | "ABSTAIN".
    events : List[Dict]
        Events emitted during this run (used by MonitoringAgent).
        Each dict: {"type": str, "field_id": str, "payload": dict, "ts": str}.
    evidence : List[Dict]
        Evidence chunks returned by KnowledgeAgent. For traceability only.
    data_quality : Dict[str, bool]
        Boolean quality signals accumulated by agents.
        Keys: has_soil_test, soil_is_fresh, has_crop, has_rec_type,
              has_weather, weather_ok, stage_in_calendar.
    """

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


def make_empty_twin_state(field_id: str, region_id: str = "") -> TwinState:
    """
    Returns a blank TwinState with all optional sub-dicts initialised to empty.
    The Orchestrator calls this before sequencing agents.
    """
    return TwinState(
        field_id=field_id,
        region_id=region_id,
        soil={},
        crop={},
        weather={},
        history=[],
        current_plan=None,
        flags=[],
        confidence="HIGH",
        events=[],
        evidence=[],
        data_quality={
            "has_soil_test": False,
            "soil_is_fresh": False,
            "has_crop": False,
            "has_rec_type": False,
            "has_weather": False,
            "weather_ok": True,
            "stage_in_calendar": True,
        },
    )


def compute_confidence(flags: List[str]) -> str:
    """
    Derives confidence from the accumulated flag list.

    Rules (matching ledger.py original logic, now generalised):
      0 flags                 → HIGH
      1 flag                  → MEDIUM
      2+ flags                → LOW
      Any "ABSTAIN" flag      → ABSTAIN (short-circuit)

    Flags that are purely informational (OPTIMIZER_*, NO_COORDINATES,
    WEATHER_FETCH_ERROR) do not downgrade confidence — they don't reflect
    uncertainty in the ledger numbers themselves.
    """
    if any("ABSTAIN" in f.upper() for f in flags):
        return "ABSTAIN"

    _skip_prefixes = (
        "OPTIMIZER_",
        "NO_COORDINATES",
        "WEATHER_FETCH_ERROR",
        "STAGE_NOT_IN_CALENDAR",
    )
    material_flags = [
        f for f in flags
        if not any(f.startswith(p) for p in _skip_prefixes)
    ]

    if len(material_flags) == 0:
        return "HIGH"
    if len(material_flags) == 1:
        return "MEDIUM"
    return "LOW"
