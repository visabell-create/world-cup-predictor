"""Prediction confidence spread."""

from __future__ import annotations

import pandas as pd


def compute(row: pd.Series) -> float:
    signals = []
    if row.get("espn_win_prob_home") is not None:
        signals.append(float(row["espn_win_prob_home"]))
    if row.get("odds_implied_home") is not None:
        signals.append(float(row["odds_implied_home"]))
    internal = (row.get("home_xg_proxy", 1.2) / (row.get("home_xg_proxy", 1.2) + row.get("away_xg_proxy", 1.2)))
    signals.append(internal)
    if len(signals) < 2:
        return 0.5
    spread = max(signals) - min(signals)
    return round(1.0 - min(1.0, spread * 2), 4)
