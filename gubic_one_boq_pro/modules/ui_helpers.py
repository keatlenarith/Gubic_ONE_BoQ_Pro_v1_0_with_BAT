"""Streamlit UI helpers."""
from __future__ import annotations

from typing import Any
import base64
import html

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
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarNavItems"],
        [data-testid="stSidebarNavSeparator"],
        section[data-testid="stSidebar"] div[role="navigation"] {{
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            overflow: hidden !important;
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


        /* Khmer text layout patch: prevent glyph clipping/overlap in widgets. */
        html, body, .stApp {{
            text-rendering: optimizeLegibility;
            -webkit-font-smoothing: antialiased;
        }}
        .stMarkdown, .stMarkdown p, .stMarkdown li,
        [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
        [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
        label, label p, .stRadio label, .stCheckbox label,
        .stSelectbox label, .stTextInput label, .stNumberInput label,
        .stMultiSelect label, .stFileUploader label {{
            line-height: 1.75 !important;
            overflow: visible !important;
        }}
        h1, h2, h3, h4, h5, h6 {{
            line-height: 1.35 !important;
            overflow: visible !important;
            padding-top: .1rem;
            padding-bottom: .18rem;
        }}
        .stMarkdown p, .stMarkdown li,
        .gubic-kpi-label, .gubic-insight-comment, .gubic-header-subtitle {{
            overflow-wrap: anywhere;
        }}

        /* Streamlit file uploader/radio/button patch. Khmer text needs taller controls. */
        button, .stButton > button,
        [data-testid="stFileUploader"] button,
        [data-testid="baseButton-secondary"],
        [data-testid="baseButton-primary"] {{
            min-height: 44px !important;
            line-height: 1.45 !important;
            white-space: nowrap !important;
            overflow: visible !important;
            padding: .55rem .9rem !important;
        }}
        [data-testid="stFileUploader"] section {{
            padding: 1rem 1.1rem !important;
            min-height: 74px !important;
            overflow: visible !important;
        }}
        [data-testid="stFileUploader"] small,
        [data-testid="stFileUploaderDropzoneInstructions"] span {{
            line-height: 1.55 !important;
            white-space: nowrap !important;
        }}
        .gubic-field-label {{
            color: #344865;
            font-weight: 700;
            line-height: 1.8 !important;
            margin: .35rem 0 .25rem 0;
            overflow: visible !important;
        }}
        [data-testid="stFileUploader"] label {{
            min-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }}
        [data-testid="stFileUploader"] button,
        [data-testid="stFileUploader"] [data-testid="baseButton-secondary"] {{
            min-width: 128px !important;
            max-width: 160px !important;
            height: 44px !important;
            min-height: 44px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            padding: .35rem .75rem !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }}
        [data-testid="stFileUploader"] button div,
        [data-testid="stFileUploader"] button p,
        [data-testid="stFileUploader"] button span {{
            display: inline-block !important;
            line-height: 1.2 !important;
            margin: 0 !important;
            padding: 0 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }}
        div[role="radiogroup"] label {{
            min-height: 34px !important;
            align-items: center !important;
            line-height: 1.7 !important;
            padding-top: .15rem !important;
            padding-bottom: .15rem !important;
        }}
        .streamlit-expanderHeader,
        [data-testid="stExpander"] details summary,
        [data-testid="stExpander"] details summary p {{
            min-height: 42px !important;
            line-height: 1.75 !important;
            overflow: visible !important;
        }}
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stSelectbox"] div,
        [data-testid="stMultiSelect"] div {{
            min-height: 42px !important;
            line-height: 1.55 !important;
        }}

        /* Dataframes and table headers need more vertical room for Khmer glyphs. */
        [data-testid="stDataFrame"], .stDataFrame {{
            overflow: visible !important;
        }}
        [data-testid="stDataFrame"] div,
        [data-testid="stDataFrame"] span,
        [data-testid="stDataFrame"] p,
        [data-testid="stDataEditor"] div,
        [data-testid="stDataEditor"] span {{
            line-height: 1.55 !important;
        }}

        .block-container {{ padding-top: 1.2rem; }}
        .stButton>button {{ border-radius: 10px; border: 1px solid {BRAND_COLOR}; }}
        .gubic-kpi {{ background: white; border: 1px solid #E6ECF2; border-radius: 16px; padding: 16px; min-height: 88px; }}
        .gubic-kpi-label {{ color: #607087; font-size: .78rem; font-weight: 600; }}
        .gubic-kpi-value {{ color: {BRAND_COLOR}; font-size: 1.35rem; font-weight: 800; }}
        .gubic-callout {{ background: {ACCENT_COLOR}; padding: 14px 16px; border-radius: 14px; color: #172033; }}
        .gubic-insight-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 12px; margin: .35rem 0 1.0rem 0; }}
        .gubic-insight {{ background: #fff; border: 1px solid #E6ECF2; border-left: 5px solid {BRAND_COLOR}; border-radius: 14px; padding: 14px 15px; box-shadow: 0 4px 14px rgba(27, 54, 93, .04); }}
        .gubic-insight.success {{ border-left-color: #1F9D55; }}
        .gubic-insight.warning {{ border-left-color: #C59D2E; }}
        .gubic-insight.danger {{ border-left-color: #D64545; }}
        .gubic-insight-title {{ color: #607087; font-weight: 800; font-size: .78rem; line-height: 1.65; }}
        .gubic-insight-value {{ color: {BRAND_COLOR}; font-weight: 900; font-size: 1.1rem; line-height: 1.55; margin-top: .15rem; }}
        .gubic-insight-comment {{ color: #4E5D70; font-size: .85rem; line-height: 1.75; margin-top: .25rem; }}
        .gubic-insight-native-title {{ color: #607087; font-weight: 800; font-size: .86rem; line-height: 1.65; }}
        .gubic-insight-native-value {{ color: {BRAND_COLOR}; font-weight: 900; font-size: 1.25rem; line-height: 1.55; margin: .15rem 0; }}
        .gubic-sidebar-brand {{ margin: -0.3rem 0 .75rem 0; padding-bottom: .85rem; border-bottom: 1px solid #E6ECF2; }}
        .gubic-sidebar-brand-card {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: .35rem 0 .9rem 0;
            border-bottom: 1px solid #E6ECF2;
            margin-bottom: .85rem;
        }}
        .gubic-sidebar-logo-box {{
            width: 64px;
            height: 64px;
            min-width: 64px;
            border-radius: 18px;
            background: #FFFFFF;
            border: 1px solid #E6ECF2;
            box-shadow: 0 4px 14px rgba(27, 54, 93, .06);
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .gubic-sidebar-logo-box img {{ width: 46px; height: 46px; object-fit: contain; display: block; }}
        .gubic-sidebar-title {{ color: {BRAND_COLOR}; font-weight: 900; font-size: 1.08rem; line-height: 1.35; }}
        .gubic-sidebar-subtitle {{ color: #607087; font-size: .82rem; margin-top: .15rem; line-height: 1.45; }}
        .gubic-sidebar-section {{ color: #607087; font-size: .78rem; font-weight: 800; text-transform: uppercase; letter-spacing: .04em; margin: .7rem 0 .2rem 0; }}
        section[data-testid="stSidebar"] a {{
            line-height: 1.55 !important;
            min-height: 40px !important;
            overflow: visible !important;
            border-radius: 10px !important;
            margin: .06rem 0 !important;
        }}
        section[data-testid="stSidebar"] a svg,
        section[data-testid="stSidebar"] a span[data-testid="stIconMaterial"],
        section[data-testid="stSidebar"] a [data-testid="stIconMaterial"] {{
            color: {BRAND_COLOR} !important;
            fill: {BRAND_COLOR} !important;
            font-size: 1.12rem !important;
            width: 1.25rem !important;
            min-width: 1.25rem !important;
        }}
        /* v1.2.4: Do not display raw Material Symbol names if Streamlit lacks the icon font. */
        section[data-testid="stSidebar"] a span[data-testid="stIconMaterial"],
        section[data-testid="stSidebar"] a [data-testid="stIconMaterial"] {{
            display: none !important;
        }}
        .gubic-nav-fallback {{
            display: flex;
            align-items: center;
            gap: .55rem;
            min-height: 40px;
            padding: .35rem .55rem;
            border-radius: 10px;
            color: #172033;
            font-weight: 600;
            line-height: 1.55;
        }}
        .gubic-nav-icon {{
            color: {BRAND_COLOR};
            font-size: 1.08rem;
            min-width: 1.35rem;
            text-align: center;
        }}
        .gubic-header-wrap {{
            display: flex;
            align-items: center;
            gap: 14px;
            margin: .15rem 0 1.05rem 0;
            padding: .1rem 0 .2rem 0;
        }}
        .gubic-header-logo-box {{
            width: 48px;
            height: 48px;
            min-width: 48px;
            border-radius: 14px;
            background: #FFFFFF;
            border: 1px solid #E6ECF2;
            box-shadow: 0 4px 14px rgba(27, 54, 93, .06);
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .gubic-header-logo-box img {{
            width: 34px;
            height: 34px;
            object-fit: contain;
            display: block;
        }}
        .gubic-header-copy {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-width: 0;
        }}
        .gubic-header-title {{
            color: {BRAND_COLOR};
            margin: 0;
            font-weight: 900;
            letter-spacing: -.02em;
            line-height: 1.35 !important;
            font-size: clamp(2.0rem, 3.2vw, 3.0rem);
            overflow: visible !important;
        }}
        .gubic-header-subtitle {{
            color: #607087;
            margin-top: .42rem;
            margin-bottom: 0;
            line-height: 1.75 !important;
            font-size: 1.02rem;
            overflow: visible !important;
        }}
        @media (max-width: 768px) {{
            .gubic-header-wrap {{ align-items: flex-start; gap: 10px; }}
            .gubic-header-logo-box {{ width: 40px; height: 40px; min-width: 40px; border-radius: 12px; }}
            .gubic-header-logo-box img {{ width: 28px; height: 28px; }}
            .gubic-header-title {{ font-size: 1.55rem; line-height: 1.42 !important; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    render_sidebar_brand()
    language_selector("sidebar")
    render_sidebar_navigation()


def render_sidebar_brand() -> None:
    """Render the Gubic logo and product mark in the sidebar.

    Use an inline image instead of Streamlit's default image widget so the
    logo stays attached to the tool name and does not disappear when the
    sidebar rerenders or when Streamlit Cloud changes the default nav layout.
    """
    logo_uri = _logo_data_uri()
    logo_html = f"<img src='{logo_uri}' alt='Gubic logo'>" if logo_uri else ""
    st.sidebar.markdown(
        f"""
        <div class='gubic-sidebar-brand-card'>
            <div class='gubic-sidebar-logo-box'>{logo_html}</div>
            <div>
                <div class='gubic-sidebar-title'>Gubic ONE<br>BoQ Pro</div>
                <div class='gubic-sidebar-subtitle'>v{APP_VERSION}</div>
            </div>
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
        ("pages/13_QA_Control.py", "qa_control", "✅"),
    ]
    for page, label_key, emoji_icon in links:
        # Avoid Streamlit Material Symbols in the icon parameter. On some
        # Community Cloud builds the icon font is not loaded and the icon name
        # renders as visible text such as "home" or "dashboard", causing
        # ugly overlap. Use compact emoji prefixes inside the label instead.
        label = f"{emoji_icon}  {t(label_key)}"
        try:
            st.sidebar.page_link(page, label=label, use_container_width=True)
        except TypeError:
            try:
                st.sidebar.page_link(page, label=label)
            except Exception:
                st.sidebar.markdown(
                    f"<div class='gubic-nav-fallback'><span class='gubic-nav-icon'>{emoji_icon}</span><span>{html.escape(t(label_key))}</span></div>",
                    unsafe_allow_html=True,
                )
        except Exception:
            st.sidebar.markdown(
                f"<div class='gubic-nav-fallback'><span class='gubic-nav-icon'>{emoji_icon}</span><span>{html.escape(t(label_key))}</span></div>",
                unsafe_allow_html=True,
            )


def _logo_data_uri() -> str:
    """Return the Gubic logo as an inline data URI for a compact HTML header."""
    if not LOGO_PATH.exists():
        return ""
    try:
        encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except Exception:
        return ""


def page_header(title: str, subtitle: str | None = None) -> None:
    """Render a compact branded page heading.

    The logo is placed in a small inline badge instead of a Streamlit image
    column, preventing the top logo from creating a large block/blank area.
    """
    logo_uri = _logo_data_uri()
    logo_html = f"<div class='gubic-header-logo-box'><img src='{logo_uri}' alt='Gubic logo'></div>" if logo_uri else ""
    subtitle_html = f"<p class='gubic-header-subtitle'>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f"""
        <div class='gubic-header-wrap'>
            {logo_html}
            <div class='gubic-header-copy'>
                <h1 class='gubic-header-title'>{title}</h1>
                {subtitle_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_insight_panel(insights: list[dict[str, str]]) -> None:
    """Render executive insight cards using Streamlit-native containers.

    The previous single raw-HTML grid could display literal <div> text on
    Streamlit Cloud when Khmer text, symbols, or sanitizer changes interrupted
    the HTML block. This version uses native containers and escapes values so
    the right panel never shows source HTML.
    """
    if not insights:
        return
    icons = {"success": "✅", "warning": "⚠️", "danger": "🚨", "info": "ℹ️"}
    cols = st.columns(2)
    for idx, item in enumerate(insights):
        status = str(item.get("status", "info"))
        title = html.escape(str(item.get("title", "")))
        value = html.escape(str(item.get("value", "")))
        comment = html.escape(str(item.get("comment", "")))
        with cols[idx % 2]:
            with st.container(border=True):
                st.markdown(f"<div class='gubic-insight-native-title'>{icons.get(status, 'ℹ️')} {title}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='gubic-insight-native-value'>{value}</div>", unsafe_allow_html=True)
                if comment:
                    st.markdown(f"<div class='gubic-insight-comment'>{comment}</div>", unsafe_allow_html=True)


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
