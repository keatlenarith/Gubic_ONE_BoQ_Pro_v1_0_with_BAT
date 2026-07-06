"""Editable BoQ workspace helpers for Gubic ONE BoQ Pro v1.3.1.

The editor is intentionally session-first so it works on Streamlit Community
Cloud without requiring a persistent external database. Users can apply edits to
session state, save the edited dataset into the local SQLite project table, and
export the revised BoQ to Excel for audit and issue control.
"""
from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any
import uuid

import pandas as pd

from config.settings import CURRENCY, STANDARD_COLUMNS
from modules.boq_cleaner import item_rows
from modules.cost_engine import calculate_kpis, validation_report

NUMERIC_COLUMNS = [
    "quantity", "rate", "amount", "material_rate", "material_cost", "labor_rate", "labor_cost",
    "equipment_rate", "equipment_cost", "transport_rate", "transport_cost", "risk_cost",
    "direct_cost", "indirect_cost", "total_cost", "area_m2", "cost_per_m2",
]

EDITABLE_COLUMNS = [
    "edit_id", "source_sheet", "section_name", "subsection_name", "item_code", "item_description",
    "brand", "unit", "quantity", "rate", "amount", "material_cost", "labor_cost",
    "equipment_cost", "transport_cost", "risk_cost", "remarks",
]

USER_EDIT_COLUMNS = [c for c in EDITABLE_COLUMNS if c != "edit_id"]


def _is_blank(value: Any) -> bool:
    """Return True for scalar blank-like values without triggering pandas ambiguity errors."""
    if value is None:
        return True
    if isinstance(value, (pd.Series, pd.DataFrame, list, tuple, dict, set)):
        return False
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _safe_text(value: Any) -> str:
    """Convert any editor cell value to stable text for audit comparisons."""
    if isinstance(value, pd.DataFrame):
        value = value.iloc[0].to_dict() if not value.empty else ""
    if isinstance(value, pd.Series):
        value = value.iloc[0] if not value.empty else ""
    if _is_blank(value):
        return ""
    return str(value)


def _row_get(row: Any, column: str, default: Any = "") -> Any:
    """Safely get a scalar-like value from a row/Series/DataFrame."""
    if isinstance(row, pd.DataFrame):
        if row.empty or column not in row.columns:
            return default
        return row.iloc[0].get(column, default)
    if isinstance(row, pd.Series):
        return row.get(column, default)
    return default


def _clean_number(value: Any) -> float | None:
    """Convert user-edited numeric fields to float where possible."""
    if _is_blank(value):
        return None
    if isinstance(value, pd.Series):
        value = value.iloc[0] if not value.empty else None
    text = str(value).strip()
    if text == "":
        return None
    for token in ["$", ",", "USD", "usd"]:
        text = text.replace(token, "")
    try:
        return float(text)
    except ValueError:
        return None


def ensure_edit_ids(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure every row has a stable, unique edit_id for comparing and merging edits."""
    out = df.copy().reset_index(drop=True)
    if "edit_id" not in out.columns:
        out.insert(0, "edit_id", [f"ROW-{i + 1:06d}" for i in range(len(out))])
        return out

    cleaned_ids: list[str] = []
    seen: set[str] = set()
    for i, value in enumerate(out["edit_id"].tolist()):
        text = _safe_text(value).strip()
        if text.lower() in {"", "nan", "none", "nat"} or text in seen:
            prefix = "NEW" if text.upper().startswith("NEW-") else "ROW"
            text = f"{prefix}-{i + 1:06d}"
            while text in seen:
                text = f"{prefix}-{i + 1:06d}-{uuid.uuid4().hex[:4].upper()}"
        cleaned_ids.append(text)
        seen.add(text)
    out["edit_id"] = cleaned_ids
    return out


def prepare_editable_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Return item rows shaped for Streamlit's editable table."""
    items = item_rows(df, positive_only=False).copy() if df is not None and not df.empty else pd.DataFrame()
    if items.empty:
        items = pd.DataFrame(columns=STANDARD_COLUMNS)
    for col in set(STANDARD_COLUMNS + EDITABLE_COLUMNS):
        if col not in items.columns:
            items[col] = None
    items = ensure_edit_ids(items.reset_index(drop=True))
    for col in NUMERIC_COLUMNS:
        if col in items.columns:
            items[col] = pd.to_numeric(items[col], errors="coerce")
    return items[EDITABLE_COLUMNS + [c for c in STANDARD_COLUMNS if c not in EDITABLE_COLUMNS]].copy()


def recalculate_edited_rows(df: pd.DataFrame, *, recalc_amount: bool = True) -> pd.DataFrame:
    """Recalculate amount/direct/total columns after user edits."""
    out = df.copy()
    for col in STANDARD_COLUMNS:
        if col not in out.columns:
            out[col] = None
    out = ensure_edit_ids(out)

    for col in NUMERIC_COLUMNS:
        if col in out.columns:
            out[col] = out[col].apply(_clean_number)

    if recalc_amount and {"quantity", "rate"}.issubset(out.columns):
        mask = out["quantity"].notna() & out["rate"].notna()
        out.loc[mask, "amount"] = out.loc[mask, "quantity"] * out.loc[mask, "rate"]

    cost_cols = ["material_cost", "labor_cost", "equipment_cost", "transport_cost", "risk_cost"]
    for col in cost_cols:
        if col not in out.columns:
            out[col] = 0.0
    component_sum = out[cost_cols].fillna(0).sum(axis=1)
    amount = pd.to_numeric(out.get("amount", pd.Series(0, index=out.index)), errors="coerce").fillna(0)
    out["direct_cost"] = component_sum.where(component_sum.abs() > 0, amount)
    out["total_cost"] = out["direct_cost"].fillna(0) + pd.to_numeric(out.get("indirect_cost", 0), errors="coerce").fillna(0)
    out["currency"] = out.get("currency", CURRENCY).fillna(CURRENCY) if isinstance(out.get("currency"), pd.Series) else CURRENCY
    out["row_type"] = "item"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if "created_at" not in out.columns:
        out["created_at"] = now
    out["updated_at"] = now
    return out


def apply_visible_edits(workspace_df: pd.DataFrame, visible_before: pd.DataFrame, visible_after: pd.DataFrame, *, recalc_amount: bool = True) -> pd.DataFrame:
    """Merge edited visible rows back into the full editing workspace.

    Rows that were visible before but missing after data_editor are treated as
    deleted. Rows added in the editor receive NEW-* edit IDs.
    """
    workspace = ensure_edit_ids(workspace_df.copy())
    before_ids = set(visible_before.get("edit_id", pd.Series(dtype=str)).astype(str))
    after = visible_after.copy()
    if "edit_id" not in after.columns:
        after["edit_id"] = ""
    after["edit_id"] = after["edit_id"].astype(str)
    missing = after["edit_id"].str.strip().isin(["", "nan", "None"])
    if missing.any():
        after.loc[missing, "edit_id"] = [f"NEW-{uuid.uuid4().hex[:10].upper()}" for _ in range(missing.sum())]

    remaining = workspace[~workspace["edit_id"].astype(str).isin(before_ids)].copy()
    merged = pd.concat([remaining, after], ignore_index=True, sort=False)
    return recalculate_edited_rows(ensure_edit_ids(merged), recalc_amount=recalc_amount)


def merge_edits_to_master(master_df: pd.DataFrame, edited_items: pd.DataFrame, *, recalc_amount: bool = True) -> pd.DataFrame:
    """Replace item rows in the master dataset with edited item rows."""
    master = master_df.copy() if master_df is not None else pd.DataFrame(columns=STANDARD_COLUMNS)
    for col in STANDARD_COLUMNS:
        if col not in master.columns:
            master[col] = None
    non_items = master[master.get("row_type", "").astype(str).str.lower().ne("item")].copy() if not master.empty else pd.DataFrame(columns=STANDARD_COLUMNS)
    edited = recalculate_edited_rows(edited_items.copy(), recalc_amount=recalc_amount)
    for col in STANDARD_COLUMNS:
        if col not in edited.columns:
            edited[col] = None
    combined = pd.concat([non_items[STANDARD_COLUMNS], edited[STANDARD_COLUMNS]], ignore_index=True, sort=False)
    return combined


def build_change_log(original_items: pd.DataFrame, edited_items: pd.DataFrame) -> pd.DataFrame:
    """Create an audit table of new/deleted/changed rows."""
    original = ensure_edit_ids(original_items.copy()) if original_items is not None and not original_items.empty else pd.DataFrame(columns=EDITABLE_COLUMNS)
    edited = ensure_edit_ids(edited_items.copy()) if edited_items is not None and not edited_items.empty else pd.DataFrame(columns=EDITABLE_COLUMNS)
    original = original.set_index("edit_id", drop=False)
    edited = edited.set_index("edit_id", drop=False)
    rows: list[dict[str, Any]] = []

    for edit_id in sorted(set(edited.index) - set(original.index)):
        row = edited.loc[edit_id]
        rows.append({
            "change_type": "added", "edit_id": edit_id, "field": "row", "old_value": "", "new_value": _safe_text(_row_get(row, "item_description")),
            "source_sheet": _safe_text(_row_get(row, "source_sheet")), "item_code": _safe_text(_row_get(row, "item_code")),
        })
    for edit_id in sorted(set(original.index) - set(edited.index)):
        row = original.loc[edit_id]
        rows.append({
            "change_type": "deleted", "edit_id": edit_id, "field": "row", "old_value": _safe_text(_row_get(row, "item_description")), "new_value": "",
            "source_sheet": _safe_text(_row_get(row, "source_sheet")), "item_code": _safe_text(_row_get(row, "item_code")),
        })
    for edit_id in sorted(set(original.index) & set(edited.index)):
        old = original.loc[edit_id]
        new = edited.loc[edit_id]
        for col in USER_EDIT_COLUMNS:
            old_text = _safe_text(_row_get(old, col))
            new_text = _safe_text(_row_get(new, col))
            if old_text != new_text:
                rows.append({
                    "change_type": "changed", "edit_id": edit_id, "field": col, "old_value": old_text, "new_value": new_text,
                    "source_sheet": _safe_text(_row_get(new, "source_sheet", _row_get(old, "source_sheet"))),
                    "item_code": _safe_text(_row_get(new, "item_code", _row_get(old, "item_code"))),
                })
    return pd.DataFrame(rows)


def build_edit_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return a compact summary table for the edited dataset."""
    kpis = calculate_kpis(df)
    validations = validation_report(df)
    return pd.DataFrame([
        {"metric": "BoQ Items", "value": kpis["number_of_boq_items"]},
        {"metric": "Total Project Cost", "value": kpis["total_project_cost"]},
        {"metric": "Material Cost", "value": kpis["total_material_cost"]},
        {"metric": "Labor Cost", "value": kpis["total_labor_cost"]},
        {"metric": "Equipment Cost", "value": kpis["total_equipment_cost"]},
        {"metric": "Transport Cost", "value": kpis["total_transport_cost"]},
        {"metric": "Validation Findings", "value": len(validations)},
    ])


def export_edited_boq_excel(edited_df: pd.DataFrame, change_log: pd.DataFrame | None = None) -> bytes:
    """Build an Excel workbook containing edited BoQ, summary, QA, and changes."""
    output = BytesIO()
    summary = build_edit_summary(edited_df)
    qa = validation_report(edited_df)
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        edited_df.to_excel(writer, sheet_name="Edited_BoQ", index=False)
        summary.to_excel(writer, sheet_name="Summary", index=False)
        qa.to_excel(writer, sheet_name="Validation", index=False)
        if change_log is not None and not change_log.empty:
            change_log.to_excel(writer, sheet_name="Change_Log", index=False)
        workbook = writer.book
        header_fmt = workbook.add_format({"bold": True, "font_color": "white", "bg_color": "#1B365D", "border": 1})
        money_fmt = workbook.add_format({"num_format": "$#,##0.00"})
        num_fmt = workbook.add_format({"num_format": "#,##0.00"})
        for sheet_name, worksheet in writer.sheets.items():
            worksheet.freeze_panes(1, 0)
            worksheet.set_row(0, 22, header_fmt)
            worksheet.set_column(0, 4, 18)
            worksheet.set_column(5, 9, 28)
            worksheet.set_column(10, 22, 16)
            if sheet_name == "Edited_BoQ":
                for idx, col in enumerate(edited_df.columns):
                    if col in {"amount", "rate", "material_cost", "labor_cost", "equipment_cost", "transport_cost", "risk_cost", "direct_cost", "total_cost"}:
                        worksheet.set_column(idx, idx, 16, money_fmt)
                    elif col in {"quantity", "area_m2", "cost_per_m2"}:
                        worksheet.set_column(idx, idx, 14, num_fmt)
    output.seek(0)
    return output.getvalue()
