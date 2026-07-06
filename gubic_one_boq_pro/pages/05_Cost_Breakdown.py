from __future__ import annotations
from config.settings import FAVICON_PATH
import streamlit as st
from modules.cost_engine import cost_breakdown, package_ranking, section_ranking, top_items, validation_report
from modules.dashboard_engine import cost_breakdown_pie, package_bar, top_items_bar
from modules.i18n import t
from modules.ui_helpers import inject_css, page_header, require_data, filter_dataframe

st.set_page_config(page_title="Cost Breakdown - Gubic ONE BoQ Pro", page_icon=str(FAVICON_PATH), layout="wide")
inject_css()
page_header(t("cost_breakdown"), t("cost_breakdown_subtitle"))
meta, df = require_data()
if df.empty: st.stop()
filtered = filter_dataframe(df)
left, right = st.columns([1,1])
with left: st.plotly_chart(cost_breakdown_pie(filtered), use_container_width=True)
with right: st.plotly_chart(package_bar(filtered, 12), use_container_width=True)

tabs = st.tabs([t("cost_type"), t("package_ranking"), t("section_ranking"), t("top_items"), t("validation")])
with tabs[0]: st.dataframe(cost_breakdown(filtered), use_container_width=True)
with tabs[1]: st.dataframe(package_ranking(filtered), use_container_width=True)
with tabs[2]: st.dataframe(section_ranking(filtered), use_container_width=True)
with tabs[3]:
    st.plotly_chart(top_items_bar(filtered, 20), use_container_width=True)
    st.dataframe(top_items(filtered, 50), use_container_width=True)
with tabs[4]: st.dataframe(validation_report(filtered), use_container_width=True)
