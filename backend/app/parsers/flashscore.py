"""Flashscore live-data provider (Playwright).

Implementation notes
--------------------
* Flashscore renders most data inside an iframe with heavy obfuscation and a
  generous use of dynamically-generated class names. The selectors below are a
  best-effort against the public HTML at the time of writing and SHOULD be
  treated as fragile — wire the production deployment to a licensed API client
  instead.
* Every Playwright interaction is wrapped in :func:`async_retry` and lives in
  its own browser context, so a single bad page does not break the monitor.
"""

from __future__ import annotations

from typing import Any

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from app.core.config import get_settings
from app.core.exceptions import ProviderError
from app.core.logging import get_logger
from app.parsers.base import LiveDataProvider
from app.parsers.match_parser import parse_match_card
from app.schemas.match import LiveMatch
from app.utils.retry import async_retry

log = get_logger(__name__)


class FlashscoreProvider(LiveDataProvider):
    """Scrape Flashscore for live football matches."""

    def __init__(self, *, headless: bool | None = None) -> None:
        settings = get_settings()
        self._url = settings.flashscore_url
        self._headless = settings.headless if headless is None else headless
        self._timeout_ms = settings.playwright_timeout_ms
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    async def start(self) -> None:
        if self._playwright is not None:
            return
        log.info("flashscore.start", headless=self._headless)
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self._headless)
        self._context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 900},
            locale="en-US",
        )

    async def stop(self) -> None:
        log.info("flashscore.stop")
        if self._context is not None:
            await self._context.close()
            self._context = None
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None

    async def __aenter__(self) -> FlashscoreProvider:
        await self.start()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.stop()

    @async_retry(attempts=3, min_wait=1.0, max_wait=4.0, exceptions=(ProviderError,))
    async def fetch_live_matches(self) -> list[LiveMatch]:
        """Return the current list of live matches.

        Raises:
            ProviderError: when the page fails to load or the parser can't
                find any match cards.
        """
        if self._context is None:
            raise ProviderError("FlashscoreProvider is not started")

        page = await self._context.new_page()
        try:
            return await self._scrape_page(page)
        finally:
            await page.close()

    async def _scrape_page(self, page: Page) -> list[LiveMatch]:
        try:
            await page.goto(self._url, timeout=self._timeout_ms, wait_until="domcontentloaded")
        except Exception as exc:
            raise ProviderError(f"page.goto failed: {exc}") from exc

        # Cookie banner.
        await self._dismiss_cookie_banner(page)

        # Wait for the live container.
        try:
            await page.wait_for_selector(
                "div.event__match, div[class*='event__match']",
                timeout=self._timeout_ms,
            )
        except Exception as exc:
            raise ProviderError(f"no match cards visible: {exc}") from exc

        cards = await page.query_selector_all("div.event__match, div[class*='event__match']")
        log.info("flashscore.cards", count=len(cards))

        matches: list[LiveMatch] = []
        for card in cards:
            try:
                html = await card.inner_html()
                external_id = await card.get_attribute("id") or ""
            except Exception as exc:
                log.warning("flashscore.card.read_failed", error=str(exc))
                continue

            parsed = parse_match_card(html=html, external_id=external_id)
            if parsed is not None:
                matches.append(parsed)
        return matches

    async def _dismiss_cookie_banner(self, page: Page) -> None:
        for selector in (
            "#onetrust-accept-btn-handler",
            "button[id*='accept']",
            "button:has-text('Accept')",
        ):
            try:
                btn = await page.query_selector(selector)
                if btn is not None:
                    await btn.click()
                    return
            except Exception:
                continue
