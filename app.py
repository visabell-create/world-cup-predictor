"""Streamlit dashboard — vibrant match-first UI."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import load_config
from src.pipeline.runner import (
    load_cached_predictions,
    load_exception_log,
    predictions_df,
    run_full_pipeline,
)
from src.ui.formatters import confidence_tier, pct, winner_label

st.set_page_config(
    page_title="World Cup Predictor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .main { background: linear-gradient(160deg, #0f172a 0%, #1e293b 45%, #0f172a 100%); }
    .match-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        border: 1px solid #475569;
        box-shadow: 0 8px 32px rgba(0,0,0,0.35);
    }
    .winner-badge {
        display: inline-block;
        background: linear-gradient(90deg, #22c55e, #16a34a);
        color: white;
        font-weight: 700;
        font-size: 1.1rem;
        padding: 0.45rem 1.2rem;
        border-radius: 999px;
        margin: 0.5rem 0;
    }
    .prob-big { font-size: 2.4rem; font-weight: 800; color: #f8fafc; line-height: 1.1; }
    .conf-high { color: #4ade80; font-weight: 700; }
    .conf-med { color: #fbbf24; font-weight: 700; }
    .conf-low { color: #f87171; font-weight: 700; }
    .vs-text { font-size: 1.4rem; font-weight: 800; color: #94a3b8; text-align: center; }
    .team-name { font-size: 1.15rem; font-weight: 700; color: #f1f5f9; text-align: center; }
    h1, h2, h3 { color: #f8fafc !important; }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

config = load_config()
league = config["framework"]["league"]

with st.sidebar:
    st.header("⚙️ Controls")
    date_input = st.text_input("Date (YYYYMMDD)", placeholder="Today if blank")
    use_google = st.checkbox("Google signal contrast", value=False)
    headless = st.checkbox("Headless browser", value=True)
    if st.button("🚀 Run predictions", type="primary", use_container_width=True):
        with st.spinner("Running pipeline…"):
            try:
                st.session_state["payload"] = run_full_pipeline(
                    date_str=date_input or None,
                    use_google=use_google,
                    headless=headless,
                )
                st.session_state["last_run_ok"] = True
            except Exception as exc:
                st.session_state["last_run_ok"] = False
                st.session_state["last_error"] = str(exc)
    if st.button("📂 Load cached", use_container_width=True):
        cached = load_cached_predictions()
        if cached:
            st.session_state["payload"] = cached
            st.session_state["last_run_ok"] = True

payload = st.session_state.get("payload") or load_cached_predictions()

st.markdown("# ⚽ World Cup Predictor")
st.markdown(f"*{league} · Who wins, with confidence*")


def _has_recon_issues(recon_df: pd.DataFrame) -> bool:
    if recon_df.empty:
        return False
    for _, r in recon_df.iterrows():
        if not r.get("score_match", True) or not r.get("status_match", True):
            return True
        warnings = r.get("warnings") or []
        if any(w != "google_source_missing" for w in warnings):
            return True
    return False


if not payload:
    st.info("Hit **Run predictions** in the sidebar to load today's matchups.")
    st.stop()

if st.session_state.get("last_run_ok") is False:
    st.error(st.session_state.get("last_error", "Pipeline failed"))

pred_df = predictions_df(payload)
enrichment = payload.get("match_enrichment", {})
feature_df = pd.DataFrame(payload.get("feature_matrix", []))

if not enrichment and not feature_df.empty:
    from src.ui.espn_enrichment import enrich_match

    raw_map = payload.get("espn_events_raw", {})
    for _, frow in feature_df.iterrows():
        mid = str(frow["match_id"])
        enrichment[mid] = enrich_match(
            mid,
            str(frow.get("home_team_id", "")),
            str(frow.get("away_team_id", "")),
            raw_map,
        )

if pred_df.empty:
    st.warning("No matches scheduled for this date.")
    st.stop()

st.markdown("## 🏆 Today's Predictions")

for _, row in pred_df.iterrows():
    mid = str(row["match_id"])
    home = row["home_team"]
    away = row["away_team"]
    enrich = enrichment.get(mid, {})
    p_home = float(row.get("p_win_90", 0.5))
    p_draw = float(row.get("p_draw_90", 0.22))
    p_away = max(0.0, 1.0 - p_home - p_draw)
    confidence = float(row.get("confidence", 0.5))
    winner, side, win_prob = winner_label(home, away, p_home, p_draw)
    conf_class = {"high": "conf-high", "medium": "conf-med", "low": "conf-low"}[confidence_tier(confidence)]

    home_logo = enrich.get("home_logo")
    away_logo = enrich.get("away_logo")

    with st.container():
        st.markdown('<div class="match-card">', unsafe_allow_html=True)

        col_home, col_vs, col_away = st.columns([2, 1, 2])

        with col_home:
            if home_logo:
                st.image(home_logo, width=100)
            st.markdown(f'<p class="team-name">{home}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="prob-big">{pct(p_home)}</p>', unsafe_allow_html=True)
            st.caption("Win probability")

        with col_vs:
            st.markdown('<p class="vs-text">VS</p>', unsafe_allow_html=True)
            if row.get("status"):
                st.caption(str(row["status"]))
            st.markdown(f'<p class="vs-text">Draw {pct(p_draw)}</p>', unsafe_allow_html=True)

        with col_away:
            if away_logo:
                st.image(away_logo, width=100)
            st.markdown(f'<p class="team-name">{away}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="prob-big">{pct(p_away)}</p>', unsafe_allow_html=True)
            st.caption("Win probability")

        st.markdown(
            f'<p class="winner-badge">✅ Predicted winner: {winner}</p>',
            unsafe_allow_html=True,
        )
        m1, m2, m3 = st.columns(3)
        m1.metric("Winner probability", pct(win_prob))
        m2.metric("Confidence", pct(confidence))
        sai_val = row.get("sai")
        if sai_val is not None and not pd.isna(sai_val):
            m3.metric("Signal agreement", pct(sai_val))

        st.markdown(
            f'<p class="{conf_class}">Confidence tier: {confidence_tier(confidence).upper()}</p>',
            unsafe_allow_html=True,
        )

        home_players = enrich.get("home_top_players", [])
        away_players = enrich.get("away_top_players", [])
        if home_players or away_players:
            st.markdown("**⭐ Key players**")
            ph, pa = st.columns(2)
            with ph:
                for pl in home_players:
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        if pl.get("headshot"):
                            st.image(pl["headshot"], width=56)
                        else:
                            st.markdown("👤")
                    with c2:
                        st.markdown(f"**{pl.get('name', '')}**")
                        pos = pl.get("position", "")
                        jersey = pl.get("jersey", "")
                        extra = " · ".join(x for x in [f"#{jersey}" if jersey else "", pos] if x)
                        if extra:
                            st.caption(extra)
            with pa:
                for pl in away_players:
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        if pl.get("headshot"):
                            st.image(pl["headshot"], width=56)
                        else:
                            st.markdown("👤")
                    with c2:
                        st.markdown(f"**{pl.get('name', '')}**")
                        pos = pl.get("position", "")
                        jersey = pl.get("jersey", "")
                        extra = " · ".join(x for x in [f"#{jersey}" if jersey else "", pos] if x)
                        if extra:
                            st.caption(extra)

        chart_path = row.get("chart_path")
        if chart_path and Path(chart_path).exists():
            with st.expander("Signal contrast chart"):
                st.image(str(chart_path))

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("")

tab_names = []
contrasts = payload.get("contrasts") or []
recon_df = pd.DataFrame(payload.get("reconciliations", []))
mc = payload.get("monte_carlo") or {}
exceptions = payload.get("exceptions") or load_exception_log()

if not feature_df.empty:
    tab_names.append("Signals")
if contrasts:
    tab_names.append("Google contrast")
if _has_recon_issues(recon_df):
    tab_names.append("Reconciliation")
if mc.get("simulations"):
    tab_names.append("Monte Carlo")
if exceptions:
    tab_names.append("Logs")

if tab_names:
    tabs = st.tabs(tab_names)
    ti = 0

    if "Signals" in tab_names:
        with tabs[ti]:
            signal_cols = payload.get("signal_columns", [])
            id_cols = [c for c in ["home_team", "away_team"] if c in feature_df.columns]
            show = feature_df[id_cols].copy()
            for col in signal_cols:
                if col in feature_df.columns:
                    show[col.replace("_", " ").title()] = feature_df[col].apply(lambda x: pct(x))
            st.dataframe(show, use_container_width=True, hide_index=True)
        ti += 1

    if "Google contrast" in tab_names:
        with tabs[ti]:
            for contrast in contrasts:
                pred_match = pred_df[pred_df["match_id"].astype(str) == str(contrast["match_id"])]
                title = f"Match {contrast['match_id']}"
                if not pred_match.empty:
                    r = pred_match.iloc[0]
                    title = f"{r['home_team']} vs {r['away_team']}"
                with st.expander(title):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Google mean", pct(contrast.get("google_signal_mean")))
                    c2.metric("Internal mean", pct(contrast.get("internal_signal_mean")))
                    c3.metric("Alignment", pct(contrast.get("signal_alignment")))
                    cdf = pd.DataFrame(contrast.get("contrasts", []))
                    if not cdf.empty:
                        display = cdf.copy()
                        for col in ("internal", "google", "delta"):
                            if col in display.columns:
                                display[col] = display[col].apply(pct)
                        st.dataframe(display, use_container_width=True, hide_index=True)
                    chart = contrast.get("chart_path")
                    if chart and Path(chart).exists():
                        st.image(chart)
        ti += 1

    if "Reconciliation" in tab_names:
        with tabs[ti]:
            st.dataframe(recon_df, use_container_width=True, hide_index=True)
        ti += 1

    if "Monte Carlo" in tab_names:
        with tabs[ti]:
            c1, c2, c3 = st.columns(3)
            c1.metric("Simulations", f"{mc.get('simulations', 0):,}")
            c2.metric("Home advance rate", pct(mc.get("home_advance_rate")))
            c3.metric("Matches", mc.get("matches_simulated", 0))
        ti += 1

    if "Logs" in tab_names:
        with tabs[ti]:
            for line in exceptions[-50:]:
                st.code(line)
