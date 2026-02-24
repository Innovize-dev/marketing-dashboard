"""
Settings page — credential management, cache control, and fetch audit log.
Credentials entered here are encrypted with Fernet and stored in SQLite,
persisting across Streamlit restarts without modifying .env.
"""
from __future__ import annotations

import streamlit as st

from config.credentials import get_platform_creds, save_platform_creds
from storage.cache import clear_cache, clear_expired
from storage.db import log_fetch

st.set_page_config(page_title="Settings | Marketing Dashboard", layout="wide")
st.title("Settings")

conn = st.session_state.get("db_conn")
if conn is None:
    st.error("Database not initialised. Please refresh the page.")
    st.stop()

# ── Credentials ───────────────────────────────────────────────────────────────
st.header("API Credentials")
st.caption(
    "Credentials are encrypted with Fernet before being stored in SQLite. "
    "Set `ENCRYPTION_KEY` in your `.env` file. Values entered here override `.env`."
)

platform_tabs = st.tabs(["Google Ads", "GA4", "Meta", "TikTok", "Reddit"])

# ── Google Ads ──────────────────────────────────────────────────────────────
with platform_tabs[0]:
    st.subheader("Google Ads")
    existing = get_platform_creds(conn, "google_ads")

    developer_token = st.text_input(
        "Developer Token", value=existing.get("developer_token", ""), type="password"
    )
    client_id = st.text_input("Client ID", value=existing.get("client_id", ""))
    client_secret = st.text_input(
        "Client Secret", value=existing.get("client_secret", ""), type="password"
    )
    refresh_token = st.text_input(
        "Refresh Token", value=existing.get("refresh_token", ""), type="password"
    )
    customer_id = st.text_input(
        "Customer ID (10-digit, no dashes)", value=existing.get("customer_id", "")
    )
    login_customer_id = st.text_input(
        "Login Customer ID (MCC, optional)", value=existing.get("login_customer_id", "")
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Google Ads", type="primary"):
            save_platform_creds(
                conn,
                "google_ads",
                {
                    "developer_token": developer_token,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                    "customer_id": customer_id,
                    "login_customer_id": login_customer_id,
                },
            )
            st.success("Google Ads credentials saved.")

    with col2:
        if st.button("Test Google Ads Connection"):
            with st.spinner("Testing..."):
                try:
                    from integrations.google_ads import GoogleAdsAdapter

                    creds = get_platform_creds(conn, "google_ads")
                    adapter = GoogleAdsAdapter(creds)
                    ok = adapter.validate_credentials()
                    if ok:
                        st.success("Connected successfully.")
                    else:
                        st.error("Connection failed — check credentials.")
                except Exception as e:
                    st.error(f"Error: {e}")

# ── GA4 ──────────────────────────────────────────────────────────────────────
with platform_tabs[1]:
    st.subheader("Google Analytics 4")
    existing = get_platform_creds(conn, "ga4")

    property_id = st.text_input(
        "GA4 Property ID (numeric)", value=existing.get("property_id", "")
    )
    st.caption(
        "Service Account JSON: paste the full contents of your service account key JSON file, "
        "or provide the file path."
    )
    sa_json = st.text_area(
        "Service Account JSON",
        value=existing.get("service_account_json", ""),
        height=150,
        type="password" if existing.get("service_account_json") else "default",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save GA4", type="primary"):
            save_platform_creds(
                conn, "ga4", {"property_id": property_id, "service_account_json": sa_json}
            )
            st.success("GA4 credentials saved.")

    with col2:
        if st.button("Test GA4 Connection"):
            with st.spinner("Testing..."):
                try:
                    from integrations.google_analytics import GA4Adapter

                    creds = get_platform_creds(conn, "ga4")
                    adapter = GA4Adapter(creds)
                    ok = adapter.validate_credentials()
                    if ok:
                        st.success("Connected successfully.")
                    else:
                        st.error("Connection failed — check credentials.")
                except Exception as e:
                    st.error(f"Error: {e}")

# ── Meta ──────────────────────────────────────────────────────────────────────
with platform_tabs[2]:
    st.subheader("Meta (Facebook / Instagram)")
    existing = get_platform_creds(conn, "meta")

    app_id = st.text_input("App ID", value=existing.get("app_id", ""))
    app_secret = st.text_input(
        "App Secret", value=existing.get("app_secret", ""), type="password"
    )
    access_token = st.text_input(
        "Access Token (long-lived)", value=existing.get("access_token", ""), type="password"
    )
    ad_account_id = st.text_input(
        "Ad Account ID (act_XXXXXXXXXX)", value=existing.get("ad_account_id", "")
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Meta", type="primary"):
            save_platform_creds(
                conn,
                "meta",
                {
                    "app_id": app_id,
                    "app_secret": app_secret,
                    "access_token": access_token,
                    "ad_account_id": ad_account_id,
                },
            )
            st.success("Meta credentials saved.")

    with col2:
        if st.button("Test Meta Connection"):
            with st.spinner("Testing..."):
                try:
                    from integrations.meta import MetaAdapter

                    creds = get_platform_creds(conn, "meta")
                    adapter = MetaAdapter(creds)
                    ok = adapter.validate_credentials()
                    if ok:
                        st.success("Connected successfully.")
                    else:
                        st.error("Connection failed — check credentials.")
                except Exception as e:
                    st.error(f"Error: {e}")

# ── TikTok ────────────────────────────────────────────────────────────────────
with platform_tabs[3]:
    st.subheader("TikTok Ads")
    existing = get_platform_creds(conn, "tiktok")

    tiktok_access_token = st.text_input(
        "Access Token", value=existing.get("access_token", ""), type="password"
    )
    tiktok_advertiser_id = st.text_input(
        "Advertiser ID", value=existing.get("advertiser_id", "")
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save TikTok", type="primary"):
            save_platform_creds(
                conn,
                "tiktok",
                {
                    "access_token": tiktok_access_token,
                    "advertiser_id": tiktok_advertiser_id,
                },
            )
            st.success("TikTok credentials saved.")

    with col2:
        if st.button("Test TikTok Connection"):
            with st.spinner("Testing..."):
                try:
                    from integrations.tiktok import TikTokAdapter

                    creds = get_platform_creds(conn, "tiktok")
                    adapter = TikTokAdapter(creds)
                    ok = adapter.validate_credentials()
                    if ok:
                        st.success("Connected successfully.")
                    else:
                        st.error("Connection failed — check credentials.")
                except Exception as e:
                    st.error(f"Error: {e}")

# ── Reddit ────────────────────────────────────────────────────────────────────
with platform_tabs[4]:
    st.subheader("Reddit Ads")
    existing = get_platform_creds(conn, "reddit")

    reddit_client_id = st.text_input("Client ID", value=existing.get("client_id", ""))
    reddit_client_secret = st.text_input(
        "Client Secret", value=existing.get("client_secret", ""), type="password"
    )
    reddit_access_token = st.text_input(
        "Access Token", value=existing.get("access_token", ""), type="password"
    )
    reddit_account_id = st.text_input(
        "Account ID (t2_XXXXXXXX)", value=existing.get("account_id", "")
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Reddit", type="primary"):
            save_platform_creds(
                conn,
                "reddit",
                {
                    "client_id": reddit_client_id,
                    "client_secret": reddit_client_secret,
                    "access_token": reddit_access_token,
                    "account_id": reddit_account_id,
                },
            )
            st.success("Reddit credentials saved.")

    with col2:
        if st.button("Test Reddit Connection"):
            with st.spinner("Testing..."):
                try:
                    from integrations.reddit import RedditAdapter

                    creds = get_platform_creds(conn, "reddit")
                    adapter = RedditAdapter(creds)
                    ok = adapter.validate_credentials()
                    if ok:
                        st.success("Connected successfully.")
                    else:
                        st.error("Connection failed — check credentials.")
                except Exception as e:
                    st.error(f"Error: {e}")

st.divider()

# ── Cache settings ────────────────────────────────────────────────────────────
st.header("Cache")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Clear All Cache", use_container_width=True):
        n = clear_cache(conn)
        st.success(f"Cleared {n} cached entries.")

with col2:
    if st.button("Clear Expired Cache", use_container_width=True):
        n = clear_expired(conn)
        st.success(f"Cleared {n} expired entries.")

with col3:
    from config.settings import settings
    st.metric("Cache TTL", f"{settings.CACHE_TTL_SECONDS // 60} min")

st.divider()

# ── Fetch audit log ───────────────────────────────────────────────────────────
st.header("Fetch Log")
st.caption("Last 100 API fetch attempts across all platforms.")

log_rows = conn.execute(
    """SELECT platform, status, row_count, duration_ms, error_msg, fetched_at
       FROM fetch_log
       ORDER BY fetched_at DESC
       LIMIT 100"""
).fetchall()

if log_rows:
    import pandas as pd

    log_df = pd.DataFrame(
        [dict(r) for r in log_rows],
        columns=["platform", "status", "row_count", "duration_ms", "error_msg", "fetched_at"],
    )
    log_df["platform"] = log_df["platform"].str.replace("_", " ").str.title()
    log_df.columns = ["Platform", "Status", "Rows", "Duration (ms)", "Error", "Fetched At"]

    st.dataframe(
        log_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn(
                "Status",
                help="success or error",
            )
        },
    )
else:
    st.info("No fetch history yet.")
