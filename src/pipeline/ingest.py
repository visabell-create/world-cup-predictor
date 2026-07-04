"""Daily ingestion CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.config import ROOT
from src.ingestion.espn import EspnDataAdapter
from src.ingestion.google_sports import GoogleSportsAdapter
from src.normalization.team_resolver import TeamResolver


def run(date_str: str | None = None, output: Path | None = None) -> dict:
    espn = EspnDataAdapter()
    google = GoogleSportsAdapter()
    resolver = TeamResolver()

    espn_events = espn.fetch_scoreboard(date_str)
    google_events = google.fetch_scoreboard(date_str)
    reconciliations = []
    for event in espn_events:
        google_match = resolver.find_google_match(event, google_events)
        reconciliations.append(resolver.reconcile(event, google_match))

    payload = {
        "espn_events": [
            {
                "match_id": e.match_id,
                "home": e.home.name,
                "away": e.away.name,
                "home_score": e.home.score,
                "away_score": e.away.score,
                "status": e.status,
            }
            for e in espn_events
        ],
        "google_events": [
            {
                "match_id": e.match_id,
                "home": e.home.name,
                "away": e.away.name,
                "home_score": e.home.score,
                "away_score": e.away.score,
                "status": e.status,
            }
            for e in google_events
        ],
        "reconciliations": [
            {
                "match_id": r.match_id,
                "score_match": r.score_match,
                "status_match": r.status_match,
                "divergence_penalty": r.divergence_penalty,
                "warnings": r.warnings,
            }
            for r in reconciliations
        ],
    }
    out_path = output or ROOT / "data" / "cache" / "ingest_latest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest ESPN + Google sports data")
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    result = run(args.date, args.output)
    print(f"Ingested {len(result['espn_events'])} ESPN events, {len(result['google_events'])} Google events")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
