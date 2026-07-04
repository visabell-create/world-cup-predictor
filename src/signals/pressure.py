"""Pressure resilience index."""

from __future__ import annotations

import pandas as pd


def compute(row: pd.Series) -> float:
    stage = str(row.get("stage", "")).lower()
    knockout_boost = 0.15 if any(k in stage for k in ("final", "semi", "quarter", "round of")) else 0.0
    experience = min(1.0, row.get("home_matches_played", 0) / 10)
    return round(min(1.0, 0.5 + knockout_boost + experience * 0.3), 4)
