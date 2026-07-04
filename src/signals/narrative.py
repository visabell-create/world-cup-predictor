"""Narrative pressure signal."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import ROOT

NARRATIVE_TAGS_PATH = ROOT / "data" / "manual" / "narrative_tags.csv"


def compute(row: pd.Series) -> float:
    home = str(row.get("home_team", "")).lower()
    away = str(row.get("away_team", "")).lower()
    pressure = 0.0
    if NARRATIVE_TAGS_PATH.exists():
        tags = pd.read_csv(NARRATIVE_TAGS_PATH)
        for _, tag_row in tags.iterrows():
            team = str(tag_row.get("team_name", "")).lower()
            if team in (home, away):
                pressure += float(tag_row.get("narrative_pressure", 0))
    host_keywords = ("united states", "mexico", "canada")
    if any(k in home or k in away for k in host_keywords):
        pressure += 0.1
    return round(min(1.0, pressure), 4)
