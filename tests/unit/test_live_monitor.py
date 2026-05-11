"""Tests for the live-monitor filter and dispatch wiring."""

from __future__ import annotations

from app.ai.prediction_engine import PredictionEngine
from app.ai.signal_classifier import SignalClassifier
from app.parsers.base import LiveDataProvider
from app.parsers.team_history import (
    InMemoryTeamHistoryProvider,
    TeamHistory,
    TeamHistoryMatch,
)
from app.schemas.match import LiveMatch, LiveOdds, LiveStats, MatchStatus
from app.services.live_monitor import LiveMonitor
from app.services.signal_dispatcher import SignalDispatcher


class StubProvider(LiveDataProvider):
    def __init__(self, matches: list[LiveMatch]) -> None:
        self._matches = matches
        self.started = False

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.started = False

    async def fetch_live_matches(self) -> list[LiveMatch]:
        return self._matches


def _candidate(minute: int = 65) -> LiveMatch:
    return LiveMatch(
        external_id=f"c-{minute}",
        home_team="Chelsea",
        away_team="Arsenal",
        score_home=0,
        score_away=0,
        minute=minute,
        status=MatchStatus.SECOND_HALF,
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


def _too_early() -> LiveMatch:
    return _candidate(minute=40).model_copy(update={"minute": 40})


def _scored() -> LiveMatch:
    return _candidate().model_copy(update={"score_home": 1})


def _first_half() -> LiveMatch:
    return _candidate().model_copy(update={"status": MatchStatus.FIRST_HALF})


async def _build_monitor(provider: LiveDataProvider) -> LiveMonitor:
    history = InMemoryTeamHistoryProvider()
    matches = [
        TeamHistoryMatch(2, 1, 1, 1),
        TeamHistoryMatch(2, 2, 1, 1),
        TeamHistoryMatch(3, 1, 2, 1),
    ] * 3
    history.set_cached(TeamHistory(team_name="Chelsea", matches=matches))
    history.set_cached(TeamHistory(team_name="Arsenal", matches=matches))
    engine = PredictionEngine(history_provider=history)
    classifier = SignalClassifier(weak=0.6, medium=0.7, strong=0.8)
    dispatcher = SignalDispatcher()
    return LiveMonitor(
        provider=provider,
        engine=engine,
        classifier=classifier,
        dispatcher=dispatcher,
        poll_interval_seconds=0.01,
        min_minute=50,
    )


async def test_filter_drops_first_half_and_scored_and_early() -> None:
    provider = StubProvider([_first_half(), _scored(), _too_early()])
    monitor = await _build_monitor(provider)
    from app.db.init_db import init_models

    await init_models()
    emitted = await monitor.tick()
    assert emitted == 0


async def test_filter_keeps_valid_candidate() -> None:
    provider = StubProvider([_candidate()])
    monitor = await _build_monitor(provider)
    from app.db.init_db import init_models

    await init_models()
    emitted = await monitor.tick()
    assert emitted == 1
