"""Plotly dashboard chart builders."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from modules.cost_engine import cost_breakdown, package_ranking, pareto_table, top_items
from modules.i18n import t
<<<<<<< HEAD
=======
from config.settings import FONT_FAMILY


def _apply_font(fig: go.Figure) -> go.Figure:
    """Apply Gubic UI font to all Plotly charts, including Khmer labels."""
    fig.update_layout(font={"family": FONT_FAMILY})
    return fig
>>>>>>> 3fa6c8a (Set app font to Noto Sans Khmer)


def _empty_figure(title: str) -> go.Figure:
    fig = go.Figure()
<<<<<<< HEAD
    fig.update_layout(title=title, template="plotly_white", height=360)
    fig.add_annotation(text=t("no_data_available"), x=0.5, y=0.5, showarrow=False)
    return fig
=======
    fig.update_layout(title=title, template="plotly_white", height=360, font={"family": FONT_FAMILY})
    fig.add_annotation(text=t("no_data_available"), x=0.5, y=0.5, showarrow=False)
    return _apply_font(fig)
>>>>>>> 3fa6c8a (Set app font to Noto Sans Khmer)


def cost_breakdown_pie(df: pd.DataFrame) -> go.Figure:
    data = cost_breakdown(df)
    if data.empty:
        return _empty_figure(t("cost_breakdown"))
    label_map = {
        "Material": t("material"),
        "Labor": t("labor"),
        "Equipment": t("equipment"),
        "Transport": t("transport"),
        "Risk / Contingency": t("risk_contingency"),
        "Unallocated / Other": t("unallocated_other"),
    }
    data = data.copy()
    data["cost_type_label"] = data["cost_type"].map(label_map).fillna(data["cost_type"])
    fig = px.pie(data, names="cost_type_label", values="amount", title=t("chart_cost_breakdown_type"), hole=0.45)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(template="plotly_white", height=420, legend_title_text=t("cost_type"))
<<<<<<< HEAD
    return fig
=======
    return _apply_font(fig)
>>>>>>> 3fa6c8a (Set app font to Noto Sans Khmer)


def package_bar(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    data = package_ranking(df).head(top_n)
    if data.empty:
        return _empty_figure(t("package_ranking"))
    fig = px.bar(data, x="total_cost", y="source_sheet", orientation="h", title=t("chart_package_ranking", n=top_n), text="total_cost")
    fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
    fig.update_layout(template="plotly_white", height=480, yaxis={"categoryorder": "total ascending"}, xaxis_title=t("total_cost_usd"), yaxis_title=t("package_sheet"))
<<<<<<< HEAD
    return fig
=======
    return _apply_font(fig)
>>>>>>> 3fa6c8a (Set app font to Noto Sans Khmer)


def material_labor_stacked(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty_figure(t("chart_material_labor"))
    items = df[df.get("row_type", "").eq("item")].copy() if "row_type" in df else df.copy()
    if items.empty:
        return _empty_figure(t("chart_material_labor"))
    data = items.groupby("source_sheet", as_index=False).agg(material=("material_cost", "sum"), labor=("labor_cost", "sum"), total=("total_cost", "sum"))
    data = data.sort_values("total", ascending=False).head(12)
    if data[["material", "labor"]].fillna(0).sum().sum() == 0:
        return _empty_figure(t("chart_material_labor"))
    fig = go.Figure()
    fig.add_bar(y=data["source_sheet"], x=data["material"], name=t("material"), orientation="h")
    fig.add_bar(y=data["source_sheet"], x=data["labor"], name=t("labor"), orientation="h")
    fig.update_layout(barmode="stack", template="plotly_white", title=t("chart_material_labor"), height=460, xaxis_title="USD", yaxis_title=t("package_sheet"))
<<<<<<< HEAD
    return fig
=======
    return _apply_font(fig)
>>>>>>> 3fa6c8a (Set app font to Noto Sans Khmer)


def top_items_bar(df: pd.DataFrame, n: int = 20) -> go.Figure:
    data = top_items(df, n)
    if data.empty:
        return _empty_figure(t("top_items"))
    data = data.copy()
    data["label"] = data["item_description"].astype(str).str.slice(0, 70)
    fig = px.bar(data, x="total_cost", y="label", orientation="h", title=t("chart_top_expensive", n=n), hover_data=[c for c in ["source_sheet", "item_code", "unit", "quantity"] if c in data])
    fig.update_layout(template="plotly_white", height=620, yaxis={"categoryorder": "total ascending"}, xaxis_title=t("total_cost_usd"), yaxis_title=t("item"))
<<<<<<< HEAD
    return fig
=======
    return _apply_font(fig)
>>>>>>> 3fa6c8a (Set app font to Noto Sans Khmer)


def pareto_chart(df: pd.DataFrame) -> go.Figure:
    data = pareto_table(df, 50)
    if data.empty:
        return _empty_figure(t("chart_pareto"))
    fig = go.Figure()
    fig.add_bar(x=data["rank"], y=data["total_cost"], name=t("item_cost"))
    fig.add_scatter(x=data["rank"], y=data["cumulative_pct"], mode="lines+markers", name=t("cumulative_pct"), yaxis="y2")
    fig.update_layout(
        template="plotly_white",
        title=t("chart_pareto"),
        height=460,
        xaxis_title=t("rank"),
        yaxis=dict(title=t("cost_usd")),
        yaxis2=dict(title=t("cumulative_pct"), overlaying="y", side="right", tickformat=".0%", range=[0, 1.05]),
    )
    return _apply_font(fig)


def cost_per_m2_indicator(cost_per_m2: float, area_m2: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="number",
        value=cost_per_m2 or 0,
        number={"prefix": "$", "suffix": "/m²", "valueformat": ",.2f"},
        title={"text": f"{t('chart_cost_per_m2')}<br><span style='font-size:0.8em;color:gray'>{t('area')}: {area_m2:,.2f} m²</span>"},
    ))
    fig.update_layout(template="plotly_white", height=260)
    return _apply_font(fig)
