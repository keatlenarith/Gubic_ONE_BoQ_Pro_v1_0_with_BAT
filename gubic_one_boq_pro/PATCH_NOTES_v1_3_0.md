# Gubic ONE BoQ Pro v1.3.0 — Editable BoQ Manager

Base version: v1.2.5 CSS Display NameError Fix.

## Added

- New **Editable BoQ Manager** page.
- Editable BoQ table using Streamlit `st.data_editor`.
- Add, delete, and edit visible BoQ item rows.
- Editable fields include package/sheet, section, subsection, item code, description, brand, unit, quantity, rate, amount, material/labor/equipment/transport/risk cost, and remarks.
- Optional automatic recalculation: `Amount = Quantity × Rate`.
- Automatic recalculation of direct cost and total cost.
- Save edited dataset to active dashboard session.
- Save edited dataset to local SQLite database for local desktop use.
- Download edited BoQ Excel with summary, validation, and change log sheets.
- Change log for added/deleted/changed rows.
- Validation tab for the edited workspace.
- KH/EN labels for the new editable workflow.

## Preserved from v1.2.5

- CSS display NameError fix.
- Escaped CSS braces in Python f-strings.
- Emoji sidebar icons.
- KH/EN sidebar navigation.
- Noto Sans Khmer styling.
- Upload button overlap fix.
- Sidebar/logo/insight panel fixes.

## Cloud note

Streamlit Community Cloud storage is not intended for permanent multi-user database editing. For production shared editing, connect this page to Supabase/PostgreSQL in a future version.
