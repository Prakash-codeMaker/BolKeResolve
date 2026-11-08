# BolKeResolve implementation milestone — 20 October 2026

## Included in this build

### Intake and case experience
- New-case intake is now a real three-stage wizard: **Your story → Confirm details → Your next action**. Only the current panel is shown; Back/Continue are functional and the stage indicator changes with it.
- Evidence upload is optional and hidden until the user chooses to add a file.
- After a case is saved, the case workspace supports focused tabs and one-tap, timestamped user-reported events (e.g. contacted support, still waiting, response received, resolved).
- Event history distinguishes the actor, channel, and source. It does not claim outside verification.
- Follow-up dates and notes persist. A one-shot worker can send a reminder using an approved WhatsApp utility template if the user opted in and the Meta Cloud API is configured.

### WhatsApp foundation
- The in-site chat screen is a preview, not a live WhatsApp chat.
- Generic `wa.me/` fallbacks are disabled. The UI says WhatsApp is not connected until the Cloud API configuration is complete.
- Signed Meta webhooks: GET challenge verification and POST HMAC validation.
- Inbound message IDs are deduplicated.
- Explicit `START` opt-in; `STOP` opt-out. New case details aren't saved until user sends `SAVE`.
- Case pairing uses a short-lived, single-use token. The user must manually send its `LINK <CODE>` message to the official business number.
- Contact phone numbers are encrypted at rest and also held as keyed fingerprints to support lookup without indexing plaintext phone numbers.
- Supported user actions include case status, timeline update, support contacted, waiting, reply received, resolution outcome, follow-up date, new case, help and opt-out.

## Local validation

- `python -m py_compile backend/main.py backend/whatsapp.py scripts/send_whatsapp_reminders.py`
- `node --check frontend/app.js`
- `python -m unittest discover -s tests -v`

The test suite has 82 passing tests, including Meta webhook signature/challenge behavior, duplicate delivery, opt-in/SAVE workflow, case pairing, reminder job behavior, intake wizard assertions and the existing case/security/voice tests. These tests do not replace a live Meta account test or hands-on user acceptance test.

## Configure live WhatsApp

1. Create a Meta developer app and a WhatsApp Business Account. Obtain a business phone number, Phone Number ID, and server-side access token.
2. Deploy to a public HTTPS host; Meta cannot call a local-only `127.0.0.1` address. Configure webhook callback `/api/webhooks/whatsapp` and the exact verify token.
3. Set `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_APP_SECRET`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_PHONE_ENCRYPTION_KEY`, `WHATSAPP_BUSINESS_NUMBER`, and optionally `WHATSAPP_GRAPH_API_VERSION` in the server environment.
4. Subscribe to the `messages` webhook and test against Meta's test number with consenting recipients.
5. For reminders, configure a utility template approved by Meta and set `WHATSAPP_REMINDER_TEMPLATE_NAME` and `WHATSAPP_REMINDER_TEMPLATE_LANGUAGE`; then schedule the one-shot Windows task or server cron.

Never place secrets in frontend JavaScript. An API accepted message only means accepted by the Cloud API, not delivered/read. Do not claim an external complaint has been submitted unless that action is separately implemented and verifiably confirmed.

## Known limitations

- No live Meta credentials, public webhook deployment, or real outbound message was available during this build, so live WhatsApp is not verified here.
- Browser-driven visual QA was attempted in the container, but Chromium navigation was blocked by the environment (`ERR_BLOCKED_BY_ADMINISTRATOR`). Automated tests and a local HTTP health check passed; inspect the updated UI on the user's Windows browser before public release.
- Production still requires security/privacy review, operational monitoring, retention/deletion policy for contact data, and user acceptance testing on mobile.

## Follow-up delivery receipts and reminder reliability (incremental milestone)

- The reminder worker now uses a short SQLite lease per case + follow-up version. Overlapping scheduled runs cannot both claim the same active reminder. A failed attempt releases the claim for a later retry; an accepted reminder is marked complete for that follow-up version.
- Reminder API acceptance is stored separately from subsequent Meta message receipts. `whatsapp_outbound_messages` tracks provider message IDs for reminder messages without storing recipient phone numbers or raw webhook payloads.
- The signed WhatsApp webhook now parses Meta `statuses` updates. For tracked reminders it records `sent`, `delivered`, `read`, or `failed` in the outbound message table and adds one timeline event per meaningful state transition. Replayed receipts are idempotent; older states cannot downgrade a newer state.
- Provider status events are evidence of the status Meta reported, not independent proof that a person read or acted on the message. `accepted` still means only that the Cloud API accepted the send request.
- Automated tests cover status parsing, duplicate receipt handling, monotonic state transitions, and overlapping reminder claims. Live receipts require a configured Meta app, valid signing secret, public HTTPS webhook, approved reminder template, and consenting contact.


## WhatsApp interactive and voice-note increment

- Key choices now use native WhatsApp reply buttons (start/status/help; save/edit/cancel; status/contacted/waiting), with stable button IDs mapped to the same case commands as typed messages.
- Signed provider receipts can track case-linked conversational replies as well as scheduled reminders.
- Opted-in users can send WhatsApp voice notes. Media is retrieved through Meta's authenticated media endpoints, HTTPS hosts are allowlisted, downloads are capped at 12 MB, and transcription reuses the existing Gnani Prisma path. A persistent per-sender quota limits voice-note transcription attempts.
- Voice-note language defaults to Hindi/Hinglish; `LANG EN`, `LANG HI`, `LANG MR`, `LANG BN`, `LANG GU`, `LANG KN`, `LANG ML`, `LANG PA`, `LANG TA`, or `LANG TE` changes the saved preference. Auto-detection is intentionally not assumed, because some Gnani keys reject REST auto-detection.
- When WhatsApp is not configured, the website's WhatsApp CTA guides the person to the on-site chat instead of ending in a dead button.
- Automated tests include interactive reply parsing, language preference persistence, voice-note metadata parsing, delivery-receipt tracking and the existing case/security workflows. Live Meta/Gnani calls still require real credentials and a public HTTPS webhook.
