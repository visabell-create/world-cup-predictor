"""Game-day prediction CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.config import ROOT
from src.pipeline.runner import run_full_pipeline


def run(date_str: str | None = None, output: Path | None = None, use_google: bool = True) -> dict:
    payload = run_full_pipeline(date_str=date_str, use_google=use_google)
    out_path = output or ROOT / "data" / "cache" / "predictions_latest.json"
    out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Run match-day predictions")
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--no-google", action="store_true", help="Skip headless Google contrast")
    args = parser.parse_args()
    result = run(args.date, args.output, use_google=not args.no_google)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
