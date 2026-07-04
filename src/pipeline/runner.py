"""Shared pipeline runner for CLI and UI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import ROOT, load_config
from src.ensemble.monte_carlo import TournamentMonteCarlo
from src.ensemble.predictor import MatchPredictor
from src.ingestion.espn import EspnDataAdapter
from src.ingestion.google_sports import GoogleSportsAdapter
from src.normalization.match_matrix import MatchMatrixBuilder
from src.normalization.team_resolver import TeamResolver
from src.signals import apply_all_signals, SIGNAL_COMPUTERS
from src.ui.espn_enrichment import enrich_match


def _build_match_enrichment(espn_events, featured: pd.DataFrame) -> dict[str, dict]:
    raw_map = {str(e.match_id): e.raw for e in espn_events}
    enrichment: dict[str, dict] = {}
    for _, row in featured.iterrows():
        mid = str(row["match_id"])
        enrichment[mid] = enrich_match(
            mid,
            str(row.get("home_team_id", "")),
            str(row.get("away_team_id", "")),
            raw_map,
        )
    return enrichment


def load_cached_predictions() -> dict[str, Any] | None:
    path = ROOT / "data" / "cache" / "predictions_latest.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def load_exception_log() -> list[str]:
    path = ROOT / "data" / "cache" / "google_exceptions.log"
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").strip().splitlines()


def run_full_pipeline(
    date_str: str | None = None,
    use_google: bool = True,
    headless: bool = True,
) -> dict[str, Any]:
    config = load_config()
    if "google_browser" in config:
        config["google_browser"]["headless"] = headless
    espn = EspnDataAdapter()
    google = GoogleSportsAdapter(config)
    resolver = TeamResolver()
    builder = MatchMatrixBuilder()
    predictor = MatchPredictor(config, use_google=use_google)
    monte_carlo = TournamentMonteCarlo()

    try:
        espn_events = espn.fetch_scoreboard(date_str)
        google_events = google.fetch_scoreboard(date_str) if use_google else []
        reconciliations = [
            resolver.reconcile(event, resolver.find_google_match(event, google_events))
            for event in espn_events
        ]
        matrix = builder.build_dataframe(espn_events, reconciliations)
        featured = apply_all_signals(matrix)
        predictions = predictor.predict_dataframe(featured)
        contrasts = predictor.last_contrasts

        mc_result = {}
        if not predictions.empty:
            mc_result = monte_carlo.run_bracket(predictions.to_dict(orient="records"))

        payload = {
            "date": date_str,
            "use_google": use_google,
            "espn_match_count": len(espn_events),
            "predictions": predictions.to_dict(orient="records"),
            "feature_matrix": featured.to_dict(orient="records"),
            "signal_columns": list(SIGNAL_COMPUTERS.keys()),
            "contrasts": contrasts,
            "monte_carlo": mc_result,
            "espn_events_raw": {str(e.match_id): e.raw for e in espn_events},
            "match_enrichment": _build_match_enrichment(espn_events, featured),
            "reconciliations": [
                {
                    "match_id": r.match_id,
                    "home_team": r.home_team,
                    "away_team": r.away_team,
                    "score_match": r.score_match,
                    "status_match": r.status_match,
                    "warnings": r.warnings,
                    "divergence_penalty": r.divergence_penalty,
                }
                for r in reconciliations
            ],
            "exceptions": load_exception_log(),
        }
        out_path = ROOT / "data" / "cache" / "predictions_latest.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return payload
    finally:
        predictor.close()
        google.close()


def predictions_df(payload: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(payload.get("predictions", []))


def contrasts_for_match(payload: dict[str, Any], match_id: str) -> dict[str, Any] | None:
    for contrast in payload.get("contrasts", []):
        if str(contrast.get("match_id")) == str(match_id):
            return contrast
    return None
