"""Match model."""

from __future__ import annotations

from sqlalchemy import Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampedMixin


class Match(Base, TimestampedMixin):
    """A football match observed during live monitoring."""

    __tablename__ = "matches"
    __table_args__ = (
        Index("ix_matches_external_id", "external_id", unique=True),
        Index("ix_matches_status_minute", "status", "minute"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(64), nullable=False)
    home_team: Mapped[str] = mapped_column(String(128), nullable=False)
    away_team: Mapped[str] = mapped_column(String(128), nullable=False)
    league: Mapped[str | None] = mapped_column(String(128), nullable=True)
    score_home: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_away: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    minute: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="scheduled", nullable=False)
