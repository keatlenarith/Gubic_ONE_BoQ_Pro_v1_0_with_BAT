from __future__ import annotations
import streamlit as st
from config.settings import APP_NAME, APP_VERSION, BRAND_COLOR, ACCENT_COLOR, DATABASE_PATH, EXPORT_DIR, UPLOAD_DIR, FAVICON_PATH
from modules.i18n import LANGUAGE_OPTIONS, get_language, language_selector, t
from modules.ui_helpers import inject_css, page_header

st.set_page_config(page_title="Settings - Gubic ONE BoQ Pro", page_icon=str(FAVICON_PATH), layout="wide")
inject_css()
page_header(t("settings"), t("settings_subtitle"))
st.write(f"**{t('product')}:** {APP_NAME} v{APP_VERSION}")
st.write(f"**{t('theme')}:** Corporate Navy `{BRAND_COLOR}` with accent `{ACCENT_COLOR}`")
st.write(f"**{t('database')}:** `{DATABASE_PATH}`")
st.write(f"**{t('uploads')}:** `{UPLOAD_DIR}`")
st.write(f"**{t('exports')}:** `{EXPORT_DIR}`")

st.subheader(t("interface_language"))
language_selector("settings")
st.info(f"{t('current_language')}: {LANGUAGE_OPTIONS.get(get_language(), get_language())}. {t('language_note')}")

st.subheader(t("future_settings"))
st.checkbox(t("enable_tax"), value=False)
st.checkbox(t("enable_contingency"), value=False)
st.checkbox(t("enable_variation"), value=False)
st.checkbox(t("enable_ai"), value=False)
st.info(t("future_settings_note"))
