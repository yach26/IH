"""Pydantic models for the proof-carrying recommendation API (docs 01 + 09)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator
from datetime import date


class SoilTestIn(BaseModel):
    p_basis: Literal["P", "P2O5"] = "P"
    k_basis: Literal["K", "K2O"] = "K"
    n_kg_ha: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    p_kg_ha: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    k_kg_ha: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    ph: float | None = Field(default=None, ge=0, le=14, allow_inf_nan=False)
    oc_percent: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    ec_ds_m: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    test_date: str | None = None
    source: Literal["lab", "ocr", "manual"] = "manual"
    ocr_confidence: float | None = None
    original_file_path: str | None = None

    @field_validator("test_date")
    @classmethod
    def validate_sample_date(cls, value):
        if value is not None:
            parsed = date.fromisoformat(value)
            if parsed > date.today():
                raise ValueError("Soil sample date cannot be in the future")
        return value


class CropAssignRequest(BaseModel):
    crop_code: str
    variety: str | None = None
    sowing_date: str | None = None
    current_stage: str | None = None
    recommendation_type: str | None = None
    target_yield_kg_ha: float | None = None


class SoilReportConfirmRequest(BaseModel):
    upload_id: int | None = None
    soil_test: SoilTestIn


class WhatIfRequest(BaseModel):
    fertilizer_delta_pct: float | None = Field(default=None, ge=-100, le=500, allow_inf_nan=False)
    rainfall_mm: float | None = Field(default=None, ge=0, allow_inf_nan=False)


class OverrideRequest(BaseModel):
    recommendation_id: int
    new_plan: dict[str, Any]
    reason: str
    agronomist_id: str = "agronomist-1"


class RecommendRequest(BaseModel):
    agents: list[str] | None = Field(
        default=None,
        description="If set, selective re-plan of these agents only.",
    )
    optimizer: str | None = Field(
        default="heuristic",
        description="Optimizer to use: 'heuristic' (default) or 'linprog' (scipy multi-objective).",
    )
    mock_weather: dict[str, Any] | None = None
    farmer_input: dict[str, Any] | None = None


class RecommendationOut(BaseModel):
    status: str
    what: str | None = None
    how_much: dict[str, float] | None = None
    when: str | None = None
    why: dict[str, Any] | None = None
    based_on: dict[str, Any] | None = None
    confidence: str
    flags: list[str] = Field(default_factory=list)
    data_quality: dict[str, Any] = Field(default_factory=dict)
    validation: dict[str, Any] | None = None
    mode: str | None = None
    agents_run: list[str] | None = None
    reason: str | None = None
    required_actions: list[str] = Field(default_factory=list)
    field_id: int | str | None = None
    field_code: str | None = None
    recommendation_id: int | None = None
    pipeline_audit: list[dict[str, Any]] | None = None

    model_config = {"extra": "allow"}


class EventIn(BaseModel):
    type: str = "HEAVY_RAIN_ALERT"
    field_id: int | None = None
    field_code: str | None = None
    payload: dict[str, Any] = Field(
        default_factory=lambda: {
            "heavy_rain_alert": True,
            "rainfall_probability": 90,
            "rainfall_mm_next_7d": 80.0,
        }
    )
    actor: str = "demo"

class FarmerCreateRequest(BaseModel):
    """Create a new farmer. region_id must already exist."""
    region_id: int
    full_name: str | None = None
    mobile: str | None = None
    preferred_lang: str = "mr"


class FieldCreateRequest(BaseModel):
    """Create a new field. region_id and district_id must already exist."""
    region_id: int
    district_id: int
    taluka_id: int | None = None
    farmer_id: int | None = None
    field_code: str | None = None
    area_ha: float
    soil_type: str | None = None
    irrigation_type: str | None = None
    lat: float | None = None
    lon: float | None = None


class ApplicationIn(BaseModel):
    product_code: str
    quantity_kg_ha: float = Field(gt=0, allow_inf_nan=False)
    application_date: str
    notes: str | None = None

    @field_validator("application_date")
    @classmethod
    def valid_date(cls, value):
        if date.fromisoformat(value) > date.today():
            raise ValueError("Record actual applications, not future plans")
        return value
