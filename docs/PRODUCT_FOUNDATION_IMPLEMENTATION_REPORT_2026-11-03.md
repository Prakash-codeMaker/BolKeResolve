# BolKeResolve Product Foundation — Implementation Report

**Build date:** 3 November 2026  
**Artifact:** `BolKeResolve_Product_Foundation_Upgrade_2026-11-03.zip`

## What was implemented

### Case fact ledger
- Added append-only `case_fact_ledger` for a controlled set of workflow facts.
- Captures source type, source event, redacted supporting excerpt, confidence, current/superseded state and timestamp.
- Corrected values create a new history row; prior values are retained as superseded rather than overwritten.
- Live-turn processing re-evaluates the latest user statement against accumulated facts so an explicit correction can replace the current value.

### Evidence-to-claim mapping
- Added `evidence_claim_links`, scoped to a case and one of its evidence items.
- Supports `supports`, `contradicts` and `context` relations.
- Added UI controls to link/unlink an evidence exhibit to a claim.
- A claim relationship does not certify authenticity, accuracy or legal sufficiency.

### Reconciliation report import
- Added `backend/reconciliation.py` and CSV preview/confirmation endpoints.
- Import limit: 8 MB and 5,000 rows. Unknown-only schemas are rejected; accepted fields come from an allowlist of payment/settlement identifiers, statuses, amounts, dates, currency, fees, tax and UTR.
- The original CSV is stored as evidence. The application previews parsed rows and requires explicit user selection and confirmation.
- Formula-like values are neutralised for preview display.
- Confirmation does not automatically overwrite case amount, payment status or workflow facts.
- The Live Room exposes a settlement CSV import control when the case is classified as a settlement/gateway issue.

### Quality measurement
- Added a whitelist-based `product_quality_events` table and instrumentation around case creation, user turns, guidance generation, repeated questions, actions, evidence, follow-ups, outcomes and semantic interpretation failures.
- Added `GET /api/internal/quality/summary`, gated by `BOLKE_QUALITY_METRICS_TOKEN` in the `X-Bolke-Metrics-Token` header.
- The endpoint emits aggregated counts/rates, not conversation text, file names, payment references or evidence content.
- The token is an operator secret and must never be added to frontend code or committed.

### Resolution Passport 1.5
- JSON export now carries fact history, evidence claim links, explicit scan status and user-confirmed reconciliation rows.
- Printable export now includes fact history/corrections and reconciliation import status.
- Evidence scan status remains `not_scanned` until an actual malware scanner is configured. The export does not imply independent verification.

### Readability and frontend controls
- Added `frontend/product-foundation.css` with a consistent 16px body type scale, improved line-height, clearer metadata and focus-visible outlines.
- Added evidence claim-link controls and settlement CSV preview/confirmation UI.
- Added the stylesheet to the public shell allowlist and bumped the service-worker cache to `v41`; `/api/` responses remain network-only.

## Verification performed

From the working tree:
- `PYTHONPATH=. pytest -q`: **340 passed, 129 subtests passed**.
- `python -m compileall -q backend`: passed.
- `node --check frontend/app.js`: passed.
- `node --check frontend/sw.js`: passed.
- `python scripts/check_release_readiness.py`: configured required checks passed; production operator checks remain open.

From a fresh extraction of the generated ZIP:
- ZIP CRC/integrity test: passed.
- Full test suite: **340 passed, 129 subtests passed**.
- Python compilation: passed.
- JavaScript syntax checks: passed.
- 165 files in archive; `.env`, runtime data, local databases, caches, compiled Python files and nested ZIPs excluded.

## What is not connected yet

- **No live Razorpay OAuth connection** is included. Razorpay's OAuth flow requires an approved partner application, merchant authorisation and secure callback/webhook implementation. The delivered CSV flow is a controlled manual import, not a live account connection.
- No direct bank data access or independent confirmation of settlement/payment status.
- No malware scanning engine. Evidence is labelled `not_scanned`; content signature checks are not antivirus.
- No new reminder delivery provider. Existing reminder mechanisms remain opt-in and require their own provider configuration.
- No hosted deployment, object storage, backup/restore verification, external penetration test or legal/privacy review has been performed.
- No completed real-browser screenshot QA at desktop/tablet/mobile breakpoints in this environment.

## Production gates

1. Deploy behind HTTPS with production authentication and exact public origin.
2. Configure monitored privacy/support channels and complete privacy/legal review.
3. Configure the quality metrics token as a long random server-side secret only.
4. Move evidence to private persistent storage with lifecycle/retention controls and tested backups.
5. Add a real malware-scanning service and quarantine workflow before public uploads.
6. Complete accessibility and visual browser QA on real browsers/devices.
7. For Razorpay OAuth, secure partner approval, merchant consent, token storage, HMAC webhook validation, duplicate-event handling, idempotency and revoke handling before any account connection.

This report describes implementation and tests, not a security certification or guarantee of real-world dispute resolution.
