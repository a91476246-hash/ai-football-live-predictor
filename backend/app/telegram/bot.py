"""Telegram bot client.

Uses the official Bot API HTTP endpoint via ``httpx`` — no third-party SDK
required. Provides a coroutine compatible with
:class:`app.services.signal_dispatcher.SignalDispatcher`.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import httpx

from app.core.config import get_settings
from app.core.exceptions import TelegramError
from app.core.logging import get_logger
from app.utils.retry import async_retry

log = get_logger(__name__)


class TelegramClient:
    """Minimal async client for ``POST sendMessage``."""

    BASE_URL = "https://api.telegram.org"

    def __init__(
        self,
        *,
        token: str,
        chat_id: str,
        timeout: float = 10.0,
        base_url: str | None = None,
    ) -> None:
        self._token = token
        self._chat_id = chat_id
        self._timeout = timeout
        self._base_url = base_url or self.BASE_URL

    @property
    def _endpoint(self) -> str:
        return f"{self._base_url}/bot{self._token}/sendMessage"

    @async_retry(attempts=3, min_wait=0.5, max_wait=4.0, exceptions=(TelegramError,))
    async def send_message(self, text: str, *, parse_mode: str | None = None) -> bool:
        if not text:
            return False
        payload: dict[str, object] = {"chat_id": self._chat_id, "text": text}
        if parse_mode is not None:
            payload["parse_mode"] = parse_mode

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                resp = await client.post(self._endpoint, json=payload)
            except httpx.HTTPError as exc:
                raise TelegramError(f"telegram transport error: {exc}") from exc

        if resp.status_code >= 500:
            raise TelegramError(f"telegram 5xx: {resp.status_code} {resp.text}")
        if resp.status_code >= 400:
            log.error("telegram.4xx", status=resp.status_code, body=resp.text)
            return False
        body: dict[str, object] = resp.json() if resp.content else {}
        ok = bool(body.get("ok", False))
        log.info("telegram.sent", ok=ok)
        return ok


def build_telegram_sender() -> Callable[[str], Awaitable[bool]] | None:
    """Return a coroutine usable by :class:`SignalDispatcher`, or ``None``.

    Returns ``None`` if Telegram is disabled or credentials are missing — the
    dispatcher gracefully skips it.
    """
    settings = get_settings()
    if not settings.telegram_enabled:
        return None
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        log.warning("telegram.disabled.missing_credentials")
        return None

    client = TelegramClient(
        token=settings.telegram_bot_token,
        chat_id=settings.telegram_chat_id,
    )

    async def send(text: str) -> bool:
        return await client.send_message(text)

    return send
