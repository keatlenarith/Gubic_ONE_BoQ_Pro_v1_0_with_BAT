"""Parser diagnostics and sheet mapping helpers for Gubic ONE BoQ Pro v1.1."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from modules.excel_importer import inspect_workbook, read_sheet_raw, detect_header_row
from modules.boq_parser import _flatten_header, _generic_column_map, _phoenix_column_map, _parse_sheet_dataframe
from modules.boq_cleaner import finalize_standard_dataframe
from modules.utils import clean_text


def analyze_sheet_mapping(path: str | Path, sheet_name: str) -> dict[str, Any]:
    """Return a compact diagnostic profile for one sheet before full import."""
    profiles = {p.name: p for p in inspect_workbook(path)}
    profile = profiles.get(sheet_name)
    raw = read_sheet_raw(path, sheet_name)
    header_row = profile.detected_header_row if profile else None
    if header_row is None:
        header_row = detect_header_row(raw.head(80).values.tolist())

    result: dict[str, Any] = {
        "sheet": sheet_name,
        "sheet_type": profile.sheet_type if profile else "unknown",
        "rows": int(raw.shape[0]),
        "columns": int(raw.shape[1]),
        "non_empty_cells": int(profile.non_empty_cells) if profile else int(raw.notna().sum().sum()),
        "detected_header_row_excel": int(header_row + 1) if header_row is not None else None,
        "mapped_columns": 0,
        "mapping": {},
        "usable_rows_preview": 0,
        "warnings": [],
    }

    if header_row is None:
        result["warnings"].append("No confident BoQ header row detected.")
        return result

    headers = _flatten_header(raw, header_row)
    mapping = _phoenix_column_map(headers) or _generic_column_map(headers)
    result["mapped_columns"] = len(mapping)
    result["mapping"] = {int(k): v for k, v in mapping.items()}
    if len(mapping) < 4:
        result["warnings"].append("Few columns were mapped; this sheet may require manual review.")

    try:
        parsed = _parse_sheet_dataframe(raw, header_row, sheet_name)
        result["usable_rows_preview"] = int(len(parsed))
    except Exception as exc:  # diagnostic only
        result["warnings"].append(f"Preview parse error: {exc}")
    return result


def workbook_diagnostics(path: str | Path, selected_sheets: list[str] | None = None) -> pd.DataFrame:
    """Analyze selected or all workbook sheets for the Parser Lab UI."""
    profiles = inspect_workbook(path)
    names = selected_sheets or [p.name for p in profiles if p.non_empty_cells > 0]
    rows: list[dict[str, Any]] = []
    for name in names:
        try:
            d = analyze_sheet_mapping(path, name)
            rows.append({
                "sheet": d["sheet"],
                "sheet_type": d["sheet_type"],
                "rows": d["rows"],
                "columns": d["columns"],
                "non_empty_cells": d["non_empty_cells"],
                "detected_header_row_excel": d["detected_header_row_excel"],
                "mapped_columns": d["mapped_columns"],
                "usable_rows_preview": d["usable_rows_preview"],
                "mapping_summary": ", ".join(sorted(set(d["mapping"].values()))),
                "warnings": "; ".join(d["warnings"]),
            })
        except Exception as exc:
            rows.append({"sheet": name, "warnings": str(exc)})
    return pd.DataFrame(rows)


def row_type_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize parsed rows by source sheet and row type."""
    if df is None or df.empty or "row_type" not in df.columns:
        return pd.DataFrame(columns=["source_sheet", "row_type", "rows", "total_cost"])
    out = (
        df.groupby(["source_sheet", "row_type"], dropna=False)
        .agg(rows=("item_description", "count"), total_cost=("total_cost", "sum"))
        .reset_index()
        .sort_values(["source_sheet", "row_type"])
    )
    return out


def description_keyword_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Quick construction keyword summary useful for parser QA and early cost review."""
    if df is None or df.empty or "item_description" not in df.columns:
        return pd.DataFrame()
    items = df[df.get("row_type", "").eq("item")].copy() if "row_type" in df.columns else df.copy()
    keywords = {
        "Concrete": r"concrete|cement|mortar",
        "Steel / Rebar": r"steel|rebar|reinforcement|metal",
        "Brick / Block": r"brick|block|masonry",
        "MEP": r"electrical|plumbing|hvac|pipe|cable|light|pump",
        "Finishes": r"paint|tile|ceiling|floor|finish|plaster",
        "Earthwork": r"excavat|backfill|soil|sand|compaction",
    }
    rows = []
    for label, pattern in keywords.items():
        mask = items["item_description"].astype(str).str.contains(pattern, case=False, na=False, regex=True)
        sub = items.loc[mask]
        rows.append({"keyword_group": label, "items": int(len(sub)), "total_cost": float(sub.get("total_cost", pd.Series(dtype=float)).sum())})
    return pd.DataFrame(rows).sort_values("total_cost", ascending=False)
