# BolKeResolve Resolution Passport — Product and Usage Guide

**Purpose:** Make the consumer/payment case workflow complete even when no external messaging provider is connected. WhatsApp is an optional user-controlled handoff, not a requirement for case intake, evidence organization, guidance, or follow-up.

## What the passport means

A Resolution Passport is a portable snapshot of a case as recorded by the user and the application. It combines:

- the issue summary and known facts;
- a deterministic resolution plan and its official source links;
- the current evidence inventory (metadata only; uploaded file contents are not embedded);
- the issue-specific evidence checklist;
- the editable support-message draft;
- user-managed follow-up information;
- a timeline of recorded actions; and
- the latest user-reported outcome.

The passport does not prove that a payment happened, a merchant answered, a refund arrived, or a government/bank complaint was submitted. User-reported statements remain labelled as such. An export can include sensitive personal information, free-text notes and reference numbers; users must inspect it before sharing.

## User workflow

1. **Explain the issue.** Use text or record a short voice note in the web intake. Voice transcription and read-aloud require a configured, valid Gnani API key and active account access.
2. **Review extracted facts.** Confirm or correct issue type, merchant, amount, date and status. Missing details remain missing instead of being guessed.
3. **Preview guidance.** Read the recommended first action, issue-specific steps, missing information and official source links. The app has not queried a bank, merchant, NPCI or government system.
4. **Save the case.** The case record and timeline become the source of truth for follow-up.
5. **Prepare evidence and a message.** Check off relevant items, prepare/edit a support message, and save follow-up date/notes.
6. **Record what happened.** In the Outcome tab, select still pending, no response, partially resolved, resolved, or stopped pursuing. The result is stored as `user_reported`, not external verification.
7. **Take the case elsewhere.** Download the text action pack, download the JSON passport, print/save a PDF, copy the draft, open an email draft, or open WhatsApp with the draft prefilled. Nothing is sent automatically.

## Export formats

### Portable JSON

`GET /api/cases/{case_id}/passport.json`

Returns a versioned JSON file with `passport_format: bolkeresolve-resolution-passport` and `format_version: 1.0`. It includes case facts, resolution plan/source references, evidence metadata (not file bytes), checklist, follow-up, draft, latest outcome and a filtered timeline. It deliberately does not export provider credentials, raw WhatsApp phone fingerprints, authentication data or evidence bytes.

### Printable passport / PDF

`GET /api/cases/{case_id}/passport/print`

Returns a self-contained HTML document that can be printed or saved as PDF using the browser. Dynamic text is HTML-escaped. The response is marked `no-store` because it includes private case details. The browser print UI is provided by the user's browser; the server does not generate or store a PDF.

### Existing action pack

`GET /api/cases/{case_id}/action-pack`

The existing text pack remains available. The passport is a more structured and portable addition, not a replacement for the action pack.

## No-API handoff

- **WhatsApp draft:** opens a `wa.me/?text=...` URL with the user's current reviewed draft. The user must choose the recipient, review the message and press Send. BolKeResolve cannot observe send, delivery or reply events through this handoff.
- **Email draft:** opens a `mailto:` draft. The user selects the recipient and reviews/sends it in their own mail client. Delivery is not tracked by BolKeResolve.
- **Copy/export:** supports workflows where the organization uses a portal, app, phone or in-person channel.

These handoffs don't bypass WhatsApp business policies and don't turn the website into an automated WhatsApp bot. No fake or inferred company support number is used.

## PWA / installable web shell

The manifest and service worker make the public shell installable on supporting browsers. The service worker may cache only an explicit list of public static UI resources. All `/api/` routes—including authentication, cases, evidence, voice and provider webhooks—are network-only. **Private case data is not available offline.** This is intentional: caching sensitive case data on a shared phone would create a privacy risk. Offline shell display does not imply offline case creation or sync.

The `Install app` button appears only when the browser exposes an install prompt. On browsers without that event, use the browser menu's “Install app” / “Add to Home screen” option if offered.

## Outcome provenance and timeline

The `PUT /api/cases/{case_id}/outcome` endpoint accepts one of:

- `still_pending`
- `no_response`
- `partially_resolved`
- `resolved`
- `stopped`

Outcome details and optional reference are best-effort screened for sensitive-looking content. The database stores the latest outcome; each save adds a timeline event. The UI and exports expressly state that an outcome is self-reported and not independently verified. Case stage may be updated to a user-reported stage to keep the journey coherent; this is not an external status check.

## Manual QA checklist

Use fictional or properly redacted test stories.

- [ ] Create a delayed refund case from text and a separate one using Gnani voice (only with an authorized key).
- [ ] Confirm the user can review/correct facts before saving.
- [ ] Check that each issue renders relevant deterministic official-source guidance.
- [ ] Check/uncheck evidence items and confirm readiness updates.
- [ ] Prepare and edit the support draft; verify it is not automatically sent.
- [ ] Save a follow-up date, note, and completion state.
- [ ] Record each outcome type; verify the latest outcome and a new timeline event.
- [ ] Download and parse the JSON passport; ensure it includes the source list and provenance note but not evidence bytes or provider credentials.
- [ ] Open the print passport, test on mobile and use Print / Save as PDF.
- [ ] Open WhatsApp and email draft handoffs; verify that the destination is not selected automatically and the user retains control over sending.
- [ ] Confirm exports warn users to review personal/reference data before sharing.
- [ ] Install the PWA on a supported browser, then verify private API/case data are not cached; disconnect network and confirm the UI explains that case actions require reconnection.
- [ ] In production mode, confirm a different user cannot access the case, outcome, timeline, evidence, JSON export or print export.
- [ ] Delete a test case and confirm local evidence deletion behavior and outcome cascading match the existing deletion workflow.

## Before public launch

This product is still an MVP. A public launch additionally requires a real privacy notice, monitored support contact, TLS and trusted proxy configuration, persistent database/evidence storage, tested backup and restoration, account recovery/deletion/retention process, production monitoring, shared AI usage quotas, upload malware scanning, dependency/security review, accessibility/mobile QA and appropriate legal/privacy review. A print or JSON export can contain sensitive information and should only be downloaded on devices the user trusts.
