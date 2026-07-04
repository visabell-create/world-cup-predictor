"""Signal Agreement Index (SAI)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.config import load_config


class SignalAgreementIndex:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        cfg = config or load_config()
        sai_cfg = cfg.get("sai", {})
        self.min_threshold = sai_cfg.get("min_agreement_threshold", 0.65)
        self.divergence_penalty = sai_cfg.get("divergence_penalty", 0.15)

    def compute(self, row: pd.Series, probs: dict[str, float | None]) -> dict[str, float]:
        signals: list[float] = []
        for key in ("internal_model", "espn_win_prob", "espn_odds_implied", "google_implied", "elo", "xg_rating"):
            value = probs.get(key)
            if value is not None:
                signals.append(float(value))

        if len(signals) < 2:
            sai = 0.5
        else:
            std = float(np.std(signals))
            sai = max(0.0, 1.0 - std * 2)

        penalty = float(row.get("source_divergence_penalty", 0.0))
        confidence = max(0.0, sai - penalty)
        high_uncertainty = confidence < self.min_threshold
        return {
            "sai": round(sai, 4),
            "confidence": round(confidence, 4),
            "high_uncertainty": float(high_uncertainty),
            "divergence_penalty_applied": round(penalty, 4),
        }

    def apply_confidence_adjustment(self, p_home: float, confidence: float) -> float:
        shrink = 0.5 + confidence * 0.5
        return 0.5 + (p_home - 0.5) * shrink
