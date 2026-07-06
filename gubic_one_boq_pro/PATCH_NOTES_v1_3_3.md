# Gubic ONE BoQ Pro v1.3.3 - Editable Grid Safe Fit Patch

- Fixed Streamlit data_editor API crash on Editable BoQ Manager by sanitizing grid data before rendering.
- Added safe no-crash fallback if the editable grid cannot render on Streamlit Cloud.
- Reduced BoQ editor header labels and pixel column widths.
- Locked edit_id using the data_editor disabled parameter instead of column-specific settings.
- Reduced grid font size without breaking Streamlit column menus.
- Preserved v1.2.5 CSS display NameError fix and v1.3.1 change-log fix.
