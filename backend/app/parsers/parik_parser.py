"""HTML → :class:`LiveMatch` parser for Parik24 live pages.

The Parik24 SEO mirror renders match data server-side, so we can parse
it with a simple HTTP GET + BeautifulSoup — no headless browser needed.

CSS class names are obfuscated but stable across deploys of the same
build.  The selectors below target the structural hierarchy rather than
exact names wherever possible, but should still be treated as fragile.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

from app.core.logging import get_logger
from app.schemas.match import LiveMatch, MatchStatus

log = get_logger(__name__)

# ── time / status patterns ────────────────────────────────────────
_TIME_RE = re.compile(r"([12])\u0422\s+(\d{1,3}):(\d{2})")
_PREMATCH_RE = re.compile(r"^(\d{2}):(\d{2})$")

_STATUS_MAP: dict[str, MatchStatus] = {
    "Перерва": MatchStatus.HALF_TIME,
    "Завершено": MatchStatus.FINISHED,
    "Перенесено": MatchStatus.POSTPONED,
}


def _classify_time(raw: str) -> tuple[MatchStatus, int]:
    """Return ``(status, minute)`` from a raw time string.

    Examples of *raw*: ``"2T 59:53"``, ``"Перерва"``, ``"02:20"``
    """
    m = _TIME_RE.search(raw)
    if m:
        half = int(m.group(1))
        mm = int(m.group(2))
        status = MatchStatus.FIRST_HALF if half == 1 else MatchStatus.SECOND_HALF
        return status, mm

    for label, st in _STATUS_MAP.items():
        if label in raw:
            minute = 45 if st == MatchStatus.HALF_TIME else 90
            return st, minute

    if _PREMATCH_RE.match(raw.strip()):
        return MatchStatus.SCHEDULED, 0

    return MatchStatus.SCHEDULED, 0


def _text(tag: Tag | None) -> str:
    if tag is None:
        return ""
    return tag.get_text(strip=True)


def _find_football_section(soup: BeautifulSoup) -> Tag | None:
    """Locate the top-level football container.

    The page groups sports in sections.  Each sport section starts with a
    header whose text begins with the sport name (e.g. "Футбол").  We look
    for the first header containing "Футбол" and return its parent.
    """
    for header in soup.select("div[class*='EC_AA']"):
        text = _text(header)
        if text.startswith("Футбол"):
            return header.parent
    return None


def parse_parik_live_page(html: str) -> list[LiveMatch]:
    """Parse the full Parik24 ``/uk/all-live`` HTML into a list of live matches.

    Only **football** matches are returned (other sports are ignored).
    """
    soup = BeautifulSoup(html, "lxml")
    football_section = _find_football_section(soup)

    if football_section is None:
        log.warning("parik.parse.no_football_section")
        return []

    league_blocks = football_section.select("div[class*='EC_Eq']")
    log.info("parik.parse.leagues", count=len(league_blocks))

    matches: list[LiveMatch] = []
    for block in league_blocks:
        league_header_el = block.select_one("div[class*='EC_Ey']")
        league_name = _text(league_header_el) if league_header_el else None

        match_links: list[Tag] = block.select("a[class*='styles_wrapper__']")
        for link in match_links:
            parsed = _parse_match_link(link, league=league_name)
            if parsed is not None:
                matches.append(parsed)

    return matches


def _parse_match_link(link: Tag, *, league: str | None) -> LiveMatch | None:
    """Extract a single :class:`LiveMatch` from an ``<a>`` element."""
    # ── time / status ──────────────────────────────────────────
    time_el = link.select_one("[class*='time-status']")
    raw_time = _text(time_el)
    if not raw_time:
        return None
    status, minute = _classify_time(raw_time)

    # ── teams ──────────────────────────────────────────────────
    comp_container = link.select_one("[class*='competitors']")
    if comp_container is None:
        return None
    competitor_els = comp_container.find_all(recursive=False)
    if len(competitor_els) < 2:
        return None
    home_team = _text(competitor_els[0])
    away_team = _text(competitor_els[1])
    if not home_team or not away_team:
        return None

    # ── score ──────────────────────────────────────────────────
    scores_el = link.select_one("[class*='scores']")
    score_home = 0
    score_away = 0
    if scores_el:
        spans = scores_el.select("span")
        if len(spans) >= 2:
            score_home = _safe_int(spans[0].get_text(strip=True))
            score_away = _safe_int(spans[1].get_text(strip=True))

    external_id = f"parik-{home_team}-{away_team}"

    return LiveMatch(
        external_id=external_id,
        home_team=home_team,
        away_team=away_team,
        league=league,
        score_home=score_home,
        score_away=score_away,
        minute=minute,
        status=status,
    )


def _safe_int(raw: str) -> int:
    digits = re.sub(r"\D", "", raw)
    return int(digits) if digits else 0
