# Focused core product increment — 22 October 2026

- Kept BolKeResolve centred on its original voice-first payment/refund helper workflow, rather than expanding it into a complaint platform.
- Reduced new-case intake from three screens to two by bringing relevant detail confirmation, optional evidence, and save together.
- Reduced visible homepage issue choices to three common paths; other issue types remain available under “Another payment issue?”.
- Kept unknown details optional and preserved transcript review, first-pass guidance, safety acknowledgement, and private saved-case behavior.
- Updated the deterministic clarification metadata to match the two-step intake.
- Added `docs/FOCUSED_CORE_PRODUCT_SCOPE_2026-10-22.md` as a scope guard for future iterations.

## Validation

Run `python -m pytest -q`, `node --check frontend/app.js`, and `python -m compileall -q backend tests scripts`. Automated validation does not prove live Gnani provider configuration or deployment readiness.


## Launch readiness follow-up — 22 October 2026

- Added password-confirmed self-service account deletion under the secondary Account & privacy disclosure on My cases. It deletes active account/case/evidence records and linked active WhatsApp app records, revokes the session, and warns that exports, external-provider copies and hosting backups cannot be recalled.
- Added no-store cache headers to all API responses.
- Hardened release preflight to require a bare HTTPS public origin, a writable production data directory, and a privacy notice without the bundled draft markers/placeholders.
- Kept verified-email/password recovery, MFA, legal policy completion, malware scanning, shared gateway quotas and external security review as explicit launch gaps rather than pretending they are done.
- Verification: 176 tests, 69 subtests, JavaScript syntax and Python compilation passed.

## Visual alignment pass — 22 October 2026

- Made the selected fictional sample case load a result automatically and update when the selected scenario changes.
- Moved the saved case primary action directly below the case heading/status and reframed the secondary overview destination as Plan & details.
- Tightened guided-chat alignment, message composer, voice controls and responsive layout while preserving existing brand styles.
- Added `docs/FRONTEND_VISUAL_ALIGNMENT_PASS_2026-10-22.md` and bumped the public shell cache to v14.
- Validation: 178 tests and 69 subtests passed; Node syntax and Python compilation passed. Browser-level visual smoke test remains unverified because Chromium navigation was blocked by the environment.
