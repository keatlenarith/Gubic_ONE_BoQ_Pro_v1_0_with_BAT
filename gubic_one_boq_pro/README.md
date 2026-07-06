# Gubic ONE BoQ Pro v1.2.4

**Gubic ONE BoQ Pro** is a professional Bill of Quantities dashboard, construction cost intelligence, validation, and report export system. It imports complex Excel-based BoQ workbooks, detects usable sheets, cleans and standardizes item rows, calculates cost breakdowns, and creates executive dashboards for project owners, consultants, contractors, and quantity surveyors.


## v1.2.4 Sidebar Menu Icon Patch

This patch restores visible icons for every custom sidebar menu item using Streamlit Material Symbols with emoji fallbacks. It keeps the translated KH/EN menu labels while adding clear visual navigation marks for Dashboard, Import BoQ, Database, Cost Breakdown, QA Control, Parser Lab, and other pages.


## v1.2.4 Khmer Text Layout Patch

The v1.2.4 patch improves Khmer font rendering and prevents text overlap in headers, file uploader controls, radio buttons, expanders, tables, and buttons.


- App interface font changed to **Noto Sans Khmer** for clearer Khmer/English display.
- CSS loads Noto Sans Khmer from Google Fonts when online and falls back to Segoe UI/system fonts if unavailable.
- Plotly dashboard charts also use the same Noto Sans Khmer font stack.
- Word report export is set to Noto Sans Khmer where the font is available on the user computer.

## v1.1 Update Summary

Version **1.1** focuses on smarter **scratching and parsing** of complex BoQ workbooks:

- New **Parser Lab** page for testing sheet detection and column mapping before import
- New parser modes:
  - **Auto**: prefer final/client-facing `Sent` BoQ sheets to avoid double-counting
  - **All detected**: parse all detected BoQ-like sheets
  - **Manual**: select exact sheets to parse
- Improved merged/grouped Excel header parsing
- Better Material / Labor / Labour / Amount / Unit Rate column mapping
- Parser diagnostics table showing header row, mapped columns, mapping summary, and usable row preview
- Import QA tabs for row types, construction keyword groups, validation findings, and parser warnings
- Updated branding to **v1.1** with Gubic logo retained
- Added `update_github.bat` helper for pushing future edits to GitHub

## Key Features

- Excel `.xlsx` BoQ import
- Automatic workbook and sheet inspection
- Flexible BoQ table detection
- Item-level data cleaning and standardization
- Section/package context detection
- USD cost calculations
- Material, labor, equipment, transport, and risk cost analysis
- Cost per square meter calculation
- Top expensive item ranking
- Package/sheet cost ranking
- Pareto 80/20 chart
- Searchable BoQ database
- Validation report for missing quantity/rate, amount mismatch, duplicate codes, negative values, and outliers
- Basic progress payment module
- Excel, Word, and PDF export
- SQLite local project database
- Predefined AI-ready query buttons

## Folder Structure

```text
gubic_one_boq_pro/
├── app.py
├── requirements.txt
├── README.md
├── install_requirements.bat
├── run_application.bat
├── launch_app.bat
├── update_github.bat
├── config/
│   └── settings.py
├── data/
│   ├── sample/
│   ├── uploads/
│   └── exports/
├── database/
│   ├── boq_database.sqlite
│   └── db_manager.py
├── modules/
│   ├── excel_importer.py
│   ├── boq_cleaner.py
│   ├── boq_parser.py
│   ├── parser_diagnostics.py
│   ├── cost_engine.py
│   ├── material_engine.py
│   ├── labor_engine.py
│   ├── equipment_engine.py
│   ├── dashboard_engine.py
│   ├── report_generator.py
│   ├── ui_helpers.py
│   └── utils.py
├── pages/
│   ├── 01_Dashboard.py
│   ├── 02_Project_Setup.py
│   ├── 03_Import_BoQ.py
│   ├── 04_BoQ_Database.py
│   ├── 05_Cost_Breakdown.py
│   ├── 06_Material_Analysis.py
│   ├── 07_Labor_Analysis.py
│   ├── 08_Equipment_Analysis.py
│   ├── 09_Progress_Payment.py
│   ├── 10_Reports.py
│   ├── 11_Settings.py
│   └── 12_Parser_Lab.py
├── assets/
│   ├── logo/
│   └── styles/
└── tests/
```

## Windows One-Click Setup

For Windows users, the easiest setup is:

1. Extract the ZIP file.
2. Open the `gubic_one_boq_pro` folder.
3. Double-click `install_requirements.bat`.
4. After installation finishes, double-click `run_application.bat`.
5. The app opens at `http://localhost:8501`.

`install_requirements.bat` creates a local `.venv` environment and installs all required Python packages.

`run_application.bat` starts the Streamlit dashboard using the local `.venv` when available.

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the App

```bash
streamlit run app.py
```

Or on Windows, double-click:

```text
launch_app.bat
```

Streamlit normally opens the browser automatically. If it does not, copy the local URL shown in the terminal into your browser.

## How to Import an Excel BoQ in v1.1

1. Open the app.
2. Go to **Parser Lab** first if you want to test sheet detection and header mapping.
3. Go to **Import BoQ**.
4. Choose **Upload Excel file** or **Use bundled sample workbook**.
5. Review the workbook sheet inspection table.
6. Choose a parser mode:
   - **Auto** for normal use and final Sent sheets
   - **All detected** when you want to include every detected BoQ-like sheet
   - **Manual** when you want to control exact sheets
7. Click **Import and standardize workbook**.
8. Review KPI summary, row types, keyword QA, validation findings, and warnings.

## How to View Dashboard

After import, go to:

- **Dashboard** for executive KPIs and charts
- **Cost Breakdown** for package and section ranking
- **Material Analysis** for material-heavy items
- **Labor Analysis** for labor-heavy items
- **Equipment Analysis** for equipment or plant-heavy items
- **BoQ Database** for filtering and searching standardized BoQ rows

## How to Export Reports

Go to **Reports** and select:

- **Generate Detailed BoQ Excel**
- **Generate Word Summary**
- **Generate PDF Summary**

The exports are saved to `data/exports/` and can also be downloaded from the Streamlit page.

## Standard BoQ Data Model

The parser standardizes imported BoQ rows into these fields:

```text
project_id, project_name, source_file, source_sheet, revision, package_name,
section_name, subsection_name, item_code, item_description, brand, unit,
quantity, rate, amount, material_rate, material_cost, labor_rate, labor_cost,
equipment_rate, equipment_cost, transport_rate, transport_cost, risk_cost,
direct_cost, indirect_cost, total_cost, currency, area_m2, cost_per_m2,
remarks, row_type, created_at, updated_at
```

## Validation Checks

The validation engine checks:

- Missing quantity
- Missing rate
- Amount mismatch where amount does not equal quantity × rate
- Negative values
- Duplicate item codes per sheet
- Empty descriptions
- Extremely high unit rates
- Extremely high quantities

## Tested Reference Workbook

The app includes the uploaded Phoenix Club mock-up BoQ workbook in `data/sample/` for local testing and demonstration.

Smoke test on the bundled sample using **Auto** mode:

```text
Standardized rows: 1,999
BoQ item rows: 1,138
Detected final BoQ sheets: 3
Total project cost: USD 4,428,368.40
Detected area: 7,073.11 m²
Cost per m²: USD 626.09/m²
```

## GitHub and Streamlit Cloud

For Streamlit Community Cloud, use:

```text
Repository: your-username/your-repository
Branch: main
Main file path: gubic_one_boq_pro/app.py
```

After editing the app locally, push updates:

```bash
git add .
git commit -m "Update Gubic ONE BoQ Pro"
git push
```

Or double-click `update_github.bat` from the Git repository root if you copied it there.

## Future Roadmap

Recommended v1.2+ improvements:

1. Variation order module
2. Interim payment certificate workflow
3. Multi-currency and exchange-rate settings
4. Tax/VAT/withholding layer
5. User-defined BoQ coding standards
6. Construction procurement list generator
7. Client/consultant/contractor approval workflow
8. FastAPI backend and React/Electron desktop interface
9. AI assistant query layer over the standardized BoQ database
10. Cloud project database with role-based access control

## Notes

- Formula-heavy workbooks may contain broken Excel references such as `#REF!`. The parser treats these as non-numeric and continues instead of crashing.
- Sheets without recognizable BoQ headers are skipped and reported as warnings.
- Lookup/material sheets are parsed separately so they do not pollute item-level calculations.
- Use **Auto** parser mode for client-facing final BoQ issue workbooks to avoid double-counting working/calculation sheets.

## Branding

The app includes the Gubic logo in `assets/logo/gubic_logo.png` and uses it in the sidebar, page headers, and browser tab icon.


## v1.2.4 KH/EN Language Setting

Gubic ONE BoQ Pro now includes a sidebar language selector for:

- **EN** — English interface
- **KH** — Khmer interface

The language selector changes the application interface labels, KPI captions, page headings, chart titles, filters, parser messages, and settings text. Imported BoQ descriptions and Excel workbook data are kept exactly as uploaded and are not translated automatically.

To update Streamlit Cloud after changing files locally:

```bash
git add .
git commit -m "Add KH EN language setting"
git push
```

Streamlit Cloud will redeploy from the GitHub `main` branch automatically.


## v1.2.4 Additions

- Executive insight cards on the main dashboard.
- New QA Control page for validation score, error/warning summary, and risk watchlist.
- Downloadable QA summary, validation findings, and risk watchlist CSV files.
- Better Streamlit Cloud update helper: `update_github_force.bat`.
- Retains KH/EN interface, Gubic logo, Noto Sans Khmer font, Parser Lab, and BoQ export tools.
