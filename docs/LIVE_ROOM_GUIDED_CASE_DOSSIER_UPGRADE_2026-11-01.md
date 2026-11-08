# Live Resolution Room — Guided Case & Evidence Dossier Upgrade

**Date:** 1 November 2026  
**Scope:** Existing BolKeResolve project; incremental changes to the Live Resolution Room.

## What changed

### 1. Automatic speech language is the default

- The first-run control is now **Automatic language detection**. The language picker is tucked into an optional “Change language” disclosure.
- The browser sends `language_code=indic-auto` to the existing Gnani WebSocket proxy unless the user explicitly chooses a language.
- A draft created in automatic mode is stored with a neutral `en-IN` placeholder plus `speech_language_mode=auto` metadata. It is not labelled as Hindi before a transcript exists.
- The first confirmed transcript updates the case language and adds the actual/inferred language to the timeline event.
- Provider language codes are normalized to the language set supported by the case backend. Unsupported provider values fall back to transcript-based inference.
- The existing explicit “Finish speaking” and recorded-voice-note fallback controls are retained.

**Provider/model detail:** Gnani documents that Prisma v2.5 accepts `indic-auto`, but only Prisma v3.0 returns a separate `detected_language_code` field. The implementation therefore uses the provider code when returned and a text/script heuristic otherwise. The default remains `prisma-v2.5` to avoid assuming that the account has v3 access. To use provider-reported language metadata, set `GNANI_STT_MODEL=prisma-v3.0` only after Gnani confirms access for the configured key. See [Gnani realtime STT documentation](https://docs.gnani.ai/api/STT/stt-websocket).

### 2. Guidance is now action-first and structured

The Live Room now displays data from the existing deterministic resolution plan and action pack:

- The immediate next action is highlighted with its detail and reason.
- Remaining steps are available in an expandable list.
- A single decision-changing question is displayed with answer buttons when the resolution engine supplies one. Answers update the same saved case and recalculate the plan.
- Official sources are shown as direct links.
- The full translated narration is kept separately in a disclosure; it no longer hides the action steps, question or checklist.

The app continues to make clear that recommendations are based on user-reported facts and do not query a bank, payment app or merchant account.

### 3. Case-specific evidence checklist

The Live Room now surfaces `action_pack.evidence_checklist`, which already varies by issue type (for example, refund-not-received versus failed-UPI evidence). Users can:

- See which files may be needed and whether each item is required or helpful.
- Mark an item ready; the existing checklist API persists the choice to the case.
- Start an upload directly from a checklist row.
- Keep original evidence files separate from candidate extracted facts. Uploading a file does not automatically assert that the checklist item is satisfied.

### 4. Evidence dossier

The former plain file list is now a filterable card collection with:

- All / Photos / Documents / Audio / Video filters and per-category counts.
- Stable exhibit numbering, media type, size, source and timestamp.
- Inline image, video, audio and PDF preview links where supported.
- Separate open and original-download links.
- A visible provenance statement: user supplied; not independently verified.

The underlying evidence remains in the existing persistent case storage and is retrieved from the backend when the case is opened again. The service worker cache was bumped to v29; `/api/` responses remain network-only.

### 5. Follow-up is surfaced in the live case

- Users can save a follow-up date and note from the Live Room.
- The case shows scheduled, due-today, overdue or completed state.
- Users can mark a follow-up complete.
- These actions use the existing `case_followups` table and timeline event API.

**Notification limitation:** A saved follow-up is not itself a push notification. Delivery still depends on a reminder channel and its scheduler being configured (for example, a linked/approved WhatsApp reminder setup). The UI says this explicitly instead of promising alerts that may not be enabled.

## Files changed

- `frontend/index.html`
- `frontend/app.js`
- `frontend/live-room.css`
- `frontend/sw.js`
- `backend/main.py`
- `.env.example`
- `tests/test_live_resolution_room.py`
- `tests/test_frontend_assets.py`

## Verification

- `node --check frontend/app.js` — passed.
- `python -m compileall -q backend` — passed.
- `PYTHONPATH=. pytest -q` — **289 passed, 117 subtests passed**.

The tests exercise API persistence, automatic-mode draft metadata, transcript language updates, evidence storage, checklist/follow-up services, and static Live Room assets. They do not authenticate against the user's Gnani account or verify a physical camera/microphone on the user's device. A local Chromium smoke run was attempted but the execution environment blocked local browser navigation (`ERR_BLOCKED_BY_ADMINISTRATOR`), so no claim of a real browser/device run is made.

## Recommended real-device acceptance test

1. Add the Gnani key to `.env`; keep `GNANI_STT_MODEL=prisma-v2.5` unless v3 access is confirmed.
2. Start the app with `run_windows.bat`, open `http://127.0.0.1:8000`, and hard-refresh with `Ctrl+F5`.
3. Start Live Resolution without changing the language setting. Speak a short Hindi sentence, then an English sentence. Use “Finish speaking” if needed.
4. Confirm each transcript is saved to the same case. Reopen the case and confirm the transcript/timeline remains.
5. Check that the guidance shows one clear next action, its reason, any single question, case-specific evidence checklist, and official-source links.
6. Answer the question and confirm the guidance recalculates. Mark one checklist item ready and confirm it stays checked after reopening.
7. Add a screenshot or PDF from a checklist row. Confirm it appears in the matching evidence filter, opens in preview where supported, and can be downloaded as the original.
8. Save a follow-up date, reopen the case, and confirm the date/note and status persist. Do not expect a notification unless the reminder channel is configured.
9. Test the camera, screen-share capture and recorded voice-note fallback on the target device and browser.
