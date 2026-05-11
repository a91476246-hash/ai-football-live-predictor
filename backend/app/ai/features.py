"""Feature extractors used by the prediction engine.

Each function returns a value in ``[0.0, 1.0]`` so the weighted FinalScore is
itself a probability-shaped number.
"""

from __future__ import annotations

from app.parsers.base import TeamRecentForm
from app.schemas.match import LiveMatch


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def compute_team_form(home: TeamRecentForm, away: TeamRecentForm) -> float:
    """Aggregate attacking output of both teams.

    A team that scores 1.5 goals/match → ``avg_goals / 3`` ≈ 0.5. Both sides are
    averaged so a single rampant team doesn't dominate the score.
    """
    if home.matches_played == 0 and away.matches_played == 0:
        return 0.5  # neutral prior

    home_attack = _clamp(home.avg_goals / 3.0)
    away_attack = _clamp(away.avg_goals / 3.0)
    home_defence = _clamp(home.avg_conceded / 3.0)
    away_defence = _clamp(away.avg_conceded / 3.0)
    # Goals are more likely when *both* sides leak and create chances.
    attack = (home_attack + away_attack) / 2
    defence = (home_defence + away_defence) / 2
    return _clamp(0.6 * attack + 0.4 * defence)


def compute_live_pressure(match: LiveMatch) -> float:
    """Translate live in-play stats into pressure intensity.

    Heuristic combining shots on target, dangerous attacks and corners. The
    raw counts are mapped onto a soft cap so a 90-minute slugfest doesn't
    saturate to 1.0 too early.
    """
    s = match.stats
    sot = s.shots_on_target_home + s.shots_on_target_away
    da = s.dangerous_attacks_home + s.dangerous_attacks_away
    corners = s.corners_home + s.corners_away

    sot_score = _clamp(sot / 12.0)
    da_score = _clamp(da / 80.0)
    corner_score = _clamp(corners / 12.0)

    pressure = 0.5 * sot_score + 0.3 * da_score + 0.2 * corner_score

    # Red cards skew the game open — bump pressure if there's a red.
    if s.red_cards_home + s.red_cards_away > 0:
        pressure = _clamp(pressure + 0.15)
    return pressure


def compute_second_half_stats(home: TeamRecentForm, away: TeamRecentForm) -> float:
    """Probability prior that *either* team scores in the 2nd half."""
    if home.matches_played == 0 and away.matches_played == 0:
        return 0.5
    # Combine each team's empirical 2H-goal rate (Over 0.5).
    avg_over_05 = (home.over_05_2h_ratio + away.over_05_2h_ratio) / 2
    avg_2h_goals = (home.second_half_goals + away.second_half_goals) / 2
    # Mix the explicit ratio with goal-volume signal.
    return _clamp(0.7 * avg_over_05 + 0.3 * _clamp(avg_2h_goals / 2.0))


def compute_odds_movement(match: LiveMatch) -> float:
    """Convert odds movement into a probability prior.

    Falling Over 0.5 odds (market sensing pressure) imply higher probability.
    If no odds are present we return a neutral 0.5.
    """
    odds = match.odds
    if odds.over_05_pre is None or odds.over_05_live is None:
        return 0.5
    if odds.over_05_pre <= 1.0 or odds.over_05_live <= 1.0:
        return 0.5

    delta = (odds.over_05_pre - odds.over_05_live) / odds.over_05_pre
    # Map -50% .. +50% drift to 0..1.
    return _clamp(0.5 + delta)
