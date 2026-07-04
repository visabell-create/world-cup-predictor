"""UI formatting helpers."""

from __future__ import annotations

from typing import Any

import pandas as pd


def pct(value: Any, digits: int = 1, missing: str = "—") -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return missing
    try:
        v = float(value)
        if v > 1.0:
            v = v / 100.0
        return f"{v * 100:.{digits}f}%"
    except (TypeError, ValueError):
        return missing


def winner_label(home: str, away: str, p_home: float, p_draw: float) -> tuple[str, str, float]:
    p_home = float(p_home or 0)
    p_draw = float(p_draw or 0)
    p_away = max(0.0, 1.0 - p_home - p_draw)
    if p_home >= p_away and p_home >= p_draw:
        return home, "home", p_home
    if p_away >= p_home and p_away >= p_draw:
        return away, "away", p_away
    return "Draw", "draw", p_draw


def confidence_tier(confidence: float) -> str:
    if confidence >= 0.75:
        return "high"
    if confidence >= 0.55:
        return "medium"
    return "low"
