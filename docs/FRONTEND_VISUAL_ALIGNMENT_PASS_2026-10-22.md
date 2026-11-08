# BolKeResolve — Frontend Visual Alignment Pass

Date: 22 October 2026

## Scope

This pass preserves the existing cream / forest-green / mint palette, DM Sans body typography, DM Serif Display headlines, rounded cards, and the voice-first product story. It targets only the three layout problems visible in the supplied screenshots.

## Changes

### Guided chat
- Removed the forced 760px minimum-height behaviour on the main shell so the page can size to its content instead of vertically centering/cropping the experience.
- Normalised the two-column desktop grid and top alignment, while stacking the intro above the chat at tablet/mobile widths.
- Improved chat message width, inner padding, quick-reply touch targets, voice/language controls and the message composer border/focus state.
- Removed the floating decorative note from the chat view to reduce overlap and distraction.

### Sample-case demo
- The selected scenario now automatically loads its first-pass result when the page initialises.
- Selecting the other scenario immediately requests its corresponding result; the demo no longer displays an empty message that asks the user to choose a scenario when one is already selected.
- Added an accessible `aria-busy` state while the result is being computed and clearer loading copy.
- Renamed the action after the first run to `Refresh example result`.
- Tightened the two-column proportions and result-panel alignment, with a clean single-column transition at smaller widths.

### Saved case
- Promoted the main next-action card to sit immediately after the case title/status header, before the case facts, provenance and tools menu.
- The primary card hides when the user switches into Prepare & Contact or Progress, and returns when they switch to Plan & Details, avoiding duplicated actions during secondary tasks.
- Renamed the first destination to `Plan & details` so the label accurately describes the remaining panel content.
- Kept facts, provenance and the additional tool menu compact; the facts grid changes to two columns on mobile.

### Cache
- Bumped the public shell cache name to `bolkeresolve-shell-v14` so the revised public interface is not stuck behind the previous installed-PWA shell.

## Validation

- `python -m pytest -q`: 178 passed, 69 subtests passed.
- `node --check frontend/app.js`: passed.
- `python -m py_compile backend/main.py`: passed.
- Service-worker cache version checked and updated.
- Browser visual smoke test attempted, but Chromium navigation to the local development server was blocked with `ERR_BLOCKED_BY_ADMINISTRATOR` in this execution environment. No screenshot-based browser pass is claimed.

## Not changed

- No product modules or backend contracts were added.
- No payment status is presented as live bank verification.
- The sample demo continues to call the read-only resolution preview endpoint; it does not create a case or submit a complaint.
- The colour palette, logo, photo style and overall visual identity remain unchanged.
