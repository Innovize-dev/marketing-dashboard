"""
Derived metric calculations.
All functions are pure transformations that add columns to a DataFrame.
Input DataFrame must contain at minimum: impressions, clicks, conversions, spend, revenue.
GA4 columns (ga4_conversions, ga4_revenue) are optional — checked before use.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds computed columns to the report DataFrame:
      ctr_pct, cost_per_conversion, cost_per_conversion_ga4,
      revenue_per_conversion, roas
    """
    if df.empty:
        return df

    df = df.copy()

    # CTR: clicks / impressions * 100
    df["ctr_pct"] = np.where(
        df["impressions"] > 0,
        (df["clicks"] / df["impressions"] * 100).round(2),
        0.0,
    )

    # Cost / Conversion (platform-reported)
    df["cost_per_conversion"] = np.where(
        df["conversions"] > 0,
        (df["spend"] / df["conversions"]).round(2),
        np.nan,
    )

    # Cost / Conversion (GA4) — only if GA4 data was joined
    if "ga4_conversions" in df.columns:
        df["ga4_cost_per_conversion"] = np.where(
            df["ga4_conversions"] > 0,
            (df["spend"] / df["ga4_conversions"]).round(2),
            np.nan,
        )

    # Revenue / Conversion
    df["revenue_per_conversion"] = np.where(
        df["conversions"] > 0,
        (df["revenue"] / df["conversions"]).round(2),
        np.nan,
    )

    # ROAS: revenue / spend
    df["roas"] = np.where(
        df["spend"] > 0,
        (df["revenue"] / df["spend"]).round(2),
        np.nan,
    )

    return df


def aggregate_totals(df: pd.DataFrame) -> dict:
    """Returns a top-line KPI summary dict for the KPI card row."""
    if df.empty:
        return {
            "total_spend": 0.0,
            "total_impressions": 0,
            "total_clicks": 0,
            "total_conversions": 0.0,
            "total_revenue": 0.0,
            "blended_roas": 0.0,
            "blended_ctr": 0.0,
        }

    total_spend = df["spend"].sum()
    total_impressions = int(df["impressions"].sum())
    total_clicks = int(df["clicks"].sum())
    total_conversions = df["conversions"].sum()
    total_revenue = df["revenue"].sum()

    return {
        "total_spend": total_spend,
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "total_conversions": total_conversions,
        "total_revenue": total_revenue,
        "blended_roas": (
            round(total_revenue / total_spend, 2) if total_spend > 0 else 0.0
        ),
        "blended_ctr": (
            round(total_clicks / total_impressions * 100, 2)
            if total_impressions > 0
            else 0.0
        ),
    }
