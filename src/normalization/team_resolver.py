"""Team name resolution and source reconciliation."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from src.ingestion.base import MatchEvent


ALIASES: dict[str, str] = {
    "usa": "united states",
    "usmnt": "united states",
    "eng": "england",
    "ger": "germany",
    "esp": "spain",
    "fra": "france",
    "bra": "brazil",
    "arg": "argentina",
    "mex": "mexico",
    "kor": "south korea",
    "korea republic": "south korea",
}


def normalize_team_name(name: str) -> str:
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return ALIASES.get(text, text)


@dataclass
class ReconciliationResult:
    match_id: str
    home_team: str
    away_team: str
    espn_home_score: int | None
    espn_away_score: int | None
    google_home_score: int | None
    google_away_score: int | None
    espn_status: str
    google_status: str
    score_match: bool
    status_match: bool
    divergence_penalty: float = 0.0
    warnings: list[str] = field(default_factory=list)


class TeamResolver:
    def resolve(self, name: str) -> str:
        return normalize_team_name(name)

    def teams_match(self, a: str, b: str) -> bool:
        na = self.resolve(a)
        nb = self.resolve(b)
        return na == nb or na in nb or nb in na

    def reconcile(self, espn: MatchEvent, google: MatchEvent | None) -> ReconciliationResult:
        result = ReconciliationResult(
            match_id=espn.match_id,
            home_team=espn.home.name,
            away_team=espn.away.name,
            espn_home_score=espn.home.score,
            espn_away_score=espn.away.score,
            google_home_score=None,
            google_away_score=None,
            espn_status=espn.status,
            google_status="",
            score_match=True,
            status_match=True,
        )
        if google is None:
            result.warnings.append("google_source_missing")
            result.divergence_penalty = 0.05
            return result

        result.google_home_score = google.home.score
        result.google_away_score = google.away.score
        result.google_status = google.status

        if result.espn_home_score is not None and result.google_home_score is not None:
            result.score_match = (
                result.espn_home_score == result.google_home_score
                and result.espn_away_score == result.google_away_score
            )
        result.status_match = self._statuses_compatible(espn.status, google.status)

        if not result.score_match:
            result.warnings.append("score_divergence")
            result.divergence_penalty += 0.15
        if not result.status_match:
            result.warnings.append("status_divergence")
            result.divergence_penalty += 0.05
        return result

    @staticmethod
    def _statuses_compatible(espn_status: str, google_status: str) -> bool:
        espn = espn_status.lower()
        google = google_status.lower()
        if espn == google:
            return True
        live_tokens = ("in progress", "live", "1st", "2nd", "halftime")
        final_tokens = ("final", "full", "ft", "status_final")
        if any(t in espn for t in live_tokens) and any(t in google for t in live_tokens):
            return True
        if any(t in espn for t in final_tokens) and any(t in google for t in final_tokens):
            return True
        return False

    def find_google_match(
        self, espn_event: MatchEvent, google_events: list[MatchEvent]
    ) -> MatchEvent | None:
        for event in google_events:
            if self.teams_match(espn_event.home.name, event.home.name) and self.teams_match(
                espn_event.away.name, event.away.name
            ):
                return event
        return None
