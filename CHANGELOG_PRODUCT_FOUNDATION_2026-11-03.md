# Product Foundation — 3 November 2026

- Added append-only `case_fact_ledger` with source, redacted excerpt, confidence and current/superseded state.
- Added `evidence_claim_links` for supports/contradicts/context relationships.
- Added bounded Razorpay/payment settlement CSV preview and explicit row confirmation; original CSV remains evidence and confirmation does not silently mutate case facts.
- Added token-gated, privacy-preserving quality metrics endpoint.
- Added scan-status disclosure to evidence records (`not_scanned` until a real scanner is configured).
- Extended Resolution Passport to format 1.5 with fact history, claim links and user-confirmed reconciliation rows.
- Added readable product-foundation CSS, claim-link controls and settlement CSV import/review UI; bumped service-worker shell cache to v41.
- Added API and export integration tests.

Validation: 340 tests passed, 129 subtests passed; Python compilation and JavaScript syntax checks passed. Release preflight passed configured required checks, with production operator tasks still outstanding.
