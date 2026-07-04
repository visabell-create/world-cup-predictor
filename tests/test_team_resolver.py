"""Tests for team resolver and reconciliation."""

from src.ingestion.base import MatchEvent, TeamSnapshot
from src.normalization.team_resolver import TeamResolver, normalize_team_name


def test_normalize_team_name_aliases():
    assert normalize_team_name("USA") == "united states"
    assert normalize_team_name("England") == "england"


def test_teams_match_fuzzy():
    resolver = TeamResolver()
    assert resolver.teams_match("United States", "USA")
    assert resolver.teams_match("Argentina", "argentina")


def test_reconcile_score_match():
    resolver = TeamResolver()
    espn = MatchEvent(
        match_id="1",
        home=TeamSnapshot("h1", "Argentina", score=2),
        away=TeamSnapshot("a1", "France", score=1),
        status="Final",
    )
    google = MatchEvent(
        match_id="g1",
        home=TeamSnapshot("gh", "Argentina", score=2),
        away=TeamSnapshot("ga", "France", score=1),
        status="Full-time",
    )
    result = resolver.reconcile(espn, google)
    assert result.score_match
    assert result.divergence_penalty == 0.0


def test_reconcile_score_divergence():
    resolver = TeamResolver()
    espn = MatchEvent(
        match_id="1",
        home=TeamSnapshot("h1", "Argentina", score=2),
        away=TeamSnapshot("a1", "France", score=1),
        status="Final",
    )
    google = MatchEvent(
        match_id="g1",
        home=TeamSnapshot("gh", "Argentina", score=1),
        away=TeamSnapshot("ga", "France", score=1),
        status="Full-time",
    )
    result = resolver.reconcile(espn, google)
    assert not result.score_match
    assert result.divergence_penalty >= 0.15
    assert "score_divergence" in result.warnings
