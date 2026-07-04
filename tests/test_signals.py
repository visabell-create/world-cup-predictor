"""Tests for signal computation."""

import pandas as pd

from src.signals import apply_all_signals
from src.signals.fatigue import compute as fatigue_compute
from src.signals.tactical_matchup import compute as tactical_compute
from src.signals.telemetry import apply_hidden_telemetry_corrections


def _sample_row() -> pd.Series:
    return pd.Series(
        {
            "minutes_last_5_home": 500,
            "minutes_last_5_away": 400,
            "travel_hours_home": 8,
            "travel_hours_away": 2,
            "recovery_days_home": 2,
            "recovery_days_away": 4,
            "extra_time_played_home": 30,
            "extra_time_played_away": 0,
            "home_possession": 60,
            "away_possession": 40,
            "home_press_intensity": 0.7,
            "away_press_intensity": 0.4,
            "home_block_height": 0.4,
            "away_block_height": 0.7,
            "home_counter_efficiency": 0.6,
            "away_counter_efficiency": 0.5,
            "home_corners": 6,
            "away_corners": 4,
            "home_fk_xg": 0.2,
            "away_fk_xg": 0.1,
            "home_aerial_win_rate": 0.55,
            "away_aerial_win_rate": 0.45,
            "home_xg_proxy": 1.8,
            "away_xg_proxy": 1.2,
            "home_xg_against_proxy": 0.9,
            "away_xg_against_proxy": 1.1,
            "stage": "Quarter-finals",
            "home_matches_played": 5,
            "home_team": "Argentina",
            "away_team": "France",
            "referee": "Szymon Marciniak",
            "home_gk_save_pct": 0.72,
            "away_gk_save_pct": 0.68,
            "top_3_player_xg": 1.0,
            "players_on_bench": 7,
            "injuries_count": 1,
            "days_rest_home": 3,
            "days_rest_away": 4,
            "espn_win_prob_home": 0.55,
            "odds_implied_home": 0.52,
            "opening_odds_home": 0.45,
            "current_odds_home": 0.52,
            "coach_win_rate": 0.6,
            "fan_sentiment": 0.7,
            "field_width_meters": 64,
            "weather_temp_celsius": 30,
        }
    )


def test_fatigue_index_bounded():
    value = fatigue_compute(_sample_row())
    assert 0.0 <= value <= 1.0


def test_tactical_matchup_bounded():
    value = tactical_compute(_sample_row())
    assert 0.0 <= value <= 1.0


def test_apply_all_signals_adds_columns():
    df = pd.DataFrame([_sample_row().to_dict()])
    result = apply_all_signals(df)
    assert "fatigue_accumulation_index" in result.columns
    assert "calibrated_score" in result.columns
    assert "depth_risk_factor" in result.columns


def test_telemetry_heat_correction():
    df = pd.DataFrame([_sample_row().to_dict()])
    result = apply_hidden_telemetry_corrections(df)
    assert result.loc[0, "fan_sentiment"] < 0.7
