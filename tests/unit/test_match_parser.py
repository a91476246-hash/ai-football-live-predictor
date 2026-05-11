"""Tests for the HTML → LiveMatch parser."""

from __future__ import annotations

from app.parsers.match_parser import parse_match_card
from app.schemas.match import MatchStatus


CARD_2H_SCORELESS = """
<div>
  <div class="event__participant--home participant__participantName--home">Chelsea</div>
  <div class="event__participant--away participant__participantName--away">Arsenal</div>
  <div class="event__score--home">0</div>
  <div class="event__score--away">0</div>
  <div class="event__stage event__stage--block">63'</div>
</div>
"""

CARD_HT = """
<div>
  <div class="participant__participantName--home">Liverpool</div>
  <div class="participant__participantName--away">Milan</div>
  <div class="event__score--home">1</div>
  <div class="event__score--away">1</div>
  <div class="event__stage">HT</div>
</div>
"""

CARD_BROKEN = "<div>not a match</div>"


def test_parses_second_half_scoreless() -> None:
    match = parse_match_card(html=CARD_2H_SCORELESS, external_id="g_1_abc")
    assert match is not None
    assert match.home_team == "Chelsea"
    assert match.away_team == "Arsenal"
    assert match.score_home == 0
    assert match.score_away == 0
    assert match.minute == 63
    assert match.status == MatchStatus.SECOND_HALF
    assert match.is_scoreless
    assert match.is_second_half


def test_parses_half_time() -> None:
    match = parse_match_card(html=CARD_HT, external_id="g_2_abc")
    assert match is not None
    assert match.status == MatchStatus.HALF_TIME
    assert not match.is_scoreless


def test_returns_none_on_broken_card() -> None:
    assert parse_match_card(html=CARD_BROKEN, external_id="g_3") is None


def test_returns_none_on_empty() -> None:
    assert parse_match_card(html="", external_id="x") is None
