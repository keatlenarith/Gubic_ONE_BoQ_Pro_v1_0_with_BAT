from __future__ import annotations
import plotly.express as px
import streamlit as st
from modules.labor_engine import labor_summary, labor_by_package
from modules.cost_engine import calculate_kpis
from modules.ui_helpers import inject_css, page_header, require_data, filter_dataframe, kpi_card

st.set_page_config(page_title="Labor Analysis - Gubic ONE BoQ Pro", layout="wide")
inject_css()
page_header("Labor Analysis", "Labor-heavy work items, package distribution, and labor percentage of project cost.")
meta, df = require_data()
if df.empty: st.stop()
filtered = filter_dataframe(df)
lab = labor_summary(filtered)
package = labor_by_package(filtered)
k = calculate_kpis(filtered)
cols = st.columns(3)
with cols[0]: kpi_card("Labor Cost", lab["labor_cost"].sum() if not lab.empty else 0)
with cols[1]: kpi_card("Labor % of Total", f"{(k['total_labor_cost']/k['total_project_cost'] if k['total_project_cost'] else 0):.1%}")
with cols[2]: kpi_card("Labor Items", f"{len(lab):,}")
if not package.empty:
    st.plotly_chart(px.bar(package.head(15), x="labor_cost", y="source_sheet", orientation="h", title="Labor Cost by Package"), use_container_width=True)
if not lab.empty:
    top = lab.head(30).copy(); top["label"] = top["item_description"].astype(str).str.slice(0,80)
    st.plotly_chart(px.bar(top, x="labor_cost", y="label", orientation="h", title="Top Labor-Heavy Items"), use_container_width=True)
st.dataframe(lab, use_container_width=True)
