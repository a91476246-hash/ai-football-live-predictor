"""HTML → :class:`LiveMatch` parser.

Kept separate from the scraper so it can be unit-tested with static fixtures.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from app.core.logging import get_logger
from app.schemas.match import LiveMatch, MatchStatus

log = get_logger(__name__)


_STATUS_RE = re.compile(r"\b(?:1H|2H|HT|FT|H1|H2)\b", re.IGNORECASE)
_MINUTE_RE = re.compile(r"(\d{1,3})\s*['′]")  # noqa: RUF001 (prime char is required to match Flashscore HTML)


_STATUS_MAP: dict[str, MatchStatus] = {
    "1H": MatchStatus.FIRST_HALF,
    "H1": MatchStatus.FIRST_HALF,
    "HT": MatchStatus.HALF_TIME,
    "2H": MatchStatus.SECOND_HALF,
    "H2": MatchStatus.SECOND_HALF,
    "FT": MatchStatus.FINISHED,
}


def _extract_text(node: object | None) -> str:
    if node is None:
        return ""
    if isinstance(node, str):
        return node.strip()
    text = getattr(node, "get_text", None)
    if callable(text):
        value = text(strip=True)
        return str(value) if value is not None else ""
    return str(node).strip()


def _coerce_int(raw: str | None) -> int:
    if raw is None:
        return 0
    digits = re.sub(r"\D", "", raw)
    return int(digits) if digits else 0


def _classify_status(raw_status: str, minute: int) -> MatchStatus:
    upper = raw_status.upper()
    match = _STATUS_RE.search(upper)
    if match:
        return _STATUS_MAP[match.group(0).upper()]
    if minute == 0:
        return MatchStatus.SCHEDULED
    if 1 <= minute <= 45:
        return MatchStatus.FIRST_HALF
    if 46 <= minute <= 120:
        return MatchStatus.SECOND_HALF
    return MatchStatus.SCHEDULED


def parse_match_card(*, html: str, external_id: str) -> LiveMatch | None:
    """Parse a single Flashscore match card.

    Returns ``None`` if the card is unparseable rather than raising — callers
    iterate over many cards and one broken element shouldn't break the batch.
    """
    if not html.strip():
        return None

    soup = BeautifulSoup(html, "lxml")

    home_el = soup.select_one("[class*='participant__participantName--home']") or soup.select_one(
        "[class*='event__participant--home']"
    )
    away_el = soup.select_one("[class*='participant__participantName--away']") or soup.select_one(
        "[class*='event__participant--away']"
    )
    score_home_el = soup.select_one("[class*='event__score--home']")
    score_away_el = soup.select_one("[class*='event__score--away']")
    stage_el = soup.select_one("[class*='event__stage--block']") or soup.select_one(
        "[class*='event__stage']"
    )

    home_team = _extract_text(home_el)
    away_team = _extract_text(away_el)
    if not home_team or not away_team:
        return None

    score_home = _coerce_int(_extract_text(score_home_el))
    score_away = _coerce_int(_extract_text(score_away_el))

    raw_stage = _extract_text(stage_el)
    minute_match = _MINUTE_RE.search(raw_stage)
    minute = int(minute_match.group(1)) if minute_match else 0
    status = _classify_status(raw_stage, minute)

    return LiveMatch(
        external_id=external_id or f"{home_team}-{away_team}",
        home_team=home_team,
        away_team=away_team,
        score_home=score_home,
        score_away=score_away,
        minute=minute,
        status=status,
    )
