# Start here — BolKeResolve Voice-First Guided Chat + Case-Specific Support

**This is a local-test build, not a production certification.** It preserves the Resolution Sprint, Resolution Passport and shared case engine, and adds multilingual voice input in Guided chat plus curated official support routes in both the preview and saved-case workspace. Meta/Twilio are optional.

## Run on Windows

1. Extract this ZIP to a new folder. Do not replace your old project folder. This ZIP intentionally excludes `.env`, `runtime/`, SQLite databases, evidence uploads, virtual environments and Python cache files.
2. Install Python 3.10 or newer.
3. Double-click `run_windows.bat`; first startup creates `.venv`, installs requirements and copies `.env.example` to `.env` if needed.
4. Open `http://127.0.0.1:8000` in Chrome or Edge.
5. Test with synthetic details only until your privacy, retention and production security controls are reviewed.

## Try the new guided chat

1. Click **Guided chat**.
2. Select a language under **Speak in**, or leave **Detect language** selected. Choices cover Hindi/Hinglish, English (India), Marathi, Bengali, Gujarati, Kannada, Malayalam, Punjabi, Tamil and Telugu.
3. Enter your own Gnani API key as `GNANI_API_KEY` in `.env`, then restart the app. Voice transcription uses paid/provider-account usage if applicable; it is not live-verified in this build environment.
4. Allow microphone access. On localhost, `getUserMedia` is normally available in Chrome/Edge; a hosted deployment needs HTTPS. Click **Speak**, record for up to 60 seconds, then **Stop and transcribe**.
5. Read or edit the transcript in the composer. It is not auto-sent. Press Send only when it is correct.
6. Review the first action, relevant official support route(s), source links and the editable draft. The app has not contacted a company and has not checked bank/merchant records.

If no Gnani key is configured or voice is disabled by production settings, use text entry. In production-auth mode, public voice remains off by default unless the operator enables `BOLKE_PUBLIC_VOICE_ENABLED=true` after reviewing privacy, rate limiting and usage controls.

## Test case-specific support

Try each preview with a fictional example:

- **Zomato refund:** `Zomato promised a refund in three days but I still have not received it after eight days.` Expected route: Zomato official support first, then National Consumer Helpline where relevant.
- **PhonePe / UPI:** `My PhonePe UPI payment failed but money was debited.` Expected route: PhonePe official support plus relevant NPCI/UPI guidance where applicable.
- **Possible unauthorised transaction:** `I do not recognise this transaction and suspect fraud.` Expected: safety/official cybercrime route first, with immediate bank contact guidance. Do not wait for the rest of the app flow in a real emergency.
- **Unknown merchant:** use a fictional brand not in the curated directory. The app must not invent customer-support phone numbers or URLs; it may provide relevant general official guidance if the issue fits.

Save one synthetic case and open it. In the saved case Overview, confirm the **Official support for your situation** cards are visible. **Prepare message** should route you to the editable Message tab. The links open in a new tab and are restricted to HTTPS URLs; review destinations periodically because organisations can change their support flows.

## What to verify manually

- At desktop and tablet widths, the intake side rail should not clip off the right edge. At mobile width, the form and helper cards should stack into a single column.
- In Guided chat, voice controls should stay within the phone-style panel; try the selector, Speak/Stop, transcript review, Send, Listen, and the text-only fallback.
- Run one case from story → preview → review → save → case overview → official support link → editable draft → outcome → export → delete.
- Check unknown merchants, contradictory amounts, low-confidence extraction and suspected-fraud priority. Never use real OTPs, UPI PINs, passwords, full card numbers or unredacted identity documents.
- Confirm keyboard focus, screen-reader labels, responsive layout, and that failed STT shows an error and allows typing.

## Commands

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
node --check frontend/app.js
python -m compileall -q backend tests scripts
python scripts/check_release_readiness.py
```

Latest code-level checks: **133 tests passed, 44 subtests passed**; JavaScript syntax and Python compilation pass. A local API smoke check returned HTTP 200 for `/`, static CSS/JS, manifest, `/api/health`, `/api/config`, and a Zomato refund preview with Zomato + National Consumer Helpline links.

Visual QA remains incomplete: the available headless-browser environment blocked/timed out while navigating to the local server. Live Gnani transcription, real microphone/device behavior, Meta and Twilio messaging, production auth, public HTTPS, and deployment are not claimed verified.

## What the app does not do

- It does not log into your bank/merchant account, verify payment or refund records, contact the organisation, file an NCH/NPCI/RBI/cybercrime complaint, or send the support draft automatically.
- A recorded/selected status and outcome are user-reported unless explicitly stated otherwise by a future verified integration.
- WhatsApp/email actions are manual handoffs; they do not provide live bot messaging unless the relevant provider is separately configured and validated.

Before public launch, configure production authentication, exact HTTPS public origin, a real privacy notice and monitored support contact; use durable database/evidence storage with backups and restore tests; add shared edge rate limits, monitoring, retention/deletion process, upload malware scanning strategy, dependency/security review, and complete privacy/legal review and real-device accessibility QA.


## UX refinement included (22 Oct 2026)
- Homepage hero now communicates the specific outcome users get.
- Guided chat starts with four common issue choices; secondary choices are under “Another issue”.
- The in-app chat is explicitly distinguished from WhatsApp.
- Case progress and export tools are collapsed under “Track this case” so the recommended next action remains dominant.
- See `docs/UX_REDESIGN_RESEARCH_AND_IMPLEMENTATION_2026-10-22.md` for research sources, design decisions and manual acceptance checks.
