"""Momentum velocity score (xG trend)."""

from __future__ import annotations

import pandas as pd


def compute(row: pd.Series) -> float:
    home_xg = row.get("home_xg_proxy", 1.2)
    away_xg = row.get("away_xg_proxy", 1.2)
    home_trend = home_xg / max(0.5, row.get("home_xg_against_proxy", 1.0))
    away_trend = away_xg / max(0.5, row.get("away_xg_against_proxy", 1.0))
    velocity = (home_trend - away_trend + 1) / 2
    return round(max(0.0, min(1.0, velocity)), 4)
