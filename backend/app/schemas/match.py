"""Match-related Pydantic schemas."""

from __future__ import annotations

import enum

from pydantic import BaseModel, ConfigDict, Field


class MatchStatus(enum.StrEnum):
    """High-level match status."""

    SCHEDULED = "scheduled"
    FIRST_HALF = "1H"
    HALF_TIME = "HT"
    SECOND_HALF = "2H"
    FINISHED = "FT"
    POSTPONED = "postponed"
    ABANDONED = "abandoned"


class LiveStats(BaseModel):
    """In-play statistics scraped per match."""

    shots_home: int = 0
    shots_away: int = 0
    shots_on_target_home: int = 0
    shots_on_target_away: int = 0
    dangerous_attacks_home: int = 0
    dangerous_attacks_away: int = 0
    possession_home: int = 50
    possession_away: int = 50
    corners_home: int = 0
    corners_away: int = 0
    yellow_cards_home: int = 0
    yellow_cards_away: int = 0
    red_cards_home: int = 0
    red_cards_away: int = 0
    xg_home: float | None = None
    xg_away: float | None = None


class LiveOdds(BaseModel):
    """Live odds used for prediction."""

    over_05_pre: float | None = None
    over_05_live: float | None = None
    over_15_pre: float | None = None
    over_15_live: float | None = None


class LiveMatch(BaseModel):
    """In-flight representation of a live match (parser output)."""

    model_config = ConfigDict(extra="ignore")

    external_id: str
    home_team: str
    away_team: str
    league: str | None = None
    score_home: int = 0
    score_away: int = 0
    minute: int = 0
    status: MatchStatus = MatchStatus.SCHEDULED
    stats: LiveStats = Field(default_factory=LiveStats)
    odds: LiveOdds = Field(default_factory=LiveOdds)

    @property
    def is_scoreless(self) -> bool:
        return self.score_home == 0 and self.score_away == 0

    @property
    def is_second_half(self) -> bool:
        return self.status == MatchStatus.SECOND_HALF


class MatchOut(BaseModel):
    """Serialised match (REST response)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str
    home_team: str
    away_team: str
    league: str | None
    score_home: int
    score_away: int
    minute: int
    status: str
