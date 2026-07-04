"""Headless browser Google search for sports widgets."""

from __future__ import annotations

import logging
import re
import time
from typing import Any

from src.config import load_config
from src.ingestion.cache import ResponseCache

logger = logging.getLogger(__name__)


class GoogleBrowser:
    """Playwright headless browser — no paid API keys required."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or load_config()
        google_cfg = self.config.get("google_browser", {})
        self.headless = google_cfg.get("headless", True)
        self.timeout_ms = google_cfg.get("timeout_ms", 15000)
        self.cache = ResponseCache()
        self.ttl = google_cfg.get("cache_ttl_sec", 600)
        self._playwright = None
        self._browser = None

    def _ensure_browser(self) -> bool:
        if self._browser is not None:
            return True
        try:
            from playwright.sync_api import sync_playwright

            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=self.headless)
            return True
        except Exception as exc:
            logger.exception("Headless browser unavailable: %s", exc)
            return False

    def close(self) -> None:
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def search(self, query: str, screenshot_path: str | None = None) -> dict[str, Any]:
        cache_key = f"google_browser:{query}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        if not self._ensure_browser():
            return {"query": query, "error": "browser_unavailable", "text": "", "home_bias": 0.5}

        try:
            assert self._browser is not None
            page = self._browser.new_page()
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            time.sleep(1.5)
            text = page.inner_text("body")
            if screenshot_path:
                page.screenshot(path=screenshot_path, full_page=False)
            page.close()
            parsed = self._parse_sports_text(text, query)
            parsed["query"] = query
            self.cache.set(cache_key, parsed, self.ttl)
            return parsed
        except Exception as exc:
            logger.exception("Google search failed for '%s': %s", query, exc)
            return {"query": query, "error": str(exc), "text": "", "home_bias": 0.5}

    def _parse_sports_text(self, text: str, query: str) -> dict[str, Any]:
        home_bias = 0.5
        status = "unknown"
        home_score = None
        away_score = None

        score_match = re.search(r"(\d+)\s*[-–]\s*(\d+)", text)
        if score_match:
            home_score = int(score_match.group(1))
            away_score = int(score_match.group(2))
            if home_score > away_score:
                home_bias = 0.65
            elif home_score < away_score:
                home_bias = 0.35
            else:
                home_bias = 0.5
            status = "scored"

        positive = ("favorite", "leading", "strong", "dominant", "win", "advantage")
        negative = ("underdog", "struggling", "injured", "weak", "loss", "doubt")
        lower = text.lower()
        pos_hits = sum(1 for w in positive if w in lower)
        neg_hits = sum(1 for w in negative if w in lower)
        if pos_hits or neg_hits:
            sentiment = (pos_hits - neg_hits) / max(1, pos_hits + neg_hits)
            home_bias = max(0.05, min(0.95, 0.5 + sentiment * 0.25))

        if any(t in lower for t in ("full-time", "full time", "final")):
            status = "final"
        elif any(t in lower for t in ("live", "half", "1st", "2nd")):
            status = "live"

        return {
            "text": text[:2000],
            "home_bias": round(home_bias, 4),
            "home_score": home_score,
            "away_score": away_score,
            "status": status,
        }
