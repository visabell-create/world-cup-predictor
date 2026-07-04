# World Cup Multi-Modal Prediction Engine

AI-powered FIFA World Cup match predictions with ESPN data, 15-signal analysis, optional Google browser contrast, and a Streamlit dashboard.

## Live demo (Streamlit Cloud)

2.](https://world-cup-predictor-kwduflwf2um9ryn2hgfvxu.streamlit.app/)


## Local setup

```

## Features

- ESPN live scores, odds, rosters, team logos
- 15 predictive signals + hidden telemetry corrections
- Signal Agreement Index (SAI) ensemble
- Match cards: winner, win %, confidence, key players
- Optional headless Google validation per signal

## Project structure

```
app.py                 # Streamlit UI (deploy entry point)
config/config.yaml     # League, signal weights, cache TTLs
src/ingestion/         # ESPN + Google browser adapters
src/signals/           # 15 signal modules
src/ensemble/          # XGBoost-style scorer, Bayesian, SAI
src/pipeline/          # Ingest → features → predict
data/manual/           # Team xG proxies, narrative tags
```

## CLI

```bash
python examples/run_matchday.py
python -m src.pipeline.predict
python -m src.pipeline.predict --no-google
```

## Tests

```bash
pytest
```
