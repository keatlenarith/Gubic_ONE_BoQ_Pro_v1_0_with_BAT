"""Equipment and plant cost analysis."""
from __future__ import annotations
import pandas as pd
from modules.boq_cleaner import item_rows


def equipment_summary(df: pd.DataFrame) -> pd.DataFrame:
    items = item_rows(df, positive_only=True)
    if items.empty:
        return pd.DataFrame()
    if "equipment_cost" in items and items["equipment_cost"].fillna(0).sum() > 0:
        out = items[items["equipment_cost"].fillna(0) > 0].copy()
    else:
        pattern = "equipment|machine|machinery|crane|pump|scaffold|truck|generator|excavator|loader"
        out = items[items["item_description"].astype(str).str.contains(pattern, case=False, na=False, regex=True)].copy()
        out["equipment_cost"] = out.get("total_cost", 0)
    cols = ["source_sheet", "section_name", "item_description", "unit", "quantity", "equipment_rate", "equipment_cost", "total_cost"]
    return out[[c for c in cols if c in out.columns]].sort_values("equipment_cost", ascending=False)


def equipment_by_package(df: pd.DataFrame) -> pd.DataFrame:
    eq = equipment_summary(df)
    if eq.empty:
        return pd.DataFrame()
    return eq.groupby("source_sheet", as_index=False).agg(equipment_cost=("equipment_cost", "sum"), items=("item_description", "count")).sort_values("equipment_cost", ascending=False)
