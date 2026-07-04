"""Goalkeeper form index."""

from __future__ import annotations

import pandas as pd


def compute(row: pd.Series) -> float:
    home_gk = row.get("home_gk_save_pct", 0.68) + row.get("home_psxg_saved", 0) * 0.1
    away_gk = row.get("away_gk_save_pct", 0.68) + row.get("away_psxg_saved", 0) * 0.1
    return round((home_gk - away_gk + 1) / 2, 4)
