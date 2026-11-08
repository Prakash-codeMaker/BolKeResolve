# Changelog — Live Room Guided Case & Evidence Dossier

## 1 November 2026

- Made `indic-auto` the default Live Room speech language and moved manual language choice into optional settings.
- Added automatic-mode metadata to draft cases and update case language when the first transcript is saved.
- Added provider language-code normalization and a text-inference fallback for model versions that do not return a detected language field.
- Replaced the Live Room paragraph-first guidance presentation with an action-first panel, one-question answer controls, expandable next steps and official-source links.
- Preserved the translated narration as a separate disclosure so it cannot hide the structured plan.
- Added the existing issue-specific evidence checklist to the Live Room with persistent checkboxes and direct upload entry points.
- Replaced the basic evidence list with filterable exhibit cards, media previews, provenance labels and separate original-download links.
- Added saved follow-up date/note, due-state display and mark-complete action to the Live Room.
- Bumped the public shell cache to v29 while keeping all `/api/` data network-only.
- Added an integration test for automatic-mode case creation and transcript-language persistence.

Verification: 289 passed, 117 subtests passed; JavaScript syntax and Python compilation passed.
