"""Signal schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.signal import SignalStrength


class SignalOut(BaseModel):
    """Serialised signal (REST/WebSocket payload)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    match_id: int
    strength: SignalStrength
    probability: float
    headline: str
    body: str
    delivered: bool
    created_at: datetime
