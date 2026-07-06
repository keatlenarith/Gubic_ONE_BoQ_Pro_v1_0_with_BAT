from __future__ import annotations
import streamlit as st
from modules.cost_engine import calculate_kpis
from modules.dashboard_engine import cost_breakdown_pie, package_bar, material_labor_stacked, top_items_bar, pareto_chart
from modules.ui_helpers import inject_css, page_header, kpi_card, require_data, filter_dataframe

st.set_page_config(page_title="Dashboard - Gubic ONE BoQ Pro", layout="wide")
inject_css()
page_header("Dashboard", "Executive project cost overview and BoQ analytics.")
meta, df = require_data()
if df.empty: st.stop()
filtered = filter_dataframe(df)
kpis = calculate_kpis(filtered)
cols = st.columns(5)
with cols[0]: kpi_card("Total Cost", kpis["total_project_cost"])
with cols[1]: kpi_card("Material", kpis["total_material_cost"])
with cols[2]: kpi_card("Labor", kpis["total_labor_cost"])
with cols[3]: kpi_card("Cost / m²", f"${kpis['cost_per_m2']:,.2f}/m²")
with cols[4]: kpi_card("Items", f"{kpis['number_of_boq_items']:,}")
left, right = st.columns([1,1])
with left: st.plotly_chart(cost_breakdown_pie(filtered), use_container_width=True)
with right: st.plotly_chart(package_bar(filtered, 10), use_container_width=True)
st.plotly_chart(material_labor_stacked(filtered), use_container_width=True)
st.plotly_chart(top_items_bar(filtered, 20), use_container_width=True)
st.plotly_chart(pareto_chart(filtered), use_container_width=True)
