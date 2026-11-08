# BolKeResolve: Adaptive Intake and WhatsApp Integration

Implementation notes: 20 October 2026

## What is connected in the code

- The web intake is a three-stage progressive flow: **Your story → Confirm details → Your next action**. The evidence upload remains optional and hidden until the user chooses to add a file.
- A case supports append-only user-reported events (`contacted_support`, `still_waiting`, `submission_reported`, `response_received`, `resolved`, `not_resolved`, `official_channel_opened`). Event metadata records actor, channel and source so a later integration can distinguish web and WhatsApp actions.
- WhatsApp webhook handlers implement the Meta GET verification challenge and check `X-Hub-Signature-256` over the exact POST body before processing.
- Incoming WhatsApp message IDs are deduplicated. Sender numbers are stored as an encrypted value plus a keyed fingerprint; phone numbers are not used as display names or printed in logs.
- Consent begins only when the sender replies `START`. `STOP` disables future messages. New cases are previewed and only created when the user replies `SAVE`.
- A web case can be paired using a short-lived, single-use 8-character code generated from the case page. The user sends `LINK CODE` to the configured business number.
- Optional scheduled follow-ups use an approved WhatsApp template and run only when the user has opted in. The worker is a one-shot script, not a background loop.

## Configure Meta WhatsApp Cloud API

Do not put credentials in `frontend/app.js`, HTML, screenshots, or source control.

1. Create/use a Meta developer app and a WhatsApp Business Account. Complete the Meta setup that gives you a business phone number, phone number ID and access token permitted to send/receive WhatsApp messages.
2. Deploy BolKeResolve to a publicly reachable HTTPS origin. Meta cannot deliver webhooks to `127.0.0.1` on your laptop. For local development, use a trusted HTTPS development tunnel and do not expose a personal database or evidence directory.
3. Configure the server-side environment variables in `.env` or your hosting secret store:
   - `WHATSAPP_BUSINESS_NUMBER`: official number in international digits, no `+` or spaces.
   - `WHATSAPP_ACCESS_TOKEN`: server-side token for the Cloud API.
   - `WHATSAPP_PHONE_NUMBER_ID`: Meta phone number ID (not the number itself).
   - `WHATSAPP_APP_SECRET`: the Meta app secret used to verify signatures.
   - `WHATSAPP_VERIFY_TOKEN`: a long random token you create for webhook verification.
   - `WHATSAPP_PHONE_ENCRYPTION_KEY`: a Fernet key for at-rest contact encryption. Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Back this up securely; changing it without migrating stored contact data prevents existing phones from being decrypted.
   - `WHATSAPP_GRAPH_API_VERSION`: the currently supported Graph version. The default is `v26.0` for this build; keep it configurable and update it after checking Meta's version lifecycle.
4. In the Meta app's Webhooks setup, set the callback URL to `https://YOUR_PUBLIC_HOST/api/webhooks/whatsapp`, enter exactly the configured verify token, and subscribe the WhatsApp Business Account to the `messages` field. Complete Meta's verification challenge.
5. Use Meta's test number and a consenting test recipient first. Test `START`, a sample story, `SAVE`, `STATUS`, `UPDATE a note`, `FOLLOWUP YYYY-MM-DD`, `STOP`, duplicate webhook delivery, and invalid signatures. Do not use real customer cases until access controls, data retention, and support escalation are reviewed.

### Useful official documentation

- WhatsApp Cloud API overview: <https://developers.facebook.com/docs/whatsapp/cloud-api/overview>
- Meta's Cloud API collection/overview and prerequisites: <https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api>
- National Consumer Helpline contact page (includes its published WhatsApp contact): <https://consumerhelpline.gov.in/public/index.php/contact>

## Commands understood by the WhatsApp service

- `START`: explicit opt-in before sharing story content.
- Free-text story, followed by `SAVE`, `EDIT`, or `CANCEL`.
- `STATUS`: show the active case's locally recorded status and follow-up date.
- `UPDATE <note>`: append a user-reported timeline event.
- `CONTACTED`, `WAITING`, `REPLY <text>`, `RESOLVED`, `NOT RESOLVED`.
- `FOLLOWUP YYYY-MM-DD`: set or replace a follow-up date.
- `LINK <CODE>`: use a one-time code created by the website to pair an existing case.
- `NEW`, `HELP`, and `STOP`.

These commands never claim that BolKeResolve has submitted an external complaint or checked the merchant/bank's systems. The WhatsApp channel records what the user reports, and its messages use the same case database and event timeline as the website.

## Reminder worker

WhatsApp messages outside the customer-service window generally need a pre-approved template. Create a utility template whose body has the case ID and follow-up date as the first two text parameters, and set:

```env
WHATSAPP_REMINDER_TEMPLATE_NAME=your_approved_template_name
WHATSAPP_REMINDER_TEMPLATE_LANGUAGE=en_US
```

Then run `run_whatsapp_reminders.bat` once to test. For scheduled execution, create a daily Windows Task Scheduler task (or server cron) pointing to that batch file. The script sends only due, unfinished follow-ups for enabled, opted-in contacts linked to a case. It records “accepted by Cloud API,” not “delivered,” in the timeline. If the Cloud API is not configured or there is no template name, it exits without sending.

## Important production limitations

- This repository has the message and webhook foundations; an app owner still must create the Meta app, provide credentials, register the public HTTPS webhook and get the templates approved.
- Webhook storage deduplicates message IDs and stores a limited reply record, but production launch still needs operational monitoring, data-retention/deletion policy, rate limiting/shared quotas, incident response, and review by a privacy/security practitioner.
- Phone number encryption-key rotation and user self-service WhatsApp unlinking are not yet implemented. Keep the encryption key stable and restrict who can access server backups.
- A webhook request accepted by Meta and an outbound message accepted by the Graph API are not proof of user delivery or read status. Do not describe them as verified completion.
- The local chat-style intake preview is not the live WhatsApp network. When the Cloud API is unconfigured the app must not open a generic `wa.me/` link or imply the business line is connected.
