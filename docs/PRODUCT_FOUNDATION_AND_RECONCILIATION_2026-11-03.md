# Product Foundation & Reconciliation — 3 November 2026

## Shipped in this increment

### 1. Versioned case fact ledger

- `case_fact_ledger` stores changes to a controlled set of case facts as an append-only history.
- Each entry records the source type, source event, redacted source excerpt, confidence, timestamp and whether it is the current value.
- Corrections deactivate the previous current value instead of erasing history.
- The live-turn path re-extracts the latest utterance against accumulated context so an explicit correction (for example, a revised amount) can supersede a prior value.

### 2. Evidence-to-claim relationships

- `evidence_claim_links` attaches one evidence exhibit to a specific claim.
- Relations are `supports`, `contradicts` or `context`.
- Links are scoped to the same case and evidence record; users can unlink them.
- A relationship is an organisational aid, not a determination of authenticity or legal sufficiency.

### 3. Payment/settlement CSV reconciliation review

- `backend/reconciliation.py` recognises a bounded allowlist of common payment/settlement columns.
- The parser enforces an 8 MB and 5,000-row cap, UTF-8 handling and basic content validation; unknown-only headers are rejected.
- Formula-like cells are neutralised in the preview to reduce spreadsheet formula injection risk.
- The original CSV is saved as evidence. A preview is created first; selected rows become `confirmed_rows` only after explicit user confirmation.
- Confirming a CSV does not silently update case amount, payment status or settlement status. Users must review and separately confirm any facts that should change their case.
- This is a file-based import, not a direct provider API connection.

### 4. Privacy-preserving product quality metrics

- `product_quality_events` stores a whitelist of event names, coarse issue family/stage/channel, duration and timestamp. It does not store user story text, file names, payment IDs, UTRs or uploaded content.
- `GET /api/internal/quality/summary` is token-gated using `BOLKE_QUALITY_METRICS_TOKEN` and the `X-Bolke-Metrics-Token` header. If the token is not configured, the endpoint responds as unavailable.
- The endpoint aggregates events for a recent reporting window and computes simple indicators such as question-repeat rate and evidence/follow-up/outcome counts.
- It is an internal diagnostic starting point, not a full analytics platform or a validated product KPI system.

### 5. Resolution Passport 1.5

JSON and printable HTML exports can include:
- fact history and superseded values,
- evidence-to-claim links,
- scan status disclosure (`not_scanned` remains explicit),
- provider reconciliation import status and user-confirmed rows.

The Passport still labels user-reported and imported data appropriately. It does not imply that a bank, merchant, gateway, organisation, evidence file or transaction has been independently verified.

### 6. Frontend foundation

- Product foundation stylesheet adds a consistent 16px base, readable long-form line height and clearer metadata scale.
- Evidence cards can display claim links and scan status.
- Settlement cases can upload a CSV, inspect a parsed preview and explicitly confirm chosen rows.
- Evidence claim relationships can be added/removed in the UI.
- Service-worker cache is bumped to v41 and includes the new stylesheet; API responses remain network-only.

## Verification

- `PYTHONPATH=. pytest -q`: 340 passed, 129 subtests passed.
- Focused product foundation and Resolution Passport tests cover fact corrections, claim linking/unlinking, CSV import/confirmation, CSV parser safeguards, token-gated metrics privacy, and Passport JSON/print export.
- `python -m compileall -q backend`: passed.
- `node --check frontend/app.js`: passed.
- `node --check frontend/sw.js`: passed.
- `python scripts/check_release_readiness.py`: configured required checks passed. It still reports operator actions needed for a public production deployment.

## Not implemented / external dependencies

- Direct Razorpay OAuth, account connection, dashboard data retrieval or webhooks. These require Razorpay partner approval, a registered OAuth application, merchant authorisation, server-side credentials, callback verification, idempotency and deployment tests. This release does not pretend a CSV upload is a live connection.
- Automatic bank account verification or reconciliation against actual bank records.
- A malware scanning engine. Evidence is explicitly labelled `not_scanned`; file-signature/content checks are not antivirus.
- Production hosting, persistent external object storage, tested backup/restore, TLS, published support/privacy details, full security and accessibility audit.
- An analytics dashboard or event retention/aggregation policy beyond this diagnostic endpoint.

## Operator setup

1. Keep API keys and provider credentials in server-side environment variables only.
2. Generate a long random `BOLKE_QUALITY_METRICS_TOKEN` if the internal quality endpoint is required. Do not expose it in frontend code or commit it.
3. Before enabling public uploads, implement and test malware scanning, object storage permissions, retention/deletion and backup restore.
4. Before connecting a Razorpay merchant account, obtain partner approval and merchant consent and implement the official OAuth and webhook security requirements.
5. Use `scripts/check_release_readiness.py`, then complete every operator check it reports before public deployment.
