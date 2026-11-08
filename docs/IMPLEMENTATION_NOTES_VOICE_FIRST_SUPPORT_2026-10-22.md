# Implementation notes — Voice-first Guided Chat + contextual support

Date: 22 October 2026

## Summary

This increment builds on the current Resolution Sprint/Passport package rather than replacing it. The case engine, database, outcome flows, export/passport, Meta adapter and Twilio Sandbox adapter are retained.

## New/updated files

- `backend/support_directory.py` — curated platform-specific official support destinations and case-specific editable draft helper.
- `backend/main.py` — attaches support context to preview, new/saved case resolution and refreshed guidance; retains `/api/voice/transcribe` with language validation and privacy/spend gates.
- `frontend/index.html` — Guided chat language selector, voice controls/status and case support components.
- `frontend/app.js` — browser audio capture, WAV encoding, transcript review before Send, browser read-aloud, official route cards for the preview and saved-case overview, HTTPS-only route handling and direct Message-tab action.
- `frontend/design-v2.css` — voice/chat guidance, support route styling and additional responsive width/overflow guardrails.
- `frontend/sw.js` — bumped the public-shell cache to `bolkeresolve-shell-v2` so installed app clients do not keep the older shell cache after updating; `/api/` remains network-only.
- `tests/test_support_directory.py`, `tests/test_frontend_assets.py`, `tests/test_resolution.py` — support routing, fraud priority, official HTTPS link constraints, draft boundary, responsive CSS, UI affordances and API output.
- `START_HERE_VOICE_FIRST_SUPPORT_2026-10-22.md` — local start, test data and manual QA.

## User-experience decisions

- Keep the first result concise: one suggested action before the details wall. The full playbook can be expanded.
- Make a specific official support route visible in Guided chat and again in the saved case workspace; do not make the user hunt among generic source lists.
- Generate an editable support draft using user-reported facts, known amount, and a clear question/request for the organisation. A draft is never submitted automatically.
- If there is a suspected unauthorised transaction, put the urgent safety route first and advise immediate bank contact; do not delay urgent advice behind a merchant route.
- Recognise a limited curated set of merchants using token-boundary matching; do not fabricate a support route for unknown merchants.
- Voice input is deliberately review-before-send: record on device, send to STT after stop, insert transcript into composer, user reviews/edits, then presses Send.
- Voice uses Gnani STT when configured; browser speech synthesis reads aloud where a usable device voice exists. TTS voice/language availability varies by browser and OS.
- The external channel remains optional. The guided chat is inside the website and must not be misrepresented as an actual WhatsApp connection.

## Verification

- `python -m pytest -q`: **134 passed, 44 subtests passed**.
- `node --check frontend/app.js`: passed.
- `python -m compileall -q backend tests scripts`: passed.
- Local smoke check through FastAPI TestClient: homepage, static CSS/JS, PWA manifest, `/api/health`, `/api/config`, and `/api/resolution/preview` returned HTTP 200. Example preview for Zomato refund returned Zomato and National Consumer Helpline routes and a draft marked not sent.
- `python scripts/check_release_readiness.py`: reports expected production warnings (development mode, no HTTPS public origin, local-style auth, privacy/support placeholders, optional Meta config). It is a preflight, not a security certification.

## Known limitations and release gates

- No real-browser screenshot/navigation pass could be completed in the build environment; local Chromium navigation was blocked/timed out. Manually test Chrome/Edge desktop, tablet and mobile widths, keyboard and screen-reader use.
- Live Gnani STT and browser recording/voice behavior were not tested with the user's credentials/device.
- Meta and Twilio live provider calls are not verified; no messaging provider is needed for the core web experience.
- Support destinations are curated and may change; periodically recheck official URLs and help instructions.
- Public voice is disabled by default in production-auth mode unless configured after privacy and spend review; voice routes have in-process rate limiting only. Multi-worker production needs a shared rate limiter.
- No direct bank/merchant verification, automatic outbound complaint submission, automatic email send, or support ticket filing exists.
- Privacy notice/legal terms, monitored support contact, retention/deletion, persistent storage/backups, upload scanning, monitoring, security review, and production deployment checks remain outstanding.
