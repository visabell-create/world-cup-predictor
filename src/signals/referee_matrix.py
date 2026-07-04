"""Referee-team interaction matrix."""

from __future__ import annotations

import pandas as pd


def compute(row: pd.Series) -> float:
    referee = str(row.get("referee", "")).lower()
    physical_teams = row.get("home_press_intensity", 0.5) + row.get("away_press_intensity", 0.5)
    if not referee:
        return 0.5
    strict_refs = ("oliver", "turpin", "szymon")
    is_strict = any(name in referee for name in strict_refs)
    if is_strict and physical_teams > 1.0:
        return 0.35
    return 0.55
