"""Bench impact index."""

from __future__ import annotations

import pandas as pd


def compute(row: pd.Series) -> float:
    bench_depth = row.get("players_on_bench", 7) / 12
    injury_penalty = row.get("injuries_count", 0) * 0.05
    return round(max(0.0, min(1.0, bench_depth - injury_penalty)), 4)
