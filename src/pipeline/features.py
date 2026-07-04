"""Feature build CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.config import ROOT
from src.ingestion.espn import EspnDataAdapter
from src.ingestion.google_sports import GoogleSportsAdapter
from src.normalization.match_matrix import MatchMatrixBuilder
from src.normalization.team_resolver import TeamResolver
from src.signals import apply_all_signals


def run(date_str: str | None = None, output: Path | None = None) -> Path:
    espn = EspnDataAdapter()
    google = GoogleSportsAdapter()
    resolver = TeamResolver()
    builder = MatchMatrixBuilder()

    espn_events = espn.fetch_scoreboard(date_str)
    google_events = google.fetch_scoreboard(date_str)
    reconciliations = [
        resolver.reconcile(event, resolver.find_google_match(event, google_events))
        for event in espn_events
    ]
    matrix = builder.build_dataframe(espn_events, reconciliations)
    featured = apply_all_signals(matrix)

    out_path = output or ROOT / "data" / "cache" / "feature_matrix.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    featured.to_json(out_path, orient="records", indent=2)
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build match feature matrix")
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    path = run(args.date, args.output)
    print(f"Feature matrix written to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
