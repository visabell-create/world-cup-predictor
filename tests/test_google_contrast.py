"""Tests for Google browser parsing and signal contrast."""

from unittest.mock import MagicMock, patch

import pandas as pd

from src.ingestion.google_browser import GoogleBrowser
from src.ensemble.google_signal_contrast import GoogleSignalContrast


def test_parse_sports_text_score_bias():
    browser = GoogleBrowser()
    result = browser._parse_sports_text("Argentina 2 - 1 France Full-time", "Argentina vs France")
    assert result["home_bias"] > 0.5
    assert result["home_score"] == 2


def test_parse_sports_text_sentiment():
    browser = GoogleBrowser()
    result = browser._parse_sports_text("Brazil strong favorite dominant win", "Brazil vs Ghana")
    assert result["home_bias"] > 0.5


@patch.object(GoogleSignalContrast, "contrast_row")
def test_final_prediction_blend(mock_contrast):
    mock_contrast.return_value = {
        "match_id": "1",
        "google_signal_mean": 0.7,
        "internal_signal_mean": 0.6,
        "signal_alignment": 0.8,
        "contrasts": [],
        "chart_path": "chart.png",
    }
    contrast = GoogleSignalContrast()
    contrast.browser = MagicMock()
    row = pd.Series(
        {
            "match_id": "1",
            "home_team": "Argentina",
            "away_team": "France",
            **{k: 0.5 for k in [
                "fatigue_accumulation_index", "tactical_matchup_score", "set_piece_differential",
                "pressure_resilience_index", "momentum_velocity", "narrative_pressure",
                "penalty_shootout_prob", "referee_team_compatibility", "game_state_elasticity",
                "sharp_money_divergence", "prediction_confidence_spread", "goalkeeper_form_index",
                "star_dependency_ratio", "bench_impact_index", "days_rest_effect",
            ]},
        }
    )
    with patch.object(contrast, "contrast_row", return_value=mock_contrast.return_value):
        result = contrast.final_prediction(0.55, mock_contrast.return_value, 0.75)
    assert 0.0 < result["p_win_90_final"] < 1.0
    assert "google_blend_weight" in result
