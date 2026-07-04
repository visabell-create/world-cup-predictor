"""Supplemental FBref-style proxy adapter (CSV/manual fallback)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.config import ROOT


class FBrefAdapter:
    def __init__(self, data_path: Path | None = None) -> None:
        self.data_path = data_path or ROOT / "data" / "manual" / "team_xg_proxy.csv"
        self._df = self._load()

    def _load(self) -> pd.DataFrame:
        if self.data_path.exists():
            return pd.read_csv(self.data_path)
        return pd.DataFrame(
            columns=[
                "team_name",
                "xg_per_match",
                "xg_against_per_match",
                "corners_per_match",
                "fk_xg",
                "aerial_win_rate",
                "possession_pct",
                "press_intensity",
                "block_height",
                "counter_efficiency",
                "gk_save_pct",
                "psxg_saved",
            ]
        )

    def get_team_stats(self, team_name: str) -> dict[str, Any]:
        if self._df.empty:
            return self._default_stats(team_name)
        row = self._df[self._df["team_name"].str.lower() == team_name.lower()]
        if row.empty:
            return self._default_stats(team_name)
        return row.iloc[0].to_dict()

    @staticmethod
    def _default_stats(team_name: str) -> dict[str, Any]:
        return {
            "team_name": team_name,
            "xg_per_match": 1.2,
            "xg_against_per_match": 1.0,
            "corners_per_match": 5.0,
            "fk_xg": 0.15,
            "aerial_win_rate": 0.5,
            "possession_pct": 50.0,
            "press_intensity": 0.5,
            "block_height": 0.5,
            "counter_efficiency": 0.5,
            "gk_save_pct": 0.68,
            "psxg_saved": 0.0,
        }
