from __future__ import annotations
from config.settings import FAVICON_PATH
import streamlit as st
from modules.report_generator import export_detailed_excel, export_pdf_summary, export_word_report
from modules.cost_engine import answer_predefined_query
from modules.i18n import t
from modules.ui_helpers import inject_css, page_header, require_data, fit_dataframe

st.set_page_config(page_title="Reports - Gubic ONE BoQ Pro", page_icon=str(FAVICON_PATH), layout="wide")
inject_css()
page_header(t("reports"), t("reports_subtitle"))
meta, df = require_data()
if df.empty: st.stop()
project_name = (meta or {}).get("project_name", t("boq_project"))

cols = st.columns(3)
with cols[0]:
    if st.button(t("generate_excel"), type="primary"):
        path = export_detailed_excel(df, project_name)
        st.success(f"{t('created')}: {path}")
        st.download_button(t("download_excel"), path.read_bytes(), path.name, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
with cols[1]:
    if st.button(t("generate_word")):
        path = export_word_report(df, project_name)
        st.success(f"{t('created')}: {path}")
        st.download_button(t("download_word"), path.read_bytes(), path.name, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
with cols[2]:
    if st.button(t("generate_pdf")):
        path = export_pdf_summary(df, project_name)
        st.success(f"{t('created')}: {path}")
        st.download_button(t("download_pdf"), path.read_bytes(), path.name, "application/pdf")

st.divider()
st.subheader(t("ai_query_buttons"))
queries = {
    t("query_highest_package"): "highest_package",
    t("query_total_material"): "total_material",
    t("query_top20"): "top20",
    t("query_cost_per_m2"): "cost_per_m2",
    t("query_highest_sheet"): "highest_sheet",
    t("query_concrete"): "concrete",
    t("query_steel"): "steel",
    t("query_brickwork"): "brickwork",
}
choice = st.selectbox(t("select_query"), list(queries.keys()))
if st.button(t("run_query")):
    answer, table = answer_predefined_query(df, queries[choice])
    st.success(answer)
    if table is not None:
        fit_dataframe(table, use_container_width=True)
