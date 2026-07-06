"""BoQ workbook parser that converts varied Excel layouts into a standard dataframe."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from config.settings import CURRENCY
from modules.boq_cleaner import finalize_standard_dataframe
from modules.excel_importer import detect_header_row, extract_metadata, inspect_workbook, read_sheet_raw
from modules.utils import clean_text, make_project_id, normalize_header


def _flatten_header(raw: pd.DataFrame, header_row: int) -> list[str]:
    """Flatten one or two header rows into usable names."""
    row1 = list(raw.iloc[header_row].fillna(""))
    row2 = list(raw.iloc[header_row + 1].fillna("")) if header_row + 1 < len(raw) else [""] * len(row1)
    headers: list[str] = []
    for a, b in zip(row1, row2):
        a_text = clean_text(a)
        b_text = clean_text(b)
        if b_text and b_text.lower() not in {"unit rate", "amount"}:
            headers.append(f"{a_text} {b_text}".strip())
        elif a_text and b_text:
            headers.append(f"{a_text} {b_text}".strip())
        else:
            headers.append(a_text or b_text)
    return headers


def _phoenix_column_map(headers: list[str]) -> dict[int, str]:
    """Prefer exact positional mapping for the uploaded Phoenix/Gubic 13-column BoQ sheets."""
    normalized = [normalize_header(h) for h in headers]
    joined = " ".join(normalized[:13])
    if "item" in joined and "description" in joined and "quantity" in joined and "material" in joined and "labor" in joined:
        return {
            0: "item_code",
            1: "item_description",
            2: "brand",
            3: "unit",
            4: "quantity",
            5: "rate",
            6: "amount",
            7: "material_rate",
            8: "material_cost",
            9: "labor_rate",
            10: "labor_cost",
            11: "total_cost",
            12: "remarks",
        }
    return {}


def _generic_column_map(headers: list[str]) -> dict[int, str]:
    mapping: dict[int, str] = {}
    used_total = False
    used_rate = False
    for i, header in enumerate(headers):
        h = normalize_header(header)
        prev = normalize_header(headers[i - 1]) if i > 0 else ""
        # use context from prior grouped header cell when merged values are not repeated
        context = " ".join([prev, h]).strip()
        if not h:
            continue
        if h in {"item", "no", "no_", "item_no"} or h.startswith("item"):
            mapping.setdefault(i, "item_code")
        elif "description" in h or "descirption" in h or h in {"desc", "work_description"}:
            mapping[i] = "item_description"
        elif h == "brand" or "brand" in h:
            mapping[i] = "brand"
        elif h == "unit" or h.endswith("_unit"):
            mapping[i] = "unit"
        elif "quantity" in h or h == "qty":
            mapping[i] = "quantity"
        elif "material" in context and "rate" in h:
            mapping[i] = "material_rate"
        elif "material" in context and "amount" in h:
            mapping[i] = "material_cost"
        elif "labor" in context and "rate" in h:
            mapping[i] = "labor_rate"
        elif "labor" in context and "amount" in h:
            mapping[i] = "labor_cost"
        elif "equipment" in context and "rate" in h:
            mapping[i] = "equipment_rate"
        elif "equipment" in context and "amount" in h:
            mapping[i] = "equipment_cost"
        elif "transport" in context and "amount" in h:
            mapping[i] = "transport_cost"
        elif "risk" in h or "contingency" in h:
            mapping[i] = "risk_cost"
        elif "rate" in h and not used_rate:
            mapping[i] = "rate"
            used_rate = True
        elif ("amount" in h or "total" in h or "budget" in h) and not used_total:
            mapping[i] = "amount"
            used_total = True
        elif ("amount" in h or "total" in h) and used_total:
            mapping[i] = "total_cost"
        elif "remark" in h:
            mapping[i] = "remarks"
        elif "code" in h and "item_code" not in mapping.values():
            mapping[i] = "item_code"
    return mapping


def _parse_sheet_dataframe(raw: pd.DataFrame, header_row: int, source_sheet: str) -> pd.DataFrame:
    headers = _flatten_header(raw, header_row)
    col_map = _phoenix_column_map(headers) or _generic_column_map(headers)
    if not col_map:
        return pd.DataFrame()

    skip = header_row + 1
    # skip the second header row when it contains subheaders like Unit Rate / Amount.
    if header_row + 1 < len(raw):
        subheader_tokens = " ".join(clean_text(v).lower() for v in list(raw.iloc[header_row + 1]) if clean_text(v))
        if "unit rate" in subheader_tokens or "amount" in subheader_tokens:
            skip = header_row + 2

    data = raw.iloc[skip:].copy()
    records = []
    for _, row in data.iterrows():
        rec: dict[str, Any] = {"source_sheet": source_sheet, "currency": CURRENCY}
        for idx, standard_name in col_map.items():
            if idx < len(row):
                rec[standard_name] = row.iloc[idx]
        if any(clean_text(v) for v in rec.values()):
            records.append(rec)
    return pd.DataFrame.from_records(records)


def parse_boq_workbook(path: str | Path, project_name: str | None = None, project_id: str | None = None) -> tuple[pd.DataFrame, list[dict[str, Any]], dict[str, Any]]:
    """Parse every usable BoQ-like sheet in a workbook."""
    path = Path(path)
    meta = extract_metadata(path)
    if project_name:
        meta["project_name"] = project_name
    meta["project_id"] = project_id or make_project_id(meta.get("project_name"))
    meta["source_file"] = path.name

    profiles = inspect_workbook(path)
    parsed_parts: list[pd.DataFrame] = []
    warnings: list[dict[str, Any]] = []
    candidate_profiles = [p for p in profiles if p.non_empty_cells > 0 and p.sheet_type not in {"lookup", "area", "summary"}]
    sent_profiles = [p for p in candidate_profiles if "sent" in p.name.lower()]
    if sent_profiles:
        # Many construction workbooks keep calculation sheets and final "Sent" BoQ sheets side by side.
        # Prefer final sent sheets to avoid double-counting the same packages.
        candidate_profiles = sent_profiles
    for profile in candidate_profiles:
        try:
            raw = read_sheet_raw(path, profile.name)
            header = profile.detected_header_row
            if header is None:
                rows = raw.head(80).values.tolist()
                header = detect_header_row(rows)
            if header is None:
                warnings.append({"sheet": profile.name, "warning": "No BoQ table header detected"})
                continue
            parsed = _parse_sheet_dataframe(raw, header, profile.name)
            if parsed.empty:
                warnings.append({"sheet": profile.name, "warning": "Header detected, but no usable columns mapped"})
                continue
            parsed["source_file"] = path.name
            parsed["project_id"] = meta["project_id"]
            parsed["project_name"] = meta["project_name"]
            parsed["package_name"] = profile.name
            parsed["area_m2"] = meta.get("area_m2")
            parsed_parts.append(parsed)
        except Exception as exc:  # defensive UI-friendly handling
            warnings.append({"sheet": profile.name, "warning": str(exc)})

    if parsed_parts:
        combined = pd.concat(parsed_parts, ignore_index=True)
    else:
        combined = pd.DataFrame()
    standardized = finalize_standard_dataframe(combined, meta) if not combined.empty else pd.DataFrame()
    return standardized, warnings, meta


def parse_material_lookup(path: str | Path) -> pd.DataFrame:
    """Parse RawData/material lookup sheets when present."""
    path = Path(path)
    profiles = inspect_workbook(path)
    frames = []
    for profile in profiles:
        lower = profile.name.lower()
        if not any(k in lower for k in ["rawdata", "mat-list", "material"]):
            continue
        try:
            raw = read_sheet_raw(path, profile.name)
            header = profile.detected_header_row
            if header is None:
                header = detect_header_row(raw.head(30).values.tolist())
            if header is None:
                # common RawData header at row 2 (zero-based 1)
                header = 1 if len(raw) > 2 else 0
            headers = [normalize_header(v) for v in list(raw.iloc[header].fillna(""))]
            data = raw.iloc[header + 1:].copy()
            data.columns = [h or f"col_{i+1}" for i, h in enumerate(headers)]
            rename = {}
            for c in data.columns:
                if c in {"no", "item", "item_no"}:
                    rename[c] = "no"
                elif "code" in c:
                    rename[c] = "code"
                elif "description" in c or "desc" in c:
                    rename[c] = "description"
                elif c == "unit":
                    rename[c] = "unit"
                elif "rate" in c or "price" in c:
                    rename[c] = "unit_rate"
                elif "remark" in c:
                    rename[c] = "remarks"
            data = data.rename(columns=rename)
            keep = [c for c in ["no", "code", "description", "unit", "unit_rate", "remarks"] if c in data.columns]
            if keep:
                out = data[keep].copy()
                out["source_sheet"] = profile.name
                frames.append(out)
        except Exception:
            continue
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
