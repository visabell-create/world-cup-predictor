"""Hidden telemetry corrections."""

from __future__ import annotations

import pandas as pd

from src.config import load_config


def apply_hidden_telemetry_corrections(df_match_matrix: pd.DataFrame) -> pd.DataFrame:
    config = load_config()
    telemetry = config.get("telemetry", {})
    heat_threshold = telemetry.get("heat_threshold_celsius", 28.0)
    narrow_width = telemetry.get("narrow_pitch_width_m", 66.0)

    df = df_match_matrix.copy()
    df["depth_risk_factor"] = df.get("players_on_bench", 7) * (
        1.0 - df.get("injuries_count", 0) * 0.15
    )
    narrow_mask = df.get("field_width_meters", 68) < narrow_width
    if "top_3_player_xg" in df.columns:
        df.loc[narrow_mask, "top_3_player_xg"] = df.loc[narrow_mask, "top_3_player_xg"] * 0.92

    hot_mask = df.get("weather_temp_celsius", 22) > heat_threshold
    if "coach_win_rate" in df.columns:
        df.loc[hot_mask, "coach_win_rate"] = df.loc[hot_mask, "coach_win_rate"] * 0.95
    if "fan_sentiment" in df.columns:
        df.loc[hot_mask, "fan_sentiment"] = df.loc[hot_mask, "fan_sentiment"] * 0.98

    df["calibrated_score"] = (
        df.get("top_3_player_xg", 1.0) * 0.40
        + df.get("coach_win_rate", 0.5) * 0.30
        + df.get("depth_risk_factor", 0.5) * 0.20
        + df.get("fan_sentiment", 0.5) * 0.10
    )
    return df
