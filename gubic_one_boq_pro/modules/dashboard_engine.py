"""Plotly dashboard chart builders."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config.settings import BRAND_COLOR
from modules.cost_engine import cost_breakdown, package_ranking, pareto_table, top_items


def _empty_figure(title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(title=title, template="plotly_white", height=360)
    fig.add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False)
    return fig


def cost_breakdown_pie(df: pd.DataFrame) -> go.Figure:
    data = cost_breakdown(df)
    if data.empty:
        return _empty_figure("Cost Breakdown")
    fig = px.pie(data, names="cost_type", values="amount", title="Cost Breakdown by Type", hole=0.45)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(template="plotly_white", height=420, legend_title_text="Cost Type")
    return fig


def package_bar(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    data = package_ranking(df).head(top_n)
    if data.empty:
        return _empty_figure("Package Ranking")
    fig = px.bar(data, x="total_cost", y="source_sheet", orientation="h", title=f"Top {top_n} Packages / Sheets by Cost", text="total_cost")
    fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
    fig.update_layout(template="plotly_white", height=480, yaxis={"categoryorder": "total ascending"}, xaxis_title="Total Cost (USD)", yaxis_title="Package / Sheet")
    return fig


def material_labor_stacked(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty_figure("Material vs Labor")
    items = df[df.get("row_type", "").eq("item")].copy() if "row_type" in df else df.copy()
    if items.empty:
        return _empty_figure("Material vs Labor")
    data = items.groupby("source_sheet", as_index=False).agg(material=("material_cost", "sum"), labor=("labor_cost", "sum"), total=("total_cost", "sum"))
    data = data.sort_values("total", ascending=False).head(12)
    if data[["material", "labor"]].fillna(0).sum().sum() == 0:
        return _empty_figure("Material vs Labor")
    fig = go.Figure()
    fig.add_bar(y=data["source_sheet"], x=data["material"], name="Material", orientation="h")
    fig.add_bar(y=data["source_sheet"], x=data["labor"], name="Labor", orientation="h")
    fig.update_layout(barmode="stack", template="plotly_white", title="Material vs Labor by Package", height=460, xaxis_title="USD", yaxis_title="Package / Sheet")
    return fig


def top_items_bar(df: pd.DataFrame, n: int = 20) -> go.Figure:
    data = top_items(df, n)
    if data.empty:
        return _empty_figure("Top BoQ Items")
    data = data.copy()
    data["label"] = data["item_description"].astype(str).str.slice(0, 70)
    fig = px.bar(data, x="total_cost", y="label", orientation="h", title=f"Top {n} Expensive BoQ Items", hover_data=[c for c in ["source_sheet", "item_code", "unit", "quantity"] if c in data])
    fig.update_layout(template="plotly_white", height=620, yaxis={"categoryorder": "total ascending"}, xaxis_title="Total Cost (USD)", yaxis_title="Item")
    return fig


def pareto_chart(df: pd.DataFrame) -> go.Figure:
    data = pareto_table(df, 50)
    if data.empty:
        return _empty_figure("Pareto 80/20")
    fig = go.Figure()
    fig.add_bar(x=data["rank"], y=data["total_cost"], name="Item Cost")
    fig.add_scatter(x=data["rank"], y=data["cumulative_pct"], mode="lines+markers", name="Cumulative %", yaxis="y2")
    # Cumulative percentage is plotted on the secondary axis. The 80% threshold can be read from that right axis.
    fig.update_layout(
        template="plotly_white",
        title="Pareto 80/20 Cost Concentration",
        height=460,
        xaxis_title="Rank",
        yaxis=dict(title="Cost (USD)"),
        yaxis2=dict(title="Cumulative %", overlaying="y", side="right", tickformat=".0%", range=[0, 1.05]),
    )
    return fig


def cost_per_m2_indicator(cost_per_m2: float, area_m2: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="number",
        value=cost_per_m2 or 0,
        number={"prefix": "$", "suffix": "/m²", "valueformat": ",.2f"},
        title={"text": f"Cost per m²<br><span style='font-size:0.8em;color:gray'>Area: {area_m2:,.2f} m²</span>"},
    ))
    fig.update_layout(template="plotly_white", height=260)
    return fig
