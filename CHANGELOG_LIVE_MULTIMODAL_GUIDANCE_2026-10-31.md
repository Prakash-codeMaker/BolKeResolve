# Live multilingual and evidence-aware guidance — 31 October 2026

## What is included in this snapshot

- Persistent draft case created before media permissions.
- Live Gnani speech proxy with server-side API key handling.
- Sequential transcript persistence and same-case timeline events.
- User-selected camera and screen captures uploaded directly to the case.
- Existing local OCR and evidence confirmation reused.
- Optional per-image visual AI analysis with separate consent and case context.
- AI observations remain unverified candidates; only individually user-confirmed facts can update resolution guidance.
- Optional same-language translation of generated guidance, persisted to the case timeline and reused for both on-screen display and Gnani spoken output.
- Existing case dashboard, Passport, evidence bundle, commitments and completion loop preserved.

## Corrections in this handoff

- Updated the vision provider notice to say that the image and its underlying claims are **not independently authenticated**.
- Corrected a provider-contract test: the API key must be present in the Authorization header for an authenticated request, but must not appear in the JSON prompt/body. It is not correct to assert that the key should not appear anywhere in a mocked transport call.

## Validation

- `PYTHONPATH=. python -m pytest -q`: 282 passed, 90 subtests passed.
- `node --check frontend/app.js`: passed.
- `node --check frontend/live-pcm-processor.js`: passed.
- `python -m compileall -q backend tests scripts`: passed.
- `python scripts/check_release_readiness.py`: configured preflight checks pass; operator warnings remain for public hosting, auth, privacy, support, durable storage and restore, security and accessibility QA.

## Not claimed as verified

- Live Gnani account credentials and paid upstream audio calls were not exercised.
- Live vision-provider credentials and image calls were not exercised.
- Native camera/microphone/screen picker browser flow was not physically tested: Chromium automation from the development environment was blocked from local server navigation. See `docs/LIVE_MULTIMODAL_MANUAL_TEST_2026-10-31.md`.
- Continuous video understanding is not included; this build analyses user-selected images/frames, and keeps video files as evidence unless a separate video-analysis feature is built.
