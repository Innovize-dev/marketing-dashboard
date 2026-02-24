"""
Merges platform DataFrames:
  1. Joins GA4 columns onto Google Ads rows (left join on period + campaign_name)
  2. Concatenates all platform DataFrames into one unified table
"""
from __future__ import annotations

import pandas as pd


def merge_google_ads_ga4(
    ads_df: pd.DataFrame, ga4_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Left-joins GA4 data onto Google Ads rows.
    Match key: (period, campaign_name) — campaign IDs differ between systems.
    GA4 columns added with prefix: ga4_conversions, ga4_revenue, ga4_sessions.
    Unmatched rows (no GA4 data for a campaign) get NaN → filled to 0.
    """
    if ads_df.empty:
        return ads_df

    if ga4_df.empty:
        ads_df = ads_df.copy()
        ads_df["ga4_conversions"] = 0.0
        ads_df["ga4_revenue"] = 0.0
        ads_df["ga4_sessions"] = 0
        return ads_df

    # Normalise period to date only (strip time component if present)
    ads = ads_df.copy()
    ga4 = ga4_df.copy()
    ads["_period_date"] = pd.to_datetime(ads["period"]).dt.normalize()
    ga4["_period_date"] = pd.to_datetime(ga4["period"]).dt.normalize()

    ga4_slim = ga4.rename(
        columns={
            "conversions": "ga4_conversions",
            "revenue": "ga4_revenue",
            "interactions": "ga4_sessions",
        }
    )[["_period_date", "campaign_name", "ga4_conversions", "ga4_revenue", "ga4_sessions"]]

    merged = ads.merge(ga4_slim, on=["_period_date", "campaign_name"], how="left")
    merged["ga4_conversions"] = merged["ga4_conversions"].fillna(0.0)
    merged["ga4_revenue"] = merged["ga4_revenue"].fillna(0.0)
    merged["ga4_sessions"] = merged["ga4_sessions"].fillna(0).astype(int)
    merged = merged.drop(columns=["_period_date"])
    return merged


def merge_all_platforms(*platform_dfs: pd.DataFrame) -> pd.DataFrame:
    """
    Vertically concatenates all platform DataFrames.
    Non-Google platforms won't have GA4 columns — they are filled with NaN
    and displayed as '-' in the table.
    """
    non_empty = [df for df in platform_dfs if not df.empty]
    if not non_empty:
        return pd.DataFrame()
    return pd.concat(non_empty, ignore_index=True, sort=False)
