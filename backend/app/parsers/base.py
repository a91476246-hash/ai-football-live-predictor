"""Abstract base classes for data providers.

These interfaces decouple the rest of the system from any specific data source.
The ``FlashscoreProvider`` is one implementation; a production deployment should
swap it for a licensed API client (api-football, Sportradar, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.schemas.match import LiveMatch


@dataclass(slots=True)
class TeamRecentForm:
    """Aggregated recent-form metrics for one team."""

    team_name: str
    matches_played: int
    avg_goals: float
    avg_conceded: float
    second_half_goals: float
    over_05_2h_ratio: float
    over_15_2h_ratio: float
    btts_ratio: float


class LiveDataProvider(ABC):
    """Interface for any source of live football matches."""

    @abstractmethod
    async def start(self) -> None:
        """Initialise underlying resources (browser, HTTP session, etc.)."""

    @abstractmethod
    async def stop(self) -> None:
        """Release underlying resources."""

    @abstractmethod
    async def fetch_live_matches(self) -> list[LiveMatch]:
        """Return the current snapshot of live matches."""


class TeamHistoryProvider(ABC):
    """Interface for team-history backends."""

    @abstractmethod
    async def get_recent_form(self, team_name: str, *, limit: int = 10) -> TeamRecentForm:
        """Return recent-form metrics for the given team."""
