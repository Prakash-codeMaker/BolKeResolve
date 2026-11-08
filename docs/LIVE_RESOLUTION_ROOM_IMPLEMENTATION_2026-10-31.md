# BolKeResolve Live Resolution Room — implementation notes

**Implementation date:** 31 October 2026  
**Source of truth:** latest uploaded BolKeResolve source archive, extended in-place.  
**Design intent:** add a voice-first guided session to the existing website and persist it inside the existing case, evidence, timeline and Resolution Passport system. This is not a second case-management product.

## Product experience

The visitor opens **Live resolution**, reads a short privacy notice, and starts a session. The browser requests microphone and rear-camera access; if camera permission is declined/unavailable, microphone-only and text/document alternatives remain available. The session workspace follows the existing cream / forest-green / mint design system, with a conversation and camera surface on the left and the current case, evidence and next-step guidance on the right. On narrow screens these areas stack vertically.

Users can:

- Speak in a selected supported Indian-language locale or Hinglish. Final transcripts arrive from Gnani Prisma realtime STT and are saved as user turns in the case timeline.
- Type a message if speech is unavailable.
- Capture a still photo from the live camera and store it as case evidence.
- Upload PNG, JPG/JPEG, WEBP, PDF, short WEBM/MP4 video and supported audio recordings. The upload uses the existing evidence store and per-case limits.
- Run the existing image/PDF evidence-review path. OCR/text extraction returns candidate facts for the user to inspect; facts only become confirmed case facts when explicitly selected and saved.
- Import a support-call recording. The original recording is stored as evidence; Gnani REST transcription produces a preview; transcript text is only added to the case conversation after the user confirms it.
- Choose a screen to share using the browser permission dialog, then capture one still image into the case. The app does not continuously record or stream screen content to a vision model.
- Record a short camera-plus-microphone WEBM clip (maximum 30 seconds, 20 MB) and store it as evidence. Video is not automatically semantically analysed in this build.
- Receive current deterministic, source-backed resolution guidance from the existing `backend.resolution` playbooks. Guidance is recorded as an assistant-originated timeline event, explicitly labelled as generated first-pass guidance and not an external organisation's response.
- End the session. Start/end lifecycle events are written to the same case timeline once a case exists.

## Architecture

- **Frontend:** `frontend/index.html`, `frontend/live-room.css`, `frontend/live-pcm-processor.js`, and the Live Resolution Room section in `frontend/app.js`. It uses the existing fonts, palette, components and `showView()` routing; no new frontend framework is introduced.
- **Speech:** browser microphone → Web Audio `AudioWorklet` (mono PCM16, 16 kHz frames) → same-origin FastAPI WebSocket proxy → Gnani Prisma realtime STT. The Gnani key is read only by the backend. Final transcript segments are de-duplicated in the browser before being saved.
- **Speech output:** uses the existing server-side `/api/voice/speak` Timbre integration. The generated plan is deterministic English text in this version; Timbre does not translate the content merely because a Hindi voice locale is selected. Do not describe this build as a complete same-language generative voice agent until a grounded translation/reasoning model is connected and evaluated.
- **Resolution:** existing deterministic resolution engine and official source directory. The server returns a bounded summary of the current plan; the browser cannot submit arbitrary text and claim it came from BolKeResolve.
- **Evidence:** existing case-scoped evidence storage and OCR review/confirmation endpoints. No second document store is created.
- **Persistence:** user turns, server-authored guidance and live-session lifecycle events are stored in the existing `timeline`; images, PDFs, audio and video are stored in the existing `evidence` table and evidence directory; extracted candidate facts use the existing provenance review system. The Resolution Passport already exports timeline/evidence metadata.
- **Security:** microphone audio used for streaming STT is forwarded to Gnani and is not stored as raw audio by the web app. Camera preview stays in the browser until the user captures/uploads. Imported audio and recorded video are persisted as evidence because the user deliberately selected/recorded them. Never capture OTPs, UPI PINs, passwords, full card numbers or Aadhaar/PAN. File signature checks are basic validation, not malware scanning.

## API surface added

- `WS /api/live-room/voice?language_code=...` — same-origin proxy to Gnani Prisma realtime STT. Provider key never reaches the browser.
- `POST /api/cases/{case_id}/live-room/turn` — stores a user turn, redacts sensitive-looking text and recalculates the existing deterministic resolution plan. Metadata records whether the source was typed, live speech or a user-confirmed imported recording transcript.
- `POST /api/cases/{case_id}/live-room/guidance` — generates and records server-authored first-pass guidance from the currently stored resolution plan.
- `POST /api/cases/{case_id}/live-room/session-event` — stores session start/end in the case timeline.
- Existing `POST /api/cases/{case_id}/evidence`, evidence review and confirmation, `/api/voice/transcribe`, `/api/voice/speak`, case bundle and passport export endpoints are reused.

## Local setup

1. Extract the ZIP to a fresh folder.
2. Install Python 3.10+.
3. Double-click `run_windows.bat`. It creates `.venv`, installs `requirements.txt`, copies `.env.example` to `.env` if needed, and starts FastAPI on `127.0.0.1:8000`.
4. Add your own `GNANI_API_KEY` to the server-side `.env` to enable live Prisma and Timbre calls; restart the server. Keep the key out of frontend files, source control, screenshots and public posts.
5. Visit `http://127.0.0.1:8000`, select **Live resolution**, and start a session. `localhost` is allowed for camera/microphone permissions in supported browsers. A hosted site must use HTTPS and configure `BOLKE_PUBLIC_ORIGIN` as its exact HTTPS origin.
6. Use synthetic/redacted cases only until production authentication, privacy, retention, secure hosting, malware scanning, backups and legal/security checks are completed.

## Validation performed in this build

- `node --check frontend/app.js` — passed.
- `node --check frontend/sw.js` — passed.
- `python -m py_compile backend/main.py` — passed.
- `python -m pytest -q` — **265 passed, 90 subtests passed**.
- Tests cover the Live Room shell/assets/security permissions, user-turn storage and redaction, source provenance for imported transcripts, server-authored guidance, same-case audio/video evidence, session lifecycle events, Resolution Passport export and missing-Gnani-key behavior.
- Browser visual/interaction QA was attempted with Playwright Chromium but navigation to the local server was blocked by the execution environment (`ERR_BLOCKED_BY_ADMINISTRATOR`). This means layout and real camera/microphone playback still need manual validation in Chrome or Edge on the user's device.
- No live Gnani API key was provided, so upstream transcription/TTS was not independently exercised in this session. Automated tests do not mock a success and then claim real provider delivery.

## Explicit limitations before public launch

1. **Not a full autonomous multimodal AI agent yet.** The existing deterministic rule engine gives the live first-pass guidance. OCR/text extraction is the existing local evidence-review path; image/video content is not continuously sent to a vision reasoning model.
2. **Guidance language:** Prisma can transcribe supported Indic languages; the deterministic rulebook response text is English in this version. Timbre's voice locale does not translate English text into Hindi or another language. Same-language generated guidance requires a separately configured and evaluated translation/reasoning model, with source-grounded output and a human-readable fallback.
3. **Screen sharing:** explicit browser permission is required; only one user-requested still image is saved, not continuous remote screen recording.
4. **Call recordings:** users must have the lawful right and any required consent to record/share other participants. Ordinary websites cannot silently record cellular call audio.
5. **Deployment:** no public deployment is performed by this code change. Production authentication, HTTPS, exact public origin, published privacy notice, support contact, persistent storage, backup/restore, malware scanning, shared quotas, monitoring, accessibility QA and independent security/legal review remain operator tasks.

## Challenge attribution

This build uses Gnani Prisma v2.5 realtime STT and the existing Gnani Timbre v2.5 TTS integration when a valid `GNANI_API_KEY` is configured. The challenge requires a genuinely working application using at least one Gnani model/API and honest public demonstration. The challenge FAQ says the Agent Builder is outside the programme API scope; do not claim it as the technology used. Recheck the official rules before final submission: https://www.gnani.ai/internship and https://www.gnani.ai/great-indian-ai-internship-registration-form.
