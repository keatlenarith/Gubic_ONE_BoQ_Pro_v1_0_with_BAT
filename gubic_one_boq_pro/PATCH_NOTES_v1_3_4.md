# Gubic ONE BoQ Pro v1.3.4 - Compact Auto-Fit Grid Patch

- All dataframe and editable table rendering now uses compact, Streamlit-safe column sizing.
- Replaced risky pixel-width column settings with `small`, `medium`, and `large` Streamlit width categories.
- Shortened headers and compacted long text for read-only grid previews.
- Kept editable text values intact while improving grid fit and fallback stability.
- Removed aggressive column-menu CSS that could make table control text messy.
- Preserved v1.2.5 CSS Display NameError fix and v1.3.1 change-log fix.
