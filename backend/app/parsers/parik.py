"""Parik24 live-data provider (HTTP + BeautifulSoup).

Unlike the Flashscore provider, Parik24's SEO mirror renders match data
server-side, so we can scrape it with a lightweight HTTP client — no
headless browser required.

Two URLs are supported (configurable):
* ``https://parik.club/uk/all-live`` — the main domain (may be
  geo-restricted to Ukrainian IPs).
* ``https://parik24ua.kyiv.ua/uk/all-live`` — the SEO mirror, accessible
  worldwide.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import ProviderError
from app.core.logging import get_logger
from app.parsers.base import LiveDataProvider
from app.parsers.parik_parser import parse_parik_live_page
from app.schemas.match import LiveMatch
from app.utils.retry import async_retry

log = get_logger(__name__)

_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class ParikProvider(LiveDataProvider):
    """Scrape Parik24 for live football matches via plain HTTP."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.parik_url).rstrip("/")
        self._live_url = f"{self._base_url}/uk/all-live"
        self._timeout = timeout or (settings.playwright_timeout_ms / 1000)
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        if self._client is not None:
            return
        log.info("parik.start", url=self._base_url)
        self._client = httpx.AsyncClient(
            headers={
                "User-Agent": _DEFAULT_USER_AGENT,
                "Accept-Language": "uk-UA,uk;q=0.9",
                "Accept": "text/html,application/xhtml+xml",
            },
            follow_redirects=True,
            timeout=httpx.Timeout(self._timeout),
        )

    async def stop(self) -> None:
        log.info("parik.stop")
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> ParikProvider:
        await self.start()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.stop()

    @async_retry(attempts=3, min_wait=1.0, max_wait=4.0, exceptions=(ProviderError,))
    async def fetch_live_matches(self) -> list[LiveMatch]:
        """Fetch and parse the live-matches page.

        Returns only **football** matches that are currently in play.

        Raises:
            ProviderError: on network or parsing failures.
        """
        if self._client is None:
            raise ProviderError("ParikProvider is not started")

        try:
            response = await self._client.get(self._live_url)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(f"parik HTTP {exc.response.status_code}: {self._live_url}") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"parik request failed: {exc}") from exc

        html = response.text
        if len(html) < 500:
            raise ProviderError("parik: response body too small — page may be blocked")

        matches = parse_parik_live_page(html)
        log.info("parik.fetched", count=len(matches))
        return matches
