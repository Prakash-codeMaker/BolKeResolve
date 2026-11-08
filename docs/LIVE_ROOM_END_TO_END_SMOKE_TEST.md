# Live Resolution Room end-to-end smoke test

Use synthetic or fully redacted financial details until the production privacy, storage and security gates are complete.

## 1. Start locally

1. Extract the project into a new folder; do not overwrite an older project directory.
2. Install Python 3.10 or newer.
3. Run `run_windows.bat` and open `http://127.0.0.1:8000`.
4. To test live speech, add a valid `GNANI_API_KEY` to the server-side `.env` and restart. Never place the key in frontend JavaScript.
5. Use HTTPS for a hosted deployment. Camera, microphone and screen sharing require a secure browser context and explicit user permission.

## 2. Create and resume one case

1. Open **Live resolution** and click **Start live resolution**.
2. Confirm a `BR-...` case ID appears immediately, before any story is spoken or evidence is selected.
3. Open **My cases** in another tab (or after ending the session) and confirm the draft is present.
4. Return to the live room; the same case ID must remain visible.

## 3. Voice and text

1. With a valid Gnani key, speak a short synthetic Hinglish example and pause naturally.
2. Confirm a final transcript appears in the conversation and is saved to the case timeline.
3. Confirm a guidance event follows and its provenance identifies it as BolKeResolve playbook guidance, not an external company response.
4. Speak a second sentence. Confirm transcript turns are saved in order.
5. With the Gnani key removed, confirm the UI reports that voice is not configured without repeated reconnect attempts. The draft case must remain usable for typing and evidence.

## 4. Camera and documents

1. Allow camera access. Confirm the camera preview is visible.
2. Click **Take photo**. Wait for the success message and a new exhibit ID (`E-001`, etc.).
3. Open the original evidence link and confirm the captured image is returned.
4. Upload a synthetic receipt image or PDF. Confirm the original file is saved before OCR review begins.
5. Review extracted candidate facts, select only details you checked, and confirm. Verify that the chosen facts show their evidence source in the case and Passport.
6. Upload a malformed file with a permitted extension and confirm the signature check rejects it without creating a successful evidence row.

## 5. Screen sharing and clips

1. Click **Share screen** and choose a test browser tab/window. The selected source should appear in the visible preview.
2. Confirm the first selected frame is saved automatically as an exhibit. The share remains active.
3. Click **Capture another frame** and confirm another exhibit is added.
4. Stop sharing using the browser's sharing indicator. The preview and button state should reset.
5. If testing clips, click **Record clip**, record a short synthetic demonstration, stop it, and wait for the original WEBM file to appear in the evidence list. Video is stored but not semantically analysed automatically.

## 6. Audio evidence

1. Upload a supported, lawfully obtained synthetic support-call recording.
2. Confirm the original file is saved even if transcription fails.
3. Review the transcript preview, correct any names/numbers/dates, and explicitly add it to the case conversation.
4. Confirm the transcript timeline event identifies it as a user-confirmed imported recording transcript.

## 7. Reports and reopen

1. Click **Print / save PDF**. In the opened report, review case facts, confirmed evidence-derived fields, exhibit register, recommended steps, source links, checklist, draft, commitments, follow-up, outcome and full timeline.
2. Use the report's **Print / Save as PDF** control or browser Print → Save as PDF.
3. Click **Download full case + evidence**. Inspect the ZIP: it must contain `case/Resolution-Passport.json`, `evidence/manifest.json` and each original evidence file that still exists.
4. Open the case from **My cases** and confirm all transcript turns, guidance, evidence and lifecycle events remain.

## Expected boundaries

- A camera preview is local until the user captures a photo. A screen share only stores the frames the user captures; no continuous screen recording is performed.
- Live microphone audio is streamed to Gnani for transcription and is not stored as raw audio by default. Final transcript text is saved after receipt.
- Uploaded videos are preserved as evidence but are not automatically understood by a vision model in this build.
- Hashes identify stored/exported file bytes. They do not prove authenticity, origin, capture time or the truth of a statement.
- OCR values remain candidates until the user confirms them.
- The agent's first-pass routing is generated from the existing deterministic playbooks. It does not access bank or merchant records and cannot promise a refund.
