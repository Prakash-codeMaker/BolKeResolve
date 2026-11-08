# Incremental update: Voice-to-case and language choice

Date: 19 October 2026

## What changed

1. Added `backend/extraction.py` and wired it into `POST /api/voice/transcribe`. A successful transcription now includes candidate fields for issue type, known merchant/app, amount, payment date, payment status, support-contact status, conflicts and clarifying questions.
2. Added a review panel in the intake UI. Clear candidates populate only default/empty fields; existing user entries are preserved and conflicting speech suggestions can be applied explicitly.
3. Multiple distinct amounts are marked as a conflict instead of choosing one. Explicit dates are parsed; dates without a year are flagged for review. Relative terms such as “yesterday” are left for clarification rather than silently converted.
4. Replaced the visible language select with an accessible popover showing native-script choices for Hindi/Hinglish, English, Marathi, Bengali, Gujarati, Kannada, Malayalam, Punjabi, Tamil and Telugu. The underlying codes remain the configured Gnani STT codes.
5. Added extraction and language UI contract tests.

## Verified in this workspace

- `python -m unittest discover -s tests -v`: 50 tests passed.
- `node --check frontend/app.js`: passed.
- `python -m compileall -q backend tests`: passed.
- FastAPI health endpoint responded successfully in local development mode.

## Not yet verified

- Live Gnani STT/TTS calls: no real `GNANI_API_KEY` was available; provider contract tests use mocked responses.
- Browser visual/interaction QA: the execution environment blocked Chromium navigation to localhost (`ERR_BLOCKED_BY_ADMINISTRATOR`). Open the app in a regular browser on the developer machine to check the review panel and language chooser.
- Rule-based extraction quality across accents and all ten languages. The extraction is a conservative first layer and requires a human-reviewed multilingual test set.

## Safe local smoke test

1. Extract the ZIP.
2. Create `.env` from `.env.example` and add your own Gnani key locally (never share or commit it).
3. Run `run_windows.bat` and open `http://127.0.0.1:8000`.
4. Record synthetic, non-sensitive speech such as: “I used Zomato and did not get my 850 refund back on 12 October 2026.”
5. Review the transcript, the merchant/amount/date suggestions, and the issue/status fields before saving. Correct anything inaccurate.

## 20 October 2026 — multilingual and case workspace pass

- Default voice language mode changed to Auto-detect across configured Gnani locales, while retaining a manual pin for each of the ten supported languages.
- Removed the explicit false `itn_native_numerals` multipart field; added request correlation IDs and safe, provider-aware STT errors.
- Redesigned case detail into an action-oriented workspace with summary strip, Next steps / Evidence / Message / Activity tabs, compact progress side rail, and collapsible story/source details.
- Added case fact editing with guidance regeneration and a refresh-plan action to reclassify older cases from their saved story.
- Important: Gnani's current REST reference and its SDK changelog describe language selection inconsistently. Auto-detection is implemented but has not been verified against the user's live account; see `docs/MULTILINGUAL_STT_AND_CASE_WORKSPACE.md`.

## 2026-10-20 — Speech UX reliability and autofill

- Replaced provider/account-specific language messages with short, user-facing recovery instructions; removed provider diagnostics and model metadata from the public transcription response.
- Kept the existing recording available for language retry and made the picker language-neutral.
- Added conservative normalization for common English phrases that the recognizer returns in Devanagari phonetics, so visible transcript and extraction can use readable English without dropping unknown words.
- Re-runs final speech transcript through the same extraction preview endpoint used by typed text before autofilling fields.
- Improved extraction status wording and made empty extraction results retryable after edits.
- Added `Cache-Control: no-store` for the HTML shell and first-party scripts/styles to prevent stale UI from hiding updates.
- Added regression coverage for provider-neutral responses, script normalization and Zomato refund autofill.


## 2026-10-20 — Resolution Prep kit and case follow-through

- Added `backend/action_pack.py`, which assembles a case-specific, reviewable pack with first action, evidence/preparation checklist, source links, follow-up state, readiness and plain-text export. It reuses the saved deterministic resolution plan and makes no external submissions.
- Added persistent SQLite state for checklist items and user-managed follow-up dates/notes, with case access checks and existing-database initialization. Follow-up dates are surfaced in the case but do not send push notifications.
- Added `GET /api/cases/{case_id}/action-pack`, `PATCH /api/cases/{case_id}/checklist/{task_key}`, and `PUT /api/cases/{case_id}/follow-up`.
- Made the complaint/support draft editable and saveable through `PUT /api/cases/{case_id}/draft`; edits are scrubbed for sensitive-looking text and recorded in the case activity. Drafts are never sent automatically.
- Added a dedicated Prep kit workspace tab with readiness feedback, category-specific preparation checklists, follow-up controls, and Copy/Download case pack actions.
- Updated official source links to include e-Jagriti help docs, clarified pre-litigation vs formal consumer-commission routes, and refreshed source review stamps after re-checking NPCI, NCH, RBI, cybercrime and e-Jagriti public guidance on 2026-10-20.
- Regression tests cover pack contents, category-specific checklist states, persistence, invalid dates, clearing reminders, draft editing, and frontend action wiring.
