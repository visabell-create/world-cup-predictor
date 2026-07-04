"""ESPN enrichment for UI: logos, colors, top players."""

from __future__ import annotations

from typing import Any

from src.config import load_config
from src.ingestion.espn import EspnDataAdapter


def _player_headshot(athlete: dict[str, Any]) -> str | None:
    headshot = athlete.get("headshot") or {}
    href = headshot.get("href") if isinstance(headshot, dict) else None
    return href or None


def _player_priority(athlete: dict[str, Any]) -> int:
    pos = athlete.get("position", {}) or {}
    abbr = (pos.get("abbreviation") or "").upper()
    priority = {"F": 0, "M": 1, "D": 2, "G": 3}
    has_photo = 1 if _player_headshot(athlete) else 0
    return priority.get(abbr, 4) - has_photo * 10


def fetch_top_players(team_id: str, limit: int = 3) -> list[dict[str, Any]]:
    if not team_id:
        return []
    espn = EspnDataAdapter()
    roster = espn.fetch_team_roster(team_id)
    athletes = roster.get("athletes", [])
    if not athletes:
        return []

    ranked = sorted(athletes, key=_player_priority)
    players: list[dict[str, Any]] = []
    for athlete in ranked:
        if len(players) >= limit:
            break
        name = athlete.get("displayName") or athlete.get("fullName", "")
        if not name:
            continue
        pos = athlete.get("position", {}) or {}
        players.append(
            {
                "name": name,
                "position": pos.get("abbreviation", pos.get("displayName", "")),
                "jersey": athlete.get("jersey", ""),
                "age": athlete.get("age"),
                "headshot": _player_headshot(athlete),
            }
        )
    return players


def extract_team_meta_from_event(espn_event_raw: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Pull logos and colors from raw ESPN scoreboard event."""
    meta: dict[str, dict[str, Any]] = {}
    competition = (espn_event_raw.get("competitions") or [{}])[0]
    for competitor in competition.get("competitors", []):
        side = competitor.get("homeAway", "home")
        team = competitor.get("team", {})
        meta[side] = {
            "team_id": str(team.get("id", "")),
            "name": team.get("displayName", team.get("name", "")),
            "abbreviation": team.get("abbreviation", ""),
            "logo": team.get("logo"),
            "color": team.get("color", "1e3a5f"),
            "alternate_color": team.get("alternateColor", "ffffff"),
            "score": competitor.get("score"),
        }
    return meta


def enrich_match(
    match_id: str,
    home_team_id: str,
    away_team_id: str,
    espn_events_raw: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    raw = espn_events_raw.get(str(match_id), {})
    team_meta = extract_team_meta_from_event(raw) if raw else {}
    home = team_meta.get("home", {})
    away = team_meta.get("away", {})
    home_id = home.get("team_id") or home_team_id
    away_id = away.get("team_id") or away_team_id
    return {
        "home_logo": home.get("logo"),
        "away_logo": away.get("logo"),
        "home_color": f"#{str(home.get('color', '1e3a5f')).lstrip('#')}",
        "away_color": f"#{str(away.get('color', 'c41e3a')).lstrip('#')}",
        "home_top_players": fetch_top_players(home_id, limit=3),
        "away_top_players": fetch_top_players(away_id, limit=3),
    }
