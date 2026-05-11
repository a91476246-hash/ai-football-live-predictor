"""Tests for the prediction engine and signal classifier."""

from __future__ import annotations

import pytest

from app.ai.prediction_engine import PredictionEngine
from app.ai.signal_classifier import SignalClassifier
from app.models.signal import SignalStrength
from app.parsers.team_history import (
    InMemoryTeamHistoryProvider,
    TeamHistory,
    TeamHistoryMatch,
)
from app.schemas.match import LiveMatch, LiveOdds, LiveStats, MatchStatus


@pytest.fixture
def history_provider() -> InMemoryTeamHistoryProvider:
    provider = InMemoryTeamHistoryProvider()
    high_scoring = [
        TeamHistoryMatch(
            goals_for=2, goals_against=1, second_half_goals_for=1, second_half_goals_against=1
        )
        for _ in range(10)
    ]
    provider.set_cached(TeamHistory(team_name="Chelsea", matches=high_scoring))
    provider.set_cached(TeamHistory(team_name="Arsenal", matches=high_scoring))
    low_scoring = [
        TeamHistoryMatch(
            goals_for=0, goals_against=0, second_half_goals_for=0, second_half_goals_against=0
        )
        for _ in range(10)
    ]
    provider.set_cached(TeamHistory(team_name="Stoic FC", matches=low_scoring))
    provider.set_cached(TeamHistory(team_name="Defenders United", matches=low_scoring))
    return provider


def _live_match(home: str, away: str, *, stats: LiveStats, odds: LiveOdds) -> LiveMatch:
    return LiveMatch(
        external_id=f"{home}-{away}",
        home_team=home,
        away_team=away,
        minute=65,
        status=MatchStatus.SECOND_HALF,
        stats=stats,
        odds=odds,
    )


async def test_predict_high_pressure_produces_strong_signal(
    history_provider: InMemoryTeamHistoryProvider,
) -> None:
    engine = PredictionEngine(history_provider=history_provider)
    classifier = SignalClassifier(weak=0.6, medium=0.7, strong=0.8)

    match = _live_match(
        "Chelsea",
        "Arsenal",
        stats=LiveStats(
            shots_on_target_home=8,
            shots_on_target_away=6,
            dangerous_attacks_home=70,
            dangerous_attacks_away=65,
            corners_home=7,
            corners_away=6,
        ),
        odds=LiveOdds(over_05_pre=1.50, over_05_live=1.10),
    )
    result = await engine.predict(match)
    assert result.probability >= 0.8
    decision = classifier.classify(result)
    assert decision.should_emit
    assert decision.strength == SignalStrength.STRONG


async def test_predict_low_pressure_produces_no_signal(
    history_provider: InMemoryTeamHistoryProvider,
) -> None:
    engine = PredictionEngine(history_provider=history_provider)
    classifier = SignalClassifier(weak=0.6, medium=0.7, strong=0.8)

    match = _live_match(
        "Stoic FC",
        "Defenders United",
        stats=LiveStats(),
        odds=LiveOdds(over_05_pre=1.50, over_05_live=1.80),
    )
    result = await engine.predict(match)
    assert result.probability < 0.6
    decision = classifier.classify(result)
    assert not decision.should_emit


async def test_breakdown_components_within_bounds(
    history_provider: InMemoryTeamHistoryProvider,
) -> None:
    engine = PredictionEngine(history_provider=history_provider)
    match = _live_match(
        "Chelsea",
        "Arsenal",
        stats=LiveStats(shots_on_target_home=3, dangerous_attacks_home=20),
        odds=LiveOdds(),
    )
    result = await engine.predict(match)
    breakdown = result.breakdown
    for value in (
        breakdown.team_form,
        breakdown.live_pressure,
        breakdown.second_half_stats,
        breakdown.odds_movement,
        breakdown.final_score,
    ):
        assert 0.0 <= value <= 1.0
