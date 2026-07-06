from __future__ import annotations

import streamlit as st

from config.settings import FAVICON_PATH
from modules.cost_engine import validation_report
from modules.i18n import t
from modules.insight_engine import qa_check_summary, qa_score, risk_watchlist
from modules.ui_helpers import inject_css, page_header, require_data, filter_dataframe, kpi_card, download_dataframe_button, fit_dataframe

st.set_page_config(page_title="QA Control - Gubic ONE BoQ Pro", page_icon=str(FAVICON_PATH), layout="wide")
inject_css()
page_header(t("qa_control"), t("qa_control_subtitle"))
meta, df = require_data()
if df.empty:
    st.stop()

filtered = filter_dataframe(df)
score = qa_score(filtered)
cols = st.columns(5)
with cols[0]: kpi_card(t("qa_score"), f"{score['score']}/100")
with cols[1]: kpi_card(t("qa_status"), score["status"])
with cols[2]: kpi_card(t("qa_findings"), f"{score['findings']:,}")
with cols[3]: kpi_card(t("qa_errors"), f"{score['errors']:,}")
with cols[4]: kpi_card(t("qa_warnings"), f"{score['warnings']:,}")

summary = qa_check_summary(filtered)
validations = validation_report(filtered)
watchlist = risk_watchlist(filtered, 30)

tabs = st.tabs([t("qa_summary"), t("validation_findings"), t("risk_watchlist"), t("download_csv")])
with tabs[0]:
    st.subheader(t("qa_summary"))
    fit_dataframe(summary, use_container_width=True)
    st.info(t("qa_workflow_note"))
with tabs[1]:
    st.subheader(t("validation_findings"))
    if validations.empty:
        st.success(t("qa_no_issues_action"))
    else:
        fit_dataframe(validations, use_container_width=True, height=560)
with tabs[2]:
    st.subheader(t("risk_watchlist"))
    st.caption(t("risk_watchlist_note"))
    fit_dataframe(watchlist, use_container_width=True, height=560)
with tabs[3]:
    st.subheader(t("download_csv"))
    download_dataframe_button(summary, "qa_check_summary.csv", t("download_qa_summary"))
    if not validations.empty:
        download_dataframe_button(validations, "qa_validation_findings.csv", t("download_validation_findings"))
    if not watchlist.empty:
        download_dataframe_button(watchlist, "qa_risk_watchlist.csv", t("download_risk_watchlist"))
