# BolKeResolve — Live multilingual, evidence-aware guidance

**Implementation snapshot:** 31 October 2026  
**Base:** the existing Live Resolution Room, case database, evidence store, resolution playbooks, commitments, timeline and Resolution Passport.  
**Purpose:** connect live speech, user-selected visual evidence, same-language guidance and case persistence into one workflow.

## 1. User experience delivered

1. The user starts a Live Resolution session. The backend creates a persistent draft case **before** asking the browser for microphone or camera permission.
2. The user can speak, type, take a camera photo, upload documents, select a screen for sharing, capture selected screen frames, record a short audio/video clip, or import a support-call recording.
3. Final speech segments are queued sequentially in the browser, saved as user turns in the existing case timeline and passed to the existing deterministic resolution engine.
4. BolKeResolve generates the next-step guidance from its existing official-source playbooks. If the user opted in to external text translation and a provider key is configured, the text is translated into the selected language. The same saved translated text is displayed in the guidance panel and passed to Gnani Timbre for spoken output.
5. Uploaded images and PDFs are saved against the same case. Existing local OCR/review creates candidate facts. Images can additionally be sent to the configured vision model only after a **separate per-image consent**.
6. Visual AI observations remain candidates. The user must explicitly select and confirm each field. Unconfirmed model summaries/observations do not enter the resolution-rule context. After confirmation, BolKeResolve recomputes the recommended route and guidance.
7. Ending a session appends a session-end event to the same timeline. The existing case page, Passport print view and evidence-bundle ZIP remain the case record.

## 2. Provider and API architecture

### Live speech

- Browser microphone audio is converted to PCM by `frontend/live-pcm-processor.js` and streamed to the same-origin WebSocket `/api/live-room/voice`.
- The backend attaches `GNANI_API_KEY` and opens `wss://api.vachana.ai/stt/v3/stream`.
- The browser never receives the Gnani API key.
- The current implementation uses the documented `language_code`, `model`, `format`, `x-sample-rate`, `x-min-silence-ms` and `x-max-speech-s` WebSocket headers. Gnani's current documentation explicitly accepts these current names; older spellings are also accepted. See https://docs.gnani.ai/api/STT/stt-websocket.
- The current model default remains `prisma-v2.5` for account compatibility. Prisma v3.0 should be enabled only after the account's access and required multilingual behaviour have been verified.

### Visual analysis and translation

- `backend/agent_assist.py` calls the OpenAI Responses API using the server-side `OPENAI_API_KEY` and configurable `BOLKE_MULTIMODAL_MODEL`.
- Calls use `store: false`. This disables Responses API storage; it does not mean the provider has no retention or processing obligations. Review provider terms and privacy notice before public use.
- The vision endpoint accepts saved JPG/PNG/WEBP images only. PDFs continue through the local PDF/OCR workflow.
- Image analysis includes the minimum relevant, user-reported case context to help compare the image with the story. Sensitive identifiers should be masked before upload and the model is instructed not to repeat credentials.
- AI output is not document authentication, transaction verification, proof of responsibility or legal eligibility.
- Only user-confirmed fields may be used by the deterministic resolution engine.
- Guidance translation is a wording layer only: it must preserve route, conditions, amounts, dates, warnings and uncertainty, and must not add advice.

### Spoken guidance

- The backend first generates guidance from the deterministic resolution engine.
- The translated or original guidance is appended to the case timeline with language and translation-status metadata.
- The frontend renders the same text in the case guidance panel and conversation, then calls the existing Gnani Timbre speech endpoint.
- If translation is not consented/configured or fails, the route remains available in the original supported guidance text. The UI must state that same-language guidance is unavailable rather than claiming it translated.

## 3. Existing case storage reused

No parallel case-management database is introduced. The implementation uses the existing:

- `cases` table and case owner checks;
- `timeline` events for session lifecycle, user turns, assistant guidance and evidence-review actions;
- `evidence` table and existing upload/serve/delete controls;
- `evidence_fact_reviews` and `case_fact_sources` for candidate and user-confirmed facts;
- `live_room_evidence_analyses` for the analysis preview/confirmation lifecycle;
- Passport JSON/print routes and evidence-bundle ZIP.

Relevant endpoints:

- `POST /api/live-room/cases`
- `POST /api/cases/{case_id}/live-room/turn`
- `POST /api/cases/{case_id}/live-room/guidance`
- `POST /api/cases/{case_id}/evidence`
- `POST /api/cases/{case_id}/live-room/evidence/{evidence_id}/analyze`
- `POST /api/cases/{case_id}/live-room/evidence-analysis/confirm`
- `POST /api/cases/{case_id}/live-room/session-event`
- `WS /api/live-room/voice`

## 4. Integrity and privacy boundaries

- A draft case is created before any capture; files are not held in a temporary client-only queue.
- The frontend shows a saved state only after the API returns successfully.
- Transcripts are user-reported speech. They are not evidence that the spoken claim is true.
- Images are user-selected. Per-image consent is required before external vision analysis.
- A user must review each extracted candidate before it can affect a route. The user may save a confirmed evidence fact without automatically overwriting case fields.
- AI image summaries and observations alone never influence routing.
- The app warns users not to share OTPs, UPI PINs, passwords, full card/bank details or other credentials.
- Browser camera and microphone require explicit permission on HTTPS or localhost. Screen sharing requires the user to choose a source; the app cannot silently view the screen.
- The default screen-share flow captures selected frames when requested. It is not continuous, automatic video understanding.
- Raw live microphone audio is streamed to Gnani for transcription; it is not stored as a raw recording by this flow. If the user wants an audio/video recording as evidence, they must explicitly record/import it, and the original file is stored in the case.

## 5. Configuration

Set these values in the server-side `.env` file only:

```dotenv
GNANI_API_KEY=your_gnani_key
GNANI_STT_MODEL=prisma-v2.5
GNANI_TTS_MODEL=timbre-v2.5

OPENAI_API_KEY=your_vision_and_translation_provider_key
BOLKE_MULTIMODAL_MODEL=gpt-6-astra
BOLKE_RESPONSES_API_URL=https://api.openai.com/v1/responses
BOLKE_LIVE_VISION_LIMIT_PER_MINUTE=8
```

The exact vision model must be available to the API account. If the account does not have access to the configured model, use a currently available image-capable Responses API model and set `BOLKE_MULTIMODAL_MODEL` accordingly. Never put provider keys in HTML, CSS or JavaScript.

To enable same-language guidance, the user must check **Enable same-language AI guidance** before starting the session. The consent scope is the generated guidance text only; images require a separate consent each time.

## 6. Automated validation

Latest run from the extracted source tree:

```text
PYTHONPATH=. python -m pytest -q
282 passed, 90 subtests passed

node --check frontend/app.js
node --check frontend/live-pcm-processor.js
python -m compileall -q backend tests scripts
```

The suite includes mocked provider-contract checks for image input, minimum case context, disabled API response storage, language translation, confirmation-only routing, case ownership, evidence confirmation and Gnani WebSocket proxy behaviour. These tests do not consume external API credits.

## 7. Manual end-to-end test still required

Browser navigation from the development container was blocked with `ERR_BLOCKED_BY_ADMINISTRATOR`, so camera, microphone and native screen-picker behaviour were not physically verified in this environment. Run `docs/LIVE_MULTIMODAL_MANUAL_TEST_2026-10-31.md` in Chrome or Edge on the user's machine.

A live provider check also remains necessary after the operator adds their own Gnani and vision-provider credentials. The release-readiness script still flags production hosting, authentication, privacy notice, monitored support route, persistent storage, backups/restore, security review and mobile/accessibility checks.
