# BolKeResolve — Condition-Aware Commitment Reconciliation

**Implementation report:** 29 October 2026  
**Code base:** `BolKeResolve_Reply_Aware_Completion_Loop_2026-10-29.zip`  
**New build:** `BolKeResolve_Condition_Aware_Commitment_Reconciliation_2026-10-29.zip`

## Executive result

Implemented a minimal vertical slice for recording and reconciling conditional statements inside BolKeResolve's existing Resolution Passport. The feature doesn't add another dashboard or replace the current case workflow. It creates a reviewable record of a statement, its prerequisite, its stated timeframe, and later updates that may support, contradict, qualify, supersede or report fulfilment of it.

This is **not** claimed to be unique or impossible to copy. The initial extractor is deterministic and deliberately narrow. The defensibility hypothesis is that careful condition-aware records, a hard evaluation set, and a growing collection of corrected edge cases could become useful over time; that asset has not yet been built.

## User journey

1. Open a saved case and expand **Prepare & Contact → Commitments & conditions**.
2. Paste an exact sentence from a support email/chat or import a short audio clip. If audio is selected, the user must confirm they have the right to use it; it is sent through the existing configured Gnani speech transcription route. The app does not save the audio.
3. Preview the suggested fields: statement type, action, amount, condition, what starts the clock, timeframe, qualifier and date. Correct them.
4. Explicitly confirm before saving. Preview is read-only.
5. Later add a reviewed reply or evidence, mark how it relates, and optionally record an occurrence date and link a file already attached to that case.
6. The evaluator updates the current interpretation while retaining the prior statement and event history. Export/print includes the record and provenance limits.

## Implementation details

### New module

`backend/commitments.py`

- `extract_commitment_candidate(text, source_type)` returns a candidate only where narrow rules identify a plausible statement/action.
- `evaluate_commitment(commitment, events, today=None)` calculates the display state from a commitment and its user-reviewed events. It does not mutate event history.
- `add_business_days()` excludes Saturdays and Sundays only.
- `source_hash()` provides integrity bookkeeping for the stored redacted excerpt; it is not proof of authenticity.

The extractor currently handles phrases such as `once/after/when/if`, `will`, common English timeframe units, common English number words, INR amounts, and selected Hinglish action/condition phrases. Negations and exception clauses such as “unless” are conservatively held for manual review. It is not a general semantic parser. Unsupported or ambiguous wording must remain a manual review case; use realistic, labelled evaluation data before broadening coverage.

### Case-scoped API

| Route | Role | Persistence |
|---|---|---|
| `POST /api/cases/{case_id}/commitments/preview` | Return a redacted, editable candidate | Does not write a case record |
| `POST /api/cases/{case_id}/commitments/confirm` | Save explicitly user-confirmed fields | Saves short redacted excerpt and structured fields |
| `POST /api/cases/{case_id}/commitments/{commitment_id}/reconcile` | Add later reviewed update/event | Appends event; never replaces original statement |
| `DELETE /api/cases/{case_id}/commitments/{commitment_id}` | Remove active commitment and its event history | Underlying case evidence remains intact |

The existing `require_case_access` checks protect the routes. Evidence IDs are accepted only when the file belongs to the same case. A future date is rejected when a user labels it the confirmed occurrence date of a trigger.

### Data model

- `case_commitments`: redacted source excerpt, hash, source type/label, user-reviewed action and amount, condition, trigger rule, duration, qualifier, statement date and review state.
- `commitment_events`: append-style, case-linked updates with relation, user-reported/reviewed status, optional case evidence ID, claimed date, confirmed occurrence date and small metadata object.

The schema keeps source authenticity explicitly false. It does not prove the recording has not been edited or the speaker works for the organisation.

### Reconciliation semantics

- **Condition unknown:** no deadline is calculated.
- **Condition reported as triggered without a date:** the event can be recorded, but the clock stays unset.
- **Condition plus a confirmed occurrence date:** an estimated timeframe can be calculated when the amount/unit are supported.
- **Contradiction:** the current state becomes conflict-needs-review; original and new statements remain in history.
- **Qualifies/supersedes:** flags review without silently replacing the first statement.
- **Fulfilment reported:** tells the user to check the relevant account or official record; a message claiming credit isn't proof that the funds arrived.
- **Refusal/negation or unclassified statement:** manual review only; no positive promise or deadline is inferred.
- **Hours-level promise:** no date-only deadline is invented because exact time and timezone are not captured.

Business-day estimates exclude weekends only. They do not know Indian public holidays, organisation calendars, exact hour-level commitments, applicable law, or contractual conditions; displayed dates are not legal deadlines.

### Integration with the existing app

- Added a disclosure panel within the existing Prepare & Contact workspace, not a separate nav section.
- Added preview/review/confirm and later-event forms.
- Kept audio optional and user-triggered.
- Added the commitments/events to Resolution Passport JSON format 1.3 and printable HTML.
- Updated the public-shell cache to `bolkeresolve-shell-v22`.

## Validation

| Check | Result |
|---|---|
| Full test suite | **253 passed, 90 subtests passed** |
| `node --check frontend/app.js` | Passed |
| `node --check frontend/sw.js` | Passed |
| `python -m compileall -q backend tests scripts` | Passed |
| Release-readiness script | Configured required checks passed; warnings/operator checks remain |
| Live Gnani STT/TTS | Not tested in this environment |
| Public Meta/Twilio/email delivery | Not tested as part of this change |
| Browser visual/interaction QA | Not verified; Playwright's navigation to the local server was blocked by environment policy (`ERR_BLOCKED_BY_ADMINISTRATOR`) |

## Before showing this publicly

Run the manual browser smoke test in `CHANGELOG_CONDITION_AWARE_COMMITMENT_RECONCILIATION_2026-10-29.md`. Use only synthetic cases and a recording you have the right to use. Check desktop and mobile layouts, keyboard focus, transcript correction, confirmation gating, conflict states, export and delete. Do not claim the extractor is accurate across Indian languages until it is evaluated on a labelled corpus. Do not claim Gnani understood a commitment: it transcribed the audio; the separate extractor proposes a candidate.

Existing release-readiness warnings remain: HTTPS origin, production authentication mode, final published privacy notice, monitored support route, persistent hosted storage, backups/restore, mobile/accessibility QA, upload scanning strategy, and external security/privacy review. This increment does not make the service production-ready.

## Practical next validation experiment

Create 35–50 labelled synthetic statements: positive promise; estimate; conditional promise; exception/`unless`; negation/refusal; two deadlines; ambiguous date; business/calendar days; refund initiation versus actual credit; conflicting follow-up; and irrelevant phrase containing a hedge word in a later sentence. Have a second reviewer label the expected interpretation without seeing the parser output. Track false-positive commitment rate, missed condition rate, amount/date accuracy, and false-clock rate. The initial safety objective should prioritise **no falsely asserted clock** over maximum extraction coverage.
