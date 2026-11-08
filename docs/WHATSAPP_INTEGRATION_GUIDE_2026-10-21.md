# BolKeResolve — WhatsApp Cloud API Integration & Launch Guide

**Review date:** 21 October 2026  
**Scope:** Existing source code in this ZIP, official Meta WhatsApp Business Platform, Gnani speech APIs, India privacy/consumer-safety practices, cost controls, deployment, testing and launch operations.

> **Read this first:** This package contains the integration code and configuration instructions, not live WhatsApp credentials or a registered business number. It is ready for operator configuration and test-number validation; it is **not** proof of live delivery or a legally approved public launch. The Privacy Notice in `frontend/privacy.html` is a draft containing placeholders. Do not use real consumer cases until the notice/contact, deletion/retention process, hosting, and security review are complete.

## 1. The intended product and design choice

BolKeResolve is a consumer-help companion. The desired WhatsApp experience is a continuation of the website's existing case engine, not a separate chatbot database:

1. The person opens the official BolKeResolve WhatsApp number and sends `START`.
2. The bot explains what the service does, privacy/processing notice, the support route and safety limits.
3. The person describes one payment/consumer issue in text or a supported voice note.
4. The shared backend redacts likely sensitive values and extracts candidate facts for review.
5. The person chooses `SAVE`, `EDIT` or `CANCEL`; no new case is created before explicit `SAVE`.
6. The person can see locally recorded status, add user-reported updates, link a pre-existing website case with a short-lived code, and choose a follow-up date.
7. Optional reminders are sent only to an opted-in, linked contact and only when an approved WhatsApp template is configured.

**The system does not check a bank, UPI, merchant or NPCI record. It does not send a complaint or payment instruction.** Its outputs are preparation, case management, and source-backed guidance. Each update must remain labelled as user-reported unless an independently authorised integration actually verifies it.

### Architecture in this build

- `backend/main.py`: FastAPI routes and the shared SQLite case/timeline/session store; WhatsApp command state machine; webhook endpoint; Gnani transcription workflow.
- `backend/whatsapp.py`: official Meta Graph API send/media helpers, webhook signature validation, payload parsing, encrypted phone storage and keyed phone fingerprint.
- `backend/extraction.py`: candidate issue facts; values are not external verification.
- `backend/resolution.py`: deterministic issue classification and source-backed playbooks.
- `backend/action_pack.py`: next-step packet, evidence checklist and follow-up summary.
- `scripts/send_whatsapp_reminders.py`: one-shot reminder worker; it is not a continuously running daemon.
- `frontend/`: existing website plus the privacy notice route at `/privacy.html`.
- `tests/test_whatsapp_integration.py`: mocked webhook, consent, pairing, receipts and reminders tests.

The WhatsApp network calls use the **official Meta WhatsApp Cloud API directly**, without a Business Solution Provider (BSP). This avoids a provider subscription/markup but does not avoid Meta message charges, hosting/database costs or Gnani usage costs.

## 2. What this package already implements

- `GET /api/webhooks/whatsapp`: webhook verification challenge.
- `POST /api/webhooks/whatsapp`: HMAC validation for `X-Hub-Signature-256` against the raw body; inbound message parsing; outbound status receipt processing.
- One primary case database shared between website and WhatsApp.
- Explicit `START` opt-in and `STOP` opt-out, plus common explicit opt-out phrases such as `UNSUBSCRIBE`, `OPT OUT`, `QUIT` and `NO MORE MESSAGES`.
- User-controlled `SAVE` before a new case is created.
- Single-use `LINK <CODE>` pairing for a web case (10-minute expiry).
- Text commands: `STATUS`, `UPDATE <note>`, `CONTACTED`, `WAITING`, `REPLY <message>`, `FOLLOWUP YYYY-MM-DD`, `RESOLVED`, `NOT RESOLVED`, `NEW`, `HELP`, `LANG ...`, `STOP`.
- Native interactive reply buttons for common choices.
- Opted-in audio messages downloaded from Meta media endpoints with HTTPS-host allowlisting and a 12 MB download limit, then passed to the existing Gnani Prisma transcription flow.
- Configurable voice-note language selection; default Hindi/Hinglish.
- Outbound message-ID receipts and reminder leases.
- Phone number encrypted at rest, keyed lookup fingerprint, server-only tokens, and no raw payload logging.
- Safe fallback to on-site chat when live WhatsApp is not fully configured.
- Public readiness gate now requires a public HTTPS privacy-notice URL and at least one configured support escalation path, in addition to the Cloud API credentials and valid phone-encryption key.

### Reliability/security improvements made in this package

1. **Recoverable webhook state.** Webhook rows now include a lease, attempt count and bounded error type. A transient failure before case-state commit releases the claim so a Meta retry can process it. A retry after case state has committed reuses the stored reply instead of applying the command twice. Stale claims can be reclaimed.
2. **Opt-out cannot be bypassed by pairing.** `LINK <CODE>` is no longer handled before the contact's enabled/consent state is checked. After `STOP` (or a recognised opt-out phrase), the person must explicitly send `START` again before linking or using the service. A first-time LINK attempt gets a specific explanation to send START, then resend the still-unused code within its 10-minute validity window.
3. **Privacy/support launch gates.** Cloud API readiness requires a syntactically valid public HTTPS privacy URL and either a valid-looking support email or public HTTPS support URL. This validates configuration shape only: the operator must still ensure the page is published, accurate, monitored and not a placeholder.
4. **Reminder dates use an explicit timezone.** The reminder query uses `BOLKE_TIMEZONE`, default `Asia/Kolkata`, rather than assuming the host's local timezone.
5. **Published draft notice.** `/privacy.html` is included and linked from the website footer, but it is deliberately marked as a draft with required fields. Replace it before use with real people.
6. **Deployment starter files.** `Dockerfile`, `render.yaml`, and `scripts/check_whatsapp_config.py` have been added. The Render example uses a persistent disk and a paid-capable plan because free-instance filesystems cannot safely store the SQLite database/evidence.

### Known limits that remain

- No live Meta credentials, business number, public webhook or template approval is included in this ZIP.
- All automated tests mock the Meta/Gnani network calls. Passing tests does not prove real delivery.
- WhatsApp images/documents are not ingested directly. The user must upload evidence through the website after creating/linking a case.
- There is no direct bank/merchant/NPCI/consumer-helpline complaint submission.
- A complete end-user deletion process covering cases, WhatsApp metadata, uploaded evidence, logs, backups and third-party providers is not implemented. This is a **public-launch blocker** until a clear, tested request-and-erasure process exists.
- The privacy notice is a draft; legal identity, real support contacts, retention rules, processing locations, provider terms and children's-data policy must be completed.
- The webhook handler still processes work within the incoming HTTP request. For material traffic, add a durable queue/worker and monitoring; SQLite plus a single service is an MVP architecture, not a horizontal-scale design.
- If Meta accepts an outbound message but the HTTP response times out before BolKeResolve records the provider message ID, a retry may send a duplicate reply. The database protects case-state processing from most duplicate deliveries; it cannot guarantee exactly-once external delivery across an ambiguous network failure.

## 3. Lowest-cost path that is actually useful

### Phase 1 — zero provider subscription, test-only

1. Use Meta's Cloud API test number and only recipients explicitly added to the test allowlist.
2. Use a temporary public HTTPS tunnel to your local FastAPI service if appropriate for testing, or a disposable public test deployment.
3. Keep `BOLKE_ENV=development` for local testing only; do not enter real personal case information in an insecure temporary tunnel.
4. Use a temporary Meta developer token for the test stage and rotate/remove it when done.
5. Use the Gnani programme/API credits you were allocated, if your account has them. Track usage; do not assume this API access remains free forever.
6. Leave reminder templates blank until interactive replies and case creation have passed tests. Without a template, the core user-initiated chat still works but off-window reminders are intentionally disabled.

This path is useful for the competition demo and integration validation. It is **not** suitable for production case data: a local laptop must stay on, quick tunnels can change URL, and development storage/backups are not a production service.

### Phase 2 — low-cost pilot

Use the direct Cloud API (no BSP), a stable HTTPS host, server-side secret storage, a persistent database/disk, backups, a real support contact and a final privacy notice. Start with a tiny consenting pilot and no marketing campaigns. A small paid persistent host may be cheaper than losing cases or missing webhook traffic.

The included `render.yaml` is a deployment starting point: a Docker web service, production auth mode and a mounted persistent disk. Render documents its free instances as for experimentation rather than production; they spin down when idle and their local filesystem is ephemeral. Do not deploy SQLite/evidence on a free ephemeral filesystem for real users. Current platform pricing may change, so check the provider dashboard before deploying.

### The true cost model

| Cost item | What to expect |
|---|---|
| BSP/platform subscription | Avoided by calling Meta Cloud API directly. |
| Meta outbound messaging | Not universally free. Pricing is based on the current message category, recipient market and delivered-message rules. As of the rate card reported effective 1 Oct 2026, India budgeting estimates are ₹0.115 per delivered utility/authentication/service message and ₹0.8631 per marketing message, with 1,000 free service messages per business phone number per month. Validate the exact current card, free allowance, billing currency and taxes in WhatsApp Manager before launch. |
| Incoming customer messages | Normally not the primary Meta billable event; budget for outbound delivered messages and verify the current card. |
| Gnani Prisma STT / Timbre TTS | Separate from Meta. Use allocated programme credits if available; Gnani's public API material describes free access as testing/experimental and does not establish a permanent free commercial tier. Confirm your dashboard balance and provider terms. |
| Hosting/database/backups | May be free for a disposable experiment, but durable production storage and reliable uptime commonly require a paid service. |
| Template reminders | Need Meta-approved template and may create billable delivered messages. No reminder template means no off-window reminders. |

**Cost rules:** no marketing broadcasts; short user-requested replies; voice-note quota on; reminders disabled until user-requested, approved and budgeted; monitor delivery status and billing. Never claim “free WhatsApp API” as a general statement.

## 4. Meta account setup, step by step

Meta periodically changes dashboard labels. The names below describe the current normal path; follow the current official setup screens if a label has moved.

### A. Create the app and test number

1. Sign in at <https://developers.facebook.com/>.
2. Create or select a Meta developer app suitable for a business integration.
3. Add the **WhatsApp** product and open the API setup / Getting Started screen.
4. Use the Meta-provided **test phone number** first. Add your own WhatsApp phone as an allowed test recipient.
5. Record, privately:
   - `Phone Number ID` (this is an ID, not the business phone number);
   - a test access token;
   - the `WhatsApp Business Account ID`, if shown for subscription/asset management.
6. In App Settings → Basic (wording may differ), find the **App Secret**. Never share it.
7. In app Webhooks, select the WhatsApp Business Account object/product and configure the `messages` field subscription.

### B. Deploy to a public HTTPS origin

Meta cannot reach `localhost`, `127.0.0.1`, a private LAN IP or a machine behind an inaccessible firewall. You need a publicly reachable HTTPS origin with a valid TLS certificate.

For quick tests, use a temporary HTTPS tunnel only with synthetic messages. For a longer test, deploy with the provided Dockerfile or an equivalent FastAPI host. Ensure `GET /api/health` responds and `GET /api/config` is reachable before attaching webhooks.

### C. Set environment variables on the server

Copy `.env.example` to `.env` for local use; in production, use the host's secret manager/environment settings. Do not commit `.env`, print secrets in logs, place tokens in browser code, or paste them into chat/screenshots.

Required for live use:

| Variable | Meaning | Where it comes from |
|---|---|---|
| `WHATSAPP_BUSINESS_NUMBER` | Public business number, digits only, country code included (India starts `91`; no `+` or spaces) | Number assigned/registered for the WhatsApp Business Platform |
| `WHATSAPP_ACCESS_TOKEN` | Bearer token for Cloud API sends/media | Temporary token for initial test; for production use a suitably permissioned System User token and rotate it per your security policy |

For production tokens, the official Meta Cloud API collection documents these core permissions: `whatsapp_business_messaging` and `whatsapp_business_management`. Assign the app and WhatsApp Business Account assets to the System User before generating a token; a token without the appropriate WABA/phone-number access can fail even if the token string itself is valid. `business_management` may be needed for API calls that directly query/manage the wider business portfolio, but this app does not need that scope for its message send endpoint alone. Meta notes that ordinary user tokens expire, while System User tokens can be issued for a finite lifetime or (where the account allows) without an expiry; inspect the generated token and document rotation rather than assuming it will never expire. See the [official Meta Cloud API collection](https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api).
| `WHATSAPP_PHONE_NUMBER_ID` | Meta phone-number ID used in Graph API URL | WhatsApp API setup screen |
| `WHATSAPP_APP_SECRET` | HMAC secret to validate webhook signatures | Meta app settings, Basic |
| `WHATSAPP_VERIFY_TOKEN` | Random token created by the operator; Meta echoes it for webhook subscription challenge | Generate your own and set exactly the same value in the server and Webhooks page |
| `WHATSAPP_PHONE_ENCRYPTION_KEY` | Fernet key to encrypt stored contact number | Generate locally; back up privately. Changing it without migrating stored ciphertext prevents decryption of previous phone numbers |
| `BOLKE_PUBLIC_ORIGIN` | Exact public origin, e.g. `https://your-domain.example` | Your deployed web origin |
| `BOLKE_PRIVACY_POLICY_URL` | Published privacy notice with `https://` | Your final published notice; must not be the draft placeholder page |
| `BOLKE_SUPPORT_EMAIL` or `BOLKE_SUPPORT_URL` | A support channel monitored by a human | Your real contact email/page; must be staffed/monitored |
| `BOLKE_TIMEZONE` | Calendar timezone for follow-up dates | Default `Asia/Kolkata` |

Optional:

- `WHATSAPP_GRAPH_API_VERSION` (current package default `v26.0`; confirm that version remains supported and review the API version lifecycle periodically).
- `WHATSAPP_REMINDER_TEMPLATE_NAME` and `WHATSAPP_REMINDER_TEMPLATE_LANGUAGE` (only after Meta approves the template).
- `GNANI_API_KEY` for WhatsApp voice note transcription. The access is independent of Meta and may draw down Gnani credits.
- `WHATSAPP_WEBHOOK_LEASE_SECONDS` (30–600 seconds; default 180).

Generate a phone-encryption key in PowerShell, Command Prompt or a terminal after the Python dependencies are installed:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Generate a webhook verify token separately:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Use different random values for the app secret, verify token and encryption key. Do not use the same key for multiple purposes.

### D. Register the webhook

In the Meta app's Webhooks configuration:

- **Callback URL:** `https://YOUR_PUBLIC_HOST/api/webhooks/whatsapp`
- **Verify token:** exactly the value in `WHATSAPP_VERIFY_TOKEN`
- **Field subscription:** `messages`

Complete Meta's verification challenge. `WHATSAPP_APP_SECRET` is separate from `WHATSAPP_VERIFY_TOKEN`; the first verifies POST signatures, the second verifies the GET subscription handshake.

For a normal production WABA, check the current Meta screen/API instructions to ensure the app is subscribed to the correct WhatsApp Business Account and `messages` field.

### E. Validate readiness without revealing secrets

On your local project folder:

```powershell
python -m pip install -r requirements.txt
python scripts/check_whatsapp_config.py
```

The preflight script prints variable presence/readiness and the API version only. It sends no messages and cannot prove that Meta accepts a token or that a privacy/support page is substantively correct.

After deployment, check:

- `https://YOUR_PUBLIC_HOST/api/health`
- `https://YOUR_PUBLIC_HOST/api/config`

`whatsapp_cloud_api_ready` must be `true`; the public config should reveal only booleans/display settings, never credentials. If false, examine server-side config and logs without printing secrets.

## 5. End-to-end test sequence

Use a consenting Meta test recipient and synthetic data. Do not use real bank transactions or customer screenshots while this is still a test setup.

1. Send `START` to the Meta test business number.
2. Confirm that the opt-in/processing notice, safety boundary, privacy URL and support escalation path appear.
3. Send a synthetic story such as: “My Zomato refund of ₹50 was promised in two to three days, but it has not arrived after seven days.”
4. Confirm the reply is a preview and clearly says nothing has been sent to the merchant.
5. Tap **Save case** or send `SAVE`; confirm the case appears in the same website's “My cases” area.
6. Send `STATUS`; confirm only locally stored, user-reported information is shown.
7. Send `UPDATE I contacted support today`; confirm it appears as a user-reported timeline item.
8. Test `CONTACTED`, `WAITING`, `REPLY <message>`, `FOLLOWUP YYYY-MM-DD`, `NEW`, `HELP`, `STOP` and a synonym such as `UNSUBSCRIBE`.
9. On a first-time connection, send `LINK <valid test code>` before opting in. It should explain that `START` is required and leave the code unused; then send `START` and resend `LINK <same code>`.
10. After `STOP`, send `LINK <valid test code>`; it must not link/reactivate. Send `START` explicitly before retrying the link.
11. Repeat the exact same webhook payload/message ID; it must not create a second case/update.
12. Simulate a transient exception or failed Graph send in tests; the database claim should be retryable without re-applying the command state.
13. Test an invalid `X-Hub-Signature-256`; expect HTTP 401.
14. Send a short consenting voice note only after `GNANI_API_KEY` is set; confirm transcript quality and user review. Keep the clip short and never include credentials.
15. If reminders are enabled, verify the approved utility template and ensure `STOP` blocks later reminders.
16. Inspect Meta's provider receipts. A Graph API HTTP success means accepted, not delivered. Only signed Meta status receipts should change the recorded `sent`/`delivered`/`read` state.

### Suggested release-acceptance matrix

| Test | Expected behaviour |
|---|---|
| Missing token/number ID | WhatsApp readiness false; no send attempt |
| Missing/HTTP privacy URL | WhatsApp readiness false |
| Missing monitored support path | WhatsApp readiness false |
| Incorrect signature | 401; no command processed |
| Duplicate inbound message ID | No duplicate case or timeline update |
| Failure before case state commit | Retry can reclaim the processing row |
| Failure after case state commit but before sending reply | Retry reuses the prepared reply rather than applying the command again |
| `LINK` before first opt-in | Clear START-first instruction; code remains unused |
| `STOP`/unsubscribe, then `LINK` | Blocked until explicit `START` |
| Invalid/expired/used `LINK` token | No case link |
| New story without `SAVE` | No case is created |
| No reminder template | No off-window reminder sent |
| API accepted, later `failed` receipt | Status/timeline reflect the provider receipt; never shown as delivered |
| User marks case `RESOLVED` | Display as user-reported; not externally verified |
| Deletion request | Must follow the actual documented erasure workflow; do not claim self-service deletion is available yet |

## 6. Optional follow-up reminder template

Do not set the template environment values until Meta has approved a matching template and the app is ready to budget for it.

One proposed utility template body with the current worker's expected two parameters:

> Your BolKeResolve follow-up for case {{1}} is due today (date: {{2}}). This is a reminder you requested. Reply STOP to stop WhatsApp updates.

Example values:

```env
WHATSAPP_REMINDER_TEMPLATE_NAME=bolke_followup_due
WHATSAPP_REMINDER_TEMPLATE_LANGUAGE=en_US
```

The template name/language must match the approved entry exactly, and its category must remain utility. Meta can reclassify, reject or pause templates. Avoid promotional content in a user-requested reminder.

The script is one-shot; it should be invoked by a scheduler (for example Windows Task Scheduler on a persistent test host). If using SQLite, run the worker against the same persistent database and disk; a separate service with a separate SQLite file cannot see the same cases. For a scalable deployment with separate workers, migrate to a shared database such as Postgres and redesign the queue/worker boundary.

## 7. Compliance, safety and privacy launch requirements

This section is an engineering checklist, **not a legal opinion or certification of compliance**. Have an India privacy/legal professional review the actual operating entity, product and data flows before public release.

### Meta policy requirements to operationalise

- Obtain clear opt-in before ongoing contact. This code records `START` as the BolKeResolve opt-in; don't buy, scrape or import phone numbers, and don't add marketing campaigns.
- Immediately respect `STOP` and other opt-out requests; make future sends conditional on an enabled consent record.
- Outside the 24-hour customer-service window after the user's most recent message, send only an approved template. Do not use free-form text as a workaround.
- Provide a prompt, clear escalation route. This build gates readiness on a valid-looking support email or HTTPS URL, but you must populate and monitor a real contact channel.
- Keep a published, accurate privacy policy and necessary notices/permissions. Do not impersonate a bank, UPI app, merchant or government helpline.
- Never request full payment-card/account numbers, OTPs, UPI PINs or passwords. Minimise what is collected and what is retained.

Official policy: <https://whatsappbusiness.com/policy/> (last-updated label on the live policy page: 23 September 2026).

### India privacy and consumer-protection practices

- The Digital Personal Data Protection Act, 2023 and DPDP Rules, 2025 have a phased commencement timetable. Official notifications split commencement into stages; the provisions should not be described as all taking effect at once. Regardless of the implementation date that applies to a given provision, build for clear notices, purpose limitation, data minimisation, security safeguards, retention limitation, user rights handling and breach response now. Check the current MeitY/Gazette timetable and obtain advice on which provisions apply to the operating entity at launch.
- Document that Meta processes WhatsApp messages and that voice-note audio is sent to Gnani for transcription. Review provider terms, retention, subprocessors, data location and any required contract before public use; don't assert that either provider stores nothing or that data remains only in India without verified support.
- Set a retention schedule for saved cases, phone fingerprints/ciphertexts, sessions, transcripts, evidence, provider receipts and backups. The current package does not implement complete self-service erasure; finish this before collecting real cases.
- Publish real operator identity and monitored contact details. Decide and document age policy/handling of children's data. Avoid collecting Aadhaar/PAN, full statements and unrelated sensitive evidence.
- For suspected unauthorised transactions, direct users to contact their bank/payment provider promptly through the official channel. BolKeResolve is not a bank, RBI, NPCI or government service.
- Keep a breach response contact/process, backup and restore test, dependency scan, access review, incident log and escalation process.

Official sources:

- MeitY's DPDP Rules 2025 listing and the enforcement timeline: <https://www.meity.gov.in/documents/act-and-policies>.
- PIB's explanation of the phased rollout: <https://www.pib.gov.in/PressReleasePage.aspx?PRID=2190014&lang=1&reg=3>.
- National Consumer Helpline official contact details: <https://consumerhelpline.gov.in/public/index.php/contact>.

### Consumer-service boundaries

- A case summary is generated from the user's story; it is not payment verification.
- Case stage, contacted-support state and resolution are user-reported.
- A support-message draft is only a draft. The user must send it through the relevant official channel.
- There is no official NPCI/bank/merchant submission integration.
- Never claim that BolKeResolve has registered or escalated a complaint unless a future dedicated, authorised integration returns a verifiable submission reference.

## 8. Troubleshooting

| Symptom | Check |
|---|---|
| Webhook verification fails | Callback is exact HTTPS path; server and Meta `WHATSAPP_VERIFY_TOKEN` match byte-for-byte; the verify token is not the app secret. |
| Webhook POST returns 401 | `WHATSAPP_APP_SECRET` belongs to the same Meta app; reverse proxy must not rewrite/re-encode the JSON body before the signature check. |
| `whatsapp_cloud_api_ready` false | Run preflight; confirm token, phone-number ID, app secret, verify token, phone encryption key, registered business number, HTTPS privacy URL and real support contact are present/valid. |
| Send returns 401/403 | Token expired/wrong; verify permissions and the correct app/WABA/phone-number ID. Create/rotate a suitable server-side token. |
| Test recipient does not receive a message | Add the recipient to the Meta test allowlist; verify country code, test number, Graph API version and response in Meta dashboard. |
| Inbound messages not received | Callback is publicly reachable; `messages` webhook field/WABA subscription is active; server is awake; check server logs for status codes without printing payloads. |
| Duplicate reply after timeout | Meta may have accepted the first outbound request even if the response was lost. Use provider receipts and bounded retries; exactly-once external sends cannot be guaranteed when acceptance is ambiguous. |
| Voice note fails | Confirm Gnani key/credits, the sender sent `START`, media URL fetch succeeds, file is below 12 MB and supported, language code is correct, and the clip is short. Offer text as fallback. |
| Reminder never arrives | Need an approved template, exact language/name, due unfinished follow-up, current opt-in, linked case, enabled contact, persistent scheduler/database and successful provider status. |
| Reminder repeats after deploy | Confirm overlapping schedulers are not running and the reminder claim table is on durable shared storage. |
| Cases disappear on hosting restart | The host filesystem is ephemeral or `BOLKE_DATA_DIR` points to a non-persistent path. Stop real-user use and restore from backup; configure a durable disk/database. |

## 9. Deployment quickstart with Docker/Render

### Docker local build

```bash
docker build -t bolkeresolve-wa .
docker run --rm -p 8000:8000 --env-file .env \
  -e BOLKE_DATA_DIR=/var/data \
  -v "$(pwd)/runtime:/var/data" \
  bolkeresolve-wa
```

PowerShell volume syntax differs; use a real persistent host directory. The container does not bake `.env` into its image. Check `http://localhost:8000/api/health` and run the preflight script on the host.

### Render

1. Push this project to a private/public Git repository without `.env`, runtime files or credentials.
2. Create a Render Blueprint from `render.yaml` or create a Docker web service with equivalent settings.
3. Use a persistent disk mounted at `/var/data`; set `BOLKE_DATA_DIR=/var/data`.
4. Set all `sync: false` variables in the Render dashboard. `BOLKE_PUBLIC_ORIGIN` and `BOLKE_PRIVACY_POLICY_URL` must use the final `https://` hostname.
5. Replace the draft privacy notice with a real one and configure a monitored support contact before turning on the Cloud API.
6. After deploy, run the `/api/health`, `/api/config` and webhook tests from Section 5.
7. Back up the SQLite file and evidence directory to protected storage. Test restoration. Restrict access to backups because they contain user data.

Free Render instances are useful for disposable experiments only: idle spin-down, cold start and ephemeral filesystem make them an unsafe choice for durable cases and webhook reliability. Read the current provider limitations before choosing a plan.

## 10. Official/current research register

The code review is grounded in the supplied 20 October ZIP and adjacent project notes. External policy/pricing statements were checked on 21 October 2026; API dashboards and live account terms may differ.

- Meta WhatsApp Business Messaging Policy: <https://whatsappbusiness.com/policy/>. It says (among other requirements) that businesses need opt-in permission, must respect opt-outs, must use approved templates to initiate conversations and outside the 24-hour service window, must comply with law/privacy notices, and must provide clear escalation paths for automated responses.
- Meta Cloud API overview/API collection: <https://developers.facebook.com/docs/whatsapp/cloud-api/overview> and <https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api>.
- Meta template messages: <https://www.postman.com/meta/whatsapp-business-platform/request/lwtlz1k/send-message-template-interactive>.
- Meta Utility category: <https://whatsappbusiness.com/products/conversation-categories/utility/>.
- Meta Service category: <https://whatsappbusiness.com/products/conversation-categories/service/>.
- Current Indian price-card reports that cite Meta's rate card effective 1 October 2026: <https://conecxt.com/resources/whatsapp-provider-pricing-audit-oct-2026/> and <https://www.flowcall.co/blog/whatsapp-business-api-pricing>. Because third-party pages can lag or disagree, confirm actual rates/free allowance inside WhatsApp Manager before enabling billable messaging.
- Gnani API dashboard/registration and credits: <https://www.gnani.ai/great-indian-ai-internship-registration-form>.
- Gnani STT docs: <https://docs.gnani.ai/api/STT/speech-to-text>.
- Gnani TTS docs: <https://docs.gnani.ai/api/TTS/tts-inference>.
- Gnani API's public testing disclaimer/usage guidance: <https://github.com/gnani-ai/API-service>.
- Render free-tier limitations: <https://render.com/docs/free>.
- National Consumer Helpline contact: <https://consumerhelpline.gov.in/public/index.php/contact>.
- MeitY DPDP Rules listing / implementation information: <https://www.meity.gov.in/documents/act-and-policies> and PIB's phased-implementation overview: <https://www.pib.gov.in/PressReleasePage.aspx?PRID=2190014&lang=1&reg=3>.

## Final launch sign-off

Do not mark this integration “live” until a person can verify each item below with the actual Meta account and public deployment:

- [ ] The legal operator name, final privacy notice, monitored support contact, data retention/deletion process and incident process are complete.
- [ ] Hosting is HTTPS, durable, backed up and restored successfully; environment secrets are private.
- [ ] Correct Meta app, WABA, phone-number ID, suitable access token and `messages` subscription are active.
- [ ] `GET` challenge verifies and invalid `POST` signatures are rejected.
- [ ] START/SAVE/EDIT/CANCEL/LINK/STATUS/UPDATE/STOP/unsubscribe/re-opt-in all work with a real consenting test phone.
- [ ] Provider message receipts are recorded accurately; accepted is not presented as delivered/read.
- [ ] Voice-note flow is tested with Gnani credentials/credits and the privacy disclosure is visible.
- [ ] Template approval, message charges, scheduler and opt-out behavior are tested—or reminders remain disabled.
- [ ] Mobile/assistive-tech QA, rate limits, monitoring, retention, deletion, backup and external security/privacy review are completed.

Only then should the business number be promoted to users beyond the pilot.

---

## Addendum: Twilio Sandbox Phase 1 adapter (21 October 2026)

The project now includes an optional Twilio WhatsApp Sandbox adapter for development while retaining the existing Meta Cloud API integration. Read [`TWILIO_SANDBOX_PHASE1.md`](TWILIO_SANDBOX_PHASE1.md) for required Twilio configuration, exact public HTTPS webhook URL, Python SDK signature verification, test workflow, Sandbox limitations and intentionally unsupported media/reminder paths.

The Twilio route uses the same case engine, encrypted phone identity and consent/opt-out/session tables as Meta. It does not create a parallel database. Twilio Sandbox remains a test-only environment, and inbound replies are sent back through the provider that received the message. The primary provider preference `BOLKE_WHATSAPP_PROVIDER=twilio` disables the Meta-template reminder worker during sandbox development; it does not affect or unlock Meta's account restrictions.
