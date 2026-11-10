<!--
  BolKeResolve README
  Product overview, workflow, setup and honest capability boundaries.
-->

<!-- Evaluator entry point: keep the one-page pitch visible above the fold. -->
# 🚀 START HERE — ONE-PAGE SOLUTION PITCH

**New to BolKeResolve?** Read the complete solution pitch first. It explains the problem, product, Gnani AI integration, Promise-to-Proof differentiator and trust boundaries in under 400 words.

### [📄 READ THE ONE-PAGE SOLUTION PITCH →](SOLUTION_PITCH.md)

### Product demonstration

[![Watch the BolKeResolve product walkthrough](https://img.youtube.com/vi/2REWdhKfT_I/hqdefault.jpg)](https://youtu.be/2REWdhKfT_I)

[**Watch the full product demonstration on YouTube →**](https://youtu.be/2REWdhKfT_I)

[**Open the live application (Vercel) →**](https://bolkeresolve.vercel.app) · [Backend health check (Render) →](https://bolkeresolve.onrender.com/api/health) · [Read the demo walkthrough](docs/challenge/GNANI_AI_CHALLENGE_60_SECOND_DEMO.md)

---

<div align="center">
  <img src="frontend/assets/bolkeresolve-icon-512.png" alt="BolKeResolve logo" width="88" height="88" />
  <h1>BolKeResolve</h1>
  <p><strong>From payment confusion to a clearer next step.</strong></p>
  <p>
    A voice-first, evidence-aware case workspace for everyday payment and refund issues in India.
  </p>
  <p>
    <a href="https://github.com/Prakash-codeMaker/BolKeResolve"><img src="https://img.shields.io/badge/project-BolKeResolve-0b5148?style=for-the-badge" alt="BolKeResolve" /></a>
    <img src="https://img.shields.io/badge/interface-voice%20%2B%20chat-159b83?style=for-the-badge" alt="Voice and chat" />
    <img src="https://img.shields.io/badge/status-MVP%20%2F%20active%20development-d5a33d?style=for-the-badge" alt="MVP in active development" />
  </p>
  <p>
    <a href="SOLUTION_PITCH.md"><strong>START HERE: Read the One-page Solution Pitch →</strong></a> ·
    <a href="docs/challenge/GNANI_AI_CHALLENGE_60_SECOND_DEMO.md">Challenge Demo Walkthrough</a>
  </p>
  <p>
    <a href="#how-it-works">How it works</a> ·
    <a href="#product-capabilities">Capabilities</a> ·
    <a href="#run-locally">Run locally</a> ·
    <a href="#deployment">Deployment</a>
  </p>
</div>

---

## Gnani challenge: evaluator quick start

**Watch first:** [BolKeResolve product demonstration](https://youtu.be/2REWdhKfT_I)  
**Read the one-page pitch:** [SOLUTION_PITCH.md](SOLUTION_PITCH.md)  
**Follow the demo walkthrough guide:** [Feature-by-feature recording guide](docs/challenge/GNANI_AI_CHALLENGE_60_SECOND_DEMO.md)

The intended review path is: open the live app → use a synthetic Hinglish payment complaint → review the actual transcript → inspect issue guidance → save the fictional ₹850 support commitment → record the later synthetic user-reported update separately → inspect the Resolution Passport.

**Model attribution:** the repository template defaults to Prisma `prisma-v3.0` (speech-to-text) and Timbre `timbre-v2.5` (text-to-speech). The public Gnani challenge page currently lists Prisma v2.5, so verify the exact successful model ID in the API/account logs before naming it in a final video. The Promise-to-Proof ledger and case-resolution workflow are application logic. This project does not claim Evon use.

**Important boundary:** this is an MVP for organising user-provided information. It does not access bank accounts, independently verify a UPI transaction, contact merchants, move money, or automatically submit a complaint. The example case data is fictional.

Before judging, test the live URL in a fresh browser and on a phone. If an account is required, use your own evaluator account; do not request or share the developer's personal credentials.

## The problem

A failed UPI payment, a delayed refund or an unfamiliar charge can quickly turn into a confusing chain of screenshots, messages, reference numbers and support conversations.

People often have the information they need, but it is scattered—and it is not always clear what to check or do next.

**BolKeResolve helps bring that information together.** Explain the issue in your own words, add the records you already have, review the important details and keep a structured case history with a practical next step.

> One conversation. Your evidence. A clearer next move.

## How it works

<p align="center">
  <img src="docs/assets/readme/workflow-overview.svg" alt="BolKeResolve workflow: tell your story, add evidence, review the next step and keep your case record" width="100%" />
</p>

1. **Tell your story.** Start with voice, Guided Chat or the issue form. You can use familiar language and leave unknown details blank.
2. **Add evidence.** Attach receipts, screenshots, PDFs, recordings or support messages. Review extracted information before confirming it.
3. **Review the next step.** BolKeResolve uses the available case details and resolution playbooks to suggest a practical, source-linked action.
4. **Keep your record.** Continue the case timeline, record follow-ups and export a portable Resolution Passport.

## Product capabilities

| Area | What it does |
|---|---|
| **Live Resolution** | Voice-led case intake with typed input, transcript review, optional camera/document/screen capture and a case-specific next-step panel. |
| **Guided Chat** | A WhatsApp-style in-site conversation. Speak or type, choose a supported speech language when configured, and save the reviewed conversation to a case. |
| **Issue guidance** | Deterministic first-pass playbooks for common failed-payment, pending-payment, delayed-refund, duplicate-charge and related issues. |
| **Evidence workspace** | Case-linked files, previews, metadata, extraction review, provenance labels and relationships between evidence and claims. |
| **Case timeline** | A chronological history of conversation turns, user-confirmed facts, support contacts, follow-ups and case events. |
| **Promise-to-Proof ledger** | Review a support statement, preserve its source wording, track conditions and estimated timeframes, and reconcile later user-reported updates without overwriting earlier history. |
| **Resolution Passport** | Structured JSON and printable case summary, plus ZIP exports containing selected case records and original evidence. |
| **Accounts** | Sign-up, sign-in, sessions, account-scoped cases, email verification and password recovery when Resend API or SMTP delivery is configured. |

### See the product

<p align="center">
  <a href="docs/assets/readme/issue-intake-preview.svg">
    <img src="docs/assets/readme/issue-intake-preview.svg" alt="BolKeResolve issue intake screen with common payment and refund paths" width="48%" />
  </a>
  <a href="docs/assets/readme/guided-chat-preview.svg">
    <img src="docs/assets/readme/guided-chat-preview.svg" alt="BolKeResolve Guided Chat with issue suggestions and voice or text input" width="48%" />
  </a>
</p>
<p align="center">
  <a href="docs/assets/readme/live-workspace-preview.svg">
    <img src="docs/assets/readme/live-workspace-preview.svg" alt="BolKeResolve Live Resolution case workspace showing conversation, evidence and next-step guidance" width="82%" />
  </a>
</p>

These are clean, scalable interface previews recreated from the product’s current screens. Names, amounts and case details are illustrative; they are not customer testimonials or proof of a real payment outcome.

## What makes the case record useful?

BolKeResolve is designed to keep related information together instead of leaving it scattered across chat messages and file uploads.

- **Facts retain their source.** A user statement, an extracted candidate and a user-confirmed fact are not treated as the same thing.
- **Original evidence is preserved.** OCR, transcription, redaction and AI observations are derivatives; they should not silently replace the original file.
- **Corrections remain traceable.** Important fact and transcript changes retain history instead of silently overwriting earlier information.
- **Claims can be linked to evidence.** A file can support, contradict or provide context for a particular claim.
- **Exports stay structured.** The Resolution Passport combines the summary, timeline, facts, conversation and evidence index.

## Resolution Passport

A case can be exported so the user can continue the conversation with the relevant support channel or organisation outside BolKeResolve.

The export can include:

- Case summary, status and next action
- Chronological timeline and conversation transcript
- User-confirmed facts and superseded/disputed details
- Evidence index and original uploaded files
- Available extraction/transcript derivatives
- Export manifest and SHA-256 file hashes

The package is a **user-assembled case record**. A hash can help detect whether a file changed; it does not prove who created the file, when it was created or whether its contents are true. The export is not a certified legal record.

See [Resolution Passport and no-API handoff](docs/RESOLUTION_PASSPORT_AND_NO_API_HANDOFF.md).

## Architecture

```mermaid
flowchart LR
    U[User] --> FE[Browser interface]
    FE --> API[FastAPI application]
    API --> DB[(SQLite case database)]
    API --> FS[(Evidence files)]
    API -. optional speech .-> GN[Gnani speech services]
    API -. optional AI review .-> AI[Configured AI provider]
    API --> RP[Resolution Passport exports]
```

**Current stack**

- **Frontend:** HTML, CSS and JavaScript; responsive browser experience and PWA shell.
- **Backend:** Python and FastAPI.
- **Persistence:** SQLite database and case-scoped evidence files.
- **Speech:** optional server-side Gnani Prisma speech-to-text and Timbre text-to-speech integrations.
- **Optional AI features:** separately configured AI case understanding, image review and translation features.

Provider credentials belong in the server environment. They must never be placed in frontend JavaScript or committed to Git.

## Run locally

### Windows

1. Download or clone this repository.
2. Open the project folder.
3. Double-click `run_windows.bat`.
4. On first launch, the script creates the virtual environment and installs the Python requirements.
5. Open **http://127.0.0.1:8000** in Chrome.
6. Create an account from the header and start a sample case.

The supplied `.env.example` contains local development defaults. The launcher copies it to `.env` only when `.env` does not already exist.

### Configure optional speech

1. Open your local `.env`.
2. Add your own key to `GNANI_API_KEY`.
3. Save the file and restart the application.
4. Test with non-sensitive sample audio.

The speech key is read by the backend. Do not add it to browser code.

### Configure optional AI assistance

AI case understanding, image review and translation are separate from speech transcription. They require their own configured AI provider and the relevant user consent. If they are not configured, the interface should explain that clearly; the core case workflow remains usable.

### Tests and checks

From the project root:

```bash
python -m pytest -q
python -m compileall -q backend
node --check frontend/app.js
node --check frontend/sw.js
python scripts/check_release_readiness.py
```

See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for the latest recorded checks and outstanding validation.

## Deployment

The recommended hosting split for the current storage architecture is:

- **Vercel frontend:** [Open the live application](https://bolkeresolve.vercel.app) — static frontend served from `frontend/`.
- **Render backend:** [Open the FastAPI service](https://bolkeresolve.onrender.com) · [Check API health](https://bolkeresolve.onrender.com/api/health) — backend service with the persistent disk used for SQLite and uploaded evidence.
- **Vercel rewrite:** same-origin `/api/*` requests are forwarded to the Render service.

Do not deploy the current SQLite/local-file backend as a Vercel Function and expect its filesystem to persist.

Follow the repository's [Vercel + Render deployment guide](VERCEL_DEPLOYMENT_GUIDE.md). Before enabling real users, validate account registration, email delivery, uploads, evidence persistence after restart, exports and the Live Resolution WebSocket on the deployed Preview URL.

## Account email delivery

BolKeResolve supports Resend HTTPS API, a Google Apps Script bridge that sends through the operator's Gmail account (no custom domain required), or SMTP on hosts that permit it. Provider priority is Resend, then Gmail Apps Script, then SMTP.

### Gmail without a custom domain (Render Free)

1. Open [Google Apps Script](https://script.google.com/) while signed in to the Gmail account that should send BolKeResolve emails.
2. Create a project and paste the contents of [integrations/google-apps-script/Code.gs](integrations/google-apps-script/Code.gs) into its editor.
3. In Project Settings > Script Properties, add `BOLKE_MAIL_BRIDGE_TOKEN` with a newly generated random value of at least 32 characters. Do not put this secret in GitHub.
4. Run the `authorizeMailBridge` function once in the editor and approve the MailApp permission.
5. Select Deploy > New deployment > Web app. Set Execute as to Me and access to Anyone (including anonymous access if that option is shown). Deploy and copy the `/exec` URL.
6. In Render Environment, set `BOLKE_GMAIL_SCRIPT_URL` to that `/exec` URL, `BOLKE_GMAIL_SCRIPT_TOKEN` to the exact same secret from Script Properties, and `BOLKE_EMAIL_FROM` to the Gmail address of the account that owns the script. Keep `BOLKE_PUBLIC_ORIGIN` as the exact HTTPS frontend origin.
7. Save the Render variables, allow the service to restart, and check `/api/config` for `auth_email_delivery_provider: gmail_apps_script`. Then test a new account registration and confirm the email arrives.

The bridge checks a shared secret before sending and uses Google's MailApp service. Consumer Gmail Apps Script accounts generally have a daily recipient quota (historically 100 recipients/day); check the live [Apps Script quotas](https://developers.google.com/apps-script/guides/services/quotas) for the current limit on the account. The public web-app URL must be protected by a high-entropy token; never store the token in browser code or commit it to Git.

### Resend alternative

Set `RESEND_API_KEY` and `BOLKE_EMAIL_FROM` to use Resend. Normal delivery requires a verified sender domain; its shared test sender is not for arbitrary public recipients.

## Privacy, safety and capability boundaries

BolKeResolve is a case-organisation and guidance tool—not a bank, payment network, merchant support agent or legal representative.

- It does **not** independently verify a bank transaction, refund credit or settlement.
- It does **not** automatically contact a merchant, file a complaint or guarantee that a support message was delivered.
- A support message remains a draft until the user sends it through their chosen channel.
- OCR and AI output are observations or candidate facts, not proof. Users review and confirm details.
- File-signature checks are not malware scanning. Production uploads still need a real scanning/quarantine strategy.
- Do not enter OTPs, UPI PINs, passwords, full card details or other authentication secrets.
- Use synthetic or redacted data during demos and testing.

Before a public launch, the operator must complete the privacy notice, configure HTTPS and trusted origins, test email verification and password recovery, verify persistent storage and backups, and complete security/accessibility review. MFA/passkeys, managed object storage and malware scanning remain separate production-hardening work.

## Project structure

```text
BolKeResolve/
├── backend/                 # FastAPI routes, case logic and integrations
├── frontend/                # Browser application, styles and PWA shell
│   └── assets/              # Product artwork and local image fallbacks
├── tests/                   # Automated regression tests
├── docs/                    # Architecture, product and manual QA guides
├── scripts/                 # Release checks and operator utilities
├── render.yaml              # Render Blueprint
├── vercel.json              # Vercel frontend and API rewrite
├── requirements.txt         # Python dependencies
├── run_windows.bat          # Windows local launcher
└── .env.example              # Safe configuration template
```

## Documentation

| Guide | Purpose |
|---|---|
| [Live Resolution implementation](docs/LIVE_RESOLUTION_ROOM_IMPLEMENTATION_2026-10-31.md) | Voice session, evidence capture and case persistence |
| [Live Room smoke test](docs/LIVE_ROOM_END_TO_END_SMOKE_TEST.md) | Manual end-to-end test sequence |
| [Resolution Passport](docs/RESOLUTION_PASSPORT_AND_NO_API_HANDOFF.md) | Export structure and user-controlled handoff |
| [Evidence provenance](docs/EVIDENCE_PROVENANCE_AND_REPLY_REVIEW_2026-10-22.md) | Source labels, claim links and reply review |
| [Vercel + Render deployment](VERCEL_DEPLOYMENT_GUIDE.md) | Hosting configuration and release checks |
| [Implementation status](IMPLEMENTATION_STATUS.md) | Verified work and outstanding gates |
| [Asset credits](ASSET_CREDITS.md) | Image and artwork source record |

## Project status

BolKeResolve is an actively developed MVP. The recorded automated suite has passed **360 tests and 129 additional subtests** in the packaged release checks. That does not replace live provider verification, deployed-browser testing, backup-restore testing, security review or legal/privacy review.

Contributions, bug reports and usability feedback are welcome. Please do not include real customer records, credentials or payment secrets in public issues.

---

<div align="center">
  <img src="frontend/assets/bolkeresolve-icon-192.png" alt="" width="32" />
  <p><strong>BolKeResolve</strong><br/>A clearer next step, with your case kept together.</p>
</div>
