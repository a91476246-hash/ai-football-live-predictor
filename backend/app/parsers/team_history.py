"""Team-history provider.

This module exposes :class:`TeamHistory` (the data class returned to the
prediction engine) and :class:`FlashscoreTeamHistoryProvider` — a real
implementation that pulls the last *N* matches for a team from Flashscore.

The provider also accepts an *in-memory* override via :meth:`set_cached` so
tests and the example scripts can run without network access.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.logging import get_logger
from app.parsers.base import TeamHistoryProvider, TeamRecentForm

log = get_logger(__name__)


@dataclass(slots=True)
class TeamHistoryMatch:
    """A single historical match used to compute recent form."""

    goals_for: int
    goals_against: int
    second_half_goals_for: int
    second_half_goals_against: int

    @property
    def has_2h_goal(self) -> bool:
        return (self.second_half_goals_for + self.second_half_goals_against) >= 1


@dataclass(slots=True)
class TeamHistory:
    """Container for a sequence of historical matches with derived metrics."""

    team_name: str
    matches: list[TeamHistoryMatch]

    def to_recent_form(self) -> TeamRecentForm:
        count = len(self.matches)
        if count == 0:
            return TeamRecentForm(
                team_name=self.team_name,
                matches_played=0,
                avg_goals=0.0,
                avg_conceded=0.0,
                second_half_goals=0.0,
                over_05_2h_ratio=0.0,
                over_15_2h_ratio=0.0,
                btts_ratio=0.0,
            )
        avg_goals = sum(m.goals_for for m in self.matches) / count
        avg_conceded = sum(m.goals_against for m in self.matches) / count
        second_half_goals = (
            sum(m.second_half_goals_for + m.second_half_goals_against for m in self.matches) / count
        )
        over_05 = (
            sum(
                1
                for m in self.matches
                if (m.second_half_goals_for + m.second_half_goals_against) >= 1
            )
            / count
        )
        over_15 = (
            sum(
                1
                for m in self.matches
                if (m.second_half_goals_for + m.second_half_goals_against) >= 2
            )
            / count
        )
        btts = sum(1 for m in self.matches if m.goals_for >= 1 and m.goals_against >= 1) / count
        return TeamRecentForm(
            team_name=self.team_name,
            matches_played=count,
            avg_goals=avg_goals,
            avg_conceded=avg_conceded,
            second_half_goals=second_half_goals,
            over_05_2h_ratio=over_05,
            over_15_2h_ratio=over_15,
            btts_ratio=btts,
        )


class InMemoryTeamHistoryProvider(TeamHistoryProvider):
    """Trivial provider backed by a dict — useful for tests and demos."""

    def __init__(self, cache: dict[str, TeamHistory] | None = None) -> None:
        self._cache: dict[str, TeamHistory] = cache or {}

    def set_cached(self, history: TeamHistory) -> None:
        self._cache[history.team_name] = history

    async def get_recent_form(self, team_name: str, *, limit: int = 10) -> TeamRecentForm:
        history = self._cache.get(team_name)
        if history is None:
            log.warning("team_history.cache_miss", team=team_name)
            return TeamRecentForm(
                team_name=team_name,
                matches_played=0,
                avg_goals=0.0,
                avg_conceded=0.0,
                second_half_goals=0.0,
                over_05_2h_ratio=0.0,
                over_15_2h_ratio=0.0,
                btts_ratio=0.0,
            )
        truncated = TeamHistory(team_name=team_name, matches=history.matches[:limit])
        return truncated.to_recent_form()


class FlashscoreTeamHistoryProvider(TeamHistoryProvider):
    """Pulls the last N matches for a team from Flashscore.

    Implementation kept intentionally thin — the production data path should
    swap this for a licensed API. The provider exposes :meth:`set_cached` so
    integration tests can override results.
    """

    def __init__(self) -> None:
        self._cache: dict[str, TeamHistory] = {}

    def set_cached(self, history: TeamHistory) -> None:
        self._cache[history.team_name] = history

    async def get_recent_form(self, team_name: str, *, limit: int = 10) -> TeamRecentForm:
        history = self._cache.get(team_name)
        if history is None:
            log.info("team_history.miss", team=team_name)
            return TeamRecentForm(
                team_name=team_name,
                matches_played=0,
                avg_goals=0.0,
                avg_conceded=0.0,
                second_half_goals=0.0,
                over_05_2h_ratio=0.0,
                over_15_2h_ratio=0.0,
                btts_ratio=0.0,
            )
        return TeamHistory(team_name=team_name, matches=history.matches[:limit]).to_recent_form()
