"""Signal dispatch — fan out a new signal to Telegram, DB, WebSocket clients."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from sqlalchemy import select

from app.ai.signal_classifier import SignalDecision
from app.core.logging import get_logger
from app.db.session import session_scope
from app.models.match import Match
from app.models.prediction import Prediction
from app.models.signal import Signal, SignalStrength
from app.schemas.match import LiveMatch
from app.schemas.signal import SignalOut

log = get_logger(__name__)


WebSocketBroadcaster = Callable[[SignalOut], Awaitable[None]]
TelegramSender = Callable[[str], Awaitable[bool]]


class SignalDispatcher:
    """Persist + fan-out a signal.

    The dispatcher is deliberately unaware of *where* a signal goes — it takes
    optional broadcaster and telegram callables and invokes them after
    persistence. This keeps the side-effects testable and pluggable.
    """

    def __init__(
        self,
        *,
        telegram_sender: TelegramSender | None = None,
        websocket_broadcaster: WebSocketBroadcaster | None = None,
    ) -> None:
        self._telegram_sender = telegram_sender
        self._websocket_broadcaster = websocket_broadcaster

    async def dispatch(
        self,
        *,
        live: LiveMatch,
        probability: float,
        decision: SignalDecision,
        expected_goals_min: float,
        expected_goals_max: float,
        prediction_notes: str | None = None,
    ) -> SignalOut | None:
        """Persist match/prediction/signal rows and trigger downstream sinks."""
        if not decision.should_emit or decision.strength is None:
            return None

        async with session_scope() as session:
            match = await self._upsert_match(session, live)
            await session.flush()
            prediction = Prediction(
                match_id=match.id,
                probability=probability,
                expected_goals_min=expected_goals_min,
                expected_goals_max=expected_goals_max,
                notes=prediction_notes,
            )
            session.add(prediction)
            signal = Signal(
                match_id=match.id,
                strength=SignalStrength(decision.strength.value),
                probability=probability,
                headline=decision.headline,
                body=decision.body,
                delivered=False,
            )
            session.add(signal)
            await session.flush()
            payload = SignalOut.model_validate(signal)
            signal_id = signal.id

        # Side-effects — both are best-effort.
        if self._telegram_sender is not None:
            try:
                ok = await self._telegram_sender(decision.as_telegram_text())
                if ok:
                    await self._mark_delivered(signal_id)
            except Exception:
                log.exception("signal.telegram_failed", signal_id=signal_id)
        if self._websocket_broadcaster is not None:
            try:
                await self._websocket_broadcaster(payload)
            except Exception:
                log.exception("signal.websocket_failed", signal_id=signal_id)

        log.info(
            "signal.dispatched",
            signal_id=signal_id,
            strength=decision.strength.value,
            probability=round(probability, 3),
        )
        return payload

    @staticmethod
    async def _upsert_match(session: object, live: LiveMatch) -> Match:
        """Insert or update a :class:`Match` row keyed by ``external_id``."""
        from sqlalchemy.ext.asyncio import AsyncSession  # local to avoid global cycle

        assert isinstance(session, AsyncSession)
        existing = (
            await session.execute(select(Match).where(Match.external_id == live.external_id))
        ).scalar_one_or_none()
        if existing is None:
            row = Match(
                external_id=live.external_id,
                home_team=live.home_team,
                away_team=live.away_team,
                league=live.league,
                score_home=live.score_home,
                score_away=live.score_away,
                minute=live.minute,
                status=live.status.value,
            )
            session.add(row)
            return row
        existing.score_home = live.score_home
        existing.score_away = live.score_away
        existing.minute = live.minute
        existing.status = live.status.value
        return existing

    async def _mark_delivered(self, signal_id: int) -> None:
        async with session_scope() as session:
            signal = await session.get(Signal, signal_id)
            if signal is not None:
                signal.delivered = True
