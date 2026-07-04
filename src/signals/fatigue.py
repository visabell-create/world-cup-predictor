"""Fatigue Accumulation Index (FAI)."""

from __future__ import annotations

import pandas as pd


def compute(row: pd.Series) -> float:
    minutes_load = (row.get("minutes_last_5_home", 450) + row.get("minutes_last_5_away", 450)) / 2
    travel_load = 1.0 + (row.get("travel_hours_home", 2) + row.get("travel_hours_away", 2)) / 20
    recovery = max(1.0, (row.get("recovery_days_home", 3) + row.get("recovery_days_away", 3)) / 2)
    extra = row.get("extra_time_played_home", 0) + row.get("extra_time_played_away", 0)
    fai = (minutes_load * travel_load * (1 + extra / 90)) / (recovery * 100)
    return round(min(1.0, fai), 4)
