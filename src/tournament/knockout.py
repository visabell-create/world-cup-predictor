"""Knockout bracket state machine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BracketMatch:
    match_id: str
    home_team: str
    away_team: str
    stage: str
    winner: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class KnockoutBracket:
    def __init__(self) -> None:
        self.matches: list[BracketMatch] = []

    def add_match(self, match: BracketMatch) -> None:
        self.matches.append(match)

    def set_winner(self, match_id: str, winner: str) -> None:
        for match in self.matches:
            if match.match_id == match_id:
                match.winner = winner
                return

    def get_stage_matches(self, stage: str) -> list[BracketMatch]:
        return [m for m in self.matches if m.stage == stage]

    def to_dict(self) -> list[dict[str, Any]]:
        return [
            {
                "match_id": m.match_id,
                "home_team": m.home_team,
                "away_team": m.away_team,
                "stage": m.stage,
                "winner": m.winner,
            }
            for m in self.matches
        ]
