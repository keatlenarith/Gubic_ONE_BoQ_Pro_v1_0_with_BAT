# Gubic ONE BoQ Pro v1.3.2 - Grid Fit and Font Patch

Patched from v1.3.1 Editable ChangeLog Fix.

## Fixes

- Reduced dataframe and data-editor font size for better BoQ grid readability.
- Added compact automatic column configuration for all `st.dataframe` and `st.data_editor` tables.
- Added `fit_dataframe()` and `fit_data_editor()` helper functions.
- Applied the fitted grid helpers across all Streamlit pages.
- Fixed table/menu overlay caused by dataframe overflow styling.
- Preserved v1.2.5 CSS Display NameError fix and v1.3.1 editable change-log fix.

## Notes

The app now uses compact column widths for cost/rate/quantity/unit/code columns and larger width for descriptions/remarks. This is intended to keep BoQ tables readable without column menu text overlap.
