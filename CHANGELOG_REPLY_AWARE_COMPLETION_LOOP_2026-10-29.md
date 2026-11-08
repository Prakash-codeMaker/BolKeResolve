# Reply-Aware Resolution Completion Loop — 29 October 2026

## Why this increment matters

The earlier completion loop updated the next action when the user changed the broad case stage. Support-reply review already recognised materially different situations, but the confirmed reply path sent every reply to the generic `Follow-up needed` stage. That collapsed a refund initiation, a document request, a rejection, an unclear reply and a potentially unsafe request into one state.

## Implemented

- Versioned the completion loop as `completion-loop-v2-reply-aware`.
- Connected the latest user-confirmed reply interpretation to the next-action engine without saving the raw pasted reply in the normal reply-review flow.
- Added distinct next actions for: potentially unsafe credential/remote-access requests; more information requested; refund claimed initiated; refund claimed credited; under review; waiting period stated; acknowledgement only; rejected/closed; mixed/conflicting reply; and manual-review fallback.
- Treats “refund initiated/processed” differently from a claimed credit. A reply claiming credit prompts a user-side account check; it cannot mark a case resolved by itself.
- Directs a document request to the existing evidence panel rather than giving a generic follow-up message.
- Directs suspicious credential or fee requests to safety-first guidance, and keeps mixed/ambiguous messages in review rather than triggering automatic escalation.
- Assigns an existing case stage based on the confirmed interpretation. Later user actions supersede an older reply-derived next action, including events recorded in the same second.
- Shows a low-emphasis explanation that the next action uses the user's reviewed reply and that its sender/claims are not independently verified.
- Bumped the public-shell service-worker cache to `bolkeresolve-shell-v21` so the revised JavaScript/CSS can reach installed PWAs.
- Added regression tests for response classes, safety boundaries, next-action targets, raw-reply retention, state supersession and frontend rendering.

## Verification

- `python -m pytest -q` — **227 passed, 77 subtests passed**.
- `node --check frontend/app.js` — passed.
- `node --check frontend/sw.js` — passed.
- `python -m compileall -q backend tests scripts` — passed.
- `python scripts/check_release_readiness.py` — configured required checks passed, but production readiness is **not** certified. HTTPS origin, production authentication, final privacy notice, monitored support route, persistent hosted storage, backups/restore, mobile/accessibility QA, upload scanning strategy and external security/privacy review still require operator work.

## Boundaries

- Reply interpretation is deterministic and provisional; it is not a legal determination, message authenticity check, or proof of merchant/bank action.
- The user must review and confirm. The normal reply-review route saves a short interpretation/category and user-supplied reference, not the raw pasted reply.
- No complaint is automatically submitted, no financial account is checked, and no refund is guaranteed.
