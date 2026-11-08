# Share-to-Case, official route snapshot and versioned rulebook — 23 October 2026

## What is implemented

### Share-to-Case (PWA Web Share Target)
- Added a Web Share Target entry in `frontend/manifest.webmanifest` for supported installed PWAs.
- Incoming text, title, HTTPS source URL and one optional PNG/JPG/JPEG/WEBP/PDF are staged for a short time in a private database table.
- Staged values and file bytes are encrypted with Fernet before persistence. Production requires `BOLKE_SHARE_INTAKE_ENCRYPTION_KEY`; local development may create `.share-intake.key` with restrictive file permissions.
- Items are not attached until the user reviews the preview and confirms an existing case or uses the item to start a new case.
- Source domain can be shown, but the full source URL, path and query are not shown back; path/query are removed from URL text because they can contain bearer credentials.
- OTP/PIN patterns are redacted, filenames are sanitised, file extension and signature are checked, file size is bounded, and one file is accepted per share.
- Public share posts are throttled by `BOLKE_SHARE_TARGET_LIMIT_PER_MINUTE` (default 12/minute per application-observed client address). Production must also set a shared reverse-proxy/gateway limit because the app limiter is per worker.
- Staged payload expires after `BOLKE_SHARE_INTAKE_RETENTION_MINUTES` (default 30; bounded to 5–60 minutes). The hourly retention sweep removes expired and old-consumed rows. Confirmation/discard clears encrypted content and file bytes.
- Normal upload remains available when the PWA share target is unsupported or unconfigured.

### Official routes and NCH snapshot
- Added `/api/support-directory` which returns first-party support routes, a selected snapshot match and the official source.
- The selected NCH convergence entries are a dated static snapshot reviewed on 23 October 2026, not a live API and not an exhaustive representation of the directory.
- A match is not a claim that a grievance has been submitted, that the partner will respond, or that BolKeResolve is an NCH partner.
- No-match results link to the full official directory and explicitly do not imply that the organisation is absent from the full live directory.

### Versioned resolution rulebook
- Added `backend/rulebook.py` with version/review metadata and conservative rules for potential unauthorised transactions, failed UPI debits, pending transfers, merchant refunds, conditional RBI Ombudsman eligibility and general guidance.
- Resolution previews and stored case recommendations carry matched rule identifiers, applicability conditions, next-action guidance and official-source URLs.
- Rule metadata does not verify a transaction, determine legal eligibility by itself, or replace review of the current official guidance.
- The UI presents the rulebook and NCH snapshot explanation under progressive disclosure to preserve the concise case experience.

## Configuration

- `BOLKE_SHARE_INTAKE_ENCRYPTION_KEY`: mandatory in production. Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Keep stable across restarts; key loss prevents decrypting unexpired staged payloads.
- `BOLKE_SHARE_INTAKE_RETENTION_MINUTES=30`
- `BOLKE_SHARE_TARGET_LIMIT_PER_MINUTE=12`
- Configure HTTPS and a supported installed PWA/browser for native share-sheet testing. Normal upload remains a fallback.
- Add a shared edge/gateway request limit and monitoring in production; the in-process limit is a supplemental control.

## Verification

- `python -m pytest -q`: **211 passed, 77 subtests passed**.
- `node --check frontend/app.js`: passed.
- `node --check frontend/share-token.js`: passed.
- `node --check frontend/sw.js`: passed.
- `python -m compileall -q backend tests scripts`: passed.
- CSS parsing: no top-level syntax errors.
- HTML ID audit: no duplicate IDs.
- ZIP archive integrity: verified.

## Not claimed / remaining for operator validation

- Native share sheet has not been browser-device tested in this environment; Web Share Target support depends on installation/browser/platform.
- Official NCH snapshot has not been live-refreshed by the application; operators must review it periodically.
- No direct NPCI, bank or government complaint API is used, and no grievance is filed automatically.
- No live Gnani request or live deployment is verified by these tests.
- In-memory rate limiting is per worker; production edge limits, privacy/legal review, file malware scanning and broader production operations remain required.

### 23 October follow-up: capability-token URL hardening

- Added a same-origin, synchronous `frontend/share-token.js` head script to capture `shared_intake` from the URL fragment into short-lived `sessionStorage` and immediately remove the fragment before page body parsing.
- Switched the attach endpoint from `/api/shared-intake/attach/{case_id}?include_context=...` to fixed `POST /api/shared-intake/attach`; `case_id` and `include_context` are validated JSON body fields. The one-time capability remains in `X-Share-Intake-Token`.
- Added the early script to service-worker shell v19 and made it receive `Cache-Control: no-store` through the security middleware. API paths remain network-only.
- Regression tests cover old dynamic path no longer attaching, body validation, token scrubbing order, constant paths, and service-worker cache inclusion.
