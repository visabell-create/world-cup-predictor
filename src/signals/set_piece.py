"""Set-piece dominance differential."""

from __future__ import annotations

import pandas as pd


def compute(row: pd.Series) -> float:
    home_sp = (
        row.get("home_corners", 5) * 0.02
        + row.get("home_fk_xg", 0.15) * 2
        + row.get("home_aerial_win_rate", 0.5)
    )
    away_sp = (
        row.get("away_corners", 5) * 0.02
        + row.get("away_fk_xg", 0.15) * 2
        + row.get("away_aerial_win_rate", 0.5)
    )
    diff = home_sp - away_sp
    return round((diff + 1) / 2, 4)
