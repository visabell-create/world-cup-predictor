"""Google Sports via headless browser only."""

from __future__ import annotations

import logging
from typing import Any

from src.config import load_config
from src.ingestion.base import DataAdapter, MatchEvent, StandingRow, TeamSnapshot
from src.ingestion.google_browser import GoogleBrowser

logger = logging.getLogger(__name__)


class GoogleSportsAdapter(DataAdapter):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or load_config()
        self.browser = GoogleBrowser(self.config)
        self.queries = self.config.get("google_browser", {}).get("queries", {})

    def close(self) -> None:
        self.browser.close()

    @property
    def available(self) -> bool:
        return True

    def fetch_scoreboard(self, date_str: str | None = None) -> list[MatchEvent]:
        query = self.queries.get("results", "FIFA World Cup results today")
        result = self.browser.search(query)
        if result.get("error"):
            logger.warning("Google scoreboard fetch: %s", result["error"])
            return []
        return self._events_from_text(result)

    def fetch_standings(self) -> list[StandingRow]:
        query = self.queries.get("standings", "FIFA World Cup standings")
        result = self.browser.search(query)
        return []

    def fetch_match(self, home: str, away: str) -> MatchEvent | None:
        template = self.queries.get("match_template", "{home} vs {away}")
        result = self.browser.search(template.format(home=home, away=away))
        if result.get("error"):
            return None
        return MatchEvent(
            match_id=f"google:{home}:{away}",
            home=TeamSnapshot(
                team_id=home.lower().replace(" ", "-"),
                name=home,
                score=result.get("home_score"),
                source="google",
            ),
            away=TeamSnapshot(
                team_id=away.lower().replace(" ", "-"),
                name=away,
                score=result.get("away_score"),
                source="google",
            ),
            status=result.get("status", "unknown"),
            source="google",
            raw=result,
        )

    def _events_from_text(self, result: dict[str, Any]) -> list[MatchEvent]:
        return []
