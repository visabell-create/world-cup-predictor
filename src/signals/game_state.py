"""Game state elasticity."""

from __future__ import annotations

import pandas as pd


def compute(row: pd.Series) -> float:
    home_xg = row.get("home_xg_proxy", 1.2)
    away_xg = row.get("away_xg_proxy", 1.2)
    trailing_boost = home_xg * 1.1
    leading_damp = away_xg * 0.9
    elasticity = (trailing_boost - leading_damp + 1) / 2
    return round(max(0.0, min(1.0, elasticity)), 4)
