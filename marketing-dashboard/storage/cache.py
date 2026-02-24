"""
SQLite-backed TTL query cache.
Stores serialized lists of RawCampaignRow as JSON.
Cache keys are SHA-256 hashes of (platform + query params).
"""
from __future__ import annotations

import hashlib
import json
import pickle
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from integrations.base import RawCampaignRow


def make_cache_key(platform: str, params: dict) -> str:
    raw = json.dumps({"platform": platform, **params}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def _serialize(rows: list[RawCampaignRow]) -> str:
    return json.dumps([vars(r) for r in rows], default=str)


def _deserialize(data_json: str) -> list[RawCampaignRow]:
    items = json.loads(data_json)
    return [RawCampaignRow(**item) for item in items]


def get_cached(
    conn: sqlite3.Connection, cache_key: str
) -> Optional[list[RawCampaignRow]]:
    """Returns cached rows if the entry exists and has not expired."""
    row = conn.execute(
        "SELECT data_json, expires_at FROM query_cache WHERE cache_key = ?",
        (cache_key,),
    ).fetchone()

    if row is None:
        return None

    expires_at = datetime.fromisoformat(row["expires_at"])
    if datetime.utcnow() > expires_at:
        # Expired — delete and return None
        conn.execute(
            "DELETE FROM query_cache WHERE cache_key = ?", (cache_key,)
        )
        conn.commit()
        return None

    return _deserialize(row["data_json"])


def set_cached(
    conn: sqlite3.Connection,
    cache_key: str,
    rows: list[RawCampaignRow],
    ttl_seconds: int,
) -> None:
    expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    conn.execute(
        """INSERT OR REPLACE INTO query_cache (cache_key, data_json, expires_at)
           VALUES (?, ?, ?)""",
        (cache_key, _serialize(rows), expires_at.isoformat()),
    )
    conn.commit()


def clear_cache(conn: sqlite3.Connection) -> int:
    """Deletes all cache entries. Returns number of rows deleted."""
    cursor = conn.execute("DELETE FROM query_cache")
    conn.commit()
    return cursor.rowcount


def clear_expired(conn: sqlite3.Connection) -> int:
    """Deletes only expired cache entries."""
    cursor = conn.execute(
        "DELETE FROM query_cache WHERE expires_at < ?",
        (datetime.utcnow().isoformat(),),
    )
    conn.commit()
    return cursor.rowcount
