from __future__ import annotations
from config.settings import FAVICON_PATH
import pandas as pd
import streamlit as st
from modules.boq_cleaner import item_rows
from modules.i18n import t
from modules.ui_helpers import inject_css, page_header, require_data, filter_dataframe, fit_dataframe, fit_data_editor

st.set_page_config(page_title="Progress Payment - Gubic ONE BoQ Pro", page_icon=str(FAVICON_PATH), layout="wide")
inject_css()
page_header(t("progress_payment"), t("progress_payment_subtitle"))
meta, df = require_data()
if df.empty: st.stop()
items = filter_dataframe(item_rows(df, positive_only=True))
base = items[["source_sheet", "item_code", "item_description", "total_cost"]].head(300).copy()
base = base.rename(columns={"total_cost": "contract_amount"})
base["previous_progress_pct"] = 0.0
base["current_progress_pct"] = 0.0
base["cumulative_progress_pct"] = 0.0
edited = fit_data_editor(base, use_container_width=True, height=520, num_rows="dynamic")
if not edited.empty:
    for c in ["previous_progress_pct", "current_progress_pct", "cumulative_progress_pct"]:
        edited[c] = pd.to_numeric(edited[c], errors="coerce").fillna(0) / 100.0
    edited["previous_payment"] = edited["contract_amount"] * edited["previous_progress_pct"]
    edited["current_payment"] = edited["contract_amount"] * edited["current_progress_pct"]
    edited["cumulative_payment"] = edited["contract_amount"] * edited["cumulative_progress_pct"]
    edited["remaining_amount"] = edited["contract_amount"] - edited["cumulative_payment"]
    st.subheader(t("payment_calculation"))
    fit_dataframe(edited, use_container_width=True)
    st.download_button(t("download_payment_csv"), edited.to_csv(index=False).encode("utf-8-sig"), "progress_payment.csv")
