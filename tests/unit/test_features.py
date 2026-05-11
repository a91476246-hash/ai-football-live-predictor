"""Unit tests for feature extractors."""

from __future__ import annotations

import pytest

from app.ai.features import (
    compute_live_pressure,
    compute_odds_movement,
    compute_second_half_stats,
    compute_team_form,
)
from app.parsers.base import TeamRecentForm
from app.schemas.match import LiveMatch, LiveOdds, LiveStats, MatchStatus


def _form(
    *,
    avg_goals: float = 0.0,
    avg_conceded: float = 0.0,
    second_half_goals: float = 0.0,
    over_05_2h_ratio: float = 0.0,
    over_15_2h_ratio: float = 0.0,
    btts_ratio: float = 0.0,
    matches_played: int = 10,
) -> TeamRecentForm:
    return TeamRecentForm(
        team_name="Test",
        matches_played=matches_played,
        avg_goals=avg_goals,
        avg_conceded=avg_conceded,
        second_half_goals=second_half_goals,
        over_05_2h_ratio=over_05_2h_ratio,
        over_15_2h_ratio=over_15_2h_ratio,
        btts_ratio=btts_ratio,
    )


def _live(**overrides: object) -> LiveMatch:
    base = {
        "external_id": "test-1",
        "home_team": "A",
        "away_team": "B",
        "minute": 65,
        "status": MatchStatus.SECOND_HALF,
        "stats": LiveStats(),
        "odds": LiveOdds(),
    }
    base.update(overrides)
    return LiveMatch.model_validate(base)


class TestComputeTeamForm:
    def test_empty_history_returns_neutral(self) -> None:
        empty = _form(matches_played=0)
        assert compute_team_form(empty, empty) == pytest.approx(0.5)

    def test_high_scoring_teams_return_higher_value(self) -> None:
        low = _form(avg_goals=0.2, avg_conceded=0.2)
        high = _form(avg_goals=2.5, avg_conceded=2.0)
        assert compute_team_form(high, high) > compute_team_form(low, low)

    def test_result_is_clamped(self) -> None:
        extreme = _form(avg_goals=10.0, avg_conceded=10.0)
        score = compute_team_form(extreme, extreme)
        assert 0.0 <= score <= 1.0


class TestComputeLivePressure:
    def test_no_stats_returns_zero(self) -> None:
        assert compute_live_pressure(_live()) == 0.0

    def test_high_pressure_above_low(self) -> None:
        low = _live(stats=LiveStats(shots_on_target_home=1, dangerous_attacks_home=10))
        high = _live(
            stats=LiveStats(
                shots_on_target_home=6,
                shots_on_target_away=5,
                dangerous_attacks_home=50,
                dangerous_attacks_away=45,
                corners_home=6,
                corners_away=5,
            )
        )
        assert compute_live_pressure(high) > compute_live_pressure(low)

    def test_red_card_bumps_pressure(self) -> None:
        without = _live(stats=LiveStats(shots_on_target_home=2))
        with_red = _live(stats=LiveStats(shots_on_target_home=2, red_cards_home=1))
        assert compute_live_pressure(with_red) > compute_live_pressure(without)


class TestComputeSecondHalfStats:
    def test_higher_over_05_returns_higher_score(self) -> None:
        low = _form(over_05_2h_ratio=0.2, second_half_goals=0.3)
        high = _form(over_05_2h_ratio=0.9, second_half_goals=1.4)
        assert compute_second_half_stats(high, high) > compute_second_half_stats(low, low)


class TestComputeOddsMovement:
    def test_missing_odds_returns_neutral(self) -> None:
        assert compute_odds_movement(_live()) == pytest.approx(0.5)

    def test_falling_odds_increase_score(self) -> None:
        falling = _live(odds=LiveOdds(over_05_pre=1.50, over_05_live=1.20))
        rising = _live(odds=LiveOdds(over_05_pre=1.50, over_05_live=1.80))
        assert compute_odds_movement(falling) > compute_odds_movement(rising)
