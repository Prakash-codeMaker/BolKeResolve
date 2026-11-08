# Live Resolution Room — 31 October 2026

## What changed

- Added a responsive Live Resolution Room entry and workspace using the existing BolKeResolve cream/forest-green/mint visual language, DM Serif Display and DM Sans. Desktop uses conversation/evidence plus a compact case/guidance column; mobile stacks the same tasks.
- Added browser permission-based microphone and camera startup. Camera failure does not prevent microphone-only or typed/document use.
- Added a same-origin backend WebSocket proxy to Gnani Prisma realtime STT. The Gnani API key stays server-side. Browser audio is converted to mono PCM16 16 kHz frames by an AudioWorklet.
- Final transcript segments and typed turns are saved to the existing case timeline and run through the existing deterministic resolution rules. Server-authored guidance is stored separately with provenance.
- Added session start/end timeline events after a case is created. User turn provenance distinguishes typed text, live speech and user-confirmed transcript from an imported support recording.
- Reused existing evidence storage and OCR review/confirmation for photos, screenshots and PDFs. Added short WEBM/MP4 video and WAV/MP3/M4A/OGG/FLAC/AAC recording support with size/signature checks. Imported audio stays evidence; its transcript is a preview until confirmed.
- Added manual camera photo capture, explicit user-selected screen capture (one still image), optional 30-second camera/microphone video clip and transcript preview/confirmation for imported support-call recordings.
- Connected Live Room to existing cases, evidence list, official source links, Resolution Passport and case-detail navigation. No new case database or separate dashboard was introduced.
- Enabled camera, microphone and display-capture only for the same origin in the response Permissions-Policy. Added `websockets` dependency and `.env.example` so the Windows launcher can create local config on first run. Static shell cache bumped to v25.

## Validation

- `node --check frontend/app.js` — passed.
- `node --check frontend/sw.js` — passed.
- `python -m py_compile backend/main.py` — passed.
- `python -m pytest -q` — **265 passed, 90 subtests passed**.
- Playwright Chromium navigation to the local test server was blocked by the environment. Manual Chrome/Edge browser and camera/microphone QA remains required.
- Live Gnani calls were not run because no user API key was provided.

## Important boundaries

- The live rule response is generated from existing deterministic resolution playbooks, not from a newly integrated autonomous LLM agent.
- Prisma provides speech recognition; Timbre reads text but does not translate the English rulebook content into Hindi merely because a Hindi locale is selected. Same-language generative guidance needs a separate translation/reasoning model and evaluation.
- Camera images and PDFs use the existing candidate extraction/review path. This increment does not add continuous video understanding or a separate vision LLM.
- The chosen screen share is user-authorised and only a single captured still is saved; it is not continuous screen recording.
- Video/audio imported by the user is stored as case evidence; browser live microphone audio is streamed to Gnani for STT and is not saved as raw audio by this app.
- Deployment, production privacy/security review, hosting, backup/restore and live provider verification remain incomplete.


## Persistence and reliability corrections — 31 October 2026

- Changed the user journey to create a persistent draft case before requesting camera/microphone permissions; the initial case state explicitly explains that it is already saved.
- Changed screen sharing so the first selected frame is uploaded immediately after the preview is ready. The preview remains visible and users can capture additional frames without stopping the share.
- Serialised typed/live-speech/imported-audio transcript turns to prevent overlapping case writes.
- Corrected permanent WebSocket close handling: missing server credentials, rejected origin/auth and rate limits no longer trigger repeated reconnect attempts.
- Set Prisma realtime headers to the currently documented names (`language_code`, `model`, `format`) and added a mocked integration test asserting the proxy request.
- Updated the service-worker shell cache to v26 and corrected the frontend regression assertion.
- Reworded print/export controls to distinguish the print/save-PDF report from the complete original evidence ZIP.
- Verification after these changes: `PYTHONPATH=. pytest -q` — **271 passed, 90 subtests passed**; `node --check frontend/app.js` and `node --check frontend/sw.js` passed.
- Real browser and live Gnani API verification are still blocked by this environment/absence of user credentials; see `docs/LIVE_ROOM_END_TO_END_SMOKE_TEST.md`.
