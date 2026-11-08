# Living Resolution Passport + Case Inbox Bridge — 23 October 2026

## Implemented

- Added bounded, local extraction for text-based/scanned PDF and image evidence (English/Hindi Tesseract in the container build), with upload, pixel, page and text limits.
- Added user-triggered evidence fact review for merchant, amount, payment date and payment-status wording. The preview compares extracted candidates to case facts and flags possible mismatches. Users confirm source facts separately from applying selected values to the saved case.
- Raw OCR text and excerpts are not persisted in the review records. Structured candidate values and confidence/method are saved; the user-visible response provides the source excerpt for immediate review. Source facts are included in Resolution Passport JSON/print output with a statement that document authenticity was not independently verified.
- Added optional, random case-specific inbound email aliases behind configuration: public FQDN, stable Fernet encryption key, and strong bearer or HTTP Basic authentication. Alias tokens are 60 lowercase hex characters (240 bits) so they survive address normalization and stay within a typical email local-part length limit. Only a hash is stored for routing; the token is encrypted for the case owner to view it.
- Added provider-parsed inbound webhook, idempotency by provider message ID, a 12 MB payload limit, maximum 10 pending replies per case, redaction, temporary encryption, and sender-identity unverified warnings.
- Added preview / confirm / discard controls for incoming email. Attachments are not imported; only bounded metadata is visible during review. Confirm/discard clears subject/body ciphertext and attachment metadata; confirmation stores only a brief interpretation and user-supplied reference (if any) in the case timeline.
- Added an hourly inbound-message retention sweeper plus endpoint-triggered expiry. Retention is capped at 1–30 days (default 14). A host backup may still retain prior database pages; production backup policy must be configured independently.
- Added `docs/LIVING_RESOLUTION_PASSPORT_AND_CASE_INBOX_BRIDGE_2026-10-23.md`, optional hosting env vars, Render blueprint entries and API/setup documentation.
- Hardened email parsing against oversized subject/body/from/recipient/attachment metadata, bounded attachment sizes and retention settings, and documented the 63-character local-part format. HTML-only inbound messages have script/style/head blocks removed and sensitive-text scrubbing applied before preview.

## Verification performed

- `python -m unittest discover -s tests -v` — 193 tests passed after the current feature additions, including HTML-body fallback and metadata/retention bounds tests.
- `python -m py_compile backend/main.py backend/evidence_review.py backend/passport.py` — passed.
- `node --check frontend/app.js` — passed.
- HTML ID audit — 100 IDs, no duplicates.
- Local synthetic OCR smoke test using a generated PNG — extracted the expected sample words.
- No live email provider, DNS/MX setup, public HTTPS delivery, live Gnani request, or full browser visual run was verified. The bridge remains disabled until the required server-side configuration and provider routing are set.

## Operational note

The generated project archive intentionally excludes `runtime/`, local SQLite databases, uploaded evidence, Python bytecode, `.env` files and other local secrets/data. On first launch, the application recreates its runtime directory. This prevents local test/case artefacts from being copied into the shared project package.


## Final verification after parser hardening

- `python -m unittest discover -s tests -v` — **193 tests passed**.
- `python -m py_compile backend/main.py backend/evidence_review.py backend/passport.py` — passed.
- `node --check frontend/app.js` — passed.
- `frontend/index.html` audit — 100 IDs, no duplicates.
- `python scripts/check_release_readiness.py` — development preflight passed its configured required checks and surfaced the expected production configuration/operator warnings.
- No live inbound-email provider, DNS/MX routing, public HTTPS delivery, live Gnani request, production deployment or full browser visual run was verified.
