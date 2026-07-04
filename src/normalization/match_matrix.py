"""Unified per-match feature matrix builder."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.ingestion.base import MatchEvent
from src.ingestion.espn import EspnDataAdapter
from src.ingestion.fbref import FBrefAdapter
from src.ingestion.statsbomb import StatsBombAdapter
from src.normalization.team_resolver import ReconciliationResult, TeamResolver


class MatchMatrixBuilder:
    def __init__(self) -> None:
        self.espn = EspnDataAdapter()
        self.fbref = FBrefAdapter()
        self.statsbomb = StatsBombAdapter()
        self.resolver = TeamResolver()

    def build_row(
        self,
        espn_event: MatchEvent,
        reconciliation: ReconciliationResult | None = None,
    ) -> dict[str, Any]:
        home_stats = self.fbref.get_team_stats(espn_event.home.name)
        away_stats = self.fbref.get_team_stats(espn_event.away.name)
        home_history = self.statsbomb.get_team_history(espn_event.home.name)
        away_history = self.statsbomb.get_team_history(espn_event.away.name)
        plays = []
        if espn_event.match_id and espn_event.competition_id:
            plays = self.espn.fetch_plays(espn_event.match_id, espn_event.competition_id)

        row: dict[str, Any] = {
            "match_id": espn_event.match_id,
            "home_team": espn_event.home.name,
            "away_team": espn_event.away.name,
            "home_team_id": espn_event.home.team_id,
            "away_team_id": espn_event.away.team_id,
            "home_score": espn_event.home.score,
            "away_score": espn_event.away.score,
            "status": espn_event.status,
            "date": espn_event.date,
            "stage": espn_event.stage,
            "venue": espn_event.venue,
            "referee": espn_event.referee,
            "espn_win_prob_home": espn_event.win_probability_home,
            "home_xg_proxy": home_stats.get("xg_per_match", 1.2),
            "away_xg_proxy": away_stats.get("xg_per_match", 1.2),
            "home_xg_against_proxy": home_stats.get("xg_against_per_match", 1.0),
            "away_xg_against_proxy": away_stats.get("xg_against_per_match", 1.0),
            "home_corners": home_stats.get("corners_per_match", 5.0),
            "away_corners": away_stats.get("corners_per_match", 5.0),
            "home_fk_xg": home_stats.get("fk_xg", 0.15),
            "away_fk_xg": away_stats.get("fk_xg", 0.15),
            "home_aerial_win_rate": home_stats.get("aerial_win_rate", 0.5),
            "away_aerial_win_rate": away_stats.get("aerial_win_rate", 0.5),
            "home_possession": home_stats.get("possession_pct", 50.0),
            "away_possession": away_stats.get("possession_pct", 50.0),
            "home_press_intensity": home_stats.get("press_intensity", 0.5),
            "away_press_intensity": away_stats.get("press_intensity", 0.5),
            "home_block_height": home_stats.get("block_height", 0.5),
            "away_block_height": away_stats.get("block_height", 0.5),
            "home_counter_efficiency": home_stats.get("counter_efficiency", 0.5),
            "away_counter_efficiency": away_stats.get("counter_efficiency", 0.5),
            "home_gk_save_pct": home_stats.get("gk_save_pct", 0.68),
            "away_gk_save_pct": away_stats.get("gk_save_pct", 0.68),
            "home_psxg_saved": home_stats.get("psxg_saved", 0.0),
            "away_psxg_saved": away_stats.get("psxg_saved", 0.0),
            "home_matches_played": len(home_history),
            "away_matches_played": len(away_history),
            "plays_count": len(plays),
            "plays": plays,
            "injuries_count": 0,
            "players_on_bench": 7,
            "field_width_meters": 68.0,
            "weather_temp_celsius": 22.0,
            "top_3_player_xg": home_stats.get("xg_per_match", 1.2) * 0.6,
            "coach_win_rate": 0.5,
            "fan_sentiment": 0.5,
            "days_rest_home": 4,
            "days_rest_away": 4,
            "minutes_last_5_home": 450,
            "minutes_last_5_away": 450,
            "travel_hours_home": 2.0,
            "travel_hours_away": 2.0,
            "recovery_days_home": 3,
            "recovery_days_away": 3,
            "extra_time_played_home": 0,
            "extra_time_played_away": 0,
            "opening_odds_home": espn_event.odds.opening_home if espn_event.odds else None,
            "current_odds_home": espn_event.odds.current_home if espn_event.odds else None,
            "odds_implied_home": espn_event.odds.home_implied if espn_event.odds else None,
            "source_divergence_penalty": reconciliation.divergence_penalty if reconciliation else 0.0,
        }
        return row

    def build_dataframe(self, events: list[MatchEvent], reconciliations: list[ReconciliationResult]) -> pd.DataFrame:
        recon_map = {r.match_id: r for r in reconciliations}
        rows = [self.build_row(event, recon_map.get(event.match_id)) for event in events]
        return pd.DataFrame(rows)
