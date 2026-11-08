# BolKeResolve WhatsApp launch playbook

**Updated:** 21 October 2026. This page is now the short index for the current implementation guide.

Use [`WHATSAPP_INTEGRATION_GUIDE_2026-10-21.md`](WHATSAPP_INTEGRATION_GUIDE_2026-10-21.md) as the current source of truth. It covers the existing code and intended journey, Meta setup, API credentials, direct Cloud API vs BSP, low-cost test setup, current pricing caveats, privacy and policy gates, deployment, troubleshooting and launch sign-off.

## Current decision

Use the official Meta WhatsApp Cloud API directly for the first release. It avoids a BSP's additional subscription/provider processing layer. It does not eliminate Meta messaging fees, Gnani usage/credit limits, hosting costs or privacy/security responsibilities.

The website and WhatsApp share the same case engine. Cases are created only after `SAVE`; `START` is explicit opt-in; `STOP` stops future messaging; case updates are user-reported; complaint submission and payment-system verification are not implemented.

## What's changed in the 21 October package

- Webhook processing claims now have leases and retry recovery for transient failures.
- A first-time `LINK <CODE>` attempt explains that `START` is required and keeps the code available for retry; a stopped contact must explicitly send `START` before linking again. Common opt-out phrases are also recognised.
- Cloud API readiness requires a valid public HTTPS privacy notice and at least one support escalation channel, in addition to Meta credentials and a valid phone encryption key.
- Follow-up due dates use `BOLKE_TIMEZONE` (default `Asia/Kolkata`).
- Added a privacy notice draft at `/privacy.html`, a configuration checker, and Docker/Render deployment starter files. The privacy page still needs the actual operator identity, monitored privacy/support contact, retention/deletion policy, provider disclosure and review.

## Key endpoints

- `GET /api/webhooks/whatsapp` — Meta verification challenge.
- `POST /api/webhooks/whatsapp` — signed inbound messages/status receipts.
- `GET /api/config` — safe readiness flags only; never returns secrets.
- `GET /api/health` — app/database readiness.
- `POST /api/cases/{case_id}/whatsapp-link` — creates one-time, 10-minute case pairing code.

## Required configuration

See `.env.example` and the full guide for definitions. The required live values include:

`WHATSAPP_BUSINESS_NUMBER`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_APP_SECRET`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_PHONE_ENCRYPTION_KEY`, `BOLKE_PRIVACY_POLICY_URL`, and either `BOLKE_SUPPORT_EMAIL` or `BOLKE_SUPPORT_URL`. Also set `BOLKE_PUBLIC_ORIGIN` and `BOLKE_ENV=production` for the public deployment. `GNANI_API_KEY` is required to transcribe incoming WhatsApp voice notes.

To check variable presence without sending a message:

```bash
python scripts/check_whatsapp_config.py
```

## Production caution

The package is ready for configuration and test-number validation, but not automatically safe/legal to launch with real users. The actual Meta account, number, credentials, public HTTPS webhook, final privacy notice, real support contact, deletion/retention workflow, backup/restore, and real-phone end-to-end test must be supplied and verified by the operator. Do not request OTPs, UPI PINs, passwords, full card/account numbers or ID numbers. Never claim a payment was checked or a complaint filed unless a future authorized integration actually verifies it.

## Optional provider adapter for testing

The optional Twilio WhatsApp Sandbox adapter is described in [`TWILIO_SANDBOX_PHASE1.md`](TWILIO_SANDBOX_PHASE1.md). It reuses the shared case engine but uses separate Twilio REST credentials and signature validation. Sandbox only; do not treat it as a production sender or as a way to bypass Meta account restrictions. Scheduled reminders remain Meta-template-only and are skipped when `BOLKE_WHATSAPP_PROVIDER=twilio`.
