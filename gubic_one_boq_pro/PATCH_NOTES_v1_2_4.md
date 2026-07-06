# Gubic ONE BoQ Pro v1.2.4 — Sidebar Icon Rendering Patch

## Fixed

- Removed Streamlit Material Symbol `icon=` usage from custom sidebar page links.
- Replaced broken material text such as `home`, `dashboard`, `upload_file`, etc. with stable emoji icons.
- Prevented raw Material Symbol names from displaying if the cloud build does not load the icon font.
- Improved sidebar link line-height and wrapping for Khmer and English labels.
- Updated version to v1.2.4.

## Why

Some Streamlit Community Cloud builds render Material Symbol icon names as plain text when the Material Symbols font is unavailable. This caused menu labels to overlap in the left panel.
