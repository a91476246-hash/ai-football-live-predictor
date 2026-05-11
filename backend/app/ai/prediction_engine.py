"""Prediction engine implementing the weighted FinalScore formula.

FinalScore =
    TeamForm * 0.25 + LivePressure * 0.35
    + SecondHalfStats * 0.25 + OddsMovement * 0.15
"""

from __future__ import annotations

from dataclasses import dataclass

from app.ai.features import (
    compute_live_pressure,
    compute_odds_movement,
    compute_second_half_stats,
    compute_team_form,
)
from app.core.logging import get_logger
from app.parsers.base import TeamHistoryProvider
from app.schemas.match import LiveMatch
from app.schemas.prediction import ProbabilityBreakdown

log = get_logger(__name__)


WEIGHTS: dict[str, float] = {
    "team_form": 0.25,
    "live_pressure": 0.35,
    "second_half_stats": 0.25,
    "odds_movement": 0.15,
}


@dataclass(slots=True)
class PredictionResult:
    """Output of :class:`PredictionEngine.predict`."""

    match: LiveMatch
    breakdown: ProbabilityBreakdown
    expected_goals_min: float
    expected_goals_max: float
    notes: str

    @property
    def probability(self) -> float:
        return self.breakdown.final_score


class PredictionEngine:
    """Stateless engine that scores a single live match.

    The engine pulls team-history features via a :class:`TeamHistoryProvider`
    and combines them with live in-play stats using the spec's weighted
    formula. Returns a :class:`PredictionResult` with both the final score and
    a per-component breakdown for transparency.
    """

    def __init__(self, history_provider: TeamHistoryProvider) -> None:
        self._history = history_provider

    async def predict(self, match: LiveMatch, *, history_limit: int = 10) -> PredictionResult:
        home_form = await self._history.get_recent_form(match.home_team, limit=history_limit)
        away_form = await self._history.get_recent_form(match.away_team, limit=history_limit)

        team_form = compute_team_form(home_form, away_form)
        live_pressure = compute_live_pressure(match)
        second_half_stats = compute_second_half_stats(home_form, away_form)
        odds_movement = compute_odds_movement(match)

        final = (
            team_form * WEIGHTS["team_form"]
            + live_pressure * WEIGHTS["live_pressure"]
            + second_half_stats * WEIGHTS["second_half_stats"]
            + odds_movement * WEIGHTS["odds_movement"]
        )
        # Numerical safety even though every component is already clamped.
        final = max(0.0, min(1.0, final))

        breakdown = ProbabilityBreakdown(
            team_form=team_form,
            live_pressure=live_pressure,
            second_half_stats=second_half_stats,
            odds_movement=odds_movement,
            final_score=final,
        )
        expected_min, expected_max = _expected_goal_band(
            final=final,
            home_form=home_form,
            away_form=away_form,
        )
        notes = (
            f"home avg goals={home_form.avg_goals:.2f} | "
            f"away avg goals={away_form.avg_goals:.2f} | "
            f"home over0.5(2H)={home_form.over_05_2h_ratio:.2f} | "
            f"away over0.5(2H)={away_form.over_05_2h_ratio:.2f}"
        )
        log.info(
            "prediction.computed",
            match=match.external_id,
            probability=round(final, 3),
            team_form=round(team_form, 3),
            live_pressure=round(live_pressure, 3),
            second_half_stats=round(second_half_stats, 3),
            odds_movement=round(odds_movement, 3),
        )
        return PredictionResult(
            match=match,
            breakdown=breakdown,
            expected_goals_min=expected_min,
            expected_goals_max=expected_max,
            notes=notes,
        )


def _expected_goal_band(
    *,
    final: float,
    home_form: object,
    away_form: object,
) -> tuple[float, float]:
    """Rough heuristic for the expected-goals band shown in alerts.

    We scale the per-team second-half goal averages by the final probability,
    then surface a band ±0.5 around the result. The values are *not* a
    posterior distribution — just a presentation aid.
    """
    home_2h = getattr(home_form, "second_half_goals", 0.0)
    away_2h = getattr(away_form, "second_half_goals", 0.0)
    avg_2h = (home_2h + away_2h) / 2
    base = max(0.5, avg_2h) * final
    return round(max(0.0, base - 0.4), 2), round(max(base + 0.4, 1.0), 2)
