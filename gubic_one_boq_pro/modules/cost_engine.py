"""Cost calculation, KPI, ranking, and validation engine."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from modules.boq_cleaner import item_rows
from modules.utils import safe_divide


def _sum(df: pd.DataFrame, col: str) -> float:
    if col not in df.columns:
        return 0.0
    return float(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())


def calculate_kpis(df: pd.DataFrame) -> dict[str, Any]:
    if df is None or df.empty:
        return {
            "total_project_cost": 0.0,
            "total_direct_cost": 0.0,
            "total_material_cost": 0.0,
            "total_labor_cost": 0.0,
            "total_equipment_cost": 0.0,
            "total_transport_cost": 0.0,
            "total_risk_cost": 0.0,
            "area_m2": 0.0,
            "cost_per_m2": 0.0,
            "number_of_boq_items": 0,
            "number_of_packages": 0,
        }
    items = item_rows(df, positive_only=False)
    total_cost = _sum(items, "total_cost") or _sum(items, "amount")
    area_m2 = float(pd.to_numeric(df.get("area_m2", pd.Series(dtype=float)), errors="coerce").dropna().max() or 0)
    return {
        "total_project_cost": total_cost,
        "total_direct_cost": _sum(items, "direct_cost"),
        "total_material_cost": _sum(items, "material_cost"),
        "total_labor_cost": _sum(items, "labor_cost"),
        "total_equipment_cost": _sum(items, "equipment_cost"),
        "total_transport_cost": _sum(items, "transport_cost"),
        "total_risk_cost": _sum(items, "risk_cost"),
        "area_m2": area_m2,
        "cost_per_m2": safe_divide(total_cost, area_m2),
        "number_of_boq_items": int(len(items)),
        "number_of_packages": int(items["source_sheet"].nunique() if "source_sheet" in items else 0),
    }


def cost_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    items = item_rows(df, positive_only=False)
    rows = [
        ("Material", _sum(items, "material_cost")),
        ("Labor", _sum(items, "labor_cost")),
        ("Equipment", _sum(items, "equipment_cost")),
        ("Transport", _sum(items, "transport_cost")),
        ("Risk / Contingency", _sum(items, "risk_cost")),
    ]
    known = sum(v for _, v in rows)
    total = _sum(items, "total_cost") or _sum(items, "amount")
    if total > known:
        rows.append(("Unallocated / Other", total - known))
    out = pd.DataFrame(rows, columns=["cost_type", "amount"])
    out = out[out["amount"].fillna(0) > 0]
    total_amt = out["amount"].sum()
    out["percentage"] = out["amount"] / total_amt if total_amt else 0
    return out.sort_values("amount", ascending=False)


def package_ranking(df: pd.DataFrame, group_col: str = "source_sheet") -> pd.DataFrame:
    items = item_rows(df, positive_only=True)
    if items.empty or group_col not in items.columns:
        return pd.DataFrame(columns=[group_col, "total_cost", "items", "percentage"])
    out = (
        items.groupby(group_col, dropna=False)
        .agg(total_cost=("total_cost", "sum"), items=("item_description", "count"))
        .reset_index()
        .sort_values("total_cost", ascending=False)
    )
    total = out["total_cost"].sum()
    out["percentage"] = out["total_cost"] / total if total else 0
    return out


def section_ranking(df: pd.DataFrame) -> pd.DataFrame:
    group = "section_name"
    return package_ranking(df[df[group].astype(str).str.len() > 0], group_col=group) if group in df else pd.DataFrame()


def top_items(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    items = item_rows(df, positive_only=True)
    if items.empty:
        return pd.DataFrame()
    cols = ["source_sheet", "section_name", "item_code", "item_description", "unit", "quantity", "rate", "total_cost", "material_cost", "labor_cost"]
    cols = [c for c in cols if c in items.columns]
    out = items[cols].sort_values("total_cost", ascending=False).head(n).copy()
    total = _sum(items, "total_cost")
    out["percentage_of_total"] = out["total_cost"] / total if total else 0
    return out


def pareto_table(df: pd.DataFrame, n: int = 50) -> pd.DataFrame:
    items = item_rows(df, positive_only=True).sort_values("total_cost", ascending=False).head(n).copy()
    if items.empty:
        return pd.DataFrame()
    total = items["total_cost"].sum()
    items["rank"] = range(1, len(items) + 1)
    items["cumulative_cost"] = items["total_cost"].cumsum()
    items["cumulative_pct"] = items["cumulative_cost"] / total if total else 0
    return items


def validation_report(df: pd.DataFrame) -> pd.DataFrame:
    items = item_rows(df, positive_only=False).copy()
    findings: list[dict[str, Any]] = []
    if items.empty:
        return pd.DataFrame(columns=["severity", "check", "source_sheet", "item_code", "item_description", "value", "message"])

    def add(row: pd.Series, severity: str, check: str, value: Any, message: str):
        findings.append({
            "severity": severity,
            "check": check,
            "source_sheet": row.get("source_sheet", ""),
            "item_code": row.get("item_code", ""),
            "item_description": row.get("item_description", ""),
            "value": value,
            "message": message,
        })

    for _, row in items.iterrows():
        qty = row.get("quantity")
        rate = row.get("rate")
        amount = row.get("amount")
        total = row.get("total_cost")
        if pd.isna(qty):
            add(row, "warning", "Missing quantity", qty, "Quantity is blank or not numeric.")
        if pd.isna(rate):
            add(row, "warning", "Missing rate", rate, "Rate is blank or not numeric.")
        if pd.notna(qty) and pd.notna(rate) and pd.notna(amount):
            expected = float(qty) * float(rate)
            tolerance = max(1.0, abs(expected) * 0.01)
            if abs(expected - float(amount)) > tolerance:
                add(row, "warning", "Amount mismatch", amount, f"Quantity x Rate = {expected:,.2f}, but Amount = {float(amount):,.2f}.")
        for col in ["quantity", "rate", "amount", "total_cost"]:
            val = row.get(col)
            if pd.notna(val) and float(val) < 0:
                add(row, "error", "Negative value", val, f"{col} is negative.")
        if pd.notna(rate) and float(rate) > items["rate"].quantile(0.99) * 3 and float(rate) > 10000:
            add(row, "info", "Very high unit rate", rate, "Unit rate is unusually high compared with the workbook.")
        if pd.notna(qty) and float(qty) > items["quantity"].quantile(0.99) * 3 and float(qty) > 100000:
            add(row, "info", "Very high quantity", qty, "Quantity is unusually high compared with the workbook.")

    if "item_code" in items.columns:
        dupes = items[items["item_code"].astype(str).str.len() > 0]
        dupes = dupes[dupes.duplicated(["source_sheet", "item_code"], keep=False)]
        for _, row in dupes.iterrows():
            add(row, "info", "Duplicate item code", row.get("item_code"), "Same item code appears more than once in the same sheet.")

    empties = items[items["item_description"].astype(str).str.strip().eq("")]
    for _, row in empties.iterrows():
        add(row, "warning", "Empty description", "", "BoQ item row has no description.")
    return pd.DataFrame(findings)


def answer_predefined_query(df: pd.DataFrame, query_key: str) -> tuple[str, pd.DataFrame | None]:
    if query_key == "highest_package":
        tbl = package_ranking(df).head(1)
        if tbl.empty:
            return "No package cost data is available.", None
        row = tbl.iloc[0]
        return f"The highest-cost package is {row['source_sheet']} at ${row['total_cost']:,.2f} ({row['percentage']:.1%} of ranked package cost).", tbl
    if query_key == "total_material":
        total = calculate_kpis(df)["total_material_cost"]
        return f"Total material cost is ${total:,.2f}.", None
    if query_key == "top20":
        return "Top 20 expensive BoQ items.", top_items(df, 20)
    if query_key == "cost_per_m2":
        k = calculate_kpis(df)
        return f"Cost per square meter is ${k['cost_per_m2']:,.2f}/m² based on area {k['area_m2']:,.2f} m².", None
    if query_key == "highest_sheet":
        tbl = package_ranking(df).head(10)
        return "Sheet ranking by cost.", tbl
    if query_key == "concrete":
        return _keyword_query(df, "concrete")
    if query_key == "steel":
        return _keyword_query(df, "steel|rebar|reinforcement|metal")
    if query_key == "brickwork":
        return _keyword_query(df, "brick")
    return "Unknown query.", None


def _keyword_query(df: pd.DataFrame, pattern: str) -> tuple[str, pd.DataFrame]:
    items = item_rows(df, positive_only=True)
    mask = items["item_description"].astype(str).str.contains(pattern, case=False, na=False, regex=True)
    out = items.loc[mask].sort_values("total_cost", ascending=False)
    return f"Found {len(out)} matching BoQ items with total value ${out['total_cost'].sum():,.2f}.", out.head(100)
