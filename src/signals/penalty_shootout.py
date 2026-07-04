"""Penalty shootout probability engine."""

from __future__ import annotations

import pandas as pd


def compute(row: pd.Series) -> float:
    home_gk = row.get("home_gk_save_pct", 0.68)
    away_gk = row.get("away_gk_save_pct", 0.68)
    home_conv = 0.75
    away_conv = 0.75
    home_edge = home_gk * home_conv
    away_edge = away_gk * away_conv
    return round((home_edge - away_edge + 1) / 2, 4)
