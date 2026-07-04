"""Smoke test for ESPN scoreboard (skipped if offline)."""

import httpx
import pytest

from src.ingestion.espn import EspnDataAdapter


def _online() -> bool:
    try:
        response = httpx.get(
            "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard",
            timeout=5.0,
        )
        return response.status_code == 200
    except httpx.HTTPError:
        return False


@pytest.mark.skipif(not _online(), reason="ESPN API unreachable")
def test_espn_scoreboard_fetch():
    adapter = EspnDataAdapter()
    events = adapter.fetch_scoreboard()
    assert isinstance(events, list)
