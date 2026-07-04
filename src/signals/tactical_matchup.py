"""Tactical matchup compatibility score."""

from __future__ import annotations

import pandas as pd


def compute(row: pd.Series) -> float:
    home_possession = row.get("home_possession", 50) / 100
    away_block = row.get("away_block_height", 0.5)
    home_press = row.get("home_press_intensity", 0.5)
    away_counter = row.get("away_counter_efficiency", 0.5)
    away_possession = row.get("away_possession", 50) / 100
    home_block = row.get("home_block_height", 0.5)
    home_counter = row.get("home_counter_efficiency", 0.5)
    away_press = row.get("away_press_intensity", 0.5)

    home_vs_away = home_possession * (1 - away_block) + home_press * away_counter
    away_vs_home = away_possession * (1 - home_block) + away_press * home_counter
    score = (home_vs_away - away_vs_home + 1) / 2
    return round(max(0.0, min(1.0, score)), 4)
