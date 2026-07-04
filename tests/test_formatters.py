"""Tests for UI formatters."""

from src.ui.formatters import pct, winner_label


def test_pct_decimal():
    assert pct(0.525) == "52.5%"


def test_pct_missing():
    assert pct(None) == "—"


def test_winner_label_home():
    name, side, prob = winner_label("Argentina", "France", 0.6, 0.22)
    assert name == "Argentina"
    assert side == "home"
    assert prob == 0.6
