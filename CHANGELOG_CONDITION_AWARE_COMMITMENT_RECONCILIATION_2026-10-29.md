# Condition-Aware Commitment Reconciliation — 29 October 2026

## Purpose

Add a narrow commitment record inside the existing Resolution Passport. It captures what a user-reviewed support statement says, what condition may have to happen first, what timeframe was stated, and how later user-reviewed updates support, contradict, qualify, supersede or report fulfilment of that statement. It does not replace the existing case, evidence, reply-review or completion-loop workflows.

## Implemented

- Added `backend/commitments.py` with a versioned, deterministic candidate extractor and a reconciliation evaluator.
- Preview extracts candidate action, amount, condition, trigger type, duration, day type and qualifier. It does not write to the case database.
- The user must edit/review the candidate and explicitly confirm it before persistence.
- A condition-based deadline remains unset until a user records that the condition occurred and supplies the occurrence date.
- Approximate business-day calculations exclude weekends only. Public holidays, company calendars, exact times and legal deadlines are not inferred.
- Later updates are appended as separate events. Contradictions and newer statements that qualify/supersede earlier statements keep the original statement visible and require review.
- A statement that appears negated/refusal-oriented, or contains a potentially material exception such as “unless,” is held for manual review; it is not converted into a positive promise or automatically assigned a deadline.
- A claim that a refund was credited is not proof the funds arrived. Reported fulfilment prompts the user to check the relevant account or official record.
- Added a case-scoped panel within existing Prepare & Contact tools, with optional imported audio sent through the existing configured Gnani transcription route. The app does not retain the audio file. Only a short redacted excerpt and user-confirmed fields are stored after explicit confirmation.
- Added case-scoped preview, confirm, reconcile and delete endpoints:
  - `POST /api/cases/{case_id}/commitments/preview`
  - `POST /api/cases/{case_id}/commitments/confirm`
  - `POST /api/cases/{case_id}/commitments/{commitment_id}/reconcile`
  - `DELETE /api/cases/{case_id}/commitments/{commitment_id}`
- Added `case_commitments` and append-style `commitment_events` tables, linked to the existing case/evidence tables.
- Added commitment and history export to Resolution Passport JSON format 1.3 and printable HTML.
- Updated the static shell cache version to `bolkeresolve-shell-v22`.
- Added parser, evaluator, API, export and frontend integration regression tests.

## Validation

- `python -m pytest -q` — **253 passed, 90 subtests passed**.
- `node --check frontend/app.js` — passed.
- `node --check frontend/sw.js` — passed.
- `python -m compileall -q backend tests scripts` — passed.
- `python scripts/check_release_readiness.py` ran. It passed configured required checks but reported the expected deployment warnings and operator checks described in `IMPLEMENTATION_STATUS.md`.

A Playwright browser smoke test was attempted, but this build environment returned `ERR_BLOCKED_BY_ADMINISTRATOR` when Chromium navigated to the local server. Therefore, full browser visual/interaction QA is **not verified here** and must be completed in local Chrome/Edge before using this feature in the public demo.

## Important boundaries

- Extraction is deterministic/rule-based and intentionally narrow, not a general-purpose promise-understanding model.
- Gnani is used by the existing audio transcription route; the new semantic candidate extraction itself does not call an LLM.
- Uploaded call recordings must be lawfully and appropriately obtained. The UI asks the user to confirm their right to use the recording. Review applicable consent, privacy and provider-retention obligations before public deployment.
- A transcription or user confirmation does not establish the speaker's identity or prove that the organisation made the statement.
- A source hash provides integrity bookkeeping only; it does not prove authenticity or an unedited original recording.
- A linked file is not automatically authentic or independently verified.
- No bank, merchant, payment-network or government record is queried; no company is contacted; no complaint is filed; no refund is guaranteed.
- This increment is a local-test implementation, not a production security/privacy certification.

## Manual smoke-test sequence

Use a synthetic case and a test recording you have permission to use.

1. Open a case and choose **Prepare & Contact → Commitments & conditions**.
2. Paste: `Once the return is scanned at the warehouse, we will initiate the ₹1,200 refund within five business days.`
3. Preview, verify the condition, amount and timeframe, and explicitly confirm.
4. Verify the initial state says the condition/date is not established and no due date is shown.
5. Add an update with relation **Condition occurred**, and a past occurrence date. Verify an estimated date appears and the UI says holidays/company calendars are not checked.
6. Add a second update with relation **Conflicts with the statement**. Verify the state becomes conflict-needs-review and the original statement remains visible.
7. Export JSON and print view; check that the commitment and event history are included and source authenticity remains false.
8. Try a negated statement such as `We will not initiate the refund within five business days.` Verify it is marked for manual review with no automatically calculated deadline.
9. Delete the commitment and verify it disappears from the active case; understand that this does not delete the underlying evidence file or any previously downloaded/exported copy.
