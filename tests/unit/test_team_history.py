"""Tests for the team-history aggregator."""

from __future__ import annotations

import pytest

from app.parsers.team_history import (
    InMemoryTeamHistoryProvider,
    TeamHistory,
    TeamHistoryMatch,
)


def _matches() -> list[TeamHistoryMatch]:
    return [
        TeamHistoryMatch(2, 1, 1, 1),
        TeamHistoryMatch(0, 0, 0, 0),
        TeamHistoryMatch(3, 2, 2, 1),
        TeamHistoryMatch(1, 0, 1, 0),
        TeamHistoryMatch(2, 2, 1, 1),
    ]


def test_recent_form_metrics_computed() -> None:
    history = TeamHistory(team_name="Chelsea", matches=_matches())
    form = history.to_recent_form()
    assert form.matches_played == 5
    assert form.avg_goals == pytest.approx(1.6)
    assert form.avg_conceded == pytest.approx(1.0)
    assert 0.0 <= form.over_05_2h_ratio <= 1.0
    assert 0.0 <= form.btts_ratio <= 1.0


def test_empty_history_returns_zeroes() -> None:
    form = TeamHistory(team_name="None FC", matches=[]).to_recent_form()
    assert form.matches_played == 0
    assert form.avg_goals == 0.0
    assert form.over_05_2h_ratio == 0.0


async def test_in_memory_provider_returns_zeroes_for_unknown_team() -> None:
    provider = InMemoryTeamHistoryProvider()
    form = await provider.get_recent_form("Unknown")
    assert form.matches_played == 0


async def test_in_memory_provider_returns_cached_history() -> None:
    provider = InMemoryTeamHistoryProvider()
    provider.set_cached(TeamHistory(team_name="Chelsea", matches=_matches()))
    form = await provider.get_recent_form("Chelsea", limit=3)
    assert form.matches_played == 3
