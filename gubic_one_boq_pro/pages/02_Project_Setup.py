from __future__ import annotations
import streamlit as st
from database.db_manager import list_projects, load_project
from modules.ui_helpers import inject_css, page_header

st.set_page_config(page_title="Project Setup - Gubic ONE BoQ Pro", layout="wide")
inject_css()
page_header("Project Setup", "Review saved projects and switch the active BoQ dataset.")
projects = list_projects()
if projects.empty:
    st.info("No saved projects yet. Import a BoQ workbook first.")
else:
    st.dataframe(projects, use_container_width=True)
    project_ids = projects["project_id"].tolist()
    selected = st.selectbox("Set active project", project_ids, format_func=lambda pid: projects.loc[projects.project_id.eq(pid), "project_name"].iloc[0])
    if st.button("Load selected project"):
        st.session_state["project_meta"] = projects.loc[projects.project_id.eq(selected)].iloc[0].to_dict()
        st.session_state["boq_df"] = load_project(selected)
        st.success("Project loaded into session.")

with st.expander("Recommended project metadata fields for future versions", expanded=False):
    st.markdown("Project code, client, contractor, consultant, revision, contract value, area, currency, base date, tax settings, contingency settings, and approval status.")
