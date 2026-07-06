from __future__ import annotations

import pandas as pd
import streamlit as st

from config.settings import FAVICON_PATH, STANDARD_COLUMNS
from database.db_manager import save_project
from modules.boq_cleaner import item_rows
from modules.cost_engine import calculate_kpis, validation_report
from modules.edit_engine import (
    EDITABLE_COLUMNS,
    apply_visible_edits,
    build_change_log,
    export_edited_boq_excel,
    merge_edits_to_master,
    prepare_editable_dataframe,
    recalculate_edited_rows,
)
from modules.i18n import t
from modules.ui_helpers import inject_css, page_header, require_data, kpi_card, download_dataframe_button

st.set_page_config(page_title="Editable BoQ Manager - Gubic ONE BoQ Pro", page_icon=str(FAVICON_PATH), layout="wide")
inject_css()
page_header(t("editable_boq_manager"), t("editable_boq_manager_subtitle"))

meta, master_df = require_data()
if master_df.empty:
    st.stop()

if "editable_original_items" not in st.session_state:
    st.session_state["editable_original_items"] = prepare_editable_dataframe(master_df)
if "editable_workspace_items" not in st.session_state:
    st.session_state["editable_workspace_items"] = prepare_editable_dataframe(master_df)

workspace = st.session_state["editable_workspace_items"].copy()

st.markdown(
    f"""
    <div class='gubic-callout'>
    <b>{t('editable_workflow')}</b> {t('editable_workflow_note')}
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader(t("editor_filters"))
    sheet_options = sorted([x for x in workspace.get("source_sheet", pd.Series(dtype=str)).dropna().astype(str).unique() if x.strip()])
    selected_sheets = st.multiselect(t("sheet_package"), sheet_options, default=[])
    keyword = st.text_input(t("search_description"), key="editable_keyword")
    recalc_amount = st.checkbox(t("auto_recalculate_amount"), value=True)

view_mask = pd.Series(True, index=workspace.index)
if selected_sheets:
    view_mask &= workspace["source_sheet"].astype(str).isin(selected_sheets)
if keyword:
    view_mask &= workspace["item_description"].astype(str).str.contains(keyword, case=False, na=False)

visible_before = workspace.loc[view_mask, EDITABLE_COLUMNS].copy()
visible_before = recalculate_edited_rows(visible_before, recalc_amount=False)

kpis = calculate_kpis(workspace)
cols = st.columns(4)
with cols[0]:
    kpi_card(t("editable_rows"), f"{len(workspace):,}")
with cols[1]:
    kpi_card(t("visible_rows"), f"{len(visible_before):,}")
with cols[2]:
    kpi_card(t("total_cost"), kpis["total_project_cost"])
with cols[3]:
    kpi_card(t("qa_findings"), f"{len(validation_report(workspace)):,}")

st.subheader(t("editable_table"))
st.caption(t("editable_table_note"))

column_config = {
    "edit_id": st.column_config.TextColumn("ID", disabled=True, width="small"),
    "source_sheet": st.column_config.TextColumn(t("sheet_package"), width="medium"),
    "section_name": st.column_config.TextColumn(t("section"), width="medium"),
    "subsection_name": st.column_config.TextColumn(t("subsection"), width="medium"),
    "item_code": st.column_config.TextColumn(t("item_code"), width="small"),
    "item_description": st.column_config.TextColumn(t("description"), width="large"),
    "brand": st.column_config.TextColumn(t("brand"), width="small"),
    "unit": st.column_config.TextColumn(t("unit"), width="small"),
    "quantity": st.column_config.NumberColumn(t("quantity"), format="%.4f"),
    "rate": st.column_config.NumberColumn(t("rate"), format="$%.2f"),
    "amount": st.column_config.NumberColumn(t("amount"), format="$%.2f"),
    "material_cost": st.column_config.NumberColumn(t("material_cost"), format="$%.2f"),
    "labor_cost": st.column_config.NumberColumn(t("labor_cost"), format="$%.2f"),
    "equipment_cost": st.column_config.NumberColumn(t("equipment_cost"), format="$%.2f"),
    "transport_cost": st.column_config.NumberColumn(t("transport_cost"), format="$%.2f"),
    "risk_cost": st.column_config.NumberColumn(t("risk_contingency"), format="$%.2f"),
    "remarks": st.column_config.TextColumn(t("remarks"), width="medium"),
}

edited_visible = st.data_editor(
    visible_before,
    use_container_width=True,
    height=620,
    num_rows="dynamic",
    column_config=column_config,
    hide_index=True,
    key="editable_boq_editor",
)

btn1, btn2, btn3, btn4 = st.columns([1.2, 1.4, 1.4, 1.2])
with btn1:
    apply_visible = st.button(t("apply_visible_edits"), type="primary", use_container_width=True)
with btn2:
    save_session = st.button(t("save_to_dashboard"), use_container_width=True)
with btn3:
    save_db = st.button(t("save_to_database"), use_container_width=True)
with btn4:
    reset_editor = st.button(t("reset_editor"), use_container_width=True)

if apply_visible:
    st.session_state["editable_workspace_items"] = apply_visible_edits(workspace, visible_before, edited_visible, recalc_amount=recalc_amount)
    st.success(t("visible_edits_applied"))
    st.rerun()

if save_session:
    edited_master = merge_edits_to_master(master_df, st.session_state["editable_workspace_items"], recalc_amount=recalc_amount)
    st.session_state["boq_df"] = edited_master
    if meta:
        st.session_state["project_meta"] = meta
    st.success(t("saved_to_dashboard"))
    st.rerun()

if save_db:
    edited_master = merge_edits_to_master(master_df, st.session_state["editable_workspace_items"], recalc_amount=recalc_amount)
    if meta:
        save_project(meta, edited_master)
        st.session_state["boq_df"] = edited_master
        st.success(t("saved_to_database"))
    else:
        st.warning(t("no_project_meta"))

if reset_editor:
    st.session_state["editable_original_items"] = prepare_editable_dataframe(master_df)
    st.session_state["editable_workspace_items"] = prepare_editable_dataframe(master_df)
    st.success(t("editor_reset_done"))
    st.rerun()

st.divider()

change_log = build_change_log(st.session_state["editable_original_items"], st.session_state["editable_workspace_items"])
tab1, tab2, tab3 = st.tabs([t("change_log"), t("validation"), t("exports")])
with tab1:
    st.caption(t("change_log_note"))
    if change_log.empty:
        st.info(t("no_changes_detected"))
    else:
        st.dataframe(change_log, use_container_width=True, height=360)
        download_dataframe_button(change_log, "boq_edit_change_log.csv", t("download_change_log"))
with tab2:
    qa = validation_report(st.session_state["editable_workspace_items"])
    if qa.empty:
        st.success(t("qa_no_issues"))
    else:
        st.dataframe(qa, use_container_width=True, height=360)
        download_dataframe_button(qa, "edited_boq_validation.csv", t("download_validation_findings"))
with tab3:
    edited_master_for_export = merge_edits_to_master(master_df, st.session_state["editable_workspace_items"], recalc_amount=recalc_amount)
    excel_bytes = export_edited_boq_excel(edited_master_for_export, change_log)
    st.download_button(
        t("download_edited_boq_excel"),
        data=excel_bytes,
        file_name="Gubic_ONE_Edited_BoQ_v1_3_0.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    st.dataframe(edited_master_for_export[[c for c in STANDARD_COLUMNS if c in edited_master_for_export.columns]].head(100), use_container_width=True, height=320)
