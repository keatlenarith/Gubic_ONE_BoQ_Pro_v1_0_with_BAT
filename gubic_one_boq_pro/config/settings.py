"""Application settings for Gubic ONE BoQ Pro."""
from pathlib import Path

APP_NAME = "Gubic ONE BoQ Pro"
APP_VERSION = "1.1.5"
BRAND_COLOR = "#1B365D"
ACCENT_COLOR = "#E8EEF5"
LIGHT_BG = "#F7F9FC"
TEXT_COLOR = "#172033"
CURRENCY = "USD"
CURRENCY_SYMBOL = "$"
FONT_FAMILY = "'Noto Sans Khmer', 'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, sans-serif"

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
EXPORT_DIR = DATA_DIR / "exports"
SAMPLE_DIR = DATA_DIR / "sample"
DATABASE_PATH = BASE_DIR / "database" / "boq_database.sqlite"
LOGO_PATH = BASE_DIR / "assets" / "logo" / "gubic_logo.png"
FAVICON_PATH = BASE_DIR / "assets" / "logo" / "gubic_favicon.png"

STANDARD_COLUMNS = [
    "project_id", "project_name", "source_file", "source_sheet", "revision",
    "package_name", "section_name", "subsection_name", "item_code",
    "item_description", "brand", "unit", "quantity", "rate", "amount",
    "material_rate", "material_cost", "labor_rate", "labor_cost",
    "equipment_rate", "equipment_cost", "transport_rate", "transport_cost",
    "risk_cost", "direct_cost", "indirect_cost", "total_cost", "currency",
    "area_m2", "cost_per_m2", "remarks", "row_type", "created_at", "updated_at"
]

BOQ_KEYWORDS = [
    "item", "description", "unit", "quantity", "qty", "rate", "amount",
    "total", "material", "labor", "labour", "equipment", "transport", "risk", "remarks"
]

SUMMARY_SHEET_KEYWORDS = ["sum", "summary"]
RAW_MATERIAL_SHEET_KEYWORDS = ["rawdata", "material", "mat-list"]
