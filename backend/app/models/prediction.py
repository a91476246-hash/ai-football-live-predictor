"""Prediction model."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampedMixin
from app.models.match import Match


class Prediction(Base, TimestampedMixin):
    """A prediction emitted by the engine for a specific match."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    expected_goals_min: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    expected_goals_max: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(512), nullable=True)

    match: Mapped[Match] = relationship(Match, lazy="joined")
