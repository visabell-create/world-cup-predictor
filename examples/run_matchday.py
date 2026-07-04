#!/usr/bin/env python3
"""Game-day orchestration script."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline.features import run as build_features
from src.pipeline.ingest import run as ingest
from src.pipeline.predict import run as predict


def main() -> int:
    print("[SYSTEM] Running situational telemetry corrections...")
    print("[1/3] Ingesting ESPN + headless Google sports data...")
    ingest_result = ingest()
    print(f"      ESPN: {len(ingest_result['espn_events'])} events")

    print("[2/3] Building feature matrix (15 signals + telemetry)...")
    feature_path = build_features()
    print(f"      Features: {feature_path}")

    print("[3/3] Google contrast per signal → chart → final prediction...")
    predictions = predict()
    print(json.dumps(predictions, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
