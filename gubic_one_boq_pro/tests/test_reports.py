import pandas as pd
from modules.report_generator import export_detailed_excel


def test_excel_export_smoke(tmp_path, monkeypatch):
    import modules.report_generator as rg
    monkeypatch.setattr(rg, "EXPORT_DIR", tmp_path)
    df = pd.DataFrame([{"row_type": "item", "item_description": "A", "source_sheet": "S1", "quantity": 1, "rate": 10, "amount": 10, "total_cost": 10}])
    path = export_detailed_excel(df, "Test")
    assert path.exists()
