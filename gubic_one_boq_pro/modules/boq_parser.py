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
    """Flatten one or two header rows into usable names.

    v1.1 improves merged/grouped header handling by forward-filling group labels
    such as Material/Labor before combining them with Unit Rate/Amount subheaders.
    """
    row1_raw = [clean_text(v) for v in list(raw.iloc[header_row].fillna(""))]
    row2_raw = [clean_text(v) for v in (list(raw.iloc[header_row + 1].fillna("")) if header_row + 1 < len(raw) else [""] * len(row1_raw))]

    row1_grouped: list[str] = []
    last_group = ""
    for txt in row1_raw:
        if txt:
            last_group = txt
            row1_grouped.append(txt)
        else:
            row1_grouped.append(last_group)

    headers: list[str] = []
    subheader_markers = {"unit rate", "amount", "total", "qty", "quantity", "rate"}
    for original_a, grouped_a, b in zip(row1_raw, row1_grouped, row2_raw):
        a = original_a or grouped_a
        b_low = b.lower().strip()
        a_low = a.lower().strip()
        if b and b_low not in {"nan", "none"}:
            if original_a and b_low not in subheader_markers and b_low not in a_low:
                header = f"{original_a} {b}".strip()
            elif grouped_a and b_low in subheader_markers and b_low not in grouped_a.lower():
                header = f"{grouped_a} {b}".strip()
            elif not original_a and grouped_a:
                header = f"{grouped_a} {b}".strip()
            else:
                header = original_a or grouped_a or b
        else:
            header = original_a or grouped_a or b
        headers.append(clean_text(header))
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
        elif ("labor" in context or "labour" in context) and "rate" in h:
            mapping[i] = "labor_rate"
        elif ("labor" in context or "labour" in context) and "amount" in h:
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


def select_candidate_profiles(profiles, parse_mode: str = "auto", selected_sheets: list[str] | None = None):
    """Select workbook sheets for BoQ parsing.

    parse_mode:
    - auto: prefer final/client-facing sheets that contain "sent" when available.
    - all_detected: parse every detected BoQ-like sheet except lookup, area, and summary sheets.
    - selected: parse only sheets chosen by the user.
    """
    selected_set = {s.strip() for s in (selected_sheets or []) if str(s).strip()}
    usable = [p for p in profiles if p.non_empty_cells > 0]
    if parse_mode == "selected" and selected_set:
        return [p for p in usable if p.name in selected_set]

    candidates = [p for p in usable if p.sheet_type == "boq" and p.detected_header_row is not None]
    # Avoid calculation-only sheets unless the user explicitly selects them manually.
    if parse_mode == "all_detected":
        candidates = [p for p in candidates if any(key in p.name.lower() for key in ["boq", "bill"])]
    if parse_mode == "auto":
        boq_named = [p for p in candidates if any(key in p.name.lower() for key in ["boq", "bill"])]
        if boq_named:
            candidates = boq_named
        sent_profiles = [p for p in candidates if "sent" in p.name.lower()]
        if sent_profiles:
            # Prefer final sent/client issue sheets to avoid double-counting working sheets.
            candidates = sent_profiles
    return candidates


def parse_boq_workbook(path: str | Path, project_name: str | None = None, project_id: str | None = None, parse_mode: str = "auto", selected_sheets: list[str] | None = None) -> tuple[pd.DataFrame, list[dict[str, Any]], dict[str, Any]]:
    """Parse every usable BoQ-like sheet in a workbook using the selected v1.1 parser mode."""
    path = Path(path)
    meta = extract_metadata(path)
    if project_name:
        meta["project_name"] = project_name
    meta["project_id"] = project_id or make_project_id(meta.get("project_name"))
    meta["source_file"] = path.name

    profiles = inspect_workbook(path)
    parsed_parts: list[pd.DataFrame] = []
    warnings: list[dict[str, Any]] = []
    candidate_profiles = select_candidate_profiles(profiles, parse_mode=parse_mode, selected_sheets=selected_sheets)
    if not candidate_profiles:
        warnings.append({"sheet": "Workbook", "warning": f"No candidate sheets selected for parse mode: {parse_mode}"})
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
