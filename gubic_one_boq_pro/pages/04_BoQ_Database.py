from __future__ import annotations
from config.settings import FAVICON_PATH
import streamlit as st
from modules.boq_cleaner import item_rows
from modules.cost_engine import calculate_kpis
from modules.i18n import t
from modules.ui_helpers import inject_css, page_header, require_data, filter_dataframe, download_dataframe_button, kpi_card

st.set_page_config(page_title="BoQ Database - Gubic ONE BoQ Pro", page_icon=str(FAVICON_PATH), layout="wide")
inject_css()
page_header(t("boq_database"), t("boq_database_subtitle"))
meta, df = require_data()
if df.empty: st.stop()
filtered = filter_dataframe(item_rows(df))
cols = st.columns(3)
k = calculate_kpis(filtered)
with cols[0]: kpi_card(t("filtered_items"), f"{len(filtered):,}")
with cols[1]: kpi_card(t("filtered_cost"), k["total_project_cost"])
with cols[2]: download_dataframe_button(filtered, "filtered_boq_items.csv")
st.dataframe(filtered, use_container_width=True, height=650)
