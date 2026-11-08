# Start Here — BolKeResolve Resolution Sprint + Passport

This build introduces **Resolution Sprint**: a first useful next-step suggestion before the user fills in every detail. It then lets people review optional details and save a portable Resolution Passport. **You do not need Meta or Twilio credentials to use the core website.** WhatsApp/email are optional, user-controlled handoff actions; they do not create a live bot conversation or delivery tracking. In hosted authentication mode, first-pass previews are public and rate-limited; saving or viewing private cases still requires an account.

## Run locally on Windows

1. Extract the ZIP into a new folder. Keep your existing project folder and database as a backup; this archive does not include your private `.env`, `runtime` database, or evidence uploads.
2. Install Python 3.10 or newer if needed.
3. Double-click `run_windows.bat` and wait for the local server to start.
4. Open `http://127.0.0.1:8000` in Chrome or Edge.
5. To use voice, set your own `GNANI_API_KEY` in a private `.env` file and restart the app. Typed intake, guidance, case saving, outcomes and exports do not need the key. Never paste keys into chat or commit `.env`.

## Try the voice-first guided chat and specific support routes

- Open **Guided chat** in the top navigation. The phone-style panel is an in-site chat, not a claim that a WhatsApp API is connected.
- Choose an issue or type the story. To speak, choose a language under **Speak in** and press **Speak**. The browser must allow microphone access; use `http://127.0.0.1:8000` for local testing or HTTPS in a hosted deployment.
- Voice transcription requires a valid server-side `GNANI_API_KEY`. For an anonymous visitor on a production-authenticated deployment, public transcription is disabled unless the operator explicitly sets `BOLKE_PUBLIC_VOICE_ENABLED=true` after privacy and spend controls are ready. Without the key, the user can type.
- A recording is sent for transcription only after the user stops it. The transcript appears in the composer for review/editing; it is not sent or saved automatically. Ten Indian-language options are available: Hindi/Hinglish, English (India), Marathi, Bengali, Gujarati, Kannada, Malayalam, Punjabi, Tamil and Telugu. Auto mode asks the STT provider to try the supported language set; always check the transcript.
- Submit the story to see a first recommendation, matched official support links when the merchant or issue is recognised, and a reviewable message draft. Save the case only after reviewing it. The saved case overview also shows official support route cards with the same case context.
- Support links point to curated first-party/government destinations; case-specific instructions are guidance, not proof of contact or complaint submission. Unknown merchant names do not get fabricated support addresses. For a new/unrecognised service, BolKeResolve falls back to relevant general official guidance when the issue class supports it.

## Try the complete case flow

Use fictional information, not real credentials or unredacted payment documents.

1. Choose “Get my next step”. Type a synthetic story such as: “My ₹500 refund from Demo Store has not arrived after the promised three days.”
2. Click **Get my next step** in Step 1. Read the prominent first action; open “See all recommended steps, missing details and official sources” if you need the full plan. Nothing is saved or sent by this preview.
3. Choose **Review details to save my Passport** when you want to keep the case. Review or correct the suggested facts. You can leave unknown details blank.
4. Continue through **Review details** and **Save case**. In local development mode, the case is stored in the local runtime database. In production authentication mode, you will be asked to sign in/create an account before the private case is saved; the story stays in the form while the auth gate is open.
5. Open the saved case. The top card focuses on the next action and includes shortcuts to prepare a support message, check evidence and record the outcome.
6. On the case Overview, check the **Official support for your situation** cards. Open the matching official channel, then switch to **Message** to review/copy or open an email/WhatsApp draft. BolKeResolve has not contacted the organisation; you select the recipient and send yourself.
7. In Prep, mark the relevant evidence checklist items, edit the support draft, and save a follow-up date.
8. In Outcome, select a truthful user-reported result. It is never presented as independent verification.
9. Download the JSON passport or use Print → Save as PDF. Inspect the export before sharing; it may contain your story, private notes and support references.
10. WhatsApp and email remain optional manual handoffs. Nothing is automatically sent. Test with synthetic cases/evidence, then delete the case to validate deletion.

## PWA install

On supported browsers, choose `Install app` when it appears, or use the browser menu → Install app / Add to Home screen. HTTPS is required outside local development. The service worker may cache public static UI resources only. It does **not** cache case API responses, authentication, uploads or private case data. The site cannot create/save/update a case offline.

## What changed in Resolution Sprint

- The first-pass recommendation now appears in Step 1 alongside the story input. It foregrounds one next action and urgency, while the complete steps, missing information and source links are inside an expandable section.
- The “Get my next step” preview does not create a case or send a message. Editing the story or important facts invalidates the prior preview so it is not mistaken for current guidance.
- Visitors in production authentication mode may use first-pass preview before registration. The endpoints are rate-limited in-process; a hosted, multi-worker production environment still needs a shared gateway/WAF or distributed rate limiter. Saving and private case access still require authentication.
- The case overview has direct shortcuts to the support draft, evidence and reported outcome.

## Run verification

From the extracted project root:

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
node --check frontend/app.js
python -m compileall -q backend tests scripts
python scripts/check_release_readiness.py
```

The release check reports configuration gaps without printing secret values. A successful check is not a production/security certification.

## Before public deployment

Do not expose local development mode. Set `BOLKE_ENV=production`, configure the exact HTTPS `BOLKE_PUBLIC_ORIGIN`, publish a real privacy notice, and configure a monitored support contact. Confirm authentication is required. Use a persistent volume or managed database for SQLite and evidence, test backups/restores, finalize retention/deletion, enable server monitoring and shared quotas, assess uploaded-file malware scanning, run dependency/security review and mobile/accessibility QA, and get appropriate privacy/legal review. The included privacy page is a draft template; replace placeholders and ensure its practices match the implementation before launch.

## Product architecture

- The shared case record is the source of truth.
- Gnani STT/TTS is optional for voice; it is not required for typed workflows.
- Meta Cloud API and Twilio Sandbox adapters remain available as optional messaging paths.
- `wa.me` and `mailto:` are user-controlled handoffs, not bot transports. No recipient is guessed, no message is automatically sent, and handoff delivery is not tracked.
- Outcomes are user-reported, not independently verified.
- See `docs/RESOLUTION_PASSPORT_AND_NO_API_HANDOFF.md`, `docs/PRODUCT_STRATEGY_RESET_AND_COMPETITIVE_RESEARCH_2026-10-21.md`, and `IMPLEMENTATION_STATUS.md` for details and remaining work.


## Living Passport and forwarded-reply integration (23 October 2026)

The current build adds optional evidence text review with explicit confirmation and a case-specific inbound email bridge. Read [`docs/LIVING_RESOLUTION_PASSPORT_AND_CASE_INBOX_BRIDGE_2026-10-23.md`](docs/LIVING_RESOLUTION_PASSPORT_AND_CASE_INBOX_BRIDGE_2026-10-23.md) before enabling it. The email bridge does not go live merely by deploying: configure an owned inbound domain/MX, stable Fernet key and strong webhook authentication first. Do not claim live provider validation until a real HTTPS webhook delivery test passes.
