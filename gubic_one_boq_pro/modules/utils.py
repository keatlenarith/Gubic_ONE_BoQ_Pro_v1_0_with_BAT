"""Shared utility functions."""
from __future__ import annotations

import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

CURRENCY_FMT = "${:,.2f}"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def make_project_id(project_name: str | None = None) -> str:
    base = re.sub(r"[^A-Za-z0-9]+", "-", (project_name or "project").strip()).strip("-").lower()
    return f"{base or 'project'}-{uuid.uuid4().hex[:8]}"


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    text = str(value).replace("\xa0", " ").replace("\u200b", " ").strip()
    if text.lower() in {"nan", "none", "nat"}:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_header(value: Any) -> str:
    text = clean_text(value).lower()
    text = text.replace("\n", " ")
    text = re.sub(r"\[[^\]]*\]|\([^\)]*\)", "", text)
    text = text.replace("labour", "labor")
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text


def to_number(value: Any) -> float | None:
    """Convert Excel-like numbers, currency strings, and percentages to floats."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        if pd.isna(value):
            return None
        return float(value)
    text = clean_text(value)
    if not text or text.upper() in {"N/A", "NA", "-", "—", "#REF!", "#VALUE!", "#DIV/0!"}:
        return None
    percent = text.endswith("%")
    text = text.replace("$", "").replace(",", "").replace("%", "")
    text = re.sub(r"[^0-9.\-]", "", text)
    if text in {"", ".", "-"}:
        return None
    try:
        number = float(text)
        return number / 100 if percent else number
    except ValueError:
        return None


def is_numeric_like(value: Any) -> bool:
    return to_number(value) is not None


def currency(value: Any) -> str:
    number = to_number(value)
    return "-" if number is None else CURRENCY_FMT.format(number)


def pct(value: Any) -> str:
    number = to_number(value)
    return "-" if number is None else f"{number:.1%}"


def safe_divide(numerator: float | int | None, denominator: float | int | None) -> float:
    try:
        if denominator in (0, None) or pd.isna(denominator):
            return 0.0
        if numerator is None or pd.isna(numerator):
            return 0.0
        return float(numerator) / float(denominator)
    except Exception:
        return 0.0


def ensure_columns(df: pd.DataFrame, columns: Iterable[str], default: Any = None) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        if col not in out.columns:
            out[col] = default
    return out


def write_uploaded_file(uploaded_file: Any, upload_dir: Path) -> Path:
    upload_dir.mkdir(parents=True, exist_ok=True)
    target = upload_dir / uploaded_file.name
    suffix = target.suffix
    stem = target.stem
    i = 1
    while target.exists():
        target = upload_dir / f"{stem}_{i}{suffix}"
        i += 1
    with target.open("wb") as f:
        f.write(uploaded_file.getbuffer())
    return target
