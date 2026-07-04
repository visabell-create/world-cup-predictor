"""Star dependency risk."""

from __future__ import annotations

import pandas as pd


def compute(row: pd.Series) -> float:
    top3_share = row.get("top_3_player_xg", 0.7) / max(0.1, row.get("home_xg_proxy", 1.2))
    fragility = min(1.0, top3_share)
    return round(fragility, 4)
