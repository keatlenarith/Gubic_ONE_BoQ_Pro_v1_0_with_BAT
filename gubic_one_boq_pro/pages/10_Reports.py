from __future__ import annotations
import streamlit as st
from modules.report_generator import export_detailed_excel, export_pdf_summary, export_word_report
from modules.cost_engine import answer_predefined_query
from modules.ui_helpers import inject_css, page_header, require_data

st.set_page_config(page_title="Reports - Gubic ONE BoQ Pro", layout="wide")
inject_css()
page_header("Reports", "Export Excel, Word, and PDF reports, plus predefined AI-ready analytical queries.")
meta, df = require_data()
if df.empty: st.stop()
project_name = (meta or {}).get("project_name", "BoQ Project")

cols = st.columns(3)
with cols[0]:
    if st.button("Generate Detailed BoQ Excel", type="primary"):
        path = export_detailed_excel(df, project_name)
        st.success(f"Created: {path}")
        st.download_button("Download Excel", path.read_bytes(), path.name, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
with cols[1]:
    if st.button("Generate Word Summary"):
        path = export_word_report(df, project_name)
        st.success(f"Created: {path}")
        st.download_button("Download Word", path.read_bytes(), path.name, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
with cols[2]:
    if st.button("Generate PDF Summary"):
        path = export_pdf_summary(df, project_name)
        st.success(f"Created: {path}")
        st.download_button("Download PDF", path.read_bytes(), path.name, "application/pdf")

st.divider()
st.subheader("AI-ready predefined query buttons")
queries = {
    "Which package costs the most?": "highest_package",
    "What is the total material cost?": "total_material",
    "What are the top 20 expensive BoQ items?": "top20",
    "What is the cost per square meter?": "cost_per_m2",
    "Which sheet has the highest cost?": "highest_sheet",
    "Find all concrete-related items": "concrete",
    "Find all steel-related items": "steel",
    "Find all brickwork items": "brickwork",
}
choice = st.selectbox("Select query", list(queries.keys()))
if st.button("Run query"):
    answer, table = answer_predefined_query(df, queries[choice])
    st.success(answer)
    if table is not None:
        st.dataframe(table, use_container_width=True)
