# Live Resolution — Auto language detection and case-specific workflow

Date: 1 November 2026

## Why this update was needed

The previous Live Room could show a connected microphone and an active level meter even when the transcription provider did not return text. The auto-detection path sent `indic-auto` while the default model remained Prisma v2.5. Gnani's current documentation describes language auto-identification as an opt-in Prisma v3.0 feature, using `model=prisma-v3.0` with `language_code=indic-auto` for REST and streaming.

The case guidance also had two continuity problems: later voice turns were not consistently included when refreshing the plan, and a question about contacting support could remain visible after the user had already answered it in their story.

## Changes

### 1. Speech and automatic language detection

- Auto mode now sends the documented `indic-auto` + `prisma-v3.0` combination for both WebSocket streaming and recorded-audio transcription.
- The Prisma v3.0 `codemix` output mode is used for recorded audio so English words in mixed-language speech remain readable in Latin script.
- The app uses the provider's `detected_language_code` when it is returned, including the recorded-voice-note fallback.
- Auto-LID provider rejection produces a clear compatibility message. It does not silently tell the user to keep selecting a language as the normal workflow.
- The Live Room now starts its transcript timeout at the provider's first `speech_start` event as well as at `processing`. A missing transcript reveals retry guidance and a saved-recording fallback instead of leaving the user waiting indefinitely.
- Audio capture remains separate from transcription. A failed transcript does not delete the saved original voice note.

### 2. Persistent, case-aware guidance

- Guidance refresh now includes the initial story and prior user turns from the case timeline.
- Conservative extraction retains only explicit user-reported facts such as a curated merchant match, a currency-marked amount, a clear support-contact statement, and a stated delay.
- These details remain labelled as user-reported; they are not represented as independently verified bank or merchant facts.
- The "refund not received" classifier recognizes common phrases such as "we have not got the refund back".
- When the user has already contacted support, the refund plan focuses on continuing the existing complaint, asking for a reference/status and avoiding duplicate tickets.
- The side panel displays one immediate action, a case-specific evidence checklist, official routes and an editable support follow-up draft.

### 3. Flipkart refund example

Regression coverage uses the reported scenario: a ₹6,000 Flipkart refund not received after three weeks, with support already contacted and no response. The saved case must:

- classify the issue as `Refund not received`;
- retain Flipkart and ₹6,000 as user-reported case details;
- retain the three-week delay and prior support contact;
- avoid asking again whether support was contacted;
- direct the user to the official order-specific support route;
- request one relevant proof and provide a follow-up draft that asks for a refund reference/ARN/UTR/RRN and expected credit date.

### 4. Voice-led evidence capture

- Photo, screen, video and voice-note controls are grouped under one collapsed "Add or show evidence" control to reduce visible one-off buttons.
- After a user transcript expresses a clear capture intent, the chat offers one contextual action (for example, choose a file, capture a document, choose a screen or start a clip).
- The user can dismiss the prompt. Existing stop/cancel controls remain available for active recording and screen sharing.
- The browser still requires a user gesture for opening a file chooser or granting screen/camera capture permission. A voice transcript cannot silently bypass those permissions; the contextual action is the permission hand-off.
- Visual AI review continues to require separate consent. AI observations are candidate facts, not proof of document authenticity.

### 5. Existing-case continuation and exports

- The saved case detail view provides a "Continue live" action that reopens the same case ID.
- New turns and evidence append to that case instead of creating a parallel case.
- The existing case passport print view, portable JSON passport and evidence bundle remain the export path. Exports are structured records of what the user supplied and what the app recommended; they are not a court-certified or police-certified report.

## Configuration and limits

- Configure `GNANI_API_KEY` and ensure the key has access to `prisma-v3.0`. The application deliberately uses that model for auto mode even if a local `.env` still sets an older default. If the account lacks Prisma v3 access, automatic language detection will be rejected by the provider and the UI will explain the entitlement/configuration issue.
- Hardware microphone/camera testing and authenticated live requests against the user's Gnani account cannot be performed in this automated build environment. The automated test suite verifies request parameters and fallback/error handling, not the user's physical device or provider entitlement.
- Follow-up dates are saved in the case. WhatsApp reminders are conditional on a correctly configured provider, business number, approved template and user consent; the app must not imply a push notification is active when those are not configured.
- Production deployments must use HTTPS, authentication, a private persistent data directory, access-controlled backups and a documented retention policy. This update does not claim end-to-end encryption or encryption-at-rest for every stored document. Review the application's privacy notice and configure storage protection before uploading real sensitive records.
- The app does not access merchant/bank accounts, send support requests automatically, or guarantee a refund. Users review and send drafts themselves.

## Validation

- `python -m compileall -q backend` — passed
- `node --check frontend/app.js` — passed
- `PYTHONPATH=. pytest -q` — 290 passed, 117 subtests passed

See `LIVE_RESOLUTION_ACCEPTANCE_TEST_2026-11-01.md` for the manual device and deployment checks still required.
