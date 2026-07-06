from __future__ import annotations
from config.settings import FAVICON_PATH
import streamlit as st
from database.db_manager import list_projects, load_project
from modules.i18n import t
from modules.ui_helpers import inject_css, page_header

st.set_page_config(page_title="Project Setup - Gubic ONE BoQ Pro", page_icon=str(FAVICON_PATH), layout="wide")
inject_css()
page_header(t("project_setup"), t("project_setup_subtitle"))
projects = list_projects()
if projects.empty:
    st.info(t("no_saved_projects"))
else:
    st.dataframe(projects, use_container_width=True)
    project_ids = projects["project_id"].tolist()
    selected = st.selectbox(t("set_active_project"), project_ids, format_func=lambda pid: projects.loc[projects.project_id.eq(pid), "project_name"].iloc[0])
    if st.button(t("load_selected_project")):
        st.session_state["project_meta"] = projects.loc[projects.project_id.eq(selected)].iloc[0].to_dict()
        st.session_state["boq_df"] = load_project(selected)
        st.success(t("project_loaded"))

with st.expander(t("future_metadata_fields"), expanded=False):
    st.markdown(t("future_metadata_text"))
