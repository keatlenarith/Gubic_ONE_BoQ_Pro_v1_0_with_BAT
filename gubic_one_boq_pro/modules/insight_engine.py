"""Executive insight and QA scoring helpers for Gubic ONE BoQ Pro."""
from __future__ import annotations

from typing import Any

import pandas as pd

from modules.boq_cleaner import item_rows
from modules.cost_engine import calculate_kpis, package_ranking, top_items, validation_report
from modules.i18n import t
from modules.utils import currency


def _pct(value: float) -> str:
    try:
        return f"{float(value):.1%}"
    except Exception:
        return "0.0%"


def executive_insights(df: pd.DataFrame) -> list[dict[str, str]]:
    """Return short executive observations from the active BoQ dataframe."""
    if df is None or df.empty:
        return []

    kpis = calculate_kpis(df)
    rankings = package_ranking(df)
    cost_total = float(kpis.get("total_project_cost") or 0)
    material = float(kpis.get("total_material_cost") or 0)
    labor = float(kpis.get("total_labor_cost") or 0)
    area = float(kpis.get("area_m2") or 0)
    validations = validation_report(df)

    insights: list[dict[str, str]] = []
    if cost_total:
        insights.append({
            "status": "info",
            "title": t("insight_total_cost_title"),
            "value": currency(cost_total),
            "comment": t("insight_total_cost_comment", items=f"{int(kpis.get('number_of_boq_items') or 0):,}"),
        })
    if area:
        insights.append({
            "status": "info",
            "title": t("insight_cost_m2_title"),
            "value": f"{currency(float(kpis.get('cost_per_m2') or 0))}/m²",
            "comment": t("insight_cost_m2_comment", area=f"{area:,.2f}"),
        })
    if material or labor:
        dominant = t("material") if material >= labor else t("labor")
        dominant_value = max(material, labor)
        insights.append({
            "status": "info",
            "title": t("insight_cost_driver_title"),
            "value": dominant,
            "comment": t("insight_cost_driver_comment", value=currency(dominant_value), pct=_pct(dominant_value / cost_total if cost_total else 0)),
        })
    if not rankings.empty:
        first = rankings.iloc[0]
        insights.append({
            "status": "warning" if float(first.get("percentage") or 0) >= 0.40 else "info",
            "title": t("insight_highest_package_title"),
            "value": str(first.get("source_sheet", "")),
            "comment": t("insight_highest_package_comment", value=currency(float(first.get("total_cost") or 0)), pct=_pct(float(first.get("percentage") or 0))),
        })
    if not validations.empty:
        errors = int((validations["severity"].astype(str).str.lower() == "error").sum()) if "severity" in validations else 0
        warnings = int((validations["severity"].astype(str).str.lower() == "warning").sum()) if "severity" in validations else len(validations)
        insights.append({
            "status": "danger" if errors else "warning",
            "title": t("insight_validation_title"),
            "value": f"{len(validations):,}",
            "comment": t("insight_validation_comment", errors=f"{errors:,}", warnings=f"{warnings:,}"),
        })
    else:
        insights.append({
            "status": "success",
            "title": t("insight_validation_title"),
            "value": t("qa_clean"),
            "comment": t("insight_validation_clean_comment"),
        })
    return insights


def qa_score(df: pd.DataFrame) -> dict[str, Any]:
    """Calculate a simple BoQ quality score from validation density and data completeness."""
    items = item_rows(df, positive_only=False) if df is not None and not df.empty else pd.DataFrame()
    validations = validation_report(df) if df is not None and not df.empty else pd.DataFrame()
    item_count = max(len(items), 1)
    errors = int((validations["severity"].astype(str).str.lower() == "error").sum()) if not validations.empty and "severity" in validations else 0
    warnings = int((validations["severity"].astype(str).str.lower() == "warning").sum()) if not validations.empty and "severity" in validations else 0
    infos = max(len(validations) - errors - warnings, 0)
    penalty = errors * 8 + warnings * 3 + infos * 1
    score = max(0, min(100, round(100 - (penalty / item_count) * 15, 1)))
    if score >= 90:
        status = t("qa_status_good")
    elif score >= 70:
        status = t("qa_status_review")
    else:
        status = t("qa_status_risk")
    return {"score": score, "status": status, "errors": errors, "warnings": warnings, "infos": infos, "findings": len(validations)}


def qa_check_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return grouped validation checks with recommended actions."""
    validations = validation_report(df)
    if validations.empty:
        return pd.DataFrame([{
            "severity": "success",
            "check": t("qa_no_issues"),
            "count": 0,
            "recommended_action": t("qa_no_issues_action"),
        }])
    group = validations.groupby(["severity", "check"], dropna=False).size().reset_index(name="count")
    group["recommended_action"] = group["check"].map(_recommended_action).fillna(t("qa_review_source_rows"))
    return group.sort_values(["severity", "count"], ascending=[True, False])


def _recommended_action(check: str) -> str:
    lookup = {
        "Missing quantity": t("qa_action_missing_quantity"),
        "Missing rate": t("qa_action_missing_rate"),
        "Amount mismatch": t("qa_action_amount_mismatch"),
        "Negative value": t("qa_action_negative"),
        "Duplicate item code": t("qa_action_duplicate"),
        "Empty description": t("qa_action_empty_description"),
        "Very high unit rate": t("qa_action_high_rate"),
        "Very high quantity": t("qa_action_high_quantity"),
    }
    return lookup.get(str(check), t("qa_review_source_rows"))


def risk_watchlist(df: pd.DataFrame, n: int = 25) -> pd.DataFrame:
    """Combine top expensive items with validation findings for a practical review list."""
    top = top_items(df, n).copy()
    if top.empty:
        return top
    vals = validation_report(df)
    if vals.empty:
        top["qa_flags"] = ""
        return top
    flag_cols = ["source_sheet", "item_code", "item_description"]
    vals2 = vals.copy()
    vals2["qa_flags"] = vals2["check"].astype(str) + " (" + vals2["severity"].astype(str) + ")"
    flags = vals2.groupby(flag_cols, dropna=False)["qa_flags"].apply(lambda s: "; ".join(sorted(set(map(str, s))))).reset_index()
    merged = top.merge(flags, on=[c for c in flag_cols if c in top.columns and c in flags.columns], how="left")
    merged["qa_flags"] = merged["qa_flags"].fillna("")
    return merged
