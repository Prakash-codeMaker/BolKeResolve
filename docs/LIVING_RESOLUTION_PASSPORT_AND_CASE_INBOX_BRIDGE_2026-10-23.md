# Living Resolution Passport + Case Inbox Bridge

**Status (updated 29 October 2026):** Manual email-reply import is available in the case inbox panel even when no provider is configured. Automatic forwarding still requires receiving-domain DNS, an inbound email provider, a stable encryption key and authenticated HTTPS webhook setup.

BolKeResolve remains a focused, voice-first helper. These additions extend the existing case without creating a separate complaint-management workspace:

1. **Evidence review:** when the user chooses `Check details` on an uploaded PNG/JPG/WEBP/PDF, the server performs bounded local OCR/text extraction and offers candidate merchant, amount, payment date and status wording. It highlights possible mismatches with current case facts. The user must explicitly confirm which facts to record and separately choose which fields, if any, to apply to the case.
2. **Case Inbox Bridge:** when configured, a user can create a random per-case forwarding address and forward an email reply. The parsed body/subject are redacted, encrypted while pending review, and shown as unverified. The app does not import attachment bytes, automatically send replies, contact a merchant, or claim the sender is verified. The user previews the reply interpretation and explicitly confirms or discards it.
3. **Manual fallback when automatic forwarding is unavailable:** the same panel offers a paste-and-review form. Paste the relevant email subject/body, preview the interpretation, and confirm only the short summary. The raw pasted reply is not stored in the case database by the preview route. This is intentionally not represented as automatic email receiving; the configured provider bridge remains separately gated by DNS/domain, encryption and webhook authentication.
4. **Retention:** pending inbound email is lazily purged when the webhook/inbox is used and by a periodic hourly retention sweep. The retention window is configurable from 1 to 30 days; default is 14 days. Once the user confirms or discards an email, the encrypted subject/body and attachment metadata are cleared immediately. Timeline entries contain only a brief interpretation, not the raw email.

## Use the manual reply import without a provider

1. Open a saved case and expand **More case tools → Forward a support reply into this case**.
2. If the automatic-forwarding warning appears, paste the relevant subject/body into **Paste the support email** and optionally add a ticket reference.
3. Click **Review email reply** and check the interpretation against the original message.
4. Confirm to save only the short, user-confirmed interpretation to the timeline, or discard it. The source text stays in the browser memory while the page is open and is sent to the server for preview, but the preview and confirm routes do not persist the raw reply.
5. Never paste OTPs, PINs, passwords, full card numbers or unrelated personal information. Sensitive-text redaction is best-effort and does not guarantee that every sensitive string is removed.

This fallback is useful immediately on a local or hosted deployment. It does not create a forwarding address, receive external messages or monitor the mailbox. For that, configure the provider steps below.

## Configure local OCR

Python requirements include `pypdf`, `Pillow`, `pytesseract` and `PyMuPDF`. The Docker image installs Tesseract English/Hindi data. Review currently supports PNG/JPEG/WEBP images and PDF text/OCR. Limits: upload source must be at most 8 MB; images are capped at 18 million pixels; PDF text extraction reads at most the first five pages and scanned-PDF OCR at most three pages; extracted text is capped at 12,000 characters. OCR is a candidate generator, not proof. The uploaded original remains a case attachment until the user deletes the evidence/case. Raw extracted text and source excerpts are not persisted by the review endpoints; only bounded structured candidates, method and confirmation/provenance metadata remain.

## Enable the Case Inbox Bridge

Keep this off until you own/control a public inbound email domain, HTTPS origin, stable durable storage and monitored operations. The feature is intentionally optional; without all three configuration components (domain, valid Fernet key, strong webhook authentication), the app will not create case aliases.

### 1. Set server-side environment values

Never put any of these values in `frontend/`, HTML, screenshots, client-side JavaScript, chat messages or source control.

- `BOLKE_INBOUND_EMAIL_DOMAIN`: a receiving domain/subdomain you control, for example `inbox.yourdomain.example`. Configure its inbound MX/provider routing separately. This value is not a guarantee the DNS is correct.
- `BOLKE_INBOUND_EMAIL_ENCRYPTION_KEY`: create a stable Fernet key with:

  ```bash
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```

  Keep it stable across deploys/restarts and back it up securely. Losing it makes pending encrypted messages unreadable. Rotating it is not a routine key-refresh; implement a planned re-encryption/rotation process if needed.
- `BOLKE_INBOUND_WEBHOOK_TOKEN`: configure a long random token (minimum 32 characters accepted). Generate one with:

  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(48))"
  ```

  Alternatively, configure both `BOLKE_INBOUND_WEBHOOK_USERNAME` (minimum 8 characters) and `BOLKE_INBOUND_WEBHOOK_PASSWORD` (minimum 24 characters) for a provider that supports HTTP Basic authentication. A strong bearer token is the preferred generic option when the provider can send an `Authorization: Bearer ...` header.
- `BOLKE_INBOUND_EMAIL_RETENTION_DAYS`: 1–30; default 14.

Set these values in your hosting provider's secret/environment settings. On Render, the blueprint declares them as unsynchronised environment values. Keep the persistent disk enabled because the case database and uploaded evidence must persist.

### 2. Configure an inbound email provider

The endpoint accepts a provider-parsed JSON payload using common fields such as `To`, `ToFull`, `Cc`, `From`, `Subject`, `TextBody`, `HtmlBody`, `MessageID` and `Attachments`. Postmark is one possible provider, not a bundled/active connection by default. Its inbound webhook documentation describes JSON parsing, inbound routing and HTTP Basic authentication:

- [Postmark inbound webhook](https://postmarkapp.com/developer/webhooks/inbound-webhook)
- [Configure a Postmark inbound server](https://postmarkapp.com/developer/user-guide/inbound/configure-an-inbound-server)
- [Postmark inbound webhook retries](https://postmarkapp.com/support/article/understanding-inbound-webhook-retries-in-postmark)

A provider-specific setup generally involves:

1. Create an inbound message stream/server and verify the domain with the provider.
2. Configure the DNS/MX records that the provider supplies for the dedicated inbound subdomain. Do not change the MX records for your main business mail domain without understanding existing mail delivery.
3. Configure its inbound webhook to post to `https://YOUR_PUBLIC_ORIGIN/api/webhooks/inbound-email`.
4. Protect the endpoint. If using Postmark's documented Basic authentication support for the inbound hook, configure the dedicated username/password in the provider's webhook URL using its documented format; if you do this, recognise that the URL contains credentials in the provider dashboard. Restrict access to that dashboard and avoid copying webhook URLs into logs/tickets. Use a proxy that injects an Authorization header if preferred. Do not place secrets in URL query parameters or disable webhook auth.
5. Leave raw email (`RawEmail`) content inclusion disabled; the application does not need the complete MIME payload.
6. Send a synthetic test message to a generated case alias, verify it arrives only in that case, inspect the review, confirm/discard it, and verify that raw content clears.

The provider must accept arbitrary case aliases at the configured inbound domain (catch-all/forwarding mode). A case address has the form `br-<60 lowercase hex characters>@<configured domain>` (63-character local part, under the common 64-octet SMTP limit). It acts as a bearer capability: keep it private and rotate it if it leaks.

### 3. Verify the bridge with synthetic test data

1. Sign in (production) and open one case.
2. Expand **More case tools → Case Inbox Bridge** and create an address.
3. Forward a synthetic email to that address.
4. Check that the case shows a pending unverified reply, and that attachment metadata is listed without importing attachment contents.
5. Preview its category/next step; nothing is saved by preview.
6. Confirm to store the interpretation only, or discard to clear the message.
7. Inspect the timeline and database in a test environment to confirm that subject/body ciphertext and attachment metadata are blank after confirmation/discard. Never run destructive test SQL against production data.

Example synthetic JSON payload for a local test (replace the `To` address with one returned by the app and use the configured webhook auth):

```json
{
  "To": "br-<60-lowercase-hex-token>@inbox.yourdomain.example",
  "From": "Support <reply@merchant.example>",
  "Subject": "Synthetic refund update",
  "TextBody": "Your refund has been initiated. Please allow 5 to 7 business days.",
  "MessageID": "synthetic-message-id-0001",
  "Attachments": []
}
```

Do not use a real customer's email for initial integration tests.

## Security and product boundaries

- Only the authenticated owner can use a case inbox in production; the public inbound webhook additionally requires the configured auth credential.
- Unknown aliases return a generic success response so the webhook doesn't disclose whether a case/address exists. Invalid webhook credentials are rejected.
- Tokens are random lowercase hex, stored as a SHA-256 hash for lookup and encrypted with Fernet only to display the forwarding address to the case owner.
- Sender identity/domain and statements are not independently verified. Email content is untrusted and must not instruct the system to take automated actions.
- Basic sensitive patterns are redacted before pending body/subject encryption. This is best-effort; do not forward messages containing credentials, full card details or other information unnecessary to resolve the issue.
- Attachment bytes are never saved by the bridge. Metadata is shown for context only; the user can download the file from their email provider and upload it to the case after reviewing it.
- There is no automatic email sending, mailbox access, bank/NPCI query or complaint submission. This is an inbound bridge for user-forwarded support replies only.
- Confirm/discard clears the encrypted body and subject plus attachment metadata. The hourly sweep clears old inbound message rows after the configured retention window. Existing host backups may still include database pages/backups; apply your host's retention/access/deletion policy.
- During production launch, also use rate limits at the reverse proxy/provider, restricted database/storage access, monitored errors, backups, dependency updates and privacy/legal review.

## Share-to-Case URL and capability hardening (23 October 2026)

- The share receiver redirects new staged items to a URL fragment (`/#shared_intake=...`), not a query parameter. URL fragments are not included in HTTP requests.
- `frontend/share-token.js` executes synchronously in the document head, copies a valid short-lived capability to `sessionStorage`, and removes it from the address bar before the page body and the main app bundle are parsed. The main app then sends it only in the `X-Share-Intake-Token` request header.
- All shared-intake API routes use constant paths: `GET /api/shared-intake/preview`, `POST /api/shared-intake/attach`, and `DELETE /api/shared-intake/discard`. The attach request places `case_id` and `include_context` in its validated JSON body; the capability is not embedded in a path or query string.
- New Share-to-Case redirects never generate query tokens. For legacy query URLs, the early script removes the token from the address bar as soon as the document begins parsing, but the initial request has already reached the server/proxy and may have been logged; if there is concern it was exposed, discard/expire that staged item and share again from the source app.
- The service-worker shell was `bolkeresolve-shell-v19` at the 23 October update; the current 29 October manual-email-import update uses `bolkeresolve-shell-v23` and includes the early token parser. API routes remain network-only and are never cached by the service worker.

## API routes

The manual paste-and-review fallback reuses `POST /api/cases/{case_id}/reply-review/preview` and `POST /api/cases/{case_id}/reply-review/confirm`; it does not require inbox alias creation.

- `POST /api/cases/{case_id}/evidence/{evidence_id}/review`
- `POST /api/cases/{case_id}/evidence-review/confirm`
- `DELETE /api/cases/{case_id}/evidence-review/{review_id}`
- `POST /api/cases/{case_id}/inbox` — create/retrieve case alias
- `GET /api/cases/{case_id}/inbox` — list pending reviews
- `POST /api/cases/{case_id}/inbox/rotate` — disable prior alias and rotate
- `POST /api/cases/{case_id}/inbox/messages/{inbound_id}/preview`
- `POST /api/cases/{case_id}/inbox/messages/{inbound_id}/confirm`
- `DELETE /api/cases/{case_id}/inbox/messages/{inbound_id}`
- `POST /api/webhooks/inbound-email` — provider-parsed inbound webhook
- `GET /api/shared-intake/preview`, `POST /api/shared-intake/attach`, `DELETE /api/shared-intake/discard` — constant-path Share-to-Case endpoints; attach uses JSON body fields `case_id` and `include_context`, and the bearer capability is only in `X-Share-Intake-Token`

## Release test commands

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m py_compile backend/main.py backend/evidence_review.py backend/passport.py
node --check frontend/app.js
```

The current test suite uses synthetic cases, mocked OCR text at the endpoint boundary, and fake email webhook payloads. It does not verify a live DNS/MX route, paid email provider, hosted HTTPS deployment or live Gnani API call.
