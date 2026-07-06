from __future__ import annotations
import streamlit as st
from config.settings import APP_NAME, APP_VERSION, BRAND_COLOR, ACCENT_COLOR, DATABASE_PATH, EXPORT_DIR, UPLOAD_DIR
from modules.ui_helpers import inject_css, page_header

st.set_page_config(page_title="Settings - Gubic ONE BoQ Pro", layout="wide")
inject_css()
page_header("Settings", "Application configuration and v1.0 roadmap placeholders.")
st.write(f"**Product:** {APP_NAME} v{APP_VERSION}")
st.write(f"**Theme:** Corporate Navy `{BRAND_COLOR}` with accent `{ACCENT_COLOR}`")
st.write(f"**Database:** `{DATABASE_PATH}`")
st.write(f"**Uploads:** `{UPLOAD_DIR}`")
st.write(f"**Exports:** `{EXPORT_DIR}`")

st.subheader("Future settings")
st.checkbox("Enable tax / VAT layer", value=False)
st.checkbox("Enable contingency override", value=False)
st.checkbox("Enable variation order module", value=False)
st.checkbox("Enable AI assistant query layer", value=False)
st.info("These settings are reserved for v1.1+. v1.0 focuses on Excel import, cleaning, dashboarding, validation, and report export.")
