"""Sharp money divergence."""

from __future__ import annotations

import pandas as pd


def compute(row: pd.Series) -> float:
    opening = row.get("opening_odds_home")
    current = row.get("current_odds_home")
    if opening is None or current is None:
        return 0.5
    movement = abs(float(current) - float(opening))
    return round(min(1.0, movement * 5), 4)
