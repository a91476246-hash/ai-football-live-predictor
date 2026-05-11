"""Signal model."""

from __future__ import annotations

import enum

from sqlalchemy import Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampedMixin
from app.models.match import Match


class SignalStrength(enum.StrEnum):
    """Signal strength buckets."""

    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"


class Signal(Base, TimestampedMixin):
    """A user-facing signal derived from a prediction."""

    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    strength: Mapped[SignalStrength] = mapped_column(
        Enum(SignalStrength, native_enum=False, length=16), nullable=False
    )
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    headline: Mapped[str] = mapped_column(String(256), nullable=False)
    body: Mapped[str] = mapped_column(String(2048), nullable=False)
    delivered: Mapped[bool] = mapped_column(default=False, nullable=False)

    match: Mapped[Match] = relationship(Match, lazy="joined")
