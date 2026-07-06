"""Labor-specific BoQ analysis."""
from __future__ import annotations
import pandas as pd
from modules.boq_cleaner import item_rows


def labor_summary(df: pd.DataFrame) -> pd.DataFrame:
    items = item_rows(df, positive_only=True)
    if items.empty or "labor_cost" not in items:
        return pd.DataFrame()
    out = items[items["labor_cost"].fillna(0) > 0].copy()
    cols = ["source_sheet", "section_name", "item_description", "unit", "quantity", "labor_rate", "labor_cost", "total_cost"]
    return out[[c for c in cols if c in out.columns]].sort_values("labor_cost", ascending=False)


def labor_by_package(df: pd.DataFrame) -> pd.DataFrame:
    lab = labor_summary(df)
    if lab.empty:
        return pd.DataFrame()
    return lab.groupby("source_sheet", as_index=False).agg(labor_cost=("labor_cost", "sum"), items=("item_description", "count")).sort_values("labor_cost", ascending=False)
