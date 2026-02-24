"""
SQLite connection management and schema initialization.
"""
from __future__ import annotations

import os
import sqlite3


_CREATE_CREDENTIALS = """
CREATE TABLE IF NOT EXISTS credentials (
    platform    TEXT NOT NULL UNIQUE,
    creds_json  TEXT NOT NULL,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

_CREATE_QUERY_CACHE = """
CREATE TABLE IF NOT EXISTS query_cache (
    cache_key   TEXT NOT NULL UNIQUE,
    data_json   TEXT NOT NULL,
    fetched_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at  TIMESTAMP NOT NULL
);
"""

_CREATE_FETCH_LOG = """
CREATE TABLE IF NOT EXISTS fetch_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    platform    TEXT NOT NULL,
    status      TEXT NOT NULL,
    error_msg   TEXT,
    row_count   INTEGER,
    duration_ms INTEGER,
    fetched_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def get_connection(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def initialize_db(db_path: str) -> sqlite3.Connection:
    conn = get_connection(db_path)
    conn.execute(_CREATE_CREDENTIALS)
    conn.execute(_CREATE_QUERY_CACHE)
    conn.execute(_CREATE_FETCH_LOG)
    conn.commit()
    return conn


def log_fetch(
    conn: sqlite3.Connection,
    platform: str,
    status: str,
    row_count: int = 0,
    duration_ms: int = 0,
    error_msg: str | None = None,
) -> None:
    conn.execute(
        """INSERT INTO fetch_log (platform, status, error_msg, row_count, duration_ms)
           VALUES (?, ?, ?, ?, ?)""",
        (platform, status, error_msg, row_count, duration_ms),
    )
    conn.commit()
