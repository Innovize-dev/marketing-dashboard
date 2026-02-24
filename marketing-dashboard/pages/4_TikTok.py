"""TikTok Ads campaigns view."""
from __future__ import annotations

import streamlit as st

from components.charts import conversions_over_time_line, spend_over_time_line
from components.date_picker import render_date_picker
from components.kpi_cards import render_kpi_cards
from components.metrics_table import render_metrics_table
from pipeline.fetcher import fetch_platforms
from pipeline.metrics import aggregate_totals, calculate_derived_metrics
from pipeline.transformer import resample_to_granularity, rows_to_dataframe

st.set_page_config(page_title="TikTok | Marketing Dashboard", layout="wide")
st.title("TikTok Ads")

date_range, granularity = render_date_picker(key_prefix="tiktok")
fetch_btn = st.sidebar.button("Fetch Data", type="primary", use_container_width=True)

conn = st.session_state.get("db_conn")
if conn is None:
    st.error("Database not initialised. Please refresh the page.")
    st.stop()

if fetch_btn or "tiktok_df" not in st.session_state:
    with st.spinner("Fetching TikTok data..."):
        from config.settings import settings
        results, errors = fetch_platforms(
            ["tiktok"], date_range, granularity, conn, ttl_seconds=settings.CACHE_TTL_SECONDS
        )

    for platform, msg in errors.items():
        st.warning(f"**TikTok**: {msg}", icon="⚠️")

    df = resample_to_granularity(
        rows_to_dataframe(results.get("tiktok", [])), granularity
    )
    if not df.empty:
        df = calculate_derived_metrics(df)
    st.session_state.tiktok_df = df

df = st.session_state.get("tiktok_df")
if df is None or df.empty:
    st.info("Click **Fetch Data** to load TikTok reports.")
    st.stop()

st.caption("**Interactions** on TikTok = video play actions (total video plays).")
render_kpi_cards(aggregate_totals(df))
st.divider()

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(spend_over_time_line(df, "tiktok"), use_container_width=True)
with col2:
    st.plotly_chart(conversions_over_time_line(df, "tiktok"), use_container_width=True)

st.divider()
render_metrics_table(df, show_platform_col=False, show_ga4_cols=False, title="TikTok Campaigns")
