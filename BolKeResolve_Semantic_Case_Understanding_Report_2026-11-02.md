# BolKeResolve — Semantic Case Understanding Upgrade

Date: 2 November 2026

## What changed

This upgrade addresses the underlying conversation-understanding problem rather than only repeated questions.

- Added an opt-in semantic interpreter for complete saved case conversations. It is designed for English, Hindi, Hinglish, Romanized Hindi, code-switching, disfluent speech and transcription mistakes.
- The interpreter classifies each new turn as an answer, new detail, correction, genuinely different issue, unrelated message or unclear turn.
- It proposes structured fact updates with exact evidence quotes from the user's saved conversation.
- The backend rejects candidate facts unless the quote is present in the saved user text, confidence meets the threshold, and the value passes a field-specific validator.
- New issue detection can reclassify a case (for example, an old marketplace refund case becoming a separate UPI transfer dispute) only when a quoted issue-family update from the latest turn is accepted. Old issue-specific facts are cleared unless they are re-established by the new conversation.
- The deterministic workflow remains responsible for stage progression, next questions, evidence requests and official support destinations. The model cannot invent a customer-care URL, deadline, phone number or escalation route.
- Added a constrained response composer that explains the workflow-selected step in straightforward, case-specific language.
- Added fallback from strict JSON Schema output to validated JSON when a configured model/provider combination does not support strict schema output.
- Added a reversible in-session AI case-understanding consent control and an explicit status indicating whether semantic interpretation was used for the latest response.
- Kept semantic case understanding consent separate from guidance translation consent and per-image visual-analysis consent.
- Updated the service-worker cache name to `bolkeresolve-shell-v33` so the frontend update is not hidden behind the previous shell cache.

## Configuration and operation

Semantic case understanding requires a server-side `OPENAI_API_KEY`, a supported model configured through `BOLKE_MULTIMODAL_MODEL`, and explicit user consent. The `.env.example` includes the configuration keys. The API key must remain server-side and must never be placed in frontend code.

At the start of Live Resolution, the user can enable "Let AI understand my case and personalise each response". During an active case, the user can also enable or disable this under **AI and privacy**. When disabled or unavailable, BolKeResolve uses the deterministic rule-based workflow and must not claim that semantic AI interpretation was used.

The semantic feature sends redacted saved typed/transcribed case text and minimum case facts to the configured provider. It does not send raw microphone audio or images through this feature. Visual evidence processing has separate per-image consent. Provider API data controls apply; do not describe this as a zero-retention configuration. Users should never provide OTPs, UPI PINs, passwords or full card details.

## Trust boundaries

- AI fact candidates are user-reported, not independently verified.
- Exact-quote validation establishes that the user said the supporting words; it does not prove the underlying claim is true.
- Official merchant and regulator routes remain selected from the reviewed support directory and deterministic workflow.
- The AI response composer may explain only the already-selected action or question.
- BolKeResolve does not access merchant/bank internal records or automatically submit complaints.

## Validation

- Full Python test suite: **315 tests passed**.
- JavaScript syntax check: passed (`node --check frontend/app.js`).
- Backend Python compilation: passed (`python -m py_compile backend/*.py`).
- Semantic interpreter tests cover structured-output fallback and rejection of unsupported/unquoted fact updates.
- Workflow integration tests cover natural-language refund answers, full-order scope, prior support status, different-issue reclassification and case continuity.

No authenticated external-model call or physical microphone/camera session was performed as part of this local test run. A real deployment still needs testing with the user's configured API credentials, selected model, browser, microphone, camera and persistent storage.
