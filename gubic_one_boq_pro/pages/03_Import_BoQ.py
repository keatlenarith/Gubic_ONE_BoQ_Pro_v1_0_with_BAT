from __future__ import annotations
import pandas as pd
import streamlit as st
from config.settings import UPLOAD_DIR, SAMPLE_DIR
from database.db_manager import save_project
from modules.boq_parser import parse_boq_workbook, parse_material_lookup
from modules.excel_importer import inspect_workbook
from modules.cost_engine import calculate_kpis, validation_report
from modules.ui_helpers import inject_css, page_header, kpi_card
from modules.utils import write_uploaded_file

st.set_page_config(page_title="Import BoQ - Gubic ONE BoQ Pro", layout="wide")
inject_css()
page_header("Import BoQ", "Upload Excel BoQ workbooks, detect sheets, clean data, and save to the local project database.")

source_mode = st.radio("Source", ["Upload Excel file", "Use bundled sample workbook"], horizontal=True)
path = None
if source_mode == "Upload Excel file":
    uploaded = st.file_uploader("Upload .xlsx workbook", type=["xlsx"])
    if uploaded:
        path = write_uploaded_file(uploaded, UPLOAD_DIR)
else:
    samples = list(SAMPLE_DIR.glob("*.xlsx"))
    if not samples:
        st.warning("No sample workbook found in data/sample.")
    else:
        path = samples[0]
        st.info(f"Using sample: {path.name}")

project_name_override = st.text_input("Project name override (optional)")
if path:
    with st.expander("Workbook sheet inspection", expanded=True):
        profiles = inspect_workbook(path)
        st.dataframe(pd.DataFrame([p.__dict__ for p in profiles]), use_container_width=True)

    if st.button("Import and standardize workbook", type="primary"):
        with st.spinner("Parsing workbook and standardizing BoQ rows..."):
            df, warnings, meta = parse_boq_workbook(path, project_name=project_name_override or None)
            meta["warnings"] = warnings
            meta["source_file"] = path.name
            materials = parse_material_lookup(path)
        if df.empty:
            st.error("No usable BoQ item data was detected. Review the sheet inspection and source workbook layout.")
        else:
            save_project(meta, df)
            st.session_state["boq_df"] = df
            st.session_state["project_meta"] = meta
            st.session_state["material_lookup"] = materials
            kpis = calculate_kpis(df)
            st.success(f"Imported {len(df):,} standardized rows. Item rows: {kpis['number_of_boq_items']:,}.")
            cols = st.columns(4)
            with cols[0]: kpi_card("Total Cost", kpis["total_project_cost"])
            with cols[1]: kpi_card("Material Cost", kpis["total_material_cost"])
            with cols[2]: kpi_card("Labor Cost", kpis["total_labor_cost"])
            with cols[3]: kpi_card("Cost / m²", f"${kpis['cost_per_m2']:,.2f}/m²")
            if warnings:
                st.warning("Some sheets were skipped or produced warnings.")
                st.dataframe(pd.DataFrame(warnings), use_container_width=True)
            st.subheader("Preview standardized BoQ")
            st.dataframe(df.head(200), use_container_width=True)
            val = validation_report(df)
            st.subheader("Validation findings")
            st.dataframe(val.head(300), use_container_width=True)
