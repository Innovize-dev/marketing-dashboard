"""
Sidebar date range selector with preset shortcuts and custom range support.
Returns (DateRange, granularity_str).
"""
from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from integrations.base import DateRange


def _first_of_month(d: date) -> date:
    return d.replace(day=1)


def _last_of_month(d: date) -> date:
    next_month = d.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)


def render_date_picker(key_prefix: str = "") -> tuple[DateRange, str]:
    """
    Renders a date range selector in the Streamlit sidebar.
    key_prefix: optional prefix to avoid widget key collisions on multi-page apps.

    Returns:
      (DateRange, granularity) where granularity is "daily" | "weekly" | "monthly"
    """
    today = date.today()

    preset = st.sidebar.selectbox(
        "Date Range",
        [
            "Today",
            "Yesterday",
            "Last 7 Days",
            "Last 30 Days",
            "This Month",
            "Last Month",
            "Custom",
        ],
        key=f"{key_prefix}_date_preset",
    )

    if preset == "Today":
        start, end = today, today
    elif preset == "Yesterday":
        yesterday = today - timedelta(days=1)
        start, end = yesterday, yesterday
    elif preset == "Last 7 Days":
        start, end = today - timedelta(days=7), today - timedelta(days=1)
    elif preset == "Last 30 Days":
        start, end = today - timedelta(days=30), today - timedelta(days=1)
    elif preset == "This Month":
        start, end = _first_of_month(today), today
    elif preset == "Last Month":
        last_month_end = _first_of_month(today) - timedelta(days=1)
        start = _first_of_month(last_month_end)
        end = last_month_end
    else:  # Custom
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start = st.date_input(
                "Start", today - timedelta(days=30), key=f"{key_prefix}_start"
            )
        with col2:
            end = st.date_input("End", today, key=f"{key_prefix}_end")
        if start > end:
            st.sidebar.error("Start date must be before end date.")
            start, end = end, start

    granularity = st.sidebar.radio(
        "Granularity",
        ["Daily", "Weekly", "Monthly"],
        key=f"{key_prefix}_granularity",
    ).lower()

    st.sidebar.caption(
        f"**{start.strftime('%d %b %Y')}** → **{end.strftime('%d %b %Y')}**"
    )

    return DateRange(start=start, end=end), granularity
