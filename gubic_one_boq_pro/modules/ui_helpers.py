"""Streamlit UI helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from config.settings import ACCENT_COLOR, BRAND_COLOR, FONT_FAMILY, SAMPLE_DIR
from database.db_manager import load_latest_project
from modules.boq_parser import parse_boq_workbook
from modules.utils import currency


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        html, body, [class*="css"] {{ font-family: {FONT_FAMILY}; }}
        .block-container {{ padding-top: 1.2rem; }}
        .stButton>button {{ border-radius: 10px; border: 1px solid {BRAND_COLOR}; }}
        .gubic-kpi {{ background: white; border: 1px solid #E6ECF2; border-radius: 16px; padding: 16px; }}
        .gubic-kpi-label {{ color: #607087; font-size: .78rem; }}
        .gubic-kpi-value {{ color: {BRAND_COLOR}; font-size: 1.35rem; font-weight: 800; }}
        .gubic-callout {{ background: {ACCENT_COLOR}; padding: 14px 16px; border-radius: 14px; color: #172033; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str | None = None) -> None:
    st.markdown(f"<h1 style='color:{BRAND_COLOR}; margin-bottom:0'>{title}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<p style='color:#607087; margin-top:0'>{subtitle}</p>", unsafe_allow_html=True)


def kpi_card(label: str, value: Any) -> None:
    display = currency(value) if isinstance(value, (float, int)) else str(value)
    st.markdown(
        f"<div class='gubic-kpi'><div class='gubic-kpi-label'>{label}</div><div class='gubic-kpi-value'>{display}</div></div>",
        unsafe_allow_html=True,
    )


def get_active_data() -> tuple[dict[str, Any] | None, pd.DataFrame]:
    if "boq_df" in st.session_state and isinstance(st.session_state["boq_df"], pd.DataFrame) and not st.session_state["boq_df"].empty:
        return st.session_state.get("project_meta"), st.session_state["boq_df"]
    meta, df = load_latest_project()
    if meta and not df.empty:
        st.session_state["project_meta"] = meta
        st.session_state["boq_df"] = df
        return meta, df
    # Try sample workbook for first-run demo.
    samples = list(SAMPLE_DIR.glob("*.xlsx"))
    if samples:
        try:
            df, warnings, meta = parse_boq_workbook(samples[0])
            if not df.empty:
                meta["warnings"] = warnings
                st.session_state["project_meta"] = meta
                st.session_state["boq_df"] = df
                return meta, df
        except Exception:
            pass
    return None, pd.DataFrame()


def require_data() -> tuple[dict[str, Any] | None, pd.DataFrame]:
    meta, df = get_active_data()
    if df.empty:
        st.info("Import a BoQ workbook first from the Import BoQ page.")
    return meta, df


def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    with st.sidebar:
        st.subheader("Filters")
        if "source_sheet" in out:
            options = sorted([x for x in out["source_sheet"].dropna().unique() if str(x).strip()])
            selected = st.multiselect("Sheet / Package", options, default=[])
            if selected:
                out = out[out["source_sheet"].isin(selected)]
        if "section_name" in out:
            options = sorted([x for x in out["section_name"].dropna().unique() if str(x).strip()])[:200]
            selected = st.multiselect("Section", options, default=[])
            if selected:
                out = out[out["section_name"].isin(selected)]
        keyword = st.text_input("Search description")
        if keyword:
            out = out[out["item_description"].astype(str).str.contains(keyword, case=False, na=False)]
    return out


def download_dataframe_button(df: pd.DataFrame, filename: str, label: str = "Download CSV") -> None:
    st.download_button(label, df.to_csv(index=False).encode("utf-8-sig"), filename, "text/csv")
