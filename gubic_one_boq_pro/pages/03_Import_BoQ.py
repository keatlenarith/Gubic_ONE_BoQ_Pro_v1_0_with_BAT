from __future__ import annotations

import pandas as pd
import streamlit as st

from config.settings import UPLOAD_DIR, SAMPLE_DIR, FAVICON_PATH
from database.db_manager import save_project
from modules.boq_parser import parse_boq_workbook, parse_material_lookup
from modules.cost_engine import calculate_kpis, validation_report
from modules.excel_importer import inspect_workbook
from modules.i18n import t
from modules.parser_diagnostics import workbook_diagnostics, row_type_summary, description_keyword_summary
from modules.ui_helpers import inject_css, page_header, kpi_card
from modules.utils import write_uploaded_file

st.set_page_config(page_title="Import BoQ - Gubic ONE BoQ Pro", page_icon=str(FAVICON_PATH), layout="wide")
inject_css()
page_header(t("import_boq"), t("import_boq_subtitle"))

source_mode = st.radio(t("source"), [t("upload_excel_file"), t("use_sample_workbook")], horizontal=True)
path = None
if source_mode == t("upload_excel_file"):
    st.markdown(f"<div class='gubic-field-label'>{t('upload_xlsx')}</div>", unsafe_allow_html=True)
    uploaded = st.file_uploader("xlsx", type=["xlsx"], label_visibility="collapsed", key="import_boq_upload")
    if uploaded:
        path = write_uploaded_file(uploaded, UPLOAD_DIR)
else:
    samples = list(SAMPLE_DIR.glob("*.xlsx"))
    if not samples:
        st.warning(t("no_sample_found"))
    else:
        path = samples[0]
        st.info(f"{t('using_sample')}: {path.name}")

project_name_override = st.text_input(t("project_name_override"))

if path:
    profiles = inspect_workbook(path)
    profiles_df = pd.DataFrame([p.__dict__ for p in profiles])

    with st.expander(t("sheet_inspection"), expanded=True):
        st.dataframe(profiles_df, use_container_width=True)

    st.subheader(t("parser_mode"))
    auto_label = t("auto_sent")
    all_label = t("all_detected")
    manual_label = t("manual_select")
    parse_mode_label = st.radio(
        t("choose_parsing_strategy"),
        [auto_label, all_label, manual_label],
        horizontal=False,
        help=t("parser_help"),
    )
    mode_map = {
        auto_label: "auto",
        all_label: "all_detected",
        manual_label: "selected",
    }
    parse_mode = mode_map[parse_mode_label]
    selected_sheets: list[str] | None = None
    if parse_mode == "selected":
        selectable = [p.name for p in profiles if p.non_empty_cells > 0]
        default = [p.name for p in profiles if "sent" in p.name.lower() and p.sheet_type == "boq"] or selectable[:1]
        selected_sheets = st.multiselect(t("sheets_to_parse"), selectable, default=default)

    with st.expander(t("parser_diagnostics"), expanded=False):
        if st.button(t("run_parser_diagnostics")):
            diag = workbook_diagnostics(path, selected_sheets=selected_sheets)
            st.dataframe(diag, use_container_width=True)
            st.caption(t("mapped_columns_caption"))

    if st.button(t("import_standardize"), type="primary"):
        with st.spinner(t("parsing_spinner")):
            df, warnings, meta = parse_boq_workbook(
                path,
                project_name=project_name_override or None,
                parse_mode=parse_mode,
                selected_sheets=selected_sheets,
            )
            meta["warnings"] = warnings
            meta["source_file"] = path.name
            meta["parse_mode"] = parse_mode
            materials = parse_material_lookup(path)

        if df.empty:
            st.error(t("no_usable_data"))
        else:
            save_project(meta, df)
            st.session_state["boq_df"] = df
            st.session_state["project_meta"] = meta
            st.session_state["material_lookup"] = materials
            kpis = calculate_kpis(df)
            st.success(t("import_success", rows=len(df), items=kpis["number_of_boq_items"]))

            cols = st.columns(5)
            with cols[0]: kpi_card(t("total_cost"), kpis["total_project_cost"])
            with cols[1]: kpi_card(t("material_cost"), kpis["total_material_cost"])
            with cols[2]: kpi_card(t("labor_cost"), kpis["total_labor_cost"])
            with cols[3]: kpi_card(t("cost_m2_short"), f"${kpis['cost_per_m2']:,.2f}/m²")
            with cols[4]: kpi_card(t("packages"), f"{kpis['number_of_packages']:,}")

            tabs = st.tabs([t("preview"), t("row_types"), t("keyword_qa"), t("validation"), t("warnings")])
            with tabs[0]:
                st.subheader(t("preview_standardized"))
                st.dataframe(df.head(300), use_container_width=True)
            with tabs[1]:
                st.subheader(t("row_type_summary"))
                st.dataframe(row_type_summary(df), use_container_width=True)
            with tabs[2]:
                st.subheader(t("construction_keyword_summary"))
                st.dataframe(description_keyword_summary(df), use_container_width=True)
            with tabs[3]:
                st.subheader(t("validation_findings"))
                val = validation_report(df)
                st.dataframe(val.head(500), use_container_width=True)
            with tabs[4]:
                if warnings:
                    st.warning(t("parser_warnings"))
                    st.dataframe(pd.DataFrame(warnings), use_container_width=True)
                else:
                    st.success(t("no_parser_warnings"))
