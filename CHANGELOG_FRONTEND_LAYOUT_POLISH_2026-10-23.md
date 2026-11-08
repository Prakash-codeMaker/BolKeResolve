# Frontend layout polish — 23 October 2026

- Fixed case workspace navigation so Prepare & contact / Progress cannot remain active while the tab control is hidden.
- Brought case panel intros onto the same width/alignment grid as the panel cards.
- Balanced the sample scenario/result columns and improved wrapping, stretch behaviour and responsive stacking.
- Removed sticky positioning from the large Guided Chat intro to avoid title/scroll clipping and stabilise reading order.
- Standardised anchor offsets and local tab/disclosure motion; honour reduced-motion preferences.
- Bumped the static shell cache to `bolkeresolve-shell-v16`; API routes remain uncached.
- Added regression checks for tab/menu state, scroll offsets, shared content grid and sample demo alignment.
- Added `docs/FRONTEND_LAYOUT_POLISH_AND_DESIGN_RESEARCH_2026-10-23.md` containing screenshot diagnosis, QA criteria and 35 public design-system references.

Validation: `196 passed, 77 subtests passed`; JavaScript syntax passed. Local Chromium visual navigation was blocked by the environment (`net::ERR_BLOCKED_BY_ADMINISTRATOR`), so browser-level screenshot verification remains outstanding.
