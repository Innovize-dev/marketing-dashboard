"""
Google Ads + GA4 combined view.
Shows Google Ads performance with GA4 attribution columns side-by-side.
"""
from __future__ import annotations

import streamlit as st

from components.charts import conversions_over_time_line, spend_over_time_line
from components.date_picker import render_date_picker
from components.kpi_cards import render_kpi_cards
from components.metrics_table import render_metrics_table
from pipeline.fetcher import fetch_platforms
from pipeline.merger import merge_google_ads_ga4
from pipeline.metrics import aggregate_totals, calculate_derived_metrics
from pipeline.transformer import resample_to_granularity, rows_to_dataframe

st.set_page_config(page_title="Google Ads | Marketing Dashboard", layout="wide")
st.title("Google Ads + GA4")

date_range, granularity = render_date_picker(key_prefix="google")
fetch_btn = st.sidebar.button("Fetch Data", type="primary", use_container_width=True)

conn = st.session_state.get("db_conn")
if conn is None:
    st.error("Database not initialised. Please refresh the page.")
    st.stop()

if fetch_btn or "google_df" not in st.session_state:
    with st.spinner("Fetching Google Ads and GA4 data..."):
        from config.settings import settings
        results, errors = fetch_platforms(
            ["google_ads", "ga4"],
            date_range,
            granularity,
            conn,
            ttl_seconds=settings.CACHE_TTL_SECONDS,
        )

    for platform, msg in errors.items():
        label = {"google_ads": "Google Ads", "ga4": "GA4"}.get(platform, platform)
        st.warning(f"**{label}**: {msg}", icon="⚠️")

    ads_df = resample_to_granularity(
        rows_to_dataframe(results.get("google_ads", [])), granularity
    )
    ga4_df = resample_to_granularity(
        rows_to_dataframe(results.get("ga4", [])), granularity
    )
    merged = merge_google_ads_ga4(ads_df, ga4_df)
    if not merged.empty:
        merged = calculate_derived_metrics(merged)

    st.session_state.google_df = merged

df = st.session_state.get("google_df")
if df is None or df.empty:
    st.info("Click **Fetch Data** to load Google Ads reports.")
    st.stop()

render_kpi_cards(aggregate_totals(df))
st.divider()

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(spend_over_time_line(df, "google_ads"), use_container_width=True)
with col2:
    st.plotly_chart(conversions_over_time_line(df, "google_ads"), use_container_width=True)

st.divider()

st.info(
    "**GA4 columns** (Conversions GA, Cost/Conv GA) are sourced from Google Analytics 4 "
    "and joined by campaign name. Discrepancies between platform and GA4 conversions are normal "
    "due to attribution window differences.",
    icon="ℹ️",
)

render_metrics_table(df, show_platform_col=False, show_ga4_cols=True, title="Google Ads Campaigns")
