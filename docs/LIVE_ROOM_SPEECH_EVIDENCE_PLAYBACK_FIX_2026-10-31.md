# BolKeResolve Live Room — Speech, recording, evidence playback and UX fixes

**Build date:** 31 October 2026  
**Base:** `BolKeResolve_Live_Multimodal_Evidence_Guidance_2026-10-31.zip` working tree  
**Scope:** Correct the failure paths reported in the Live Resolution Room screenshots without replacing the existing FastAPI case model, resolution engine, evidence store, commitment tools or Resolution Passport.

## Executive result

This build adds two user-controlled speech recovery paths, preserves original audio notes, improves microphone diagnosis, exposes evidence from the case overview, and strengthens inline playback and media recording. Automated validation passes **288 tests and 117 subtests**; JavaScript syntax and Python compilation pass. Actual Gnani transcription and physical Chrome camera/microphone/screen tests still require the operator's credentials and device.

## Root causes addressed

### 1. Live transcription can appear connected without returning a transcript

The streaming microphone path depends on the upstream VAD deciding when an utterance has ended. A connected socket or active audio meter does not prove that a transcript was returned. Long monologues, a noisy room, a selected wrong input, soft voice, or a provider error can leave the UI waiting.

**Changes:**
- Added **Finish speaking**, which sends Gnani's documented `commit` control message through the existing backend WebSocket proxy. This asks the provider to close the current utterance immediately rather than relying only on silence detection.
- Added a **Record voice note** fallback. It records up to 60 seconds from a cloned microphone track while pausing live-stream forwarding to avoid duplicate speech recognition. The original recording is uploaded into the existing case as evidence. A temporary 16 kHz mono WAV copy is created client-side for the existing Gnani REST transcription endpoint. The original remains stored even when WAV conversion or transcription fails.
- The transcript is still a preview. The user must confirm it before it is added as a case turn and used to refresh guidance.
- The record-note control gives an explicit status, auto-stops at 60 seconds, preserves partial media on stop, and restores live microphone state after completion.

### 2. Audio-only WebM could be labelled and rendered as video

Some browsers emit audio-only WebM from `MediaRecorder`. The evidence extension was allowed, but the upload path previously mapped `.webm` to `video/webm` unconditionally.

**Changes:** the upload endpoint now preserves `audio/webm` when the browser declares an audio WebM recording. Existing case renderers therefore choose an audio player. Video WebM remains `video/webm`.

### 3. Evidence was hard to find after reopening a case

The full case page already had inline preview elements for image, video, audio and PDF, but all evidence lived behind a nested **Prepare & contact → Evidence & receipts** disclosure. Users could see a file count in the overview without a direct path to the originals.

**Changes:**
- Added an at-a-glance **Evidence attached** panel to the case overview, with the first three saved items, type, exhibit number, file size and direct open link.
- Added **View all** which opens the existing Evidence & receipts section in the Prepare & contact tab.
- Existing full evidence rows keep inline previews and a separate download-original action.
- The evidence endpoint is tested for inline responses, attachment downloads and byte-range requests needed for video playback.

### 4. Blank camera frames could be presented as a live camera preview

The previous check treated `videoWidth`/`videoHeight` as proof that a usable frame was visible. Some privacy shutters, driver states or virtual camera devices can return dimensions but only black frames.

**Changes:** the browser now samples a tiny downscaled frame before hiding the placeholder. If it receives only a blank black frame, it keeps a helpful placeholder and asks the user to check the lens/privacy shutter or use an upload.

### 5. Consent, microphone settings and cached UI

- Added explicit finish-speech and voice-note controls in the same control area as the microphone.
- The consent checkbox remains a separate, two-column card with the title and explanation stacked for readability.
- Bumped the service-worker shell cache from `bolkeresolve-shell-v27` to `bolkeresolve-shell-v28` so updated CSS, HTML and JavaScript are fetched together.

## Existing integrations preserved

- Draft case creation before media capture.
- Speech turn persistence in the existing case timeline.
- Original image, PDF, video and audio evidence in the existing evidence table and upload directory.
- User review and confirmation before extracted document facts influence routing.
- Existing deterministic resolution rules, official sources, case commitments, reply review, case history, print Passport and evidence-bundle ZIP.
- Server-side Gnani API key; no API key is sent to the browser.

## Gnani protocol notes

The current official realtime STT documentation describes:
- 48 kHz as the browser `getUserMedia` default and supports 44.1/48 kHz sources with server-side resampling.
- PCM signed 16-bit little-endian mono frames of 512 samples / 1,024 bytes at real-time cadence.
- A `commit` control message to close an open utterance immediately.
- `processing` as an acknowledgement that transcription began, followed by a `transcript` event.
- The browser must use a same-origin backend proxy to attach authentication headers; browser WebSockets cannot set arbitrary headers.

References: [Gnani realtime STT](https://docs.gnani.ai/api/STT/stt-websocket), [MediaRecorder dataavailable](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/dataavailable_event), [MediaRecorder start](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/start).

The app preserves the actual AudioContext sample rate. It does not relabel 48 kHz samples as 16 kHz. Live account credentials were not available during the automated tests, so a real upstream transcription was not verified.

## Test results

- `PYTHONPATH=. python -m pytest -q` — **288 passed, 117 subtests passed**.
- `node --check frontend/app.js` — passed.
- `python -m compileall -q backend tests scripts` — passed.
- Evidence API tests cover inline previews, attachment download, byte-range playback and audio-only WebM MIME preservation.
- Frontend tests cover finish-speech commit, original voice-note preservation, WAV conversion for transcription, evidence overview navigation and inline media previews.

## Operator verification still required

1. Set `GNANI_API_KEY` in server-side `.env`, restart, then verify a real short Hindi/Hinglish utterance.
2. Test **Finish speaking** and confirm the transcript appears in the conversation and timeline.
3. Test **Record voice note**, stop it, confirm the original recording appears in Evidence, and confirm the transcript before it becomes a case turn.
4. Take a camera photo, share a screen and record a short video; reopen the case and play each saved original.
5. Test Chrome/Edge with a real camera, microphone and screen picker. The automated browser harness cannot exercise the user's hardware or real provider account.
6. Use a durable data directory and complete the existing privacy, authentication, HTTPS, backup/restore, malware-scanning and production security checks before public deployment.

This build does not claim continuous AI video understanding. Camera/screen capture stores selected evidence; image analysis requires the separately configured vision provider and user consent.
