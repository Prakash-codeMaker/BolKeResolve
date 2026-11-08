# BolKeResolve — Twilio WhatsApp Sandbox adapter (Phase 1)

**Purpose:** develop and test the WhatsApp conversation path when the current Meta WABA is restricted. This is a testing adapter, not a production sender. The existing Meta Cloud API adapter and the shared BolKeResolve case engine are retained.

## What Phase 1 adds

- `backend/messaging.py`: provider-neutral inbound/send result contracts and provider-scoped persistence IDs.
- `backend/twilio_whatsapp.py`: Twilio configuration checks, inbound form normalisation, SDK-backed signature validation, text send via Twilio REST API, and status-payload normalisation.
- `POST /api/webhooks/twilio/whatsapp`: validated inbound Twilio webhook, routed into the same consent/command/case workflow as Meta.
- `POST /api/webhooks/twilio/whatsapp/status`: validated delivery-status callback for case-linked outbound messages.
- Schema migration adds a `provider` column to the existing WhatsApp inbound/outbound message tables. It does not create another cases/contact/session database.
- Twilio Sandbox replies are text-only in this phase. Interactive Meta reply buttons and Meta voice-note downloads remain available only on the Meta route; Twilio replies tell the user to type commands such as `SAVE`, `EDIT`, and `STOP`.

## Important limit

Twilio documents its WhatsApp Sandbox as testing/discovery only, not production. Every test recipient must join the particular sandbox. A recipient's join/session expires after three days and must be renewed. The shared sandbox supports only its built-in pre-approved templates for business-initiated messages. Sandbox messages are subject to Twilio WhatsApp pricing; a Twilio trial also has limited free trial units. See the [official Sandbox guide](https://www.twilio.com/docs/whatsapp/sandbox).

The Sandbox is not a way to bypass Meta/WhatsApp policies, and it may have country or recipient limitations. Use only a provider/account you are authorised to access, test with consenting participants, and do not send real consumer-case personal data during early integration tests.

## 1. Create and join the sandbox

1. Create/sign into a Twilio account and open the Twilio Console's WhatsApp Sandbox / Try WhatsApp page. The Console UI may label this differently for trial accounts.
2. Activate the Sandbox and note the channel sender address shown by Twilio (commonly `whatsapp:+14155238886`; use the value Twilio actually shows).
3. From the phone you will test with, send the exact `join <your sandbox code>` phrase shown in the Twilio Console to the sandbox number. Wait for Twilio's join confirmation.
4. Do not share the Account Auth Token or put it in frontend files, Git, screenshots or chat.

## 2. Configure environment variables

Add these to the server-side `.env` or hosting secret manager. The `.env.example` contains blank placeholders:

```dotenv
TWILIO_ACCOUNT_SID=AC...your-account-sid
TWILIO_AUTH_TOKEN=...server-side-secret...
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_WEBHOOK_PUBLIC_URL=https://YOUR_PUBLIC_HOST/api/webhooks/twilio/whatsapp
TWILIO_STATUS_CALLBACK_URL=https://YOUR_PUBLIC_HOST/api/webhooks/twilio/whatsapp/status
BOLKE_WHATSAPP_PROVIDER=twilio
```

Also retain the existing common BolKeResolve settings required by the case workflow:

- `WHATSAPP_PHONE_ENCRYPTION_KEY` — valid Fernet key for encrypted sender-number storage (generate using the command in the main README).
- `BOLKE_PRIVACY_POLICY_URL` — a real public HTTPS privacy notice.
- `BOLKE_SUPPORT_EMAIL` or `BOLKE_SUPPORT_URL` — a real, monitored contact.
- `BOLKE_PUBLIC_ORIGIN` — the app's public HTTPS origin when deployed.

`BOLKE_WHATSAPP_PROVIDER=twilio` is an operator preference; each inbound webhook reply is sent through the provider that received it. It also causes the Meta-only template reminder worker to skip sending, so testing Twilio doesn't accidentally trigger Meta reminders. Set it back to `meta` when operating Meta reminder delivery. It does not unlock an account or switch Meta webhook traffic to Twilio.

Install dependencies after updating the package: `python -m pip install -r requirements.txt`. Twilio signature verification uses the official `twilio` Python SDK's `RequestValidator`; validation fails closed if the SDK or token is missing.

## 3. Expose a public HTTPS endpoint

Twilio cannot reach `localhost` directly. Use a public HTTPS deploy, or a temporary HTTPS tunnel for development only. Twilio's docs warn that tunnels expose the development server to the internet; use a temporary tunnel only with synthetic test data and stop it afterward.

Configure the Sandbox's **When a message comes in** webhook to the exact value of `TWILIO_WEBHOOK_PUBLIC_URL`, with method `POST`. Configure the Sandbox's status callback to `TWILIO_STATUS_CALLBACK_URL` if the Console offers the setting; otherwise the app includes the status callback on outbound API requests when the endpoint URL is configured.

Signature validation requires the public URL in `.env` to exactly match the externally configured callback URL (HTTPS scheme, host, path and any query string). If validation fails behind a reverse proxy, do not disable validation; correct the configured URL and HTTPS proxy setup.

## 4. Verify setup without sending a live message

Run:

```powershell
python scripts/check_whatsapp_config.py
```

With `BOLKE_WHATSAPP_PROVIDER=twilio`, the preflight reports which Twilio values are missing without printing their values or sending a message. It also checks that the existing phone encryption key, privacy notice and support contact are ready. A green preflight checks presence and shape only; it does not prove that the credentials work with Twilio.

## 5. Test the intended flow

1. Confirm your handset has joined the Twilio sandbox.
2. Start the app and configure the inbound webhook URL in Twilio Sandbox.
3. Send `START` to the Twilio Sandbox number.
4. Send a synthetic text story (e.g. a fictional small refund issue).
5. Review the generated summary and send `SAVE` only if it is correct.
6. Confirm one case appears in the normal BolKeResolve website/case database.
7. Send `STATUS`, then `UPDATE I contacted support today` and confirm the same case timeline updates.
8. Send `STOP`; check that later messages do not re-enable the contact. A fresh `START` is required to opt back in.
9. If the case-linked outbound message has a tracked Twilio SID, confirm the status callback updates its status and timeline. API acceptance alone is not delivery confirmation.
10. Re-run all automated tests: `python -m unittest discover -s tests -q` and `node --check frontend/app.js`.

## 6. Current intentional gaps

- Twilio Sandbox media/voice-note downloads and Gnani transcription are not implemented in this Phase 1 adapter. Send text during this test; the existing Meta audio-to-Gnani path remains unchanged.
- Native interactive/reply buttons are Meta-specific; on Twilio, type the commands shown by the bot.
- Scheduled reminders continue to use Meta's approved utility template flow only. The worker skips when `BOLKE_WHATSAPP_PROVIDER=twilio`; arbitrary reminders are not sent through the Twilio Sandbox.
- This adapter is not production-ready. Production needs an officially provisioned sender, current WhatsApp/Meta policy compliance, approved templates where required, data-retention/deletion operations, monitoring, durable backup/restore, external security review and live-device verification.
- Provider callbacks can race with local persistence if a provider returns a status update before an outbound message row has been committed. For Phase 1 the callback is applied only to known case-linked outbound IDs. A transactional outbox/message-attempt ledger is the next hardening step if operating at scale.

## Official references

- [Twilio WhatsApp Sandbox](https://www.twilio.com/docs/whatsapp/sandbox)
- [Twilio secure webhooks and request validation](https://www.twilio.com/docs/usage/webhooks/webhooks-security)
- [Twilio Message resource and status callbacks](https://www.twilio.com/docs/messaging/api/message-resource)
- [Twilio WhatsApp quickstart](https://www.twilio.com/docs/whatsapp/quickstart)
- [Meta WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api/overview)
