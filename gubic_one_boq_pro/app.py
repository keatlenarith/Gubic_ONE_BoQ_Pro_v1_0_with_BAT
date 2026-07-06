from __future__ import annotations

import streamlit as st

from config.settings import APP_NAME, APP_VERSION, BRAND_COLOR, FAVICON_PATH
from database.db_manager import init_db
from modules.cost_engine import calculate_kpis
from modules.dashboard_engine import cost_breakdown_pie, package_bar, material_labor_stacked, top_items_bar, cost_per_m2_indicator, pareto_chart
from modules.i18n import t
from modules.ui_helpers import get_active_data, inject_css, kpi_card, page_header

st.set_page_config(page_title=f"{APP_NAME} v{APP_VERSION}", page_icon=str(FAVICON_PATH), layout="wide")
inject_css()
init_db()

page_header(f"{APP_NAME} v{APP_VERSION}", t("home_subtitle"))

meta, df = get_active_data()

if df.empty:
    st.markdown(
        f"""
        <div class='gubic-callout'>
        <b>{t('welcome_title')}</b> {t('welcome_body')}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

project_name = (meta or {}).get("project_name", "Imported BoQ Project")
st.markdown(f"<h3 style='color:{BRAND_COLOR}'>{t('active_project')}: {project_name}</h3>", unsafe_allow_html=True)

kpis = calculate_kpis(df)
row1 = st.columns(4)
with row1[0]: kpi_card(t("total_project_cost"), kpis["total_project_cost"])
with row1[1]: kpi_card(t("direct_cost"), kpis["total_direct_cost"])
with row1[2]: kpi_card(t("material_cost"), kpis["total_material_cost"])
with row1[3]: kpi_card(t("labor_cost"), kpis["total_labor_cost"])
row2 = st.columns(4)
with row2[0]: kpi_card(t("equipment_cost"), kpis["total_equipment_cost"])
with row2[1]: kpi_card(t("transport_cost"), kpis["total_transport_cost"])
with row2[2]: kpi_card(t("cost_per_m2"), f"${kpis['cost_per_m2']:,.2f}/m²")
with row2[3]: kpi_card(t("boq_items"), f"{kpis['number_of_boq_items']:,}")

st.divider()
left, right = st.columns([1, 1])
with left:
    st.plotly_chart(cost_breakdown_pie(df), use_container_width=True)
with right:
    st.plotly_chart(cost_per_m2_indicator(kpis["cost_per_m2"], kpis["area_m2"]), use_container_width=True)

st.plotly_chart(package_bar(df), use_container_width=True)
st.plotly_chart(material_labor_stacked(df), use_container_width=True)
st.plotly_chart(top_items_bar(df, 20), use_container_width=True)
st.plotly_chart(pareto_chart(df), use_container_width=True)
