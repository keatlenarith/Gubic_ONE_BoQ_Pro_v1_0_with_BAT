from pathlib import Path
from modules.excel_importer import workbook_sheet_names, inspect_workbook


def test_sample_workbook_exists_and_inspects():
    sample_dir = Path(__file__).resolve().parents[1] / "data" / "sample"
    samples = list(sample_dir.glob("*.xlsx"))
    assert samples
    names = workbook_sheet_names(samples[0])
    assert len(names) > 0
    profiles = inspect_workbook(samples[0])
    assert len(profiles) == len(names)
