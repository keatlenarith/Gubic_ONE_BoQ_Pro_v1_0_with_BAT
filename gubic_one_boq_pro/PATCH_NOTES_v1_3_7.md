# Gubic ONE BoQ Pro v1.3.7 - Icon Font and Grid Column Fix

## Icons (arrows)

Root cause: the global Khmer font rule in `inject_css()` matched every element with
a `data-testid` or an `st-` class, including Streamlit's Material Symbol spans.
Those spans render an icon only when their font stays `Material Symbols Rounded`,
so with the override in place the browser printed the ligature name as plain text
(`keyboard_double_arrow_left` on the sidebar collapse button, `upload` in the file
uploader, `keyboard_arrow_right` on expanders).

- Icon elements are now excluded from the Khmer font override and pinned back to
  `Material Symbols Rounded`. Every built-in Streamlit icon renders again.
- Removed the `::before` "▸" arrow that v1.3.6 added to expander headers. That
  workaround produced a second arrow next to the restored native one.

## Grid columns

Root cause: the standard BoQ schema has 34 columns, and the read-only grid asked
for ~4,575px of width inside an ~810px container, so most columns sat off screen.
The sample project leaves 8 of those columns completely empty
(`revision`, `subsection_name`, `equipment_rate/cost`, `transport_rate/cost`,
`risk_cost`, `indirect_cost`).

- Read-only grids now drop columns that are empty for the current selection.
- BoQ Database shows a core column set by default with a "Show all columns"
  toggle. CSV download still contains every column.
- `remarks` uses the medium width category instead of large.
- Removed the CSS rule that tried to set a font on the grid `<canvas>`; canvas
  text is painted by the grid renderer and cannot be styled from CSS.
