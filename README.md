# World Cup Multi-Modal Prediction Engine

AI-powered FIFA World Cup match predictions with ESPN data, 15-signal analysis, optional Google browser contrast, and a Streamlit dashboard.

## Live demo (Streamlit Cloud)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub → **New app**
4. Repository: `your-username/world-cup-predictor`
5. Main file: `app.py`
6. Click **Deploy**

> **Note:** Google headless browser contrast requires Playwright and does not run on Streamlit Cloud free tier. Use **Load cached** or run predictions with Google contrast disabled on cloud. ESPN + internal signals work fine.

## Local setup

```bash
git clone https://github.com/YOUR_USERNAME/world-cup-predictor.git
cd world-cup-predictor
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
playwright install chromium     # optional, for Google contrast
streamlit run app.py
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
