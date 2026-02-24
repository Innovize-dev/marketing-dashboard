"""
Credential access abstraction.

Priority order:
  1. SQLite (runtime-saved via Settings UI)
  2. .env / environment variables (fallback)

This means credentials saved in the UI override .env values without requiring
a restart.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from config.settings import settings


def _get_fernet() -> Optional[Fernet]:
    if not settings.ENCRYPTION_KEY:
        return None
    try:
        return Fernet(settings.ENCRYPTION_KEY.encode())
    except Exception:
        return None


def _decrypt(blob: str) -> dict:
    fernet = _get_fernet()
    if fernet is None:
        # No encryption key — try plain JSON (dev mode)
        return json.loads(blob)
    try:
        return json.loads(fernet.decrypt(blob.encode()).decode())
    except InvalidToken:
        return {}


def _encrypt(data: dict) -> str:
    fernet = _get_fernet()
    raw = json.dumps(data)
    if fernet is None:
        return raw
    return fernet.encrypt(raw.encode()).decode()


def get_platform_creds(conn: sqlite3.Connection, platform: str) -> dict:
    """
    Returns decrypted credentials dict for the given platform.
    Falls back to environment variables if not found in SQLite.
    """
    row = conn.execute(
        "SELECT creds_json FROM credentials WHERE platform = ?", (platform,)
    ).fetchone()

    if row:
        creds = _decrypt(row[0])
        if creds:
            return creds

    # Fallback to .env-sourced settings
    return _env_creds(platform)


def save_platform_creds(conn: sqlite3.Connection, platform: str, creds: dict) -> None:
    """Encrypts and upserts credentials for the given platform."""
    blob = _encrypt(creds)
    conn.execute(
        """INSERT INTO credentials (platform, creds_json, updated_at)
           VALUES (?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(platform) DO UPDATE SET
             creds_json = excluded.creds_json,
             updated_at = CURRENT_TIMESTAMP""",
        (platform, blob),
    )
    conn.commit()


def _env_creds(platform: str) -> dict:
    """Builds a credentials dict from environment variables for a given platform."""
    s = settings
    mapping = {
        "google_ads": {
            "developer_token": s.GOOGLE_ADS_DEVELOPER_TOKEN,
            "client_id": s.GOOGLE_ADS_CLIENT_ID,
            "client_secret": s.GOOGLE_ADS_CLIENT_SECRET,
            "refresh_token": s.GOOGLE_ADS_REFRESH_TOKEN,
            "customer_id": s.GOOGLE_ADS_CUSTOMER_ID,
            "login_customer_id": s.GOOGLE_ADS_LOGIN_CUSTOMER_ID,
        },
        "ga4": {
            "property_id": s.GA4_PROPERTY_ID,
            "service_account_json": s.GA4_SERVICE_ACCOUNT_JSON,
        },
        "meta": {
            "app_id": s.META_APP_ID,
            "app_secret": s.META_APP_SECRET,
            "access_token": s.META_ACCESS_TOKEN,
            "ad_account_id": s.META_AD_ACCOUNT_ID,
        },
        "tiktok": {
            "access_token": s.TIKTOK_ACCESS_TOKEN,
            "advertiser_id": s.TIKTOK_ADVERTISER_ID,
        },
        "reddit": {
            "client_id": s.REDDIT_CLIENT_ID,
            "client_secret": s.REDDIT_CLIENT_SECRET,
            "access_token": s.REDDIT_ACCESS_TOKEN,
            "account_id": s.REDDIT_ACCOUNT_ID,
        },
    }
    return mapping.get(platform, {})
