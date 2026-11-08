# Latest verified state — 4 November 2026 (Guided Chat voice, consent controls and homepage visual refresh)

- Fixed Guided Chat voice readiness for signed-in users in production. `/api/config` now follows the same authorization rule as `/api/voice/transcribe`: a configured `GNANI_API_KEY` enables voice for an authenticated user; `BOLKE_PUBLIC_VOICE_ENABLED` is required only for anonymous production voice use. The previous config response incorrectly applied the anonymous-use flag to signed-in users, producing a misleading red warning while Live Resolution voice remained available.
- Replaced provider/deployment-specific Guided Chat warning text with plain-language availability and recording status. Visitors no longer see API-key or environment-variable instructions.
- Corrected the two optional Live Resolution consent controls. The old CSS cascade forced a hidden label back into a grid, leaving a dead empty square. When the relevant feature is unavailable, the checkbox is hidden and a compact status message is shown. When configured, the native checkbox is enabled, the complete row is clickable, keyboard-operable and has a visible focus state.
- Important configuration distinction: `GNANI_API_KEY` enables speech transcription; the optional AI case-understanding and guidance-translation capabilities are backed by `OPENAI_API_KEY`. A Gnani key alone does not make those two AI consent options available. No fake consent toggle is shown for an unavailable service.
- Replaced the technical vendor explanation below the Live Resolution start action with a short user-facing privacy explanation. Camera and screen sharing remain off until the user chooses them.
- Added a final homepage stylesheet with a photo-led hero presentation, slow real-photo sequence, stronger deep-evergreen issue-selection section, higher-contrast issue cards, more prominent interaction states and responsive spacing. Existing credited imagery and local fallbacks are reused.
- Bumped the public service-worker shell cache to `bolkeresolve-shell-v47`, ensuring the corrected JavaScript, homepage styles and consent UI are fetched after the service worker updates.
- Verification: `python -m py_compile backend/main.py`, `node --check frontend/app.js`, and `python -m unittest discover -s tests` — **355 tests passed** at the implementation checkpoint; regression coverage includes authenticated/anonymous Guided Chat voice readiness, the consent hidden-state defect, visitor-facing copy and homepage stylesheet inclusion.
- Local HTTP health and stylesheet checks passed. Playwright Chromium navigation remains blocked by the execution environment (`ERR_BLOCKED_BY_ADMINISTRATOR`), so real-browser visual QA and physical microphone interaction have not been claimed as verified.
- Production still requires real SMTP delivery, HTTPS and trusted origin, malware scanning, private/durable object storage, backups/restore testing, MFA/passkey decision, independent security/privacy/legal review and real browser accessibility QA.

# Latest verified state — 31 October 2026 (Live multilingual and evidence-aware guidance)

- Added an optional, consent-gated multimodal assistance layer for Live Resolution. Selected JPG/PNG/WEBP evidence can be analysed with minimum relevant user-reported case context; PDFs continue through local OCR. AI observations remain candidates and do not affect routing until the user explicitly confirms individual fields.
- Generated deterministic next-step guidance can optionally be translated into the session language using the configured Responses API model. The translated wording is persisted in the existing case timeline, displayed in the guidance panel and passed to the existing Gnani Timbre speech endpoint. Translation is opt-in; raw live audio is not sent to the translation model.
- The current Gnani streaming WebSocket headers (`language_code`, `model`, `format`) are documented as supported by Gnani; the proxy keeps the key server-side. The API key must appear in the upstream Authorization/header only, never in browser code or the JSON model prompt.
- Provider notice now explicitly states that an image and its underlying claims are not independently authenticated. The related transport test verifies the credential is present only in the auth header and absent from the request JSON.
- Verification: `PYTHONPATH=. python -m pytest -q` — **282 passed, 90 subtests passed**; `node --check frontend/app.js`; `node --check frontend/live-pcm-processor.js`; `python -m compileall -q backend tests scripts` passed.
- Browser QA caveat: Chromium navigation to the local server was blocked in this environment (`ERR_BLOCKED_BY_ADMINISTRATOR`). Run the manual steps in `docs/LIVE_MULTIMODAL_MANUAL_TEST_2026-10-31.md` on the target Windows/Chrome or Edge device.
- Provider caveat: no user Gnani or vision-provider credentials were supplied, so live upstream transcription, Timbre speech and external visual analysis were not exercised. Mocked contract tests are not live provider verification.
- Visual caveat: this build supports user-selected image/frame analysis with per-image consent. It does not perform continuous, automatic video understanding. Uploaded video remains original evidence unless separately processed in a future feature.
- Production release still requires public HTTPS, production authentication, final privacy notice, monitored support route, durable storage and successful backup/restore, upload malware scanning, shared rate limiting, security/privacy/legal review, and browser/mobile/accessibility QA.

# Latest verified state — 31 October 2026 (Live Resolution Room: persistence and reliability pass)

- Live Resolution starts by creating a persistent draft case before opening microphone/camera permission prompts. The case ID, session start/end events and all subsequent material remain in the existing case database and timeline; there is no separate Live Room case store.
- The same-origin Gnani Prisma WebSocket proxy now uses the documented modern `language_code`, `model`, and `format` parameters, keeps the API key server-side, limits frame sizes and usage, and returns clear no-key/auth/rate-limit states. Browser-side speech turns are queued sequentially to avoid overlapping case writes. Transient provider closes use bounded reconnect attempts; permanent configuration/auth/rate-limit failures do not retry pointlessly.
- Final live speech transcripts and typed turns are scrubbed and saved to the existing case timeline with input-source provenance. Server-authored deterministic guidance and live-session lifecycle markers are saved separately. Live mic audio is streamed for transcription and is not retained as a raw recording by default.
- Camera photos, document uploads, imported audio, short WEBM/MP4 clips and screen captures upload directly to the draft case. There is no temporary page-memory evidence queue. Screen sharing shows a visible preview and saves the first selected frame immediately; the user can capture additional frames while sharing. Stop sharing through the browser's sharing indicator or end the session.
- Image/PDF uploads reuse the existing OCR candidate extraction and explicit user review/confirmation. Imported audio gets a transcript preview; its original file remains attached even if transcription fails. Video files remain stored as evidence and are not automatically semantically analysed in this build.
- Evidence rows now record capture source, client capture time, live-session ID and SHA-256. The hash identifies exported bytes; it does not prove who created the content or when it was created.
- The Live Room links to the existing case overview, print/save-PDF view and complete evidence ZIP. The print report contains confirmed case facts, source-backed route, checklist, commitments, timeline and exhibit register with original-file links. The evidence ZIP contains the JSON Resolution Passport, every available original evidence file and a SHA-256 manifest.
- Static shell cache is `bolkeresolve-shell-v26`. The Live Room case card now explains that the draft is created when the session starts; export actions become visible after the case is returned by the server.
- Verification: `node --check frontend/app.js`, `node --check frontend/sw.js`, `python -m py_compile backend/main.py`, and `PYTHONPATH=. pytest -q` — **271 passed, 90 subtests passed**. A mocked WebSocket integration test checks the documented provider URL/headers without using a live API key.
- Browser QA caveat: a Playwright Chromium attempt against the local server was blocked by the environment (`ERR_BLOCKED_BY_ADMINISTRATOR`). Manual Chrome/Edge camera, microphone, screen-share, mobile layout, print and end-to-end interaction tests remain necessary.
- Provider caveat: no user Gnani API key was supplied, so the real upstream Prisma/Timbre connection was not exercised. The no-key path is tested. Live AI vision/video reasoning is not implemented; screen captures and photos use the existing OCR/evidence review path.
- Guidance caveat: first-pass guidance comes from existing deterministic resolution playbooks. Timbre can read guidance aloud when configured, but speech locale selection alone does not translate English rule text into Hindi or other Indian languages.
- Production release still requires HTTPS, production authentication, final privacy/support configuration, durable storage and backup/restore, malware scanning, shared usage limits, monitoring, legal/security review and manual browser/accessibility QA. Do not use live consumer financial records before these gates are completed.

# Latest verified state — 29 October 2026 (Manual Case Email Reply Fallback)

- The unconfigured Case Inbox Bridge panel now offers a manual paste-and-review flow instead of a dead-end warning. A user pastes the support email subject/body, reviews the first-pass interpretation, optionally includes a ticket reference, and confirms a short interpretation to the case timeline.
- The fallback reuses the existing case-scoped reply preview/confirm API; the raw pasted message is not persisted by those endpoints. The user's browser form is cleared when they confirm or discard.
- Automatic forwarding still remains disabled until a real receiving domain/subdomain, provider DNS/MX configuration, stable Fernet key, authenticated webhook and public HTTPS deployment are configured. No fake email alias is presented and no external mail reception is claimed.
- Verification: `python -m pytest -q` — **254 passed, 90 subtests passed**; `node --check frontend/app.js`; `node --check frontend/sw.js`; `python -m compileall -q backend tests scripts` passed.
- The public shell cache is now `bolkeresolve-shell-v23` so browsers should fetch the updated script/style. Hard-refresh if a previously open tab still displays the old panel.
- Browser interaction QA is not verified in this environment. The release-readiness script still warns about public HTTPS origin, production authentication, final privacy notice, monitored support route, durable storage/backups, mobile/accessibility QA and security/privacy review.

# Latest verified state — 29 October 2026 (Condition-Aware Commitment Reconciliation)

- Added a first-class commitment record inside the existing case workspace. A user can preview, edit and explicitly confirm the meaning of a support statement, its condition/trigger, timeframe and stated action; later updates are appended rather than silently replacing history.
- Condition-based timing is not calculated until a user records that the condition occurred and supplies an occurrence date. Business-day dates exclude weekends only; holiday calendars and legal deadlines are not inferred. Refusal/negated statements and ambiguous exception clauses such as “unless” require manual review and do not receive automatic deadlines.
- Commitment events and conditions are included in Resolution Passport JSON format 1.3 and the printable HTML export. New routes are case-scoped and respect the existing case-access checks.
- Verification: `python -m pytest -q` — **253 passed, 90 subtests passed**; `node --check frontend/app.js`; `node --check frontend/sw.js`; `python -m compileall -q backend tests scripts` passed.
- `python scripts/check_release_readiness.py` still reports release warnings: public HTTPS origin, production authentication, final privacy notice, monitored support route, persistent storage/backup restore, mobile/accessibility QA and security/privacy review.
- Browser visual/interaction QA is not yet verified: a Playwright Chromium smoke attempt was blocked by the environment when navigating to the local server (`ERR_BLOCKED_BY_ADMINISTRATOR`). Follow the manual smoke-test steps in `CHANGELOG_CONDITION_AWARE_COMMITMENT_RECONCILIATION_2026-10-29.md` before demoing this feature.
- This is a deterministic rule-based candidate extractor and state evaluator, not an LLM promise-understanding engine. Gnani is used only by the existing speech-transcription path. Source identity, company action, and any reported outcome remain unverified unless an authorised external integration proves them.

# Latest verified state — 29 October 2026 (Reply-Aware Resolution Completion Loop)

- Added the `completion-loop-v2-reply-aware` layer: the most recent user-confirmed support-reply category now changes the primary next action for information requests, refund initiation/credit claims, review/waiting/acknowledgement, rejection, conflicting or ambiguous replies, and potentially unsafe requests.
- A document request can direct the user to the evidence panel; a reply claiming credit asks the user to check their own account; initiation does not mean credit; unsafe credential/remote-access/fee patterns prompt safety-first guidance.
- Normal reply review still stores a short user-confirmed interpretation/category rather than the raw pasted reply. Later user actions supersede an older reply-specific recommendation. Sender identity and support claims remain unverified.
- Verification: `python -m pytest -q` — **227 passed, 77 subtests passed**; `node --check frontend/app.js`; `node --check frontend/sw.js`; `python -m compileall -q backend tests scripts` all passed.
- `python scripts/check_release_readiness.py` confirms configured required checks only. It continues to warn about the missing HTTPS public origin, local-style auth, draft/placeholder privacy notice, monitored support route and incomplete optional messaging configuration. Persistent host storage, TLS, backups/restore, browser/mobile/accessibility, upload scanning and independent security/privacy review remain manual release gates.

# Current verified state — 23 October 2026 (Living Resolution Passport + Case Inbox Bridge)

- Added bounded local image/PDF text extraction, source-linked candidate fact review, mismatch highlighting, and explicit user confirmation before selected candidate fields update a case. Raw OCR excerpts are returned only in the review response; only structured candidate values/method/status and confirmed source metadata are persisted.
- Added an optional case-specific email forwarding alias and authenticated provider-parsed inbound webhook. Alias lookup is hash-based; the displayed token is encrypted at rest. Pending subject/body are redacted and encrypted, then cleared with attachment metadata on confirm/discard. Sender identity/claims stay unverified; attachments are not imported.
- Added an hourly retention sweep plus request-time expiry for inbound emails, a 1–30 day retention setting (default 14), strong webhook-credential readiness checks, provider setup documentation and Render environment variable placeholders. The bridge remains unavailable until a receiving domain, stable Fernet key and strong webhook authentication are configured.
- Resolution Passport JSON format is now 1.2 and includes confirmed document-derived fact provenance with `source_authenticity_verified: false`. Printed export includes confirmed document facts without embedding upload bytes.
- Verification: `python -m unittest discover -s tests -v` — **193 tests passed**; Python compilation, JavaScript syntax, HTML ID audit and a generated PNG OCR smoke test passed. Added regression coverage for HTML-only inbound emails, sensitive-value scrubbing, invalid attachment sizes and retention-setting bounds. This does not verify a live email provider/DNS route, live Gnani request, production deployment or full browser visual QA.

# Current verified state — 22 October 2026 (Voice-First Support UX)

- Current working build adds a guided-chat voice control with locale selection for ten Indian speech-language codes; transcript is reviewed in the composer before user send/save. Read-aloud in guided chat uses browser speech synthesis so it does not incur a server TTS call by default.
- Added a curated `backend/support_directory.py` to provide at most two HTTPS first-party/government support destinations based on the known merchant and reported issue; urgent suspected-fraud routes are ordered first. A reviewable issue-specific support draft is returned separately.
- The same support destinations now render both in the guided-chat recommendation card and in the saved case overview. A “Prepare message” action takes the user to the editable draft. External links are restricted to HTTPS and open in a separate tab with `noopener noreferrer`.
- No automated merchant contact or complaint filing was added. WhatsApp/email remain user-controlled handoffs. No transaction or merchant data is checked automatically.
- Verification from the current voice-first worktree: `python -m pytest -q` — **134 passed, 44 subtests passed**; `node --check frontend/app.js` and `python -m compileall -q backend tests scripts` pass. A local route smoke check returned HTTP 200 for the site shell/static assets/config/health and for a Zomato refund preview with Zomato + National Consumer Helpline destinations. Browser visual/interaction QA is still required in normal Chrome/Edge; a local Chromium screenshot attempt timed out in this environment. Live Gnani STT, browser/device voices, Meta and Twilio were not verified here.

# BolKeResolve implementation status

Updated: 22 October 2026

## Latest increment — Resolution Sprint UX (22 October 2026)

- Moved the first-pass recommendation into the first/story step so people can receive a useful next action before completing the full detail form. The complete plan remains available in an accessible expandable section.
- Clarified the three-stage wizard as story → review details → save case. The save action remains explicit; the first-pass preview does not persist a case or submit a complaint.
- In production authentication mode, anonymous first-pass previews and fact extraction remain public but rate-limited. Case creation, case listing, case details, exports and other private case operations remain behind the existing authentication middleware.
- Added a request sequence guard so a slow previous preview cannot overwrite a newer one. Editing the description or decision-relevant facts invalidates the displayed preview.
- Reworded the homepage CTA around “Get my next step” and added direct case-overview shortcuts to prepare the support message, inspect evidence, and record an outcome.
- Added regression coverage for public preview/private-save separation, preview throttling, result placement and direct case actions.
- Added responsive overflow guardrails for the intake workspace: at tablet widths the helper rail moves beneath the form, and at narrow widths its cards and official support route cards use a single column to avoid clipping.

### Verification for this increment

- `python -m pytest -q` — **123 tests passed; 34 subtests passed**.
- `node --check frontend/app.js` — passed.
- `python -m compileall -q backend tests scripts` — passed (generated bytecode removed from release archive).
- Hosted rate limiting is currently in-process, not a shared multi-worker quota. Before public production launch, add distributed edge/gateway rate limiting and complete real-browser mobile/accessibility QA. No live provider calls are required for this UX increment.


This file separates features implemented in the current code snapshot from features that still require live credentials, further implementation, or production review. A green automated test is not evidence that a third-party live service or public deployment has been verified.

## Latest increment — Resolution Passport and API-optional handoff (21 October 2026)

- Repositioned the core experience around a portable Resolution Passport rather than requiring a connected messaging provider. The web app remains usable for guided intake, deterministic source-backed guidance, evidence checklist, editable draft, timeline, follow-up and user-reported outcomes when WhatsApp credentials are absent.
- Added `backend/passport.py`, `GET /api/cases/{case_id}/passport.json` for a versioned structured export, and `GET /api/cases/{case_id}/passport/print` for a self-contained HTML print view that the user can save as PDF in the browser. Export contents include case facts, resolution steps/source references, evidence metadata (not file bytes), checklist, follow-up, draft, outcome and filtered timeline metadata. Export/print responses are private, case-scoped and no-store where appropriate.
- Added the `case_outcomes` table and `PUT /api/cases/{case_id}/outcome`. Supported results are still pending, no response, partially resolved, resolved, or stopped pursuing. The latest record is marked `user_reported`, each save adds a timeline event, and user-reported outcomes are not represented as bank/merchant verification.
- Added user-controlled WhatsApp and email draft handoffs from the editable message. These open an editable handoff; no message is automatically sent, no recipient is guessed, and handoff delivery is not tracked.
- Added PWA manifest, first-party app icons, install prompt affordance and an allowlisted static-shell service worker. Private `/api/` routes, case records, evidence, auth data and provider callbacks are never cached; the app explicitly remains network-dependent for private case actions.
- Added `docs/RESOLUTION_PASSPORT_AND_NO_API_HANDOFF.md`, release QA steps and `scripts/check_release_readiness.py`. The readiness script checks configuration without printing secret values and explicitly cannot certify TLS, persistent storage, provider behavior, security or legal compliance.

### Verification for this increment

- Seven new API/frontend regression tests cover JSON export provenance, printable HTML escaping/no-store behavior, outcome persistence and timeline provenance, invalid outcomes, unknown cases, PWA public-shell/network-only behavior, and per-account access controls for exports/outcomes.
- Run the final archive checks with `python -m pytest -q`, `node --check frontend/app.js`, `python -m compileall -q backend tests scripts`, and `python scripts/check_release_readiness.py`.
- PWA/install experience has not been visually verified in a real browser here. Live Gnani, Meta or Twilio services were not called in this build environment. Do not treat this increment as production-certified.

## Latest increment — Multi-provider WhatsApp Phase 1 (21 October 2026)

- Added `backend/messaging.py` with a normalized inbound-message contract, stable provider-scoped DB IDs, a small adapter protocol, and Meta/Twilio reply adapters.
- Retained the existing Meta Cloud API route and voice-note transcription; inbound Meta and Twilio text messages now call the same consent, command, case-creation, and case-timeline engine.
- Added `backend/twilio_whatsapp.py` using the official Twilio Python SDK `RequestValidator` for form-encoded webhook authentication, Twilio REST API text sends, inbound payload normalisation, and status payload normalisation. Validation fails closed if the SDK/secret is missing.
- Added signed Twilio inbound and delivery-status webhook endpoints; added `provider` columns via SQLite migration rather than introducing another case or contact database.
- Added provider-aware case-link generation/UI copy for Twilio Sandbox and explicit text-only notices so the sandbox does not incorrectly promise voice-note transcription.
- Disabled the Meta-template reminder worker when `BOLKE_WHATSAPP_PROVIDER=twilio`. Reminder templates remain Meta-only in this phase.
- Added `docs/TWILIO_SANDBOX_PHASE1.md` and multi-provider research notes. Twilio Sandbox is development/testing only and is not a production sender.

### Verification for the multi-provider increment

- `python -m unittest discover -s tests -q` — **111 tests passed** (provider calls are mocked in tests).
- `python -m py_compile backend/main.py backend/whatsapp.py backend/twilio_whatsapp.py backend/messaging.py scripts/send_whatsapp_reminders.py scripts/check_whatsapp_config.py tests/test_whatsapp_integration.py` — passed.
- `node --check frontend/app.js` — passed.
- Live Twilio requests, real webhook signature validation against an actual Twilio callback, live delivery and phone QA have not been run. This environment could not install the Twilio SDK because package-network access is unavailable; the package declares `twilio>=9.0,<11.0` in `requirements.txt`, and the included preflight checks the SDK is installed. Run `python -m pip install -r requirements.txt` before configuring the sandbox.

## Latest increment — Resolution Prep kit and follow-through (20 October 2026)

- Added a new Prep kit tab for each case, with category-specific evidence/document checklists and a readiness score. Checklist choices persist in SQLite per case and are not represented as external verification.
- Added case-pack export and copy. The plain-text pack brings together saved case facts, recommended first action, guided steps, preparation checklist, current official-source links, support draft state, follow-up state and a safety reminder.
- Added user-managed follow-up date and note with overdue/due-today/upcoming/completed states. This is a visible saved reminder inside the case only; it does not send push notifications, emails, WhatsApp messages or contact the merchant.
- Made the support request draft a real textarea that can be edited, saved, copied or read aloud. A saved edit is stored with best-effort sensitive-text scrubbing and is added to the activity timeline; it remains unsent.
- Added e-Jagriti official help links as a later-stage option after consumer-help routes, with explicit caveats that formal filing eligibility and required documents depend on the case. NPCI, National Consumer Helpline, RBI and the cybercrime portal remain distinct routes rather than one generic escalation.
- Added API/database migrations that create checklist and follow-up tables during app initialization, so existing SQLite cases can be kept when updating the code.

## Automated verification for this increment

Run from the project root:

```bash
python -m pytest -q
node --check frontend/app.js
python -m compileall -q backend tests
```

The current suite passes 72 pytest tests with 24 subtest cases, plus JavaScript syntax and Python compilation. API tests cover checklist persistence, action-pack export, follow-up save/clear/date validation, and draft editing. These are local automated tests, not live provider tests or an independent visual usability study.

## Known limitations for the next iteration

1. **Live voice:** Gnani STT/TTS still requires testing with the user's real API key. No live provider call is claimed as verified.
2. **Browser visual QA:** a local headless Chromium attempt was blocked by this environment's policy (`ERR_BLOCKED_BY_ADMINISTRATOR`). The changes have automated coverage, but the developer should open the build in a normal Chrome browser to review responsive layouts and keyboard/screen-reader behavior.
3. **Evidence:** uploaded files are not OCR'd, malware-scanned or automatically classified. Checklist state means the user marked an item ready; it does not mean the app verified the file.
4. **Follow-up reminders:** due dates are persisted and shown when the case is opened. There is no background scheduler, browser notification, email or WhatsApp reminder.
5. **Resolution accuracy:** rules are deterministic and need a human-reviewed test corpus for all ten languages and common code-mixed speech. A complaint draft must be reviewed by the user.
6. **External filing:** the app does not file grievances with NPCI, NCH, RBI, e-Jagriti or the cybercrime portal, and does not check bank/merchant records.
7. **Production security:** password-confirmed self-service account deletion is implemented for active application records and linked app data; email verification, password reset and MFA are not implemented. Formal data retention/backup policy, upload malware scanning, shared quotas, monitoring, dependency auditing, external security review and privacy/legal review remain before public deployment. The release preflight now fails closed if the bundled privacy notice still contains its draft banner/placeholders.

## Research and official links reviewed on 20 October 2026

- NPCI UPI FAQs: https://www.npci.org.in/what-we-do/upi/faqs
- National Consumer Helpline: https://consumerhelpline.gov.in/public/index.php/contact
- RBI Integrated Ombudsman Scheme, 2026 FAQ: https://old.rbi.org.in/commonman/english/scripts/faqs.aspx?id=3407
- National Cyber Crime Reporting Portal: https://cybercrime.gov.in/
- e-Jagriti official help documents: https://e-jagriti.gov.in/help-docs

These links are starting points; users should open the official pages before acting because eligibility, procedures and time limits can change.


## Focused core product increment — 22 October 2026

- Preserved the product's original promise: voice/text intake for common payment/refund problems, first-pass source-backed guidance, and an optional concise saved case. No complaint marketplace, community, automatic filing or new integration was added.
- Changed the creation journey from three screens to two: tell the story/get a first suggestion; review the issue/details and save in one screen. Optional evidence remains collapsed.
- Reduced the homepage's visible issue choices to three primary paths (missing refund, failed payment, unrecognised payment). Other supported issue types remain available under a disclosure and remain represented in the underlying case engine.
- Kept the concise case workspace and optional guided chat intact. Case fields remain user-reported and the product does not claim to verify bank records or send complaints.
- Verification in this source snapshot: `python -m pytest -q` — 166 tests and 64 subtests passed; `node --check frontend/app.js` and `python -m compileall -q backend tests scripts` passed. Release-readiness preflight reports required local configuration checks passed but warns that HTTPS, production authentication, public privacy notice, monitored support route, persistence/backups, live providers and full production review still need operator work.


## Launch-readiness hardening — 22 October 2026

- Added `DELETE /api/auth/account`, available only in production/authenticated mode. It requires the current password, deletes the user account and active owned case/evidence metadata, cleans linked WhatsApp contact/session and webhook records from the active database, removes linked evidence files after the database transaction, and revokes the session cookie. The response and UI explicitly explain that exported copies, data already sent to external providers, and host backups are outside this deletion action.
- Added a secondary `My cases → Account & privacy` control and an accessible confirmation dialog. The operation requires both password re-entry and a second irreversible-action acknowledgement; no action is taken merely by opening the dialog.
- Added `Cache-Control: no-store, max-age=0` and `Pragma: no-cache` to `/api/` responses, as a central safeguard against caching future private API payloads.
- Strengthened `scripts/check_release_readiness.py`: `BOLKE_PUBLIC_ORIGIN` must be a bare HTTPS origin, the configured data directory must already exist and be writable in production, and production preflight fails when the bundled privacy notice still carries operator draft markers/placeholders. The helper also reports missing email verification/password recovery as an explicit warning rather than claiming launch readiness.
- Updated privacy-notice draft language and regression tests. This still requires operator-specific legal identity, monitored privacy/support contact, retention periods and legal review; this code does not generate or certify the legal policy.

Verification after this increment: `python -m pytest -q` — **176 passed, 69 subtests passed**; `node --check frontend/app.js` passed; `python -m compileall -q backend tests scripts` passed. A configured production preflight with the current bundled privacy draft was verified to exit nonzero, as intended. Live provider calls and real-browser visual QA remain unverified.

## Frontend visual alignment pass (22 October 2026)

Applied targeted layout fixes based on the supplied guided-chat, sample-demo and saved-case screenshots while preserving the existing brand design. The sample demo auto-loads the selected fictional scenario, the saved-case primary action appears immediately beneath the heading/status, and guided-chat alignment/composer/responsive rules are more consistent. Details: `docs/FRONTEND_VISUAL_ALIGNMENT_PASS_2026-10-22.md`.

Validation: 178 tests, 69 subtests, JavaScript syntax and Python compilation passed. Chromium navigation was blocked by the environment, so a real browser visual pass has not been verified here.

## Frontend layout polish and interaction repair — 23 October 2026

- Reviewed the user-provided Guided Chat, sample demo and saved-case screenshots against 30+ public design-system/product UX references. The research notes are in `docs/FRONTEND_LAYOUT_POLISH_AND_DESIGN_RESEARCH_2026-10-23.md`.
- Case workspace: kept the tab disclosure expanded while Prepare & contact / Progress is selected so the visible panel cannot be detached from its navigation controls. Returned-to-overview closes the disclosure and scrolls to the primary action.
- Case content: standardised the secondary-panel intro with the support cards' parent grid, made long text/link/action elements shrink and wrap, and stacked contact actions at mobile widths.
- Sample demo: stretched its paired cards on desktop and used natural single-column heights on smaller screens so the scenario and result look like one composition.
- Guided Chat: moved the large introduction into normal flow to prevent sticky-position clipping, made the composer/grid more resilient, and retained the existing palette and type style.
- Scroll behavior: view changes start at the top rather than scrolling through a clipped intermediate state; section anchor targets account for the sticky header. Local panel transitions honour `prefers-reduced-motion`.
- Bumped the public shell cache to `bolkeresolve-shell-v16`; private API routes continue to bypass static caching.

Verification: `python -m pytest -q` — **196 passed, 77 subtests passed**; `node --check frontend/app.js`; `node --check frontend/sw.js`; `python -m compileall -q backend`; CSS parsing returned no top-level syntax errors; index has 100 IDs with no duplicates. Chromium navigation was attempted but blocked by the environment (`net::ERR_BLOCKED_BY_ADMINISTRATOR`), so target-browser visual QA remains outstanding.

## Share-to-Case, official route snapshot and versioned rulebook — 23 October 2026

- Added a PWA Web Share Target flow so supported installed PWAs can receive a title, text, HTTPS source and one optional evidence file. Items are staged encrypted for a short TTL and remain unattached until the user reviews and confirms.
- Added extension/signature/size checks, one-file limits, filename sanitisation, sensitive-value and URL-path/query scrubbing, early share-token removal from the browser address bar, token-hash lookup, expiration cleanup and a public POST throttle. Standard evidence upload remains the fallback.
- Aligned the manifest file picker with backend-supported formats: PNG, JPG/JPEG, WEBP and PDF.
- Added `/api/support-directory` with first-party support routes and a dated, selected snapshot of entries from the public NCH convergence directory. Match and no-match results both display limitations; the endpoint is not a live NCH API and does not file a grievance.
- Added versioned resolution-rule metadata carrying rule IDs, scope, suggested action, official source links and review date, visible through progressive disclosure.
- Added tests for share-target success/attach/consume, expiry, discard, bad signature/unsupported file, secret/path redaction, configuration, rate limiting, rulebook distinctions, and directory-match caveats.

Verification for this release: `python -m pytest -q` — **208 passed, 77 subtests passed**; `node --check frontend/app.js`, `node --check frontend/sw.js`, `python -m compileall -q backend tests scripts`, CSS parse and HTML ID audit passed. Chromium navigation is blocked in this environment, so real browser/device visual QA remains outstanding. Native share-target behaviour requires HTTPS, an installed supported PWA and device/browser testing.


## Share-to-Case token hardening — 23 October 2026

- New redirects put one-time tokens in URL fragments; an early same-origin head script removes the fragment before the page body is parsed. The token is retained in session storage only for the short review flow and sent to API handlers in `X-Share-Intake-Token`.
- Preview, attach and discard now use constant API paths. Attach receives `case_id` and `include_context` in a validated JSON body rather than a dynamic path/query.
- Service-worker cache bumped to `bolkeresolve-shell-v19` with the early parser included. `/share-token.js` receives no-store headers from the middleware.
- Final tests: 211 passed, 77 subtests passed; Node syntax checks and Python compilation pass.
