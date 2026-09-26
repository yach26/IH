"""
Event model for the closed-loop monitoring path (doc 08).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class EventType(str, Enum):
    SOIL_REPORT_UPDATED = "SOIL_REPORT_UPDATED"
    WEATHER_FORECAST_CHANGED = "WEATHER_FORECAST_CHANGED"
    HEAVY_RAIN_ALERT = "HEAVY_RAIN_ALERT"
    CROP_STAGE_CHANGED = "CROP_STAGE_CHANGED"
    FERTILIZER_APPLIED = "FERTILIZER_APPLIED"
    IRRIGATION_RECORDED = "IRRIGATION_RECORDED"
    PLAN_CREATED = "PLAN_CREATED"
    PLAN_INVALIDATED = "PLAN_INVALIDATED"
    RECOMMENDATION_RECALCULATED = "RECOMMENDATION_RECALCULATED"
    EXPERT_OVERRIDE = "EXPERT_OVERRIDE"


@dataclass
class Event:
    type: str
    field_id: int
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    event_id: str = field(default_factory=lambda: str(uuid4()))
    field_code: str | None = None
    actor: str = "system"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def create(
        cls,
        event_type: str | EventType,
        field_id: int,
        payload: dict[str, Any] | None = None,
        field_code: str | None = None,
        actor: str = "system",
    ) -> "Event":
        etype = event_type.value if isinstance(event_type, EventType) else str(event_type)
        return cls(
            type=etype,
            field_id=field_id,
            payload=payload or {},
            field_code=field_code,
            actor=actor,
        )
