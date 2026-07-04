"""ESPN API data adapter."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from src.config import load_config
from src.ingestion.base import DataAdapter, MatchEvent, OddsSnapshot, StandingRow, TeamSnapshot
from src.ingestion.cache import ResponseCache

logger = logging.getLogger(__name__)


class EspnDataAdapter(DataAdapter):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or load_config()
        espn = self.config["espn"]
        self.league = self.config["framework"]["league"]
        self.base_site = espn["base_site"]
        self.base_site_v2 = espn["base_site_v2"]
        self.base_core = espn["base_core"]
        self.cache = ResponseCache()
        self.ttl_live = espn["cache_ttl_live_sec"]
        self.ttl_static = espn["cache_ttl_static_sec"]
        self.client = httpx.Client(
            timeout=30.0,
            headers={"User-Agent": "world-cup-predictor/1.0"},
        )

    def _get_json(self, url: str, cache_key: str, ttl: int) -> dict[str, Any]:
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        for attempt in range(3):
            try:
                response = self.client.get(url)
                response.raise_for_status()
                payload = response.json()
                self.cache.set(cache_key, payload, ttl)
                return payload
            except httpx.HTTPStatusError as exc:
                if 400 <= exc.response.status_code < 500:
                    logger.debug("ESPN client error for %s: %s", url, exc)
                    return {}
                logger.warning("ESPN request failed (%s): %s", attempt + 1, exc)
                time.sleep(2 ** attempt)
            except httpx.HTTPError as exc:
                logger.warning("ESPN request failed (%s): %s", attempt + 1, exc)
                time.sleep(2 ** attempt)
        return {}

    def fetch_scoreboard(self, date_str: str | None = None) -> list[MatchEvent]:
        url = f"{self.base_site}/{self.league}/scoreboard"
        if date_str:
            url += f"?dates={date_str.replace('-', '')}"
        cache_key = f"espn:scoreboard:{self.league}:{date_str or 'today'}"
        data = self._get_json(url, cache_key, self.ttl_live)
        return [self._parse_event(event) for event in data.get("events", [])]

    def fetch_standings(self) -> list[StandingRow]:
        url = f"{self.base_site_v2}/{self.league}/standings"
        cache_key = f"espn:standings:{self.league}"
        data = self._get_json(url, cache_key, self.ttl_static)
        rows: list[StandingRow] = []
        for child in data.get("children", []):
            for entry in child.get("standings", {}).get("entries", []):
                team = entry.get("team", {})
                stats = {s["name"]: s.get("displayValue", s.get("value", 0)) for s in entry.get("stats", [])}
                rows.append(
                    StandingRow(
                        team_name=team.get("displayName", team.get("name", "")),
                        position=int(stats.get("rank", stats.get("playoffSeed", 0)) or 0),
                        points=int(float(stats.get("points", 0) or 0)),
                        played=int(float(stats.get("gamesPlayed", 0) or 0)),
                        last_5=str(stats.get("record", "")),
                        source="espn",
                    )
                )
        return rows

    def fetch_summary(self, event_id: str) -> dict[str, Any]:
        url = f"{self.base_site}/{self.league}/summary?event={event_id}"
        return self._get_json(url, f"espn:summary:{event_id}", self.ttl_live)

    def fetch_team_roster(self, team_id: str) -> dict[str, Any]:
        url = f"{self.base_site}/{self.league}/teams/{team_id}/roster"
        return self._get_json(url, f"espn:roster:{team_id}", self.ttl_static)

    def fetch_team_injuries(self, team_id: str) -> dict[str, Any]:
        url = f"{self.base_site}/{self.league}/teams/{team_id}/injuries"
        return self._get_json(url, f"espn:injuries:{team_id}", self.ttl_live)

    def fetch_odds(self, event_id: str, competition_id: str) -> OddsSnapshot | None:
        url = (
            f"{self.base_core}/{self.league}/events/{event_id}"
            f"/competitions/{competition_id}/odds"
        )
        data = self._get_json(url, f"espn:odds:{event_id}", self.ttl_live)
        items = data.get("items", [])
        if not items:
            return None
        odds = items[0]
        home_odds = odds.get("homeTeamOdds", {})
        away_odds = odds.get("awayTeamOdds", {})
        draw_odds = odds.get("drawOdds", {})
        return OddsSnapshot(
            home_implied=self._american_to_implied(home_odds.get("moneyLine")),
            away_implied=self._american_to_implied(away_odds.get("moneyLine")),
            draw_implied=self._american_to_implied(draw_odds.get("moneyLine")),
            current_home=self._american_to_implied(home_odds.get("moneyLine")),
            source="espn",
        )

    def fetch_probabilities(self, event_id: str, competition_id: str) -> float | None:
        url = (
            f"{self.base_core}/{self.league}/events/{event_id}"
            f"/competitions/{competition_id}/probabilities"
        )
        data = self._get_json(url, f"espn:prob:{event_id}", self.ttl_live)
        items = data.get("items", [])
        if not items:
            return None
        last = items[-1]
        home = last.get("homeWinPercentage")
        if home is not None:
            return float(home)
        return None

    def fetch_officials(self, event_id: str, competition_id: str) -> str:
        url = (
            f"{self.base_core}/{self.league}/events/{event_id}"
            f"/competitions/{competition_id}/officials"
        )
        data = self._get_json(url, f"espn:officials:{event_id}", self.ttl_static)
        items = data.get("items", [])
        if not items:
            return ""
        official = items[0]
        return official.get("displayName", official.get("fullName", ""))

    def fetch_plays(self, event_id: str, competition_id: str) -> list[dict[str, Any]]:
        url = (
            f"{self.base_core}/{self.league}/events/{event_id}"
            f"/competitions/{competition_id}/plays?limit=500"
        )
        data = self._get_json(url, f"espn:plays:{event_id}", self.ttl_live)
        return data.get("items", [])

    def _parse_event(self, event: dict[str, Any]) -> MatchEvent:
        competition = (event.get("competitions") or [{}])[0]
        competitors = competition.get("competitors", [])
        home = self._parse_competitor(self._find_competitor(competitors, "home"))
        away = self._parse_competitor(self._find_competitor(competitors, "away"))
        status_type = event.get("status", {}).get("type", {})
        venue = competition.get("venue", {})
        event_id = str(event.get("id", ""))
        competition_id = str(competition.get("id", ""))
        odds = self.fetch_odds(event_id, competition_id) if event_id and competition_id else None
        win_prob = (
            self.fetch_probabilities(event_id, competition_id)
            if event_id and competition_id
            else None
        )
        referee = (
            self.fetch_officials(event_id, competition_id)
            if event_id and competition_id
            else ""
        )
        return MatchEvent(
            match_id=event_id,
            home=home,
            away=away,
            status=status_type.get("description", status_type.get("name", "scheduled")),
            date=event.get("date", ""),
            stage=event.get("season", {}).get("slug", ""),
            venue=venue.get("fullName", ""),
            competition_id=competition_id,
            win_probability_home=win_prob,
            odds=odds,
            referee=referee,
            source="espn",
            raw=event,
        )

    @staticmethod
    def _find_competitor(competitors: list[dict[str, Any]], home_away: str) -> dict[str, Any]:
        for competitor in competitors:
            if competitor.get("homeAway") == home_away:
                return competitor
        return competitors[0] if competitors else {}

    def _parse_competitor(self, competitor: dict[str, Any]) -> TeamSnapshot:
        team = competitor.get("team", {})
        score = competitor.get("score")
        return TeamSnapshot(
            team_id=str(team.get("id", "")),
            name=team.get("displayName", team.get("name", "")),
            abbreviation=team.get("abbreviation", ""),
            score=int(score) if score not in (None, "") else None,
            source="espn",
        )

    @staticmethod
    def _american_to_implied(value: Any) -> float | None:
        if value in (None, ""):
            return None
        odds = float(value)
        if odds > 0:
            return 100.0 / (odds + 100.0)
        return abs(odds) / (abs(odds) + 100.0)
