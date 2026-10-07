"""Araştırma sonuçları için basit SQLite deposu (stdlib sqlite3)."""
from __future__ import annotations

import os
import sqlite3
import time
from contextlib import closing
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,        -- github / gmail / x / canva / supabase / vercel
    kind TEXT NOT NULL,          -- repo / issue / message / bookmark / export ...
    ref TEXT,                    -- url veya id
    title TEXT,
    content TEXT,
    fetched_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_results_source ON results(source);
"""


def _db_path() -> Path:
    return Path(os.environ.get("STORE_DB", "data/results.db"))


def _connect() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.executescript(_SCHEMA)
    return conn


def save(source: str, kind: str, ref: str | None, title: str | None,
         content: str | None) -> int:
    with closing(_connect()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO results (source, kind, ref, title, content, fetched_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (source, kind, ref, title, content,
             time.strftime("%Y-%m-%dT%H:%M:%S")),
        )
        return int(cur.lastrowid)


def recent(source: str | None = None, limit: int = 20) -> list[tuple]:
    with closing(_connect()) as conn:
        if source:
            cur = conn.execute(
                "SELECT id, source, kind, ref, title, fetched_at FROM results "
                "WHERE source = ? ORDER BY id DESC LIMIT ?", (source, limit))
        else:
            cur = conn.execute(
                "SELECT id, source, kind, ref, title, fetched_at FROM results "
                "ORDER BY id DESC LIMIT ?", (limit,))
        return cur.fetchall()
