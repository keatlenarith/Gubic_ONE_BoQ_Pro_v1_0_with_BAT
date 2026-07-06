from __future__ import annotations
from config.settings import FAVICON_PATH
import plotly.express as px
import streamlit as st
from modules.equipment_engine import equipment_summary, equipment_by_package
from modules.i18n import t
from modules.ui_helpers import inject_css, page_header, require_data, filter_dataframe, kpi_card

st.set_page_config(page_title="Equipment Analysis - Gubic ONE BoQ Pro", page_icon=str(FAVICON_PATH), layout="wide")
inject_css()
page_header(t("equipment_analysis"), t("equipment_analysis_subtitle"))
meta, df = require_data()
if df.empty: st.stop()
filtered = filter_dataframe(df)
eq = equipment_summary(filtered)
package = equipment_by_package(filtered)
cols = st.columns(3)
with cols[0]: kpi_card(t("equipment_cost"), eq["equipment_cost"].sum() if not eq.empty else 0)
with cols[1]: kpi_card(t("equipment_items"), f"{len(eq):,}")
with cols[2]: kpi_card(t("packages"), f"{package['source_sheet'].nunique() if not package.empty else 0:,}")
if not package.empty:
    st.plotly_chart(px.bar(package.head(15), x="equipment_cost", y="source_sheet", orientation="h", title=t("equipment_cost_by_package")), use_container_width=True)
if not eq.empty:
    top = eq.head(30).copy(); top["label"] = top["item_description"].astype(str).str.slice(0,80)
    st.plotly_chart(px.bar(top, x="equipment_cost", y="label", orientation="h", title=t("top_equipment_items")), use_container_width=True)
st.dataframe(eq, use_container_width=True)
