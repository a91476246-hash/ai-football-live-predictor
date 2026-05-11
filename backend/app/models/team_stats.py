"""Aggregated team statistics."""

from __future__ import annotations

from sqlalchemy import Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampedMixin


class TeamStats(Base, TimestampedMixin):
    """Recent-form statistics for a team."""

    __tablename__ = "team_stats"
    __table_args__ = (Index("ix_team_stats_team", "team_name", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_name: Mapped[str] = mapped_column(String(128), nullable=False)
    matches_played: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_goals: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_conceded: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    second_half_goals: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    over_05_2h_ratio: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    over_15_2h_ratio: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    btts_ratio: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
