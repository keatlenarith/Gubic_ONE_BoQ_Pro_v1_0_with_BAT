from __future__ import annotations
from config.settings import FAVICON_PATH
import plotly.express as px
import streamlit as st
from modules.material_engine import material_summary, material_by_package
from modules.i18n import t
from modules.ui_helpers import inject_css, page_header, require_data, filter_dataframe, kpi_card

st.set_page_config(page_title="Material Analysis - Gubic ONE BoQ Pro", page_icon=str(FAVICON_PATH), layout="wide")
inject_css()
page_header(t("material_analysis"), t("material_analysis_subtitle"))
meta, df = require_data()
if df.empty: st.stop()
filtered = filter_dataframe(df)
mat = material_summary(filtered)
package = material_by_package(filtered)
cols = st.columns(3)
with cols[0]: kpi_card(t("material_cost"), mat["material_cost"].sum() if not mat.empty else 0)
with cols[1]: kpi_card(t("material_items"), f"{len(mat):,}")
with cols[2]: kpi_card(t("packages"), f"{package['source_sheet'].nunique() if not package.empty else 0:,}")
if not package.empty:
    st.plotly_chart(px.bar(package.head(15), x="material_cost", y="source_sheet", orientation="h", title=t("material_cost_by_package")), use_container_width=True)
if not mat.empty:
    top = mat.head(30).copy(); top["label"] = top["item_description"].astype(str).str.slice(0,80)
    st.plotly_chart(px.bar(top, x="material_cost", y="label", orientation="h", title=t("top_material_items")), use_container_width=True)
st.dataframe(mat, use_container_width=True)
