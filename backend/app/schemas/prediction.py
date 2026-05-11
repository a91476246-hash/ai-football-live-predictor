"""Prediction Pydantic schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProbabilityBreakdown(BaseModel):
    """Breakdown of the weighted FinalScore components."""

    team_form: float = Field(ge=0.0, le=1.0)
    live_pressure: float = Field(ge=0.0, le=1.0)
    second_half_stats: float = Field(ge=0.0, le=1.0)
    odds_movement: float = Field(ge=0.0, le=1.0)
    final_score: float = Field(ge=0.0, le=1.0)


class PredictionOut(BaseModel):
    """Serialised prediction (REST response)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    match_id: int
    probability: float
    expected_goals_min: float
    expected_goals_max: float
    notes: str | None = None
