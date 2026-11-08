**Current release update (4 November 2026):** The Product Research & Implementation Blueprint and subsequent UI/account pass have been applied. The latest corrective pass fixes the signed-in Guided Chat voice configuration mismatch, removes provider/deployment jargon from visitor-facing status, corrects the Live Resolution consent-control visibility/click-target behavior, replaces the technical start-screen note with plain language, and makes the photo-led homepage/issue picker visibly more distinctive. The shell cache is `bolkeresolve-shell-v47`. See [`FOLLOWUP_GUIDED_CHAT_AND_HOMEPAGE_FIX_2026-11-04.md`](FOLLOWUP_GUIDED_CHAT_AND_HOMEPAGE_FIX_2026-11-04.md), [`BLUEPRINT_IMPLEMENTATION_2026-11-04.md`](BLUEPRINT_IMPLEMENTATION_2026-11-04.md), and [`CHANGELOG_UI_ACCOUNT_REFRESH_2026-11-04.md`](CHANGELOG_UI_ACCOUNT_REFRESH_2026-11-04.md). Latest automated checks: **360 tests passed, 129 additional subtests passed**. Real browser rendering remains unverified because Chromium navigation is blocked in this execution environment.

# BolKeResolve

**Latest increment (31 October 2026): Live multilingual and evidence-aware guidance.** The Live Resolution Room can use the configured image-capable Responses API model for user-selected images after separate per-image consent, with minimum relevant user-reported case context. Model observations remain unverified candidates; only user-confirmed individual fields are allowed to influence the existing deterministic route. Generated guidance can be optionally translated into the session language; that same text is saved to the case timeline, shown in the guidance panel and passed to Gnani Timbre for read-aloud. No raw live audio is sent to the translation model. Continuous video understanding is not included. See [`docs/LIVE_MULTIMODAL_GUIDANCE_IMPLEMENTATION_2026-10-31.md`](docs/LIVE_MULTIMODAL_GUIDANCE_IMPLEMENTATION_2026-10-31.md) and [`docs/LIVE_MULTIMODAL_MANUAL_TEST_2026-10-31.md`](docs/LIVE_MULTIMODAL_MANUAL_TEST_2026-10-31.md). Latest suite: **282 tests passed, 90 subtests passed**; provider and physical browser checks remain outstanding.

## Live Resolution Room (31 October 2026)

The latest build creates a persistent draft case as soon as a Live Resolution session starts. Live speech turns, typed messages, server-generated guidance, session events and uploaded evidence are recorded in the existing case/timeline system. Camera photos, documents, imported recordings and user-selected screen captures are uploaded directly to that draft case. The print view can be saved as PDF, and the evidence ZIP contains the Resolution Passport JSON, a provenance/hash manifest and original files.

See `docs/LIVE_ROOM_END_TO_END_SMOKE_TEST.md` for the complete manual verification sequence and important capability boundaries. Live Prisma requires a valid server-side `GNANI_API_KEY`; no provider secret belongs in browser code.

# BolKeResolve — local MVP

## Great Indian AI Internship Challenge (Gnani AI), 2026

This project is being prepared as **BolKeResolve: Hinglish Voice-to-Resolution Passport**. The app has server-side integration adapters for Gnani AI Prisma v2.5 speech-to-text and Timbre v2.5 text-to-speech. In a challenge demo, show a real successful API call; the included automated tests use mocked provider responses and do not verify the live service.

Start here: [`START_HERE_GNANI_AI_CHALLENGE_2026.md`](START_HERE_GNANI_AI_CHALLENGE_2026.md). The challenge folder in `docs/challenge/` contains the submission explanation, 60-second demo plan, public post draft, current-rules checklist, interview prep and source notes. Official challenge page: https://www.gnani.ai/internship. Recheck the official rules before submitting.


**Focused core increment (22 October 2026):** New-case creation is now a two-step flow—tell the story/get the first suggestion, then review and save. Three common issue paths are visible up front while less-common types remain available. The existing concise saved-case view and optional guided chat are preserved. See [`docs/FOCUSED_CORE_PRODUCT_SCOPE_2026-10-22.md`](docs/FOCUSED_CORE_PRODUCT_SCOPE_2026-10-22.md).

**Latest UX increment (22 October 2026): Voice-First Guided Chat + Case-Specific Support.** Guided chat now includes voice capture with a 10-language selector when Gnani is configured, transcript review before send, read-aloud controls, official support destinations tailored to the reported merchant/issue, and clearer support-route cards in saved cases. The first-pass Resolution Sprint, Resolution Passport and optional Meta/Twilio adapters remain intact. See [`START_HERE_RESOLUTION_PASSPORT.md`](START_HERE_RESOLUTION_PASSPORT.md) and [`docs/VOICE_FIRST_CASE_SPECIFIC_SUPPORT_2026-10-22.md`](docs/VOICE_FIRST_CASE_SPECIFIC_SUPPORT_2026-10-22.md).
See [`docs/CASE_WORKSPACE_VISUAL_REFRESH_2026-10-20.md`](docs/CASE_WORKSPACE_VISUAL_REFRESH_2026-10-20.md) for the latest Prep Kit and Activity timeline layout changes, research benchmark, and desktop/mobile QA notes.

BolKeResolve is deliberately a focused, voice-first helper for everyday Indian payment and refund problems. A user explains the issue in familiar words, reviews the facts, receives one source-backed next step, and may save a concise **Resolution Passport** to carry the important details into the appropriate support channel. It is not a full complaint platform, public complaint marketplace or automatic filing service. See [`docs/FOCUSED_CORE_PRODUCT_SCOPE_2026-10-22.md`](docs/FOCUSED_CORE_PRODUCT_SCOPE_2026-10-22.md) for the scope guardrails. WhatsApp is an optional handoff—not a requirement for the core product. The case can be carried out through a JSON export, print/save-as-PDF, or a user-controlled WhatsApp/email draft. The case workspace deliberately avoids implying that payment records have been independently verified. See `ASSET_CREDITS.md` for photo sources and licensing notes.

See [`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md) for the current verified test status, the live-provider items still unverified, and production-readiness gaps.

**New product upgrade (22 October 2026): Interactive Sample Case + deep research.** The homepage now lets visitors compare two fictional, read-only journeys (failed UPI payment and delayed merchant refund) using the same source-backed resolution preview as intake. The demo does not save a case or claim any payment/complaint action. See [`docs/PRODUCT_RESEARCH_AND_CHALLENGE_UPGRADE_2026-10-22.md`](docs/PRODUCT_RESEARCH_AND_CHALLENGE_UPGRADE_2026-10-22.md) for differentiation strategy, the 90-day roadmap, challenge demo plan, release gates and 189 research references.

**Follow-through upgrade (22 October 2026): Evidence Provenance + Reply Review.** Case facts and uploads now carry explicit source/verification labels. Users can paste a support reply for a deterministic, privacy-conscious preview, review its possible meaning and explicitly save only the interpretation to their timeline. This does not verify the sender or organisation action. See [`docs/EVIDENCE_PROVENANCE_AND_REPLY_REVIEW_2026-10-22.md`](docs/EVIDENCE_PROVENANCE_AND_REPLY_REVIEW_2026-10-22.md).

**Latest increment (29 October 2026): usable email-reply fallback.** The case panel now supports paste-and-review of a support email even when automatic inbound email is not configured. The preview stores no raw reply; after user confirmation, only the interpretation and optional reference are added to the timeline. Automatic forwarding remains separately disabled until an inbound domain/provider, stable encryption key and authenticated webhook are configured. See [`docs/LIVING_RESOLUTION_PASSPORT_AND_CASE_INBOX_BRIDGE_2026-10-23.md`](docs/LIVING_RESOLUTION_PASSPORT_AND_CASE_INBOX_BRIDGE_2026-10-23.md) for the manual flow and provider setup.
See [`docs/PRODUCT_STRATEGY_RESET_AND_COMPETITIVE_RESEARCH_2026-10-21.md`](docs/PRODUCT_STRATEGY_RESET_AND_COMPETITIVE_RESEARCH_2026-10-21.md) for the competitive research and why the product is centred on the Resolution Passport rather than requiring WhatsApp.
See [`docs/UX_MESSAGE_REFRESH_2026-10-20.md`](docs/UX_MESSAGE_REFRESH_2026-10-20.md) for the comparative UX benchmark and design changes in the latest pass.

**Latest product increment (29 October 2026): Reply-Aware Resolution Completion Loop.** A user-confirmed support reply now updates the primary next action according to its provisional category—information requested, refund initiated, credit claimed, waiting, under review, rejection, mixed/ambiguous reply or a potentially unsafe credential request. The normal reply-review flow stores its short interpretation/category rather than raw pasted reply text. A reply saying “initiated” does not equal credit; a “credited” claim asks the user to check their own account. This is deterministic, requires user review and does not authenticate the sender or verify external status. See [`CHANGELOG_REPLY_AWARE_COMPLETION_LOOP_2026-10-29.md`](CHANGELOG_REPLY_AWARE_COMPLETION_LOOP_2026-10-29.md) and [`docs/research/BOLKERESOLVE_DEFENSIBILITY_AND_FINAL_POLISH_2026-10-29.md`](docs/research/BOLKERESOLVE_DEFENSIBILITY_AND_FINAL_POLISH_2026-10-29.md).

**Latest product increment (29 October 2026): Condition-Aware Commitment Reconciliation.** The existing case workspace can now record a reviewed support statement, the condition that may start its clock, the stated timeframe, and later updates that support, qualify, supersede or contradict it. The clock remains unset until a user records a trigger and date; business-day estimates exclude weekends only. Negations and “unless” exceptions require manual review. This is a deterministic candidate extractor—not a source-authentication system or a promise-understanding LLM. The original statement is retained alongside later events, and the portable passport includes the record. See [`CHANGELOG_CONDITION_AWARE_COMMITMENT_RECONCILIATION_2026-10-29.md`](CHANGELOG_CONDITION_AWARE_COMMITMENT_RECONCILIATION_2026-10-29.md) and [`docs/research/BOLKERESOLVE_CONDITION_AWARE_COMMITMENT_IMPLEMENTATION_REPORT_2026-10-29.md`](docs/research/BOLKERESOLVE_CONDITION_AWARE_COMMITMENT_IMPLEMENTATION_REPORT_2026-10-29.md). Latest checks: **253 tests passed, 90 subtests passed**. Full browser visual/interaction QA and production readiness remain outstanding.

## Features

- Simplified responsive homepage with one clear primary action, three common payment paths up front, secondary issue types kept behind a disclosure, and a compact three-step explanation; choosing an issue preselects it in the intake flow.
- Voice capture in the browser and a real Gnani Prisma v2.5 REST transcription call when `GNANI_API_KEY` is configured.
- A compact native-script language chooser for ten STT language codes, replacing the default-style dropdown. The choice still needs to match the language you speak; this UI does not claim automatic spoken-language detection.
- Optional read-aloud using the Gnani Timbre v2.5 REST endpoint.
- Editable voice transcript or typed complaint. After voice transcription, a conservative extraction layer proposes the issue type, known merchant/app, amount, payment date, payment status and support-contact status, then fills only untouched/default fields. The user can review and apply competing suggestions; multiple amounts are flagged instead of guessed, and dates without a year are marked for confirmation.
- SQLite-backed case creation, case list, case details and timeline, with progress states that are explicitly labelled user-reported and a case deletion action that also removes stored evidence files when possible.
- A deterministic resolution playbook for common payment issues, with official NPCI, RBI, National Consumer Helpline, e-Jagriti and cybercrime sources linked beside relevant steps.
- A persistent Prep kit with category-specific evidence checklists, a completion/readiness indicator, action-pack export/copy, and user-managed follow-up date and note. These reminders appear in the case; they do not send push notifications or contact companies.
- **Resolution Passport:** portable versioned JSON export, standalone printable passport (browser Print / Save as PDF), outcome reporting, and a privacy-conscious service-worker shell. API responses, cases, evidence, auth data and provider callbacks are never cached offline.
- An editable and saveable support draft tailored to refund, failed/pending UPI, duplicate-charge, amount-discrepancy, undelivered-order and suspected-fraud cases. It includes only known case facts, omits unknown dates/amounts, and asks the organisation issue-specific questions. User-edited messages are saved to the case and activity timeline; saving does not send the message.
- A pre-save resolution preview that identifies missing facts and asks a clarifying question where useful. It does not query a bank or payment network.
- Best-effort server-side redaction of obvious OTP/PIN/passwords, labelled Aadhaar/PAN/account/mobile details and Luhn-valid payment-card numbers in submitted text, plus redaction of sensitive-looking filenames. This is not a guarantee. An explicit user-triggered evidence review can run bounded local OCR/text extraction on uploaded image/PDF files; only structured candidate facts are persisted, and users must confirm all use.
- **Living Resolution Passport / Evidence Review:** `Check details` locally extracts candidate merchant, amount, date and status wording from an uploaded image/PDF, highlights possible mismatches, and lets the user confirm document-derived facts and separately choose which values update the case. Exported passports include this source trail and continue to label evidence as not independently authenticated.
- **Case reply import / optional Case Inbox Bridge:** the panel now works even without an email provider: paste a support email, preview a cautious interpretation and confirm only the short summary to the case timeline. The raw pasted reply is not saved by the preview/confirm API. Automatic forwarding to a random case-specific alias remains disabled until a receiving domain, DNS/MX provider routing, stable encryption key and authenticated webhook are configured. The system does not import attachment bytes, verify sender identity, send mail or contact a merchant. Setup and limits: [`docs/LIVING_RESOLUTION_PASSPORT_AND_CASE_INBOX_BRIDGE_2026-10-23.md`](docs/LIVING_RESOLUTION_PASSPORT_AND_CASE_INBOX_BRIDGE_2026-10-23.md).
- Optional upload for PNG/JPG/WEBP/PDF evidence, with extension/signature checks, an 8 MB per-file limit, ten-file and 40 MB per-case caps. Signature checks are not malware scanning.
- Support-request drafting in English, Hindi or Hinglish, context chips outside the copied message, copy-to-clipboard, read-aloud through Timbre and personal notes on a case timeline. Hindi/Hinglish templates and source-story translation still need native-speaker QA.
- Optional production-mode account sign-in, password hashing, revocable server-side sessions, request-origin checks, per-account case/evidence access controls, and password-confirmed self-service account deletion for active application records.
- API responses use `Cache-Control: no-store` so account, case, evidence metadata, and provider event payloads are not retained by browser/shared caches.
- Per-IP in-process voice API throttling to guard against accidental request loops and unexpected paid-model usage; a shared production gateway quota is still required for multiple workers.
- A voice-first, WhatsApp-style guided chat inside the website. Users can select an issue, speak or type, choose among ten Indian-language STT codes when Gnani is configured, review the transcript before sending, hear responses through the browser speech-synthesis API where voices are available, and save a case through the same case API. This is an in-site chat, not a claim of an external WhatsApp connection.
- Curated, case-specific official support destinations for supported merchants and general official routes (NCH, NPCI and cybercrime), surfaced both in the guided-chat result and saved-case overview. Urgent suspected-fraud routing is presented first; unknown merchant contacts are never invented. User-controlled handoff buttons open WhatsApp with the reviewed draft or open an email draft. The app does not choose the recipient, send automatically, or claim delivery through these handoffs.

## Resolution Passport — no messaging API required

The core case workflow is designed to remain useful even if Meta or Twilio is not configured. The user's case is the system of record; WhatsApp is only one optional way for a person to hand off a reviewed message. See [`docs/RESOLUTION_PASSPORT_AND_NO_API_HANDOFF.md`](docs/RESOLUTION_PASSPORT_AND_NO_API_HANDOFF.md) for the complete workflow, export fields, provenance rules, manual QA checklist and production gates.

New routes: `GET /api/cases/{case_id}/passport.json` downloads a structured, versioned passport; `GET /api/cases/{case_id}/passport/print` opens a self-contained print page; and `PUT /api/cases/{case_id}/outcome` records a user-reported outcome. Outcome values remain explicitly self-reported. The printable passport is generated as HTML and saved to PDF by the user's browser; no PDF is generated or stored on the server.

The website is installable as a PWA on compatible browsers. The service worker caches only an allow-listed public UI shell; every `/api/` route is network-only. Case records and uploaded evidence are **not available offline**. This is intentional to avoid caching private case information on shared devices.

Run `python scripts/check_release_readiness.py` to check configured origin, authentication, privacy/support paths and provider readiness without printing secrets. The script cannot validate live TLS, volume persistence, provider credentials, external service behavior or legal/security readiness.

## Photo handling

Most lifestyle/scenario image sources in the HTML use selected Pexels stock photographs. The BolKeResolve guide character is an original AI-generated illustration served locally from `frontend/assets/bolke-guide.webp` and `frontend/assets/bolke-guide-avatar.webp`. If that remote image host fails or is blocked, the page uses a local visual fallback from the design exploration so the layout does not collapse into an empty box. The fallback images are not the sourced stock photographs; on a connected browser the page attempts to display the Pexels sources first. For a production deployment, consider storing properly downloaded copies of the selected Pexels photographs locally and keeping their source/license record from `ASSET_CREDITS.md`. Pexels says the images are free for commercial use under its license, but product imagery must not imply endorsement by the people pictured.

## Run on Windows

1. Extract the ZIP to a normal folder, for example `D:\Projects\BolKeResolve_MVP`.
2. Install Python 3.10+ if it is not already installed.
3. Double-click `run_windows.bat`. The first run creates a virtual environment, installs dependencies and copies `.env.example` to `.env` if needed.
4. The supplied local configuration enables visible **Sign in / Sign up** and requires sign-in before private cases/evidence are saved. Create an account from the header. Local signup works without SMTP; email verification is mandatory only when `BOLKE_EMAIL_VERIFICATION_REQUIRED=true` or in production. Use a unique password of at least 12 characters.
5. Open `http://127.0.0.1:8000` in Chrome. On an existing installation, check `.env`: set `BOLKE_ACCOUNTS_ENABLED=true` and `BOLKE_AUTH_REQUIRED=true`, then restart the server to make account sign-in mandatory for private case storage. Do not overwrite an existing `.env` blindly because it may contain provider credentials.
6. To enable Gnani speech services, edit `.env`, add your key after `GNANI_API_KEY=`, save and restart the server. Get API access from the [Gnani API platform](https://app.gnani.ai/). Keep the key on the server and never put it in frontend files or commit `.env` to GitHub.
7. Run the checks with `python -m pytest -q` and `node --check frontend/app.js`.

The typed workflow, guided playbooks and WhatsApp-style in-browser intake work without a Gnani key. Voice transcription and spoken output require a valid key, account access and available credits; this environment did not have the user's key, so live audio has not been verified here. Timbre v2.5 defaults now use the voice catalog documented by Gnani for each selected language (including `hi-en` / `Poorvi` for Hinglish).

## Optional messaging integrations (not required for core product)

Use [`docs/WHATSAPP_INTEGRATION_GUIDE_2026-10-21.md`](docs/WHATSAPP_INTEGRATION_GUIDE_2026-10-21.md) as the current source of truth for Meta setup, API credentials, the low-cost testing path, current pricing caveats, privacy/legal launch gates, deployment and troubleshooting. The older [`docs/WHATSAPP_LAUNCH_PLAYBOOK.md`](docs/WHATSAPP_LAUNCH_PLAYBOOK.md) remains useful background but is superseded where details differ. The `frontend/privacy.html` page is a **draft template**, not a publish-ready legal notice: replace every bracketed placeholder and configure a real monitored support contact before live use. `scripts/check_whatsapp_config.py` checks whether the environment variables are present without printing secret values; it does not send a message or verify the credentials with Meta.

### Meta Cloud API adapter (optional; account setup required)

The website includes an **in-site chat-style intake** that can save a normal BolKeResolve case in the same case store. It is not itself a live WhatsApp conversation. When WhatsApp is not configured, the CTA now directs users to the on-site flow instead of failing silently. The cloud webhook bot is optional. For a prepared support message, the user can open WhatsApp with the reviewed draft using a user-controlled click-to-chat handoff; this does not deliver a message to BolKeResolve or track its status. The app does not pretend a click-to-chat handoff is a connected bot.

The backend now includes a two-way WhatsApp Cloud API foundation: webhook challenge verification, HMAC signature validation, message-ID deduplication, explicit `START` consent and `STOP` opt-out, case creation only after `SAVE`, one-time case pairing, user-reported case updates, native interactive reply buttons, opt-in voice-note transcription through Gnani Prisma, tracked outbound conversation receipts, and an optional reminder worker that uses an approved template. Live use is **not active until** you configure a Meta app / WhatsApp Business Account, deploy to a publicly reachable HTTPS origin, configure the server-side secrets below, and subscribe the business account's `messages` webhook. Never put these settings in frontend files or commit `.env` to source control.

Required server-side variables for live messaging: `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_APP_SECRET`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_PHONE_ENCRYPTION_KEY`, and `WHATSAPP_BUSINESS_NUMBER`. `WHATSAPP_GRAPH_API_VERSION` is configurable. Follow `docs/WHATSAPP_LAUNCH_PLAYBOOK.md` for the complete setup, test, production and cost-control checklist; `docs/ADAPTIVE_INTAKE_AND_WHATSAPP.md` explains the product workflow. If you want automatic follow-up reminders outside the customer-service window, also configure an approved `WHATSAPP_REMINDER_TEMPLATE_NAME` and language, then schedule `run_whatsapp_reminders.bat` with Task Scheduler. A Graph API acceptance is not proof that a message was delivered or read. Refer to Meta's [WhatsApp Cloud API documentation](https://developers.facebook.com/docs/whatsapp/cloud-api/overview). Do not use unofficial WhatsApp Web automation.

### Twilio WhatsApp Sandbox adapter (optional development channel)

This build adds a second provider adapter for development while preserving the Meta Cloud API route and the same case engine/database. See [`docs/TWILIO_SANDBOX_PHASE1.md`](docs/TWILIO_SANDBOX_PHASE1.md) for the step-by-step setup. The Twilio adapter supports inbound text, `START`/`STOP`, story review, `SAVE`, status/update commands and provider delivery callbacks. It validates Twilio webhooks with Twilio's official Python SDK request validator. Twilio Sandbox replies use plain text; the Meta-only native buttons and Gnani voice-note media download remain unchanged.

Set `BOLKE_WHATSAPP_PROVIDER=twilio` in `.env` while doing Twilio sandbox development, then set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM`, `TWILIO_WEBHOOK_PUBLIC_URL`, and optionally `TWILIO_STATUS_CALLBACK_URL`. Also keep the common phone-encryption, real privacy-notice and monitored support contact settings configured. The preference disables the Meta-only reminder worker during Twilio tests; inbound replies always go through the provider which received the message. Do not put credentials in frontend files, Git, screenshots or chat. Install new dependencies with `python -m pip install -r requirements.txt`.

The Twilio Sandbox is testing/discovery only and is not a production sender. Every test participant must join your sandbox, and the join/session expires after three days. It has pre-approved-template restrictions for business-initiated messages and Twilio's normal WhatsApp pricing applies beyond any trial units. This does not bypass Meta/WhatsApp policies or unlock a restricted Meta account. See [Twilio's official Sandbox documentation](https://www.twilio.com/docs/whatsapp/sandbox).

New routes: `POST /api/webhooks/twilio/whatsapp` receives signed form-encoded inbound messages and `POST /api/webhooks/twilio/whatsapp/status` receives signed delivery status callbacks. Configure the exact public HTTPS callback URL in Twilio; signature validation is fail-closed and should never be disabled. This first phase intentionally does not process Twilio media/voice notes or route scheduled templates through Twilio.

## Live Resolution Room (31 October 2026)

The new **Live resolution** view adds a voice-first session to the existing product. It is not a separate case store: after the first user utterance or typed message, the app creates or updates the existing case and writes live conversation turns, server-authored guidance, evidence references and session lifecycle events to the existing case timeline. Photos, PDFs, audio and video use the existing case-scoped evidence table and evidence directory. Confirmed OCR facts remain attached to their source evidence and retain the existing provenance controls.

- Live voice: browser microphone → local AudioWorklet resampling → same-origin `WS /api/live-room/voice` → Gnani Prisma realtime STT. Configure `GNANI_API_KEY` in the server-side `.env`; the key is never placed in browser code.
- Camera: optional browser permission, local preview and explicit photo capture. Camera frames are not streamed to a vision model in this build.
- Documents: PNG/JPG/WEBP/PDF upload uses the existing OCR/text review and explicit confirmation flow.
- Screen: `getDisplayMedia()` requires a user gesture and browser permission; the user can save a still image from the selected screen. No continuous screen monitoring is performed.
- Recordings: user-imported audio can be preview-transcribed by Gnani and the transcript is saved only after user confirmation. Short camera/mic WEBM clips and supported audio/video files are retained as case evidence. A video clip is not automatically analysed in this build.
- Guidance: the existing deterministic source-backed resolution playbooks create the first-pass next action. The app records that text as generated guidance rather than an external organisation response. It does not verify payment rails, bank records or merchant systems.

Important language limit: Prisma can transcribe supported Indian languages, but the deterministic resolution playbook's guidance text is English in this build. Timbre can speak text using a selected voice; selecting Hindi does not translate English guidance into Hindi. A grounded translation/reasoning model needs to be connected and tested before promising fully same-language generated guidance. This version should be described as an Indian-language live speech intake with source-backed English first-pass guidance, not a full multilingual autonomous agent.

See [`docs/LIVE_RESOLUTION_ROOM_IMPLEMENTATION_2026-10-31.md`](docs/LIVE_RESOLUTION_ROOM_IMPLEMENTATION_2026-10-31.md) for architecture, permission behaviour, persistence, setup and limitations. For local Windows setup, run `run_windows.bat`; it copies `.env.example` to `.env` on first launch. Add your own `GNANI_API_KEY` and restart to enable live speech. The app runs locally at `http://127.0.0.1:8000` by default.

## API routes

- `GET /api/health` — service readiness and honest integration/configuration flags
- `GET /api/config` — public UI configuration only
- `GET /api/auth/me`, `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout` — production-mode account flows
- `POST /api/voice/transcribe` (multipart `audio_file`, `language_code`; returns transcript plus reviewable `extracted_facts`)
- `POST /api/voice/speak` (JSON `text`, `language_code`, optional matching v2.5 `voice`)
- `WS /api/live-room/voice?language_code=...` — same-origin proxy to Gnani Prisma realtime streaming STT
- `POST /api/cases/{case_id}/live-room/turn` — persist a user turn and recalculate the existing resolution plan
- `POST /api/cases/{case_id}/live-room/guidance` — store server-authored guidance from the deterministic playbook
- `POST /api/cases/{case_id}/live-room/session-event` — store live-room start/end in the case timeline
- `POST /api/resolution/preview` — classify and preview a source-linked deterministic playbook
- `GET /api/cases`, `POST /api/cases`, `GET /api/cases/{case_id}`
- `POST /api/cases/{case_id}/evidence`
- `GET /api/shared-intake/preview` / `POST /api/shared-intake/attach` / `DELETE /api/shared-intake/discard` — fixed-path share-to-case routes; one-time capability is carried in `X-Share-Intake-Token`, and case ID/options for attach are in JSON body
- `POST /api/cases/{case_id}/evidence/{evidence_id}/review` / `POST /api/cases/{case_id}/evidence-review/confirm` — candidate fact extraction/review and explicit confirmation
- `POST /api/cases/{case_id}/inbox`, `GET /api/cases/{case_id}/inbox`, `POST /api/cases/{case_id}/inbox/rotate` — optional per-case forwarding alias
- `POST /api/cases/{case_id}/inbox/messages/{inbound_id}/preview` / `/confirm`, `DELETE /api/cases/{case_id}/inbox/messages/{inbound_id}` — user-reviewed reply interpretation and discard
- `POST /api/webhooks/inbound-email` — authenticated provider-parsed inbound email webhook
- `POST /api/cases/{case_id}/draft` — prepare a support message
- `PUT /api/cases/{case_id}/draft` — edit and save the draft (not sent)
- `GET /api/cases/{case_id}/action-pack` — get an export-ready summary, case-specific checklist and source links
- `GET /api/cases/{case_id}/passport.json` — download the versioned, portable Resolution Passport JSON
- `GET /api/cases/{case_id}/passport/print` — open a no-store, self-contained print page for browser PDF export
- `PUT /api/cases/{case_id}/outcome` — save a user-reported outcome and append a provenance-labelled timeline event
- `PATCH /api/cases/{case_id}/checklist/{task_key}` — save a checklist item state
- `PUT /api/cases/{case_id}/follow-up` — save/clear a user-managed follow-up date and note
- `POST /api/cases/{case_id}/timeline`
- `POST /api/cases/{case_id}/events` — append a user-reported lifecycle event (contacted support, reply received, still waiting, resolved, etc.)
- `POST /api/cases/{case_id}/whatsapp-link` — create a short-lived, single-use code to pair this case with the configured WhatsApp contact
- `GET /api/webhooks/whatsapp` and `POST /api/webhooks/whatsapp` — Meta webhook challenge and signed inbound-message processing
- `POST /api/webhooks/twilio/whatsapp` — signed Twilio Sandbox text-message ingress
- `POST /api/webhooks/twilio/whatsapp/status` — signed Twilio delivery status callback
- `PATCH /api/cases/{case_id}/progress` — updates a clearly user-reported status
- `DELETE /api/cases/{case_id}` — deletes the case and its locally stored evidence
- `GET /api/cases/{case_id}/evidence/{evidence_id}`

## Vercel launch configuration (4 November 2026)

The recommended hosting shape is a static Vercel frontend with the FastAPI backend on Render using the persistent disk in `render.yaml`. The root `vercel.json` serves `frontend/` and reverse-proxies same-origin `/api/*` requests to the Render service. Do not host the current SQLite/local-evidence backend as a Vercel Function: the Vercel function filesystem is not durable.

See [`VERCEL_DEPLOYMENT_GUIDE.md`](VERCEL_DEPLOYMENT_GUIDE.md) for exact Vercel/Render setup, server-side environment variables, Preview testing and the production acceptance checklist. Replace the default Render origin in `vercel.json` if Render assigns a different service URL. The Vercel Preview must pass account, upload, export and Live Resolution WebSocket tests before production. The current privacy notice still contains operator/legal placeholders; production preflight correctly blocks launch until it is completed and reviewed.

## Gnani API connection

This build uses the documented Prisma endpoint `POST https://api.vachana.ai/stt/v3` with the `X-API-Key-ID` header, and the Timbre endpoint `POST https://api.vachana.ai/api/v1/tts/inference` with `model: timbre-v2.5`. See the [Prisma STT REST docs](https://docs.gnani.ai/api/STT/speech-to-text) and [Timbre TTS REST docs](https://docs.gnani.ai/api/TTS/tts-inference). Live calls could not be tested in this packaged environment because it does not have a user API key. Add your own valid key and test with synthetic audio before relying on the result.

Voice endpoints are throttled in-process by source IP: 8 STT calls/minute and 20 TTS calls/minute by default (`BOLKE_STT_LIMIT_PER_MINUTE`, `BOLKE_TTS_LIMIT_PER_MINUTE` can adjust the thresholds). This is a prototype guard, not a shared multi-worker or infrastructure quota.

## Local vs production mode, and security limits

This remains an MVP, **not a production finance service**. It does not independently verify bank transactions, determine whether a refund has actually been credited, contact merchants or banks, or receive real company replies. It records user-provided statements and treats uploaded evidence as unverified.

The Windows launcher binds to `127.0.0.1` and runs in local development mode. The current `.env.example` enables accounts and sets `BOLKE_AUTH_REQUIRED=true`, so the local app asks users to sign in before accessing or saving private cases. Account registration and login work locally without SMTP when email verification is not enabled. For a temporary guest-only demo, an operator can set `BOLKE_AUTH_REQUIRED=false`; in that mode, anonymous cases are stored in a shared local guest workspace and must contain synthetic/redacted test data only. Existing `.env` files are not overwritten by the launcher, so update the setting manually on an older installation.

For a hosted deployment, configure HTTPS first, set `BOLKE_ENV=production`, and set `BOLKE_PUBLIC_ORIGIN` to the exact public origin (e.g. `https://your-domain.example`). Production mode automatically requires authentication, uses `Secure`/`HttpOnly`/`SameSite=Lax` session cookies, hashes passwords with PBKDF2, stores only hashed session tokens, rate-limits account endpoints, applies request-origin checks for mutating APIs, and scopes case/evidence access to the authenticated account. Accounts require a password of at least 12 characters. Do not override production mode's authentication or secure-cookie protections.

Email verification and password reset are now implemented when SMTP is configured; production mode requires verification and refuses registration when a trusted HTTPS origin and TLS-protected SMTP delivery are not configured. Account security also includes session listing/revocation and password change. MFA/passkeys are not yet implemented. Passwords use PBKDF2-HMAC-SHA256 with 600,000 iterations (and legacy hashes are upgraded after successful sign-in); evaluate a managed identity provider or Argon2id-backed migration before a larger public launch. Account deletion removes active account/case/evidence and linked WhatsApp contact records, but cannot recall downloaded/exported copies, data already sent to external providers, or host backups. Configure and test backup/retention policies, shared rate limiting/usage quotas for paid AI endpoints, a real malware-scanning strategy for uploads, monitoring, dependency scanning, external penetration testing, privacy/legal review and HTTPS deployment/reverse-proxy settings. `scripts/check_release_readiness.py` checks configured values but cannot test live mail delivery, TLS, provider behavior, restore procedures or legal/security readiness. Sensitive-text detection is best-effort; ordinary form scrubbing does not OCR images/PDFs. Share-export redaction is a best-effort text transformation, not DLP, and does not alter original media. File-signature checks are not malware scanning. Local evidence is stored in `runtime/evidence`; SQLite is stored in `runtime/`. The current SQLite-backed project does not have PostgreSQL Row Level Security; the API enforces owner access on each protected resource request.

Never collect OTPs, UPI PINs, passwords, full card details or Aadhaar/PAN for this workflow. Before connecting real banking data or a public support channel, use a compliant source, obtain clear user consent, and complete a security and legal review.

## Data reset

Stop the server and delete the `runtime` folder to remove local cases and uploaded evidence. Keep secrets out of the source code.


## Reminder delivery tracking

Follow-up reminders remain opt-in. A reminder is sent only when the WhatsApp Cloud API is configured, the contact has opted in and linked the case, and an approved utility template is configured. Schedule `run_whatsapp_reminders.bat` with Windows Task Scheduler or run `python scripts/send_whatsapp_reminders.py` manually. The worker uses a per-follow-up lease to avoid duplicate sends from overlapping runs.

The signed `/api/webhooks/whatsapp` endpoint also consumes Meta delivery receipts for tracked reminders and case-linked conversation replies and records provider-reported `sent`, `delivered`, `read`, or `failed` states in the case timeline. API acceptance is not delivery confirmation; provider receipts are not proof that the user acted on the message. Live behavior requires a public HTTPS deployment and real Meta configuration.


WhatsApp deployment and launch checklist: [`docs/WHATSAPP_LAUNCH_PLAYBOOK.md`](docs/WHATSAPP_LAUNCH_PLAYBOOK.md).


Resolution Passport usage and QA: [`docs/RESOLUTION_PASSPORT_AND_NO_API_HANDOFF.md`](docs/RESOLUTION_PASSPORT_AND_NO_API_HANDOFF.md).

## Frontend visual alignment pass — 23 October 2026

The latest pass fixes alignment across Guided Chat, the fictional sample-resolution demo, and the saved-case secondary workspaces while preserving the existing visual identity. It keeps case navigation visible when a secondary panel is active, aligns case headings/support cards to a shared grid, equalises demo-card behaviour, and adds sticky-header-aware anchor offsets and reduced-motion-safe transitions. See [`docs/FRONTEND_LAYOUT_POLISH_AND_DESIGN_RESEARCH_2026-10-23.md`](docs/FRONTEND_LAYOUT_POLISH_AND_DESIGN_RESEARCH_2026-10-23.md). The test suite passes, but a local Chromium visual pass is still required because browser navigation is blocked in this build environment.


## Next-feature research (23 Oct 2026)

See `FEATURE_OPPORTUNITY_RESEARCH_README.md` and `docs/research/FEATURE_OPPORTUNITY_RESEARCH_2026-10-23.md` for the ranked, source-backed roadmap. This research-only package does not alter application behavior.

## Share-to-Case and official resolution rules (23 October 2026)

The Share-to-Case token is placed in the URL fragment, scrubbed by an early same-origin head script, and sent only in `X-Share-Intake-Token`. Shared-intake API URLs are constant; attach case ID/options live in a validated JSON body.

The project includes an optional PWA Share Target, a reviewed snapshot matcher for selected entries in the National Consumer Helpline convergence directory, and versioned source-backed resolution metadata. Shared items are encrypted temporarily and are never attached to a case before a user confirms the action. The support-directory snapshot is not live and does not file a complaint. No bank or NPCI transaction access is claimed.

Configure `BOLKE_SHARE_INTAKE_ENCRYPTION_KEY` on production deployments and use the bounded retention/throttle settings documented in `.env.example`. See `CHANGELOG_SHARE_TO_CASE_ROUTEBOOK_2026-10-23.md` for security behaviour and remaining production validation. Native Share Target requires a supported installed PWA/browser; normal evidence upload remains available.

## Product foundation increment (3 November 2026)

This increment adds an append-only case fact history with source provenance, explicit evidence-to-claim relationships (`supports`, `contradicts`, `context`), and a user-reviewed CSV reconciliation import for payment/settlement reports. A CSV is retained as original evidence, its recognised columns and rows are previewed, and selected rows are stored only after an explicit user confirmation. Importing or confirming a report does **not** automatically change case amount, payment status, settlement status or workflow facts. See [`docs/PRODUCT_FOUNDATION_AND_RECONCILIATION_2026-11-03.md`](docs/PRODUCT_FOUNDATION_AND_RECONCILIATION_2026-11-03.md), [`docs/PRODUCT_FOUNDATION_IMPLEMENTATION_REPORT_2026-11-03.md`](docs/PRODUCT_FOUNDATION_IMPLEMENTATION_REPORT_2026-11-03.md), and [`docs/PRODUCT_FOUNDATION_ACCEPTANCE_TEST_2026-11-03.md`](docs/PRODUCT_FOUNDATION_ACCEPTANCE_TEST_2026-11-03.md).

The operator-only `GET /api/internal/quality/summary` endpoint exposes aggregate workflow quality events without conversation text, uploaded filenames, payment references or evidence content. Configure a long random `BOLKE_QUALITY_METRICS_TOKEN` in the server environment and send it in `X-Bolke-Metrics-Token`; without a configured token the endpoint is unavailable. Treat this as an internal diagnostic endpoint, not a public analytics API.

The Resolution Passport export is now format 1.5 and can include fact revisions, evidence claim links, the explicit `not_scanned` malware-scan status, and user-confirmed reconciliation rows. Evidence authenticity and malware scanning are not implied. CSV reconciliation is a user-controlled import, not a live Razorpay connection. A direct Razorpay integration requires an approved OAuth partner application and the merchant's explicit authorisation; no API credentials are collected in the browser and no account is simulated. See Razorpay's [OAuth partner flow](https://razorpay.com/docs/api/oauth/).

Current release checks: `python -m pytest -q` (360 passed, 129 subtests passed), `python -m compileall -q backend`, `node --check frontend/app.js`, `node --check frontend/sw.js`, and `python scripts/check_release_readiness.py`. The production preflight currently blocks on the draft privacy notice placeholders. SMTP delivery, the deployed Vercel API rewrite/WebSocket path, persistent-disk restore, malware scanning, and privacy/security/accessibility review still require operator verification. This is not a production-security certification.


## Blueprint implementation increment (4 November 2026)

This release applies the 4 November product blueprint to the supplied codebase without replacing the existing case-resolution engine. It adds a case workspace presentation for Live Resolution, readable capability/consent states, improved evidence previews and derivative review, append-only conversation correction history, case search/status filters and next-action/follow-up summaries. The case export now creates a structured PDF + ZIP dossier with a manifest, CSV indexes, fact history, chronological events, conversation transcript, derivative records and original files; it preserves the original evidence bytes and labels the package as a user-assembled record rather than a certified legal record. A selected-evidence share export supports best-effort redaction of text only.

Authentication updates include SMTP-backed email verification and password reset, single-use expiring action tokens stored as hashes, generic password-reset responses to avoid account enumeration, session listing/revocation, password change, persistent SQLite sign-in rate limiting, a 600,000-iteration PBKDF2-HMAC-SHA256 setting and transparent upgrade of older PBKDF2 hashes after successful login. Production registration requires working email delivery configuration. This is still not MFA/passkey support or a managed identity-provider migration.

See [`CHANGELOG_BLUEPRINT_IMPLEMENTATION_2026-11-04.md`](CHANGELOG_BLUEPRINT_IMPLEMENTATION_2026-11-04.md) and [`BLUEPRINT_IMPLEMENTATION_2026-11-04.md`](BLUEPRINT_IMPLEMENTATION_2026-11-04.md) for what changed and the remaining deployment gates. The release was tested from a fresh extracted archive; local browser rendering, real SMTP delivery, malware scanning, private cloud object storage, backup restoration, production HTTPS, external penetration testing and India-specific privacy/legal review still require deployment/operator work.
