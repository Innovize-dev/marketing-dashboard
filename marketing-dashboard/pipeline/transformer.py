"""
Normalizes raw adapter output into typed pandas DataFrames and handles
resampling from daily rows to weekly or monthly granularity.
"""
from __future__ import annotations

import pandas as pd

from integrations.base import RawCampaignRow

CANONICAL_COLUMNS = [
    "platform",
    "period",
    "campaign_id",
    "campaign_name",
    "impressions",
    "clicks",
    "interactions",
    "conversions",
    "spend",
    "revenue",
]

NUMERIC_COLS = ["impressions", "clicks", "interactions", "conversions", "spend", "revenue"]


def rows_to_dataframe(rows: list[RawCampaignRow]) -> pd.DataFrame:
    """Converts a list of RawCampaignRow to a typed DataFrame."""
    if not rows:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)

    data = [
        {
            "platform": r.platform,
            "period": r.period,
            "campaign_id": r.campaign_id,
            "campaign_name": r.campaign_name,
            "impressions": r.impressions,
            "clicks": r.clicks,
            "interactions": r.interactions,
            "conversions": r.conversions,
            "spend": r.spend,
            "revenue": r.revenue if r.revenue is not None else 0.0,
        }
        for r in rows
    ]
    df = pd.DataFrame(data)

    for col in ["impressions", "clicks", "interactions"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    for col in ["conversions", "spend", "revenue"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0).astype(float)

    df["period"] = pd.to_datetime(df["period"], format="mixed", errors="coerce")
    df = df.dropna(subset=["period"])
    return df


def resample_to_granularity(df: pd.DataFrame, granularity: str) -> pd.DataFrame:
    """
    Aggregates daily-granularity rows to weekly or monthly.
    For weekly, weeks start on Monday (W-MON).
    For monthly, rows are grouped to month-start (MS).
    campaign_id / platform / campaign_name are preserved via groupby.
    """
    if df.empty:
        return df

    freq_map = {"daily": None, "weekly": "W-MON", "monthly": "MS"}
    freq = freq_map.get(granularity)

    if freq is None:
        return df  # already daily

    df = df.copy()
    df = df.set_index("period")

    grouped = (
        df.groupby(["platform", "campaign_id", "campaign_name"])[NUMERIC_COLS]
        .resample(freq)
        .sum()
        .reset_index()
    )
    return grouped
