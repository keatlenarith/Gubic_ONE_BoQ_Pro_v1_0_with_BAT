import pandas as pd
from modules.cost_engine import calculate_kpis, cost_breakdown, top_items


def test_cost_engine_basic():
    df = pd.DataFrame([
        {"row_type": "item", "item_description": "A", "source_sheet": "S1", "quantity": 2, "rate": 10, "amount": 20, "material_cost": 15, "labor_cost": 5, "total_cost": 20},
        {"row_type": "item", "item_description": "B", "source_sheet": "S2", "quantity": 1, "rate": 30, "amount": 30, "material_cost": 10, "labor_cost": 20, "total_cost": 30},
    ])
    k = calculate_kpis(df)
    assert k["total_project_cost"] == 50
    assert k["total_material_cost"] == 25
    assert k["total_labor_cost"] == 25
    assert len(cost_breakdown(df)) >= 2
    assert top_items(df, 1).iloc[0]["item_description"] == "B"
