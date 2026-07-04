"""Penalty shootout probability engine."""

from __future__ import annotations

import pandas as pd


class PenaltyEngine:
    def predict(self, row: pd.Series) -> float:
        home_gk = row.get("home_gk_save_pct", 0.68)
        away_gk = row.get("away_gk_save_pct", 0.68)
        home_conv = 0.75
        away_conv = 0.75
        home_score = home_conv * (1 - away_gk)
        away_score = away_conv * (1 - home_gk)
        total = home_score + away_score
        if total == 0:
            return 0.5
        return round(home_score / total, 4)
