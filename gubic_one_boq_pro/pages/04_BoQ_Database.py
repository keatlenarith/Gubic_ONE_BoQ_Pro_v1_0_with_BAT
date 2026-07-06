from __future__ import annotations
import streamlit as st
from modules.boq_cleaner import item_rows
from modules.cost_engine import calculate_kpis
from modules.ui_helpers import inject_css, page_header, require_data, filter_dataframe, download_dataframe_button, kpi_card

st.set_page_config(page_title="BoQ Database - Gubic ONE BoQ Pro", layout="wide")
inject_css()
page_header("BoQ Database", "Searchable standardized BoQ table with filters and download.")
meta, df = require_data()
if df.empty: st.stop()
filtered = filter_dataframe(item_rows(df))
cols = st.columns(3)
k = calculate_kpis(filtered)
with cols[0]: kpi_card("Filtered Items", f"{len(filtered):,}")
with cols[1]: kpi_card("Filtered Cost", k["total_project_cost"])
with cols[2]: download_dataframe_button(filtered, "filtered_boq_items.csv")
st.dataframe(filtered, use_container_width=True, height=650)
