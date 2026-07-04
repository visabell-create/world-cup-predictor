"""StatsBomb open data adapter (historical WC matches)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import ROOT


class StatsBombAdapter:
    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or ROOT / "data" / "manual" / "statsbomb"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_matches(self) -> pd.DataFrame:
        records: list[dict[str, Any]] = []
        for path in self.data_dir.glob("*.json"):
            with path.open(encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, list):
                records.extend(payload)
            elif isinstance(payload, dict):
                records.append(payload)
        if not records:
            return pd.DataFrame(
                columns=[
                    "match_id",
                    "home_team",
                    "away_team",
                    "home_xg",
                    "away_xg",
                    "home_goals",
                    "away_goals",
                    "stage",
                    "date",
                    "went_to_penalties",
                    "home_pen_score",
                    "away_pen_score",
                ]
            )
        return pd.DataFrame(records)

    def get_team_history(self, team_name: str) -> pd.DataFrame:
        df = self.load_matches()
        if df.empty:
            return df
        mask = (df["home_team"].str.lower() == team_name.lower()) | (
            df["away_team"].str.lower() == team_name.lower()
        )
        return df[mask].sort_values("date")
