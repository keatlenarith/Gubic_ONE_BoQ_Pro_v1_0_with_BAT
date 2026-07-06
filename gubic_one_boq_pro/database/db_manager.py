"""SQLite storage for imported BoQ projects."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from config.settings import DATABASE_PATH, STANDARD_COLUMNS


def connect(db_path: str | Path = DATABASE_PATH) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | Path = DATABASE_PATH) -> None:
    conn = connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            project_id TEXT PRIMARY KEY,
            project_name TEXT,
            source_file TEXT,
            location TEXT,
            owner TEXT,
            revision TEXT,
            area_m2 REAL,
            imported_at TEXT
        )
        """
    )
    column_defs = ",\n".join([f"{col} TEXT" for col in STANDARD_COLUMNS])
    conn.execute(f"CREATE TABLE IF NOT EXISTS boq_items ({column_defs})")
    conn.commit()
    conn.close()


def save_project(meta: dict[str, Any], df: pd.DataFrame, db_path: str | Path = DATABASE_PATH) -> None:
    init_db(db_path)
    conn = connect(db_path)
    conn.execute(
        """
        INSERT OR REPLACE INTO projects (project_id, project_name, source_file, location, owner, revision, area_m2, imported_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (
            meta.get("project_id"), meta.get("project_name"), meta.get("source_file"), meta.get("location"),
            meta.get("owner"), meta.get("revision"), meta.get("area_m2"),
        ),
    )
    if not df.empty:
        df = df.copy()
        for col in STANDARD_COLUMNS:
            if col not in df.columns:
                df[col] = None
        conn.execute("DELETE FROM boq_items WHERE project_id = ?", (meta.get("project_id"),))
        df[STANDARD_COLUMNS].to_sql("boq_items", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()


def list_projects(db_path: str | Path = DATABASE_PATH) -> pd.DataFrame:
    init_db(db_path)
    conn = connect(db_path)
    out = pd.read_sql_query("SELECT * FROM projects ORDER BY imported_at DESC", conn)
    conn.close()
    return out


def load_project(project_id: str, db_path: str | Path = DATABASE_PATH) -> pd.DataFrame:
    init_db(db_path)
    conn = connect(db_path)
    df = pd.read_sql_query("SELECT * FROM boq_items WHERE project_id = ?", conn, params=(project_id,))
    conn.close()
    numeric_cols = [
        "quantity", "rate", "amount", "material_rate", "material_cost", "labor_rate", "labor_cost",
        "equipment_rate", "equipment_cost", "transport_rate", "transport_cost", "risk_cost", "direct_cost",
        "indirect_cost", "total_cost", "area_m2", "cost_per_m2"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_latest_project(db_path: str | Path = DATABASE_PATH) -> tuple[dict[str, Any] | None, pd.DataFrame]:
    projects = list_projects(db_path)
    if projects.empty:
        return None, pd.DataFrame()
    meta = projects.iloc[0].to_dict()
    return meta, load_project(meta["project_id"], db_path)
