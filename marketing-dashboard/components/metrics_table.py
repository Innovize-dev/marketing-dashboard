"""
Canonical report table renderer.
Displays the full set of report columns matching the agency's existing layout.
Handles formatting, column ordering, campaign search filter, and missing GA4 columns.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

# Internal column name → display label
DISPLAY_COLUMNS: dict[str, str] = {
    "period": "Period",
    "platform": "Platform",
    "campaign_name": "Campaign",
    "impressions": "Impressions",
    "clicks": "Clicks",
    "interactions": "Interactions",
    "conversions": "Conversions",
    "ctr_pct": "CTR (%)",
    "cost_per_conversion": "Cost/Conv",
    "spend": "Total Spend",
    "ga4_conversions": "Conversions (GA)",
    "ga4_cost_per_conversion": "Cost/Conv (GA)",
    "revenue": "Revenue",
    "revenue_per_conversion": "Rev/Conv",
    "roas": "ROAS",
}

# Ordered list for column display
COLUMN_ORDER = list(DISPLAY_COLUMNS.keys())


def _format_df(df: pd.DataFrame) -> pd.DataFrame:
    """Returns a display-ready copy of the DataFrame with formatted values."""
    display = df.copy()

    # Period: format as readable date string
    if "period" in display.columns:
        display["period"] = pd.to_datetime(
            display["period"], errors="coerce"
        ).dt.strftime("%d %b %Y")

    # Round numeric columns
    for col in ["ctr_pct"]:
        if col in display.columns:
            display[col] = display[col].round(2)

    for col in ["roas"]:
        if col in display.columns:
            display[col] = display[col].round(2)

    return display


def render_metrics_table(
    df: pd.DataFrame,
    show_platform_col: bool = True,
    show_ga4_cols: bool = True,
    title: str = "",
) -> None:
    """
    Renders the full campaign report table.

    Parameters:
      df: processed DataFrame with derived metrics already calculated
      show_platform_col: whether to show the Platform column (hide on single-platform pages)
      show_ga4_cols: whether to show GA4 columns (hide on non-Google pages)
      title: optional section title above the table
    """
    if df.empty:
        st.info("No data available for the selected date range.")
        return

    if title:
        st.subheader(title)

    # Campaign search
    search = st.text_input(
        "Search campaigns", "", placeholder="Filter by campaign name..."
    )
    if search:
        mask = df["campaign_name"].str.contains(search, case=False, na=False)
        df = df[mask]

    # Select and order columns
    available_cols = [c for c in COLUMN_ORDER if c in df.columns]

    if not show_platform_col and "platform" in available_cols:
        available_cols.remove("platform")

    if not show_ga4_cols:
        ga4_cols = ["ga4_conversions", "ga4_cost_per_conversion"]
        available_cols = [c for c in available_cols if c not in ga4_cols]

    display_df = _format_df(df[available_cols])
    display_df = display_df.rename(columns=DISPLAY_COLUMNS)

    # Build column config
    column_config = {
        "CTR (%)": st.column_config.NumberColumn(
            "CTR (%)", format="%.2f%%", help="Click-through rate"
        ),
        "ROAS": st.column_config.NumberColumn(
            "ROAS", format="%.2fx", help="Return on ad spend"
        ),
        "Cost/Conv": st.column_config.NumberColumn(
            "Cost/Conv", format="$%.2f", help="Spend / platform conversions"
        ),
        "Cost/Conv (GA)": st.column_config.NumberColumn(
            "Cost/Conv (GA)", format="$%.2f", help="Spend / GA4 conversions"
        ),
        "Total Spend": st.column_config.NumberColumn(
            "Total Spend", format="$%.2f"
        ),
        "Revenue": st.column_config.NumberColumn(
            "Revenue", format="$%.2f"
        ),
        "Rev/Conv": st.column_config.NumberColumn(
            "Rev/Conv", format="$%.2f", help="Revenue / conversions"
        ),
    }

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
    )

    # Row count
    st.caption(f"{len(display_df):,} rows")
