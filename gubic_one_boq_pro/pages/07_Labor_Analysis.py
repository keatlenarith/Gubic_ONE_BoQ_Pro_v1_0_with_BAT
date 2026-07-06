from __future__ import annotations
from config.settings import FAVICON_PATH
import plotly.express as px
import streamlit as st
from modules.labor_engine import labor_summary, labor_by_package
from modules.cost_engine import calculate_kpis
from modules.i18n import t
from modules.ui_helpers import inject_css, page_header, require_data, filter_dataframe, kpi_card

st.set_page_config(page_title="Labor Analysis - Gubic ONE BoQ Pro", page_icon=str(FAVICON_PATH), layout="wide")
inject_css()
page_header(t("labor_analysis"), t("labor_analysis_subtitle"))
meta, df = require_data()
if df.empty: st.stop()
filtered = filter_dataframe(df)
lab = labor_summary(filtered)
package = labor_by_package(filtered)
k = calculate_kpis(filtered)
cols = st.columns(3)
with cols[0]: kpi_card(t("labor_cost"), lab["labor_cost"].sum() if not lab.empty else 0)
with cols[1]: kpi_card(t("labor_total_pct"), f"{(k['total_labor_cost']/k['total_project_cost'] if k['total_project_cost'] else 0):.1%}")
with cols[2]: kpi_card(t("labor_items"), f"{len(lab):,}")
if not package.empty:
    st.plotly_chart(px.bar(package.head(15), x="labor_cost", y="source_sheet", orientation="h", title=t("labor_cost_by_package")), use_container_width=True)
if not lab.empty:
    top = lab.head(30).copy(); top["label"] = top["item_description"].astype(str).str.slice(0,80)
    st.plotly_chart(px.bar(top, x="labor_cost", y="label", orientation="h", title=t("top_labor_items")), use_container_width=True)
st.dataframe(lab, use_container_width=True)
