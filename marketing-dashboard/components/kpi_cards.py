"""
Top-line KPI card row component.
Displays Spend, Impressions, Clicks, Conversions, Revenue, ROAS, and CTR
as metric tiles across the top of each page.
"""
from __future__ import annotations

import streamlit as st


def _fmt_currency(value: float) -> str:
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.2f}"


def _fmt_number(value: int | float) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{int(value):,}"


def render_kpi_cards(totals: dict) -> None:
    """
    Renders a row of 7 KPI metric tiles.
    totals dict keys:
      total_spend, total_impressions, total_clicks,
      total_conversions, total_revenue, blended_roas, blended_ctr
    """
    cols = st.columns(7)
    metrics = [
        ("Total Spend", _fmt_currency(totals.get("total_spend", 0)), None),
        ("Impressions", _fmt_number(totals.get("total_impressions", 0)), None),
        ("Clicks", _fmt_number(totals.get("total_clicks", 0)), None),
        ("Conversions", _fmt_number(totals.get("total_conversions", 0)), None),
        ("Revenue", _fmt_currency(totals.get("total_revenue", 0)), None),
        ("ROAS", f"{totals.get('blended_roas', 0):.2f}x", None),
        ("CTR", f"{totals.get('blended_ctr', 0):.2f}%", None),
    ]
    for col, (label, value, delta) in zip(cols, metrics):
        col.metric(label, value, delta)
