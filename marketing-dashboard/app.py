"""
Marketing Dashboard — Streamlit entry point.
Initializes the SQLite database and sets global page config.
Navigation is handled automatically by Streamlit's multi-page app
based on the files in the pages/ directory.
"""
import os

import streamlit as st

from config.settings import settings
from storage.db import initialize_db

st.set_page_config(
    page_title="Marketing Dashboard",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize DB once per session
if "db_conn" not in st.session_state:
    os.makedirs(os.path.dirname(settings.DB_PATH), exist_ok=True)
    st.session_state.db_conn = initialize_db(settings.DB_PATH)

st.title("Marketing Dashboard")
st.markdown(
    """
    Welcome to the agency reporting dashboard. Use the sidebar to navigate between pages.

    **Pages:**
    - **Overview** — Cross-platform summary with unified campaign table
    - **Google Ads** — Google Ads performance with GA4 attribution
    - **Meta** — Facebook & Instagram campaigns
    - **TikTok** — TikTok Ads campaigns
    - **Reddit** — Reddit Ads campaigns
    - **Settings** — Configure API credentials and cache settings

    > **First time?** Go to **Settings** to enter your API credentials before viewing reports.
    """
)

# Quick-link buttons
col1, col2, col3 = st.columns(3)
with col1:
    st.page_link("pages/1_Overview.py", label="Open Overview", icon=":bar_chart:")
with col2:
    st.page_link("pages/6_Settings.py", label="Configure Credentials", icon=":key:")
