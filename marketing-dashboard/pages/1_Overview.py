"""
Cross-platform Overview page.
Fetches data from all connected platforms, merges them, and displays
a unified campaign report with KPI cards and charts.
"""
from __future__ import annotations

import streamlit as st

from components.charts import (
    conversions_over_time_line,
    impressions_clicks_bar,
    roas_by_platform_bar,
    spend_by_platform_bar,
    spend_over_time_line,
)
from components.date_picker import render_date_picker
from components.kpi_cards import render_kpi_cards
from components.metrics_table import render_metrics_table
from pipeline.fetcher import fetch_platforms
from pipeline.merger import merge_all_platforms, merge_google_ads_ga4
from pipeline.metrics import aggregate_totals, calculate_derived_metrics
from pipeline.transformer import resample_to_granularity, rows_to_dataframe

st.set_page_config(page_title="Overview | Marketing Dashboard", layout="wide")
st.title("Cross-Platform Overview")

# ── Sidebar controls ──────────────────────────────────────────────────────────
date_range, granularity = render_date_picker(key_prefix="overview")

all_platforms = ["google_ads", "ga4", "meta", "tiktok", "reddit"]
platform_labels = {
    "google_ads": "Google Ads",
    "ga4": "GA4",
    "meta": "Meta",
    "tiktok": "TikTok",
    "reddit": "Reddit",
}
selected_labels = st.sidebar.multiselect(
    "Platforms",
    options=list(platform_labels.values()),
    default=list(platform_labels.values()),
)
selected_platforms = [k for k, v in platform_labels.items() if v in selected_labels]

fetch_btn = st.sidebar.button("Fetch Data", type="primary", use_container_width=True)

# ── Data fetching ─────────────────────────────────────────────────────────────
conn = st.session_state.get("db_conn")
if conn is None:
    st.error("Database not initialised. Please refresh the page.")
    st.stop()

if fetch_btn or "overview_df" not in st.session_state:
    if not selected_platforms:
        st.warning("Select at least one platform.")
        st.stop()

    with st.spinner("Fetching data from selected platforms..."):
        from config.settings import settings
        results, errors = fetch_platforms(
            selected_platforms,
            date_range,
            granularity,
            conn,
            ttl_seconds=settings.CACHE_TTL_SECONDS,
        )

    # Show platform-level error banners (non-blocking)
    for platform, msg in errors.items():
        label = platform_labels.get(platform, platform)
        st.warning(f"**{label}**: {msg}", icon="⚠️")

    # Transform each platform's rows
    ads_rows = results.get("google_ads", [])
    ga4_rows = results.get("ga4", [])
    meta_rows = results.get("meta", [])
    tiktok_rows = results.get("tiktok", [])
    reddit_rows = results.get("reddit", [])

    ads_df = resample_to_granularity(rows_to_dataframe(ads_rows), granularity)
    ga4_df = resample_to_granularity(rows_to_dataframe(ga4_rows), granularity)
    meta_df = resample_to_granularity(rows_to_dataframe(meta_rows), granularity)
    tiktok_df = resample_to_granularity(rows_to_dataframe(tiktok_rows), granularity)
    reddit_df = resample_to_granularity(rows_to_dataframe(reddit_rows), granularity)

    # Merge GA4 onto Google Ads
    google_merged = merge_google_ads_ga4(ads_df, ga4_df)

    # Combine all platforms
    unified_df = merge_all_platforms(google_merged, meta_df, tiktok_df, reddit_df)

    if not unified_df.empty:
        unified_df = calculate_derived_metrics(unified_df)

    st.session_state.overview_df = unified_df
    st.session_state.overview_errors = errors

df = st.session_state.get("overview_df")
errors = st.session_state.get("overview_errors", {})

if df is None or df.empty:
    st.info("Click **Fetch Data** to load reports.")
    st.stop()

# ── KPI cards ─────────────────────────────────────────────────────────────────
render_kpi_cards(aggregate_totals(df))

st.divider()

# ── Charts row 1 ─────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(spend_by_platform_bar(df), use_container_width=True)
with col2:
    st.plotly_chart(roas_by_platform_bar(df), use_container_width=True)

# ── Charts row 2 ─────────────────────────────────────────────────────────────
col3, col4 = st.columns(2)
with col3:
    st.plotly_chart(spend_over_time_line(df), use_container_width=True)
with col4:
    st.plotly_chart(conversions_over_time_line(df), use_container_width=True)

st.divider()

# ── Unified campaign table ────────────────────────────────────────────────────
render_metrics_table(df, show_platform_col=True, show_ga4_cols=True, title="Campaign Report")
