"""Streamlit UI helpers."""
from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from config.settings import ACCENT_COLOR, BRAND_COLOR, FONT_FAMILY, SAMPLE_DIR, LOGO_PATH, APP_VERSION
from database.db_manager import load_latest_project
from modules.boq_parser import parse_boq_workbook
from modules.i18n import language_selector, t
from modules.utils import currency


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Khmer:wght@400;500;600;700;800;900&display=swap');

        /* Hide Streamlit's automatic multipage menu so we can render KH/EN labels. */
        [data-testid="stSidebarNav"] {{
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
        }}

        /* Force Noto Sans Khmer across Streamlit widgets, markdown, tables and headings. */
        html, body, .stApp, .main, .block-container,
        h1, h2, h3, h4, h5, h6, p, div, span, label, section, article,
        button, input, textarea, select, option, table, thead, tbody, tr, th, td,
        [class^="st-"], [class*=" st-"], [class*="css"], [data-testid],
        .stMarkdown, .stText, .stCaption, .stAlert, .stButton button,
        .stSelectbox, .stMultiSelect, .stTextInput, .stNumberInput,
        .stDataFrame, .stDataEditor, .stMetric, .stRadio, .stCheckbox {{
            font-family: {FONT_FAMILY} !important;
        }}

        svg text, .plotly text, .js-plotly-plot text {{
            font-family: {FONT_FAMILY} !important;
        }}

        .block-container {{ padding-top: 1.2rem; }}
        .stButton>button {{ border-radius: 10px; border: 1px solid {BRAND_COLOR}; }}
        .gubic-kpi {{ background: white; border: 1px solid #E6ECF2; border-radius: 16px; padding: 16px; min-height: 88px; }}
        .gubic-kpi-label {{ color: #607087; font-size: .78rem; font-weight: 600; }}
        .gubic-kpi-value {{ color: {BRAND_COLOR}; font-size: 1.35rem; font-weight: 800; }}
        .gubic-callout {{ background: {ACCENT_COLOR}; padding: 14px 16px; border-radius: 14px; color: #172033; }}
        .gubic-sidebar-brand {{ margin: -0.3rem 0 .75rem 0; padding-bottom: .85rem; border-bottom: 1px solid #E6ECF2; }}
        .gubic-sidebar-title {{ color: {BRAND_COLOR}; font-weight: 900; font-size: 1.08rem; line-height: 1.15; }}
        .gubic-sidebar-subtitle {{ color: #607087; font-size: .82rem; margin-top: .15rem; }}
        .gubic-sidebar-section {{ color: #607087; font-size: .78rem; font-weight: 800; text-transform: uppercase; letter-spacing: .04em; margin: .7rem 0 .2rem 0; }}
        .gubic-header-wrap {{ display: flex; align-items: center; gap: 16px; margin-bottom: .4rem; }}
        .gubic-header-title {{ color: {BRAND_COLOR}; margin: 0; font-weight: 900; letter-spacing: -.02em; }}
        .gubic-header-subtitle {{ color: #607087; margin-top: .25rem; margin-bottom: 0; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    render_sidebar_brand()
    language_selector("sidebar")
    render_sidebar_navigation()


def render_sidebar_brand() -> None:
    """Render the Gubic logo and product mark in the sidebar."""
    if LOGO_PATH.exists():
        st.sidebar.image(str(LOGO_PATH), width=92)
    st.sidebar.markdown(
        f"""
        <div class='gubic-sidebar-brand'>
            <div class='gubic-sidebar-title'>Gubic ONE</div>
            <div class='gubic-sidebar-subtitle'>BoQ Pro v{APP_VERSION}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_navigation() -> None:
    """Render a localized sidebar navigation menu.

    Streamlit's default multipage menu uses file names and cannot be translated
    at runtime, so it is hidden with CSS and replaced with page_link entries.
    """
    st.sidebar.markdown(f"<div class='gubic-sidebar-section'>{t('navigation')}</div>", unsafe_allow_html=True)
    links = [
        ("app.py", "home", "🏠"),
        ("pages/01_Dashboard.py", "dashboard", "📊"),
        ("pages/02_Project_Setup.py", "project_setup", "🏗️"),
        ("pages/03_Import_BoQ.py", "import_boq", "📥"),
        ("pages/04_BoQ_Database.py", "boq_database", "🧾"),
        ("pages/05_Cost_Breakdown.py", "cost_breakdown", "💰"),
        ("pages/06_Material_Analysis.py", "material_analysis", "🧱"),
        ("pages/07_Labor_Analysis.py", "labor_analysis", "👷"),
        ("pages/08_Equipment_Analysis.py", "equipment_analysis", "🚜"),
        ("pages/09_Progress_Payment.py", "progress_payment", "📈"),
        ("pages/10_Reports.py", "reports", "📄"),
        ("pages/11_Settings.py", "settings", "⚙️"),
        ("pages/12_Parser_Lab.py", "parser_lab", "🧪"),
    ]
    for page, label_key, icon in links:
        try:
            st.sidebar.page_link(page, label=t(label_key), icon=icon)
        except Exception:
            # page_link is available in Streamlit >=1.34; keep a harmless fallback.
            st.sidebar.markdown(f"{icon} {t(label_key)}")


def page_header(title: str, subtitle: str | None = None) -> None:
    """Render a branded page heading with the Gubic logo."""
    logo_col, title_col = st.columns([0.09, 0.91])
    with logo_col:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=62)
    with title_col:
        st.markdown(f"<h1 class='gubic-header-title'>{title}</h1>", unsafe_allow_html=True)
        if subtitle:
            st.markdown(f"<p class='gubic-header-subtitle'>{subtitle}</p>", unsafe_allow_html=True)


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
        st.info(t("import_first"))
    return meta, df


def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    with st.sidebar:
        st.subheader(t("filters"))
        if "source_sheet" in out:
            options = sorted([x for x in out["source_sheet"].dropna().unique() if str(x).strip()])
            selected = st.multiselect(t("sheet_package"), options, default=[])
            if selected:
                out = out[out["source_sheet"].isin(selected)]
        if "section_name" in out:
            options = sorted([x for x in out["section_name"].dropna().unique() if str(x).strip()])[:200]
            selected = st.multiselect(t("section"), options, default=[])
            if selected:
                out = out[out["section_name"].isin(selected)]
        keyword = st.text_input(t("search_description"))
        if keyword:
            out = out[out["item_description"].astype(str).str.contains(keyword, case=False, na=False)]
    return out


def download_dataframe_button(df: pd.DataFrame, filename: str, label: str | None = None) -> None:
    st.download_button(label or t("download_csv"), df.to_csv(index=False).encode("utf-8-sig"), filename, "text/csv")
