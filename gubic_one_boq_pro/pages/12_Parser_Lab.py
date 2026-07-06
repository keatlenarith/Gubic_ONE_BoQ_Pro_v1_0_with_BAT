from __future__ import annotations

import pandas as pd
import streamlit as st

from config.settings import FAVICON_PATH, SAMPLE_DIR, UPLOAD_DIR
from modules.excel_importer import inspect_workbook
from modules.i18n import t
from modules.parser_diagnostics import workbook_diagnostics
from modules.ui_helpers import inject_css, page_header, fit_dataframe
from modules.utils import write_uploaded_file

st.set_page_config(page_title="Parser Lab - Gubic ONE BoQ Pro", page_icon=str(FAVICON_PATH), layout="wide")
inject_css()
page_header(t("parser_lab"), t("parser_lab_subtitle"))

source_mode = st.radio(t("source"), [t("upload_excel_file"), t("use_sample_workbook")], horizontal=True)
path = None
if source_mode == t("upload_excel_file"):
    st.markdown(f"<div class='gubic-field-label'>{t('upload_xlsx')}</div>", unsafe_allow_html=True)
    uploaded = st.file_uploader("xlsx", type=["xlsx"], label_visibility="collapsed", key="parser_lab_upload")
    if uploaded:
        path = write_uploaded_file(uploaded, UPLOAD_DIR)
else:
    samples = list(SAMPLE_DIR.glob("*.xlsx"))
    if samples:
        path = samples[0]
        st.info(f"{t('using_sample')}: {path.name}")
    else:
        st.warning(t("no_sample_found"))

if path:
    profiles = inspect_workbook(path)
    profile_df = pd.DataFrame([p.__dict__ for p in profiles])
    st.subheader(t("workbook_sheet_profile"))
    fit_dataframe(profile_df, use_container_width=True)

    names = [p.name for p in profiles if p.non_empty_cells > 0]
    default = [p.name for p in profiles if "sent" in p.name.lower() and p.sheet_type == "boq"] or names[:3]
    selected = st.multiselect(t("sheets_for_diagnostics"), names, default=default)
    if st.button(t("analyze_selected_sheets"), type="primary"):
        with st.spinner(t("reading_mapping_spinner")):
            diag = workbook_diagnostics(path, selected_sheets=selected)
        st.subheader(t("parser_mapping_diagnostics"))
        fit_dataframe(diag, use_container_width=True)
        st.markdown(
            f"""
            **{t('how_to_use_parser_lab')}** {t('parser_lab_help')}
            """
        )
