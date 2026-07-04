"""SQLite TTL cache for API responses."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from src.config import ROOT


class ResponseCache:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or ROOT / "data" / "cache" / "responses.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    expires_at REAL NOT NULL
                )
                """
            )

    def get(self, key: str) -> Any | None:
        now = time.time()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT payload, expires_at FROM cache WHERE key = ?", (key,)
            ).fetchone()
        if not row:
            return None
        payload, expires_at = row
        if expires_at < now:
            self.delete(key)
            return None
        return json.loads(payload)

    def set(self, key: str, payload: Any, ttl_sec: int) -> None:
        expires_at = time.time() + ttl_sec
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO cache (key, payload, expires_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET payload = excluded.payload, expires_at = excluded.expires_at
                """,
                (key, json.dumps(payload), expires_at),
            )

    def delete(self, key: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))
