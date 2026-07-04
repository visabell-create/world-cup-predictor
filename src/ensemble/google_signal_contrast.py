"""Per-signal Google contrast: headless search, compare, chart, final blend."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import ROOT, load_config
from src.ensemble.signal_chart import save_signal_contrast_chart
from src.ingestion.google_browser import GoogleBrowser
from src.signals import SIGNAL_COMPUTERS

logger = logging.getLogger(__name__)

SIGNAL_QUERIES: dict[str, str] = {
    "fatigue_accumulation_index": "{home} vs {away} squad fatigue injury minutes",
    "tactical_matchup_score": "{home} vs {away} tactical style possession press",
    "set_piece_differential": "{home} vs {away} set pieces corners free kick",
    "pressure_resilience_index": "{home} knockout pressure elimination record",
    "momentum_velocity": "{home} form trend last matches xG",
    "narrative_pressure": "{home} {away} World Cup narrative host pressure",
    "penalty_shootout_prob": "{home} {away} penalty shootout record goalkeeper",
    "referee_team_compatibility": "{home} vs {away} referee cards fouls",
    "game_state_elasticity": "{home} comeback trailing leading performance",
    "sharp_money_divergence": "{home} vs {away} betting odds line movement",
    "prediction_confidence_spread": "{home} vs {away} prediction odds favorite",
    "goalkeeper_form_index": "{home} goalkeeper saves form World Cup",
    "star_dependency_ratio": "{home} star player dependency goals",
    "bench_impact_index": "{home} bench depth substitutes impact",
    "days_rest_effect": "{home} vs {away} rest days recovery schedule",
}


class GoogleSignalContrast:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or load_config()
        self.browser = GoogleBrowser(self.config)
        self.chart_dir = ROOT / "data" / "cache" / "charts"
        self.log_path = ROOT / "data" / "cache" / "google_exceptions.log"
        self.chart_dir.mkdir(parents=True, exist_ok=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def close(self) -> None:
        self.browser.close()

    def _log_exception(self, match_id: str, signal: str, error: str) -> None:
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{match_id}|{signal}|{error}\n")
        logger.warning("Google signal exception [%s] %s: %s", match_id, signal, error)

    def contrast_row(self, row: pd.Series) -> dict[str, Any]:
        home = row["home_team"]
        away = row["away_team"]
        match_id = str(row["match_id"])
        contrasts: list[dict[str, Any]] = []
        google_values: list[float] = []
        internal_values: list[float] = []

        for signal_name, template in SIGNAL_QUERIES.items():
            internal = float(row.get(signal_name, 0.5))
            query = template.format(home=home, away=away)
            screenshot = self.chart_dir / f"{match_id}_{signal_name}.png"
            try:
                result = self.browser.search(query, screenshot_path=str(screenshot))
                if result.get("error"):
                    self._log_exception(match_id, signal_name, result["error"])
                google_val = float(result.get("home_bias", 0.5))
            except Exception as exc:
                self._log_exception(match_id, signal_name, str(exc))
                google_val = 0.5

            delta = round(internal - google_val, 4)
            contrasts.append(
                {
                    "signal": signal_name,
                    "internal": round(internal, 4),
                    "google": round(google_val, 4),
                    "delta": delta,
                }
            )
            google_values.append(google_val)
            internal_values.append(internal)

        chart_path = save_signal_contrast_chart(
            contrasts,
            match_id=match_id,
            home=home,
            away=away,
            output_dir=self.chart_dir,
        )

        google_mean = sum(google_values) / len(google_values) if google_values else 0.5
        internal_mean = sum(internal_values) / len(internal_values) if internal_values else 0.5
        alignment = 1.0 - min(1.0, sum(abs(c["delta"]) for c in contrasts) / len(contrasts))

        return {
            "match_id": match_id,
            "google_signal_mean": round(google_mean, 4),
            "internal_signal_mean": round(internal_mean, 4),
            "signal_alignment": round(alignment, 4),
            "contrasts": contrasts,
            "chart_path": str(chart_path),
        }

    def contrast_dataframe(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        results = []
        for _, row in df.iterrows():
            results.append(self.contrast_row(row))
        return results

    def final_prediction(
        self,
        internal_p_home: float,
        contrast: dict[str, Any],
        sai_confidence: float,
    ) -> dict[str, float]:
        google_prob = float(contrast["google_signal_mean"])
        alignment = float(contrast["signal_alignment"])
        blend_weight = 0.3 + alignment * 0.4
        final = internal_p_home * (1 - blend_weight) + google_prob * blend_weight
        final = 0.5 + (final - 0.5) * (0.5 + sai_confidence * 0.5)
        return {
            "p_win_90_final": round(max(0.05, min(0.95, final)), 4),
            "google_blend_weight": round(blend_weight, 4),
            "google_signal_mean": google_prob,
            "signal_alignment": alignment,
        }
