"""
Plotly chart wrappers for the dashboard.
All charts return Plotly figures — call st.plotly_chart(fig, use_container_width=True).
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

_PLATFORM_COLORS = {
    "google_ads": "#4285F4",
    "meta": "#1877F2",
    "tiktok": "#010101",
    "reddit": "#FF4500",
    "ga4": "#34A853",
}

_DEFAULT_COLOR = "#6366F1"


def spend_by_platform_bar(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart: total spend per platform."""
    if df.empty or "spend" not in df.columns:
        return go.Figure()

    summary = (
        df.groupby("platform")["spend"]
        .sum()
        .reset_index()
        .sort_values("spend", ascending=True)
    )
    colors = [_PLATFORM_COLORS.get(p, _DEFAULT_COLOR) for p in summary["platform"]]

    fig = go.Figure(
        go.Bar(
            x=summary["spend"],
            y=summary["platform"].str.replace("_", " ").str.title(),
            orientation="h",
            marker_color=colors,
            text=summary["spend"].map(lambda v: f"${v:,.0f}"),
            textposition="outside",
        )
    )
    fig.update_layout(
        title="Spend by Platform",
        xaxis_title="Spend (USD)",
        yaxis_title="",
        margin=dict(l=20, r=40, t=40, b=20),
        height=300,
    )
    return fig


def roas_by_platform_bar(df: pd.DataFrame) -> go.Figure:
    """Bar chart: blended ROAS per platform."""
    if df.empty:
        return go.Figure()

    summary = (
        df.groupby("platform")
        .agg(spend=("spend", "sum"), revenue=("revenue", "sum"))
        .reset_index()
    )
    summary["roas"] = summary.apply(
        lambda r: round(r["revenue"] / r["spend"], 2) if r["spend"] > 0 else 0,
        axis=1,
    )
    summary = summary.sort_values("roas", ascending=False)
    colors = [_PLATFORM_COLORS.get(p, _DEFAULT_COLOR) for p in summary["platform"]]

    fig = go.Figure(
        go.Bar(
            x=summary["platform"].str.replace("_", " ").str.title(),
            y=summary["roas"],
            marker_color=colors,
            text=summary["roas"].map(lambda v: f"{v:.2f}x"),
            textposition="outside",
        )
    )
    fig.update_layout(
        title="ROAS by Platform",
        yaxis_title="ROAS",
        xaxis_title="",
        margin=dict(l=20, r=20, t=40, b=20),
        height=300,
    )
    return fig


def spend_over_time_line(df: pd.DataFrame, platform: str | None = None) -> go.Figure:
    """Line chart: daily / weekly / monthly spend over time."""
    if df.empty:
        return go.Figure()

    period_col = "period"
    group_df = (
        df.groupby([period_col, "platform"])["spend"].sum().reset_index()
        if platform is None
        else df[df["platform"] == platform]
        .groupby(period_col)["spend"]
        .sum()
        .reset_index()
    )

    if platform is None:
        fig = px.line(
            group_df,
            x=period_col,
            y="spend",
            color="platform",
            color_discrete_map=_PLATFORM_COLORS,
            title="Spend Over Time",
            labels={"spend": "Spend (USD)", period_col: ""},
        )
    else:
        color = _PLATFORM_COLORS.get(platform, _DEFAULT_COLOR)
        fig = go.Figure(
            go.Scatter(
                x=group_df[period_col],
                y=group_df["spend"],
                mode="lines+markers",
                line=dict(color=color),
                name="Spend",
            )
        )
        fig.update_layout(
            title="Spend Over Time",
            yaxis_title="Spend (USD)",
            xaxis_title="",
        )

    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def conversions_over_time_line(
    df: pd.DataFrame, platform: str | None = None
) -> go.Figure:
    """Line chart: conversions over time."""
    if df.empty:
        return go.Figure()

    period_col = "period"
    group_df = (
        df.groupby([period_col, "platform"])["conversions"].sum().reset_index()
        if platform is None
        else df[df["platform"] == platform]
        .groupby(period_col)["conversions"]
        .sum()
        .reset_index()
    )

    if platform is None:
        fig = px.line(
            group_df,
            x=period_col,
            y="conversions",
            color="platform",
            color_discrete_map=_PLATFORM_COLORS,
            title="Conversions Over Time",
            labels={"conversions": "Conversions", period_col: ""},
        )
    else:
        color = _PLATFORM_COLORS.get(platform, _DEFAULT_COLOR)
        fig = go.Figure(
            go.Scatter(
                x=group_df[period_col],
                y=group_df["conversions"],
                mode="lines+markers",
                line=dict(color=color),
                name="Conversions",
            )
        )
        fig.update_layout(
            title="Conversions Over Time",
            yaxis_title="Conversions",
            xaxis_title="",
        )

    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def impressions_clicks_bar(df: pd.DataFrame) -> go.Figure:
    """Grouped bar: impressions vs clicks per platform."""
    if df.empty:
        return go.Figure()

    summary = (
        df.groupby("platform")
        .agg(impressions=("impressions", "sum"), clicks=("clicks", "sum"))
        .reset_index()
    )
    platforms = summary["platform"].str.replace("_", " ").str.title()

    fig = go.Figure(
        [
            go.Bar(name="Impressions", x=platforms, y=summary["impressions"]),
            go.Bar(name="Clicks", x=platforms, y=summary["clicks"]),
        ]
    )
    fig.update_layout(
        barmode="group",
        title="Impressions vs Clicks by Platform",
        yaxis_title="Count",
        margin=dict(l=20, r=20, t=40, b=20),
        height=320,
    )
    return fig
