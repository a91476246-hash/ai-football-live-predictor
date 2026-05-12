"""Parsers and data providers."""

from app.parsers.base import LiveDataProvider, TeamHistoryProvider
from app.parsers.flashscore import FlashscoreProvider
from app.parsers.match_parser import parse_match_card
from app.parsers.parik import ParikProvider
from app.parsers.parik_parser import parse_parik_live_page
from app.parsers.team_history import FlashscoreTeamHistoryProvider, TeamHistory

__all__ = [
    "FlashscoreProvider",
    "FlashscoreTeamHistoryProvider",
    "LiveDataProvider",
    "ParikProvider",
    "TeamHistory",
    "TeamHistoryProvider",
    "parse_match_card",
    "parse_parik_live_page",
]
