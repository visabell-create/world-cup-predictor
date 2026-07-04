"""Tests for SAI computation."""

import pandas as pd

from src.ensemble.sai import SignalAgreementIndex


def test_sai_high_agreement():
    sai = SignalAgreementIndex()
    row = pd.Series({"source_divergence_penalty": 0.0})
    result = sai.compute(
        row,
        {
            "internal_model": 0.55,
            "espn_win_prob": 0.54,
            "espn_odds_implied": 0.53,
            "elo": 0.56,
            "xg_rating": 0.55,
            "google_implied": None,
        },
    )
    assert result["sai"] > 0.8
    assert not result["high_uncertainty"]


def test_sai_divergence_penalty():
    sai = SignalAgreementIndex()
    row = pd.Series({"source_divergence_penalty": 0.15})
    result = sai.compute(
        row,
        {
            "internal_model": 0.7,
            "espn_win_prob": 0.4,
            "espn_odds_implied": None,
            "elo": None,
            "xg_rating": None,
            "google_implied": None,
        },
    )
    assert result["confidence"] < result["sai"]
