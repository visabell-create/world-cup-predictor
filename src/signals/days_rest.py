"""Recovery-to-performance curve."""

from __future__ import annotations

import pandas as pd


def compute(row: pd.Series) -> float:
    home_rest = row.get("days_rest_home", 4)
    away_rest = row.get("days_rest_away", 4)
    home_effect = min(1.0, home_rest / 5)
    away_effect = min(1.0, away_rest / 5)
    return round((home_effect - away_effect + 1) / 2, 4)
