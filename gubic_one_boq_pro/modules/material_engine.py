"""Material-specific BoQ analysis."""
from __future__ import annotations
import pandas as pd
from modules.boq_cleaner import item_rows


def material_summary(df: pd.DataFrame) -> pd.DataFrame:
    items = item_rows(df, positive_only=True)
    if items.empty or "material_cost" not in items:
        return pd.DataFrame()
    out = items[items["material_cost"].fillna(0) > 0].copy()
    cols = ["source_sheet", "section_name", "item_description", "unit", "quantity", "material_rate", "material_cost", "total_cost"]
    return out[[c for c in cols if c in out.columns]].sort_values("material_cost", ascending=False)


def material_by_package(df: pd.DataFrame) -> pd.DataFrame:
    mats = material_summary(df)
    if mats.empty:
        return pd.DataFrame()
    return mats.groupby("source_sheet", as_index=False).agg(material_cost=("material_cost", "sum"), items=("item_description", "count")).sort_values("material_cost", ascending=False)
