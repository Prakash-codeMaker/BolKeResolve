# Live Resolution Room speech and evidence fixes — 31 October 2026

- Added **Finish speaking** control that sends Gnani's `commit` WebSocket message to close an utterance immediately.
- Added 60-second **Record voice note** fallback using a cloned microphone track, pausing the live stream to avoid duplicate transcripts.
- Stores the original audio-only WebM/OGG/M4A recording in the existing case; converts a temporary copy to 16 kHz mono PCM WAV for the existing REST transcription API when required.
- Keeps the original voice recording even if the transcript conversion or API call fails. Transcript text remains a reviewable preview until the user confirms it.
- Preserves `audio/webm` MIME for audio-only WebM, so reopened cases render an audio player.
- Adds evidence summary and direct item access to the full case overview, with a one-click route to the complete Evidence & receipts section.
- Adds a blank-frame visibility check for camera and screen video elements so a black frame isn't presented as a working preview.
- Keeps inline preview plus separate original-download actions for evidence.
- Adds regression tests for voice fallback, original media preservation, audio-only WebM, case overview evidence, inline playback and range requests.
- Bumps service-worker cache to `bolkeresolve-shell-v28`.

Validation: 288 tests passed, 117 subtests passed; `node --check frontend/app.js` and Python compilation passed. Physical hardware and live Gnani calls remain operator verification steps.
