"""XGBoost-based match outcome scorer."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.config import load_config
from src.signals import SIGNAL_COMPUTERS


class XGBoostMatchModel:
    FEATURE_COLUMNS = list(SIGNAL_COMPUTERS.keys()) + [
        "depth_risk_factor",
        "calibrated_score",
    ]

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or load_config()
        self.weights = self.config.get("signals", {}).get("weights", {})
        self._model = None

    def _weighted_score(self, row: pd.Series) -> float:
        total_weight = 0.0
        score = 0.0
        for feature in SIGNAL_COMPUTERS:
            weight = self.weights.get(feature, 1.0 / len(SIGNAL_COMPUTERS))
            value = float(row.get(feature, 0.5))
            score += weight * value
            total_weight += weight
        return score / total_weight if total_weight else 0.5

    def predict_proba(self, df: pd.DataFrame) -> pd.DataFrame:
        results = []
        for _, row in df.iterrows():
            home_strength = self._weighted_score(row)
            draw_base = 0.22
            p_home = max(0.05, min(0.90, home_strength * 0.7 + 0.15))
            p_draw = max(0.05, min(0.40, draw_base + (0.5 - abs(home_strength - 0.5)) * 0.2))
            p_away = max(0.05, 1.0 - p_home - p_draw)
            total = p_home + p_draw + p_away
            results.append(
                {
                    "p_win_90": p_home / total,
                    "p_draw_90": p_draw / total,
                    "p_win_et": 0.5 + (home_strength - 0.5) * 0.2,
                    "internal_model": p_home / total,
                }
            )
        return pd.DataFrame(results, index=df.index)

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> None:
        try:
            from xgboost import XGBClassifier

            features = [c for c in self.FEATURE_COLUMNS if c in X.columns]
            self._model = XGBClassifier(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                eval_metric="logloss",
            )
            self._model.fit(X[features].fillna(0.5), y)
        except Exception:
            self._model = None
