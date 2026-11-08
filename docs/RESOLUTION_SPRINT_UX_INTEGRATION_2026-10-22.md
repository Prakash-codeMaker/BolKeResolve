# Resolution Sprint UX Integration — 22 October 2026

## Goal

Get a first-time visitor to a useful, source-backed next action before asking them to complete the full intake or create a saved case. The product remains a preparation and follow-through assistant: no bank, merchant, NPCI or government record is queried, and no complaint is submitted.

## What changed

- `frontend/index.html`: placed the `previewResolutionButton` and `resolutionPreview` in the first intake panel, clarified the homepage promise and renamed the wizard stages to Story → Review details → Save case.
- `frontend/app.js`: added a concise first-move result with urgency, one decision-relevant clarifying question, explicit trust boundaries and an expandable complete plan; added stale-response protection; added direct case overview actions for the support draft, evidence and user-reported outcome.
- `frontend/design-v2.css`: added responsive Resolution Sprint styling with mobile button stacking and reduced-motion support.
- `backend/main.py`: the `/api/resolution/preview` and `/api/extraction/preview` endpoints are public in authentication-required mode but use a per-IP, per-action in-memory rate limit. Case persistence and private data continue to use existing authentication.
- `tests/test_auth.py`: verifies that guests can preview but cannot list or save private cases; checks rate-limit response semantics.
- `tests/test_frontend_assets.py`: checks first-step placement, expandable plan, public-preview security boundary and action-first case controls.

## Visitor path

1. Select a common issue or open the intake.
2. Speak or type a story. Voice still requires the configured Gnani integration; text preview works without external provider credentials.
3. Click **Get my next step**. The preview is generated from the user's report and existing deterministic resolution playbooks.
4. Read the prominent first move. The complete steps, missing information and official sources are expandable.
5. Edit the story or decision-relevant facts to invalidate the prior result; run the preview again when ready.
6. Choose **Review details to save my Passport** only if the user wants a persistent case record. In production authentication mode, saving asks the user to sign in/create an account.
7. The saved case overview points directly to the support draft, evidence and user-reported outcome.

## Security and operational boundaries

- Preview requests do not create records. The public preview routes accept POST and are protected by the same-origin Origin requirement when authentication is required.
- The in-process rate limiter is a prototype guard. Horizontal/multi-worker deployments need shared rate limiting at a trusted gateway, WAF or distributed store, plus monitoring and a quota for any paid model usage.
- Do not put credentials in text submitted to the preview. Sensitive-text scrubbing is best-effort, not a guarantee. The page warns users and the saved flow still requires review.
- The service does not confirm a refund, check transaction systems or file an official complaint. User outcomes remain user-reported.

## Validation

- `python -m pytest -q`: 123 tests passed; 34 subtests passed at packaging time.
- `node --check frontend/app.js`: passed.
- `python -m compileall -q backend tests scripts`: passed.
- Browser visual/interaction QA remains a manual launch gate. Check keyboard navigation, focus visibility, mobile layout, loading/error states and the auth gate preserving an unsaved story.

## Deferred

No database schema change was needed. Do not add more channels or public community features before testing the current sprint with 10–20 consenting users and measuring time-to-first-useful-action, first action completion, correction rate, user comprehension and referrals.
