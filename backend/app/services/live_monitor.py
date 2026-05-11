"""Live monitor — the orchestration loop.

Polls a :class:`LiveDataProvider`, filters candidate matches, runs the
:class:`PredictionEngine`, and dispatches signals.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterable

from app.ai.prediction_engine import PredictionEngine
from app.ai.signal_classifier import SignalClassifier
from app.core.config import get_settings
from app.core.logging import get_logger
from app.parsers.base import LiveDataProvider
from app.schemas.match import LiveMatch, MatchStatus
from app.services.signal_dispatcher import SignalDispatcher

log = get_logger(__name__)


class LiveMonitor:
    """Coordinates parser → engine → dispatcher.

    Parameters
    ----------
    provider:
        Any concrete :class:`LiveDataProvider`.
    engine:
        Prediction engine instance.
    classifier:
        Signal classifier instance.
    dispatcher:
        Side-effect-aware dispatcher.
    poll_interval_seconds:
        Override the env-provided interval (mostly useful for tests).
    """

    def __init__(
        self,
        *,
        provider: LiveDataProvider,
        engine: PredictionEngine,
        classifier: SignalClassifier,
        dispatcher: SignalDispatcher,
        poll_interval_seconds: float | None = None,
        min_minute: int | None = None,
    ) -> None:
        settings = get_settings()
        self._provider = provider
        self._engine = engine
        self._classifier = classifier
        self._dispatcher = dispatcher
        self._poll_interval = (
            poll_interval_seconds
            if poll_interval_seconds is not None
            else settings.monitor_interval_seconds
        )
        self._min_minute = min_minute if min_minute is not None else settings.min_minute
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        """Spawn the polling task. No-op if already running."""
        if self._task is not None and not self._task.done():
            return
        log.info(
            "monitor.start",
            interval_seconds=self._poll_interval,
            min_minute=self._min_minute,
        )
        await self._provider.start()
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run(), name="live-monitor")

    async def stop(self) -> None:
        """Signal the loop and clean up."""
        log.info("monitor.stop")
        self._stop_event.set()
        if self._task is not None:
            try:
                await asyncio.wait_for(self._task, timeout=10)
            except TimeoutError:
                self._task.cancel()
            self._task = None
        await self._provider.stop()

    async def tick(self) -> int:
        """Run a single iteration. Returns the number of signals emitted.

        Exposed for tests and the CLI ``afp-monitor`` entry-point.
        """
        try:
            matches = await self._provider.fetch_live_matches()
        except Exception:
            log.exception("monitor.fetch_failed")
            return 0
        candidates = list(self._filter(matches))
        log.info("monitor.tick", live_total=len(matches), candidates=len(candidates))
        emitted = 0
        for live in candidates:
            try:
                result = await self._engine.predict(live)
            except Exception:
                log.exception("monitor.predict_failed", match=live.external_id)
                continue
            decision = self._classifier.classify(result)
            if not decision.should_emit:
                continue
            await self._dispatcher.dispatch(
                live=live,
                probability=result.probability,
                decision=decision,
                expected_goals_min=result.expected_goals_min,
                expected_goals_max=result.expected_goals_max,
                prediction_notes=result.notes,
            )
            emitted += 1
        return emitted

    async def _run(self) -> None:
        while not self._stop_event.is_set():
            await self.tick()
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._poll_interval)
            except TimeoutError:
                continue

    def _filter(self, matches: Iterable[LiveMatch]) -> Iterable[LiveMatch]:
        """Apply the spec's filter: 2H + 0:0 + minute > min_minute."""
        for m in matches:
            if m.status != MatchStatus.SECOND_HALF:
                continue
            if not m.is_scoreless:
                continue
            if m.minute < self._min_minute:
                continue
            yield m


def run() -> None:  # pragma: no cover - thin shim for console_script
    """Console-script entry point: build and run a monitor loop forever."""
    import signal as posix_signal

    from app.ai.prediction_engine import PredictionEngine
    from app.ai.signal_classifier import SignalClassifier
    from app.core.logging import configure_logging
    from app.parsers.flashscore import FlashscoreProvider
    from app.parsers.team_history import FlashscoreTeamHistoryProvider
    from app.services.signal_dispatcher import SignalDispatcher
    from app.telegram.bot import build_telegram_sender

    async def _amain() -> None:
        configure_logging()
        provider = FlashscoreProvider()
        history = FlashscoreTeamHistoryProvider()
        engine = PredictionEngine(history_provider=history)
        classifier = SignalClassifier()
        dispatcher = SignalDispatcher(telegram_sender=build_telegram_sender())
        monitor = LiveMonitor(
            provider=provider,
            engine=engine,
            classifier=classifier,
            dispatcher=dispatcher,
        )
        await monitor.start()
        stop = asyncio.Event()

        loop = asyncio.get_running_loop()
        for sig in (posix_signal.SIGTERM, posix_signal.SIGINT):
            loop.add_signal_handler(sig, stop.set)
        await stop.wait()
        await monitor.stop()

    asyncio.run(_amain())
