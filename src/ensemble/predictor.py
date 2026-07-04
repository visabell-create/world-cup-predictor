"""Game-day prediction orchestrator with Google signal contrast as final answer."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.config import load_config
from src.ensemble.bayesian import BayesianEngine
from src.ensemble.google_signal_contrast import GoogleSignalContrast
from src.ensemble.sai import SignalAgreementIndex
from src.ensemble.xgboost_model import XGBoostMatchModel
from src.tournament.penalty_engine import PenaltyEngine


class MatchPredictor:
    def __init__(self, config: dict[str, Any] | None = None, use_google: bool = True) -> None:
        self.config = config or load_config()
        self.model = XGBoostMatchModel(self.config)
        self.bayesian = BayesianEngine(self.config.get("bayesian", {}))
        self.sai = SignalAgreementIndex(self.config)
        self.penalty = PenaltyEngine()
        self.use_google = use_google
        self.google_contrast = GoogleSignalContrast(self.config) if use_google else None
        self.last_contrasts: list[dict[str, Any]] = []

    def close(self) -> None:
        if self.google_contrast:
            self.google_contrast.close()

    def predict_match(self, row: pd.Series, contrast: dict[str, Any] | None = None) -> dict[str, Any]:
        probs_df = self.model.predict_proba(pd.DataFrame([row]))
        base = probs_df.iloc[0]
        p_win_pens = self.penalty.predict(row)

        google_implied = None
        if contrast:
            google_implied = float(contrast["google_signal_mean"])

        signal_probs = {
            "internal_model": float(base["internal_model"]),
            "espn_win_prob": float(row["espn_win_prob_home"]) if pd.notna(row.get("espn_win_prob_home")) else None,
            "espn_odds_implied": float(row["odds_implied_home"]) if pd.notna(row.get("odds_implied_home")) else None,
            "google_implied": google_implied,
            "elo": float(row.get("home_xg_proxy", 1.2) / (row.get("home_xg_proxy", 1.2) + row.get("away_xg_proxy", 1.2))),
            "xg_rating": float(row.get("home_xg_proxy", 1.2) / (row.get("home_xg_proxy", 1.2) + row.get("away_xg_proxy", 1.2))),
        }
        sai_result = self.sai.compute(row, signal_probs)

        p_home_internal = float(base["p_win_90"])
        if contrast and self.google_contrast:
            final_blend = self.google_contrast.final_prediction(
                p_home_internal, contrast, sai_result["confidence"]
            )
            p_home_final = final_blend["p_win_90_final"]
        else:
            p_home_final = self.sai.apply_confidence_adjustment(p_home_internal, sai_result["confidence"])
            final_blend = {}

        team_key = f"{row['home_team']}:{row['away_team']}"
        posterior = self.bayesian.update(team_key, likelihood=p_home_final, evidence="google_contrast_final")

        result = {
            "match_id": row["match_id"],
            "home_team": row["home_team"],
            "away_team": row["away_team"],
            "p_win_90": p_home_final,
            "p_win_90_internal": round(p_home_internal, 4),
            "p_draw_90": round(float(base["p_draw_90"]), 4),
            "p_win_et": round(float(base["p_win_et"]), 4),
            "p_win_pens": round(p_win_pens, 4),
            "bayesian_posterior": round(posterior, 4),
            "sai": sai_result["sai"],
            "confidence": sai_result["confidence"],
            "high_uncertainty": bool(sai_result["high_uncertainty"]),
        }
        if contrast:
            result["signal_alignment"] = contrast["signal_alignment"]
            result["chart_path"] = contrast["chart_path"]
            result.update(final_blend)
        return result

    def predict_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.google_contrast:
            self.last_contrasts = self.google_contrast.contrast_dataframe(df)
        else:
            self.last_contrasts = []
        contrast_map = {c["match_id"]: c for c in self.last_contrasts}
        predictions = [
            self.predict_match(row, contrast_map.get(str(row["match_id"])))
            for _, row in df.iterrows()
        ]
        return pd.DataFrame(predictions)
