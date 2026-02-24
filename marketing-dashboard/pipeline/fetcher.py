"""
Orchestrates parallel data fetching from all configured platforms.
Each platform runs in its own thread; failures are caught per-platform
so a broken token on one platform does not block others.
"""
from __future__ import annotations

import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from config.credentials import get_platform_creds
from integrations.base import DateRange, RawCampaignRow
from storage.cache import get_cached, make_cache_key, set_cached
from storage.db import log_fetch


def _build_adapter(platform: str, creds: dict):
    """Instantiates the correct adapter class for the given platform."""
    if platform == "google_ads":
        from integrations.google_ads import GoogleAdsAdapter
        return GoogleAdsAdapter(creds)
    if platform == "ga4":
        from integrations.google_analytics import GA4Adapter
        return GA4Adapter(creds)
    if platform == "meta":
        from integrations.meta import MetaAdapter
        return MetaAdapter(creds)
    if platform == "tiktok":
        from integrations.tiktok import TikTokAdapter
        return TikTokAdapter(creds)
    if platform == "reddit":
        from integrations.reddit import RedditAdapter
        return RedditAdapter(creds)
    raise ValueError(f"Unknown platform: {platform}")


def _fetch_one(
    platform: str,
    date_range: DateRange,
    granularity: str,
    conn: sqlite3.Connection,
    ttl_seconds: int,
    campaign_ids: Optional[list[str]] = None,
) -> tuple[str, list[RawCampaignRow] | Exception]:
    """Fetches one platform, using cache if available."""
    cache_key = make_cache_key(
        platform,
        {
            "start": str(date_range.start),
            "end": str(date_range.end),
            "granularity": granularity,
            "campaign_ids": sorted(campaign_ids or []),
        },
    )

    # Cache hit
    cached = get_cached(conn, cache_key)
    if cached is not None:
        return platform, cached

    # Cache miss — call API
    creds = get_platform_creds(conn, platform)
    if not any(creds.values()):
        return platform, ValueError(f"No credentials configured for {platform}")

    try:
        adapter = _build_adapter(platform, creds)
        t0 = time.monotonic()
        rows = adapter.fetch_campaigns(date_range, granularity, campaign_ids)
        duration_ms = int((time.monotonic() - t0) * 1000)
        log_fetch(conn, platform, "success", len(rows), duration_ms)
        set_cached(conn, cache_key, rows, ttl_seconds)
        return platform, rows
    except Exception as exc:
        log_fetch(conn, platform, "error", error_msg=str(exc))
        return platform, exc


def fetch_platforms(
    platforms: list[str],
    date_range: DateRange,
    granularity: str,
    conn: sqlite3.Connection,
    ttl_seconds: int = 3600,
    campaign_ids: Optional[list[str]] = None,
) -> tuple[dict[str, list[RawCampaignRow]], dict[str, str]]:
    """
    Fetches all requested platforms in parallel.

    Returns:
      results: {platform: [RawCampaignRow, ...]}
      errors:  {platform: error_message}
    """
    results: dict[str, list[RawCampaignRow]] = {}
    errors: dict[str, str] = {}

    with ThreadPoolExecutor(max_workers=min(len(platforms), 5)) as executor:
        futures = {
            executor.submit(
                _fetch_one, p, date_range, granularity, conn, ttl_seconds, campaign_ids
            ): p
            for p in platforms
        }
        for future in as_completed(futures):
            platform, result = future.result()
            if isinstance(result, Exception):
                errors[platform] = str(result)
            else:
                results[platform] = result

    return results, errors
