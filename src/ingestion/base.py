"""Base data adapter types and ABC."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TeamSnapshot:
    team_id: str
    name: str
    abbreviation: str = ""
    score: int | None = None
    penalty_score: int | None = None
    source: str = ""


@dataclass
class OddsSnapshot:
    home_implied: float | None = None
    draw_implied: float | None = None
    away_implied: float | None = None
    opening_home: float | None = None
    current_home: float | None = None
    source: str = "espn"


@dataclass
class MatchEvent:
    match_id: str
    home: TeamSnapshot
    away: TeamSnapshot
    status: str = "scheduled"
    date: str = ""
    stage: str = ""
    venue: str = ""
    competition_id: str = ""
    win_probability_home: float | None = None
    odds: OddsSnapshot | None = None
    referee: str = ""
    source: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class StandingRow:
    team_name: str
    position: int
    points: int
    played: int = 0
    last_5: str = ""
    source: str = ""


class DataAdapter(ABC):
    @abstractmethod
    def fetch_scoreboard(self, date_str: str | None = None) -> list[MatchEvent]:
        raise NotImplementedError

    @abstractmethod
    def fetch_standings(self) -> list[StandingRow]:
        raise NotImplementedError
