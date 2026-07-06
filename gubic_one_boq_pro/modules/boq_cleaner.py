"""Data cleaning and normalization utilities for imported BoQ rows."""
from __future__ import annotations

import re
from typing import Any

import pandas as pd

from config.settings import CURRENCY, STANDARD_COLUMNS
from modules.utils import clean_text, ensure_columns, now_iso, safe_divide, to_number

TOTAL_PATTERNS = re.compile(r"\b(sub\s*total|grand\s*total|total\s*amount|total\s*=|subtotal)\b", re.I)
ROMAN_RE = re.compile(r"^(?=[MDCLXVI]+$)M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", re.I)
ITEM_CODE_RE = re.compile(r"^\d+(?:\.\d+)*$|^[A-Za-z]{1,4}\d{1,5}$")


def normalize_numeric_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        if col in out.columns:
            out[col] = out[col].map(to_number)
    return out


def infer_row_type(row: pd.Series) -> str:
    desc = clean_text(row.get("item_description"))
    code = clean_text(row.get("item_code"))
    unit = clean_text(row.get("unit"))
    qty = to_number(row.get("quantity"))
    rate = to_number(row.get("rate"))
    amount = to_number(row.get("amount")) or to_number(row.get("total_cost"))

    if not desc and not code:
        return "blank"
    if TOTAL_PATTERNS.search(desc):
        return "total"
    if unit or qty is not None or rate is not None:
        return "item"
    if code and (ROMAN_RE.match(code) or ITEM_CODE_RE.match(code)) and amount is not None:
        return "section_total"
    return "section"


def apply_section_context(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    current_section = ""
    current_subsection = ""
    sections: list[str] = []
    subsections: list[str] = []

    for _, row in out.iterrows():
        rtype = row.get("row_type") or infer_row_type(row)
        desc = clean_text(row.get("item_description"))
        code = clean_text(row.get("item_code"))
        if rtype == "section":
            if ROMAN_RE.match(code) or len(code) <= 4:
                current_section = desc
                current_subsection = ""
            else:
                current_subsection = desc
        elif rtype == "section_total" and desc and not current_section:
            current_section = desc
        sections.append(current_section)
        subsections.append(current_subsection)

    out["section_name"] = out.get("section_name", "")
    out["subsection_name"] = out.get("subsection_name", "")
    out["section_name"] = out["section_name"].where(out["section_name"].astype(str).str.len() > 0, sections)
    out["subsection_name"] = out["subsection_name"].where(out["subsection_name"].astype(str).str.len() > 0, subsections)
    return out


def finalize_standard_dataframe(df: pd.DataFrame, project_meta: dict[str, Any] | None = None) -> pd.DataFrame:
    meta = project_meta or {}
    out = ensure_columns(df, STANDARD_COLUMNS)
    text_cols = [
        "project_id", "project_name", "source_file", "source_sheet", "revision", "package_name",
        "section_name", "subsection_name", "item_code", "item_description", "brand", "unit",
        "currency", "remarks", "row_type"
    ]
    for col in text_cols:
        out[col] = out[col].map(clean_text)

    numeric_cols = [
        "quantity", "rate", "amount", "material_rate", "material_cost", "labor_rate", "labor_cost",
        "equipment_rate", "equipment_cost", "transport_rate", "transport_cost", "risk_cost",
        "direct_cost", "indirect_cost", "total_cost", "area_m2", "cost_per_m2"
    ]
    out = normalize_numeric_columns(out, numeric_cols)

    out["currency"] = out["currency"].replace("", CURRENCY).fillna(CURRENCY)
    out["project_name"] = out["project_name"].replace("", meta.get("project_name", "Imported BoQ Project"))
    out["revision"] = out["revision"].replace("", meta.get("revision", ""))
    out["area_m2"] = out["area_m2"].fillna(meta.get("area_m2"))

    out["amount"] = out["amount"].fillna(out["quantity"].fillna(0) * out["rate"].fillna(0))
    component_cols = ["material_cost", "labor_cost", "equipment_cost", "transport_cost", "risk_cost"]
    components = out[component_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
    component_sum = components.sum(axis=1)
    out["direct_cost"] = pd.to_numeric(out["direct_cost"], errors="coerce").fillna(component_sum.where(component_sum != 0, out["amount"]))
    out["total_cost"] = out["total_cost"].fillna(out["direct_cost"].fillna(out["amount"]))
    out["cost_per_m2"] = out.apply(lambda r: safe_divide(r.get("total_cost"), r.get("area_m2")), axis=1)

    out["row_type"] = out.apply(infer_row_type, axis=1)
    out = apply_section_context(out)

    now = now_iso()
    out["created_at"] = out["created_at"].replace("", now).fillna(now)
    out["updated_at"] = out["updated_at"].replace("", now).fillna(now)
    return out[STANDARD_COLUMNS]


def item_rows(df: pd.DataFrame, positive_only: bool = False) -> pd.DataFrame:
    out = df[df["row_type"].eq("item")].copy()
    out = out[out["item_description"].astype(str).str.len() > 0]
    if positive_only:
        out = out[out["total_cost"].fillna(0) > 0]
    return out
