# Evidence provenance and reply-aware follow-through — 22 October 2026

## What changed

- Case bundles now expose `fact_provenance` for the issue category, story, merchant/app, amount, payment date, displayed payment status and prior-support contact. These identify whether a value was selected, entered, reported or not provided; they never imply bank or merchant verification.
- Evidence inventory entries identify files as user-uploaded and not independently authenticated. The JSON Resolution Passport format is now version 1.1 and includes fact-source labels plus safe reply-review metadata. The printable passport avoids calling user-entered details “confirmed facts.”
- The new `POST /api/cases/{case_id}/reply-review/preview` endpoint uses deterministic rules to interpret common support-reply patterns. It checks for potentially unsafe requests, claimed refund initiation/credit, document requests, rejection/closure, investigation, wait estimates and acknowledgement-only replies. Unclear replies fall back to manual review; conflicting refund/rejection statements also fall back to a mixed-signals warning.
- Preview redacts common sensitive patterns, checks case access, and does not write the pasted reply text to the case database. This is a best-effort text scrubber, not a privacy guarantee; the UI tells the user not to paste credentials.
- `POST /api/cases/{case_id}/reply-review/confirm` requires explicit confirmation and recomputes the classification. It writes only a short interpretation, suggested next action, user-confirmation marker and optional user-supplied reference to the timeline. The raw pasted reply is not retained by that endpoint.
- Case UI adds a collapsed “Where these details came from” panel and a collapsed “Understand a support reply” workflow in Progress. The latter previews the interpretation first, then requires a user action to save it. Discard removes the in-memory draft without saving.
- Public shell cache version bumped to `bolkeresolve-shell-v9`; API routes remain network-only and private case data is not added to service-worker caches.

## Reply interpretation categories

The interpreter is deliberately deterministic and limited. It does not verify the sender, resolve a dispute, apply all official rules to a reply, or decide legal eligibility. Basic Hinglish patterns are covered for refund initiation, credential requests, document requests and wait estimates, but these do not establish broad multilingual accuracy. It should be evaluated against a multilingual, adversarially curated test corpus before general availability. Regex detection can miss paraphrases and can misunderstand quoted text. Always review the original message.

## Manual validation checklist

1. Create a case with a fictional story and check the provenance disclosure.
2. Paste “Your refund has been initiated. Please allow 5 business days.” Preview should say initiation is claimed, not verified. The timeline must not change before save.
3. Paste “Please share your OTP to release the refund.” Preview should show an urgent safety warning.
4. Paste “Your refund has been initiated, but your complaint has been rejected.” Preview should show mixed signals and advise checking the latest original response.
5. Click Discard; confirm no timeline event was added.
6. Preview then explicitly save an interpretation; verify the timeline contains the category/next step but not the pasted raw message.
7. Export JSON and print PDF; verify provenance labels survive, and the user is told to review exports before sharing.
8. Repeat on a narrow mobile viewport, keyboard only, and with a screen reader.

## Next product gate

Do not present classification accuracy as measured until testing on representative real-world examples has been reviewed by humans. Next work should build labelled multilingual reply-review tests, expose source freshness in one place, offer a user-controlled follow-up date from a confirmed wait estimate, and validate file/image scanning before processing uploaded evidence.

## Current automated validation

Latest local validation: `node --check frontend/app.js`, `python -m py_compile backend/*.py`, and `PYTHONPATH=. python -m pytest -q` pass. Tests include user-confirmed export provenance, no raw reply retention, explicit confirmation, common English patterns, and selected Hinglish patterns. Passing deterministic unit/API tests is not a claim of field-level classification accuracy or live Gnani API validation.
