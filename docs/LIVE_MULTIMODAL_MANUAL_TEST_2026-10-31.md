# Live Resolution Room — manual Chrome/Edge test

Use fictional information only. Do not show real UPI PINs, OTPs, full bank/card identifiers, personal addresses or other secrets.

## A. Local startup

1. Extract this ZIP to a new folder.
2. Install Python 3.10 or newer.
3. Copy `.env.example` to `.env` if the launcher did not do so.
4. Add server-side `GNANI_API_KEY`. Add `OPENAI_API_KEY` only if you intend to test same-language guidance and visual AI analysis.
5. Run `run_windows.bat` and open `http://127.0.0.1:8000` in Chrome or Edge.

## B. Draft case and media permissions

1. Open **Live resolution**.
2. Choose English (India) for a baseline test, or Hindi/Hinglish for the language test.
3. Optionally check **Enable same-language AI guidance**. This sends generated guidance text—not raw audio—to the configured text model for translation. Do not enable if you do not consent.
4. Click **Start live resolution**.
5. Confirm that a case ID appears before you speak or upload anything.
6. Grant microphone and camera permission separately. Deny either one once and verify that typing/upload still works.

## C. Live speech

1. Speak a synthetic example: "My UPI payment of 1200 rupees was debited but the demo merchant did not receive it."
2. Wait for a final transcript segment.
3. Confirm the words appear in the conversation and that the case panel reflects the new case state.
4. Check the case timeline after opening **Open full case**. The turn must be labelled as a user-reported live-speech event.
5. Check the guidance panel. It must display the next step and its official sources.
6. If same-language guidance was consented and configured, verify that the guidance is translated and spoken. If the provider is unavailable, the UI must disclose the fallback; it must not claim translation succeeded.

## D. Camera evidence

1. Return to the Live Resolution Room for the same case.
2. Click **Take photo** and capture a synthetic receipt or test image.
3. Confirm that the evidence count increases only after the server accepts the upload.
4. Confirm the original image can be opened from the evidence register.
5. Review local OCR candidates and check only facts you can verify against the image.
6. If visual AI is configured, separately check the per-image consent box and request image analysis.
7. Verify that the model output remains a candidate until each selected fact is checked and confirmed.
8. Verify that unconfirmed AI observations do not change the route. Confirm one fact and request guidance again; the route may then update based on that confirmed field.

## E. Screen sharing

1. Click **Share screen**.
2. Choose a test browser tab/window in the native browser picker.
3. Confirm that a visible preview appears.
4. Capture a frame. Confirm it appears in the same case's evidence register.
5. Capture a second frame and verify that it is stored as a separate exhibit.
6. Stop sharing using the browser's sharing indicator and confirm the preview stops.

The application does not silently capture a screen or analyse every frame. The user must select the source and request each capture. Continuous video understanding is not part of this build.

## F. Documents and recordings

1. Upload a synthetic JPG or PNG receipt and verify immediate storage.
2. Upload a PDF and verify the existing local document/OCR review path.
3. Optionally upload a short WAV/MP3 support recording. Verify the original recording is retained and the transcript is only added to the case after the user reviews and confirms it.
4. Optionally record a short camera or screen clip; verify the original media is attached and clearly labelled as not automatically analysed.

## G. Reopen and export

1. End the Live Resolution session.
2. Open **My cases**, reopen the same case and confirm the timeline and evidence are still present.
3. Open **Print / save PDF** and inspect the chronology and evidence register.
4. Download **Full case + evidence** and confirm the ZIP includes the structured case JSON, manifest and original uploaded evidence.
5. Compare the manifest hashes with the included original files using SHA-256 tooling.

## Pass criteria

- No speech, photo, screenshot or file is shown as saved before server confirmation.
- A case exists before first speech or media upload.
- Speech turns, guidance, uploads, evidence reviews, confirmation events and session lifecycle are preserved in one case.
- Only user-confirmed fields influence the resolution engine.
- The guidance panel and spoken guidance use the same final wording and language.
- The user can reopen the case and produce a usable report and evidence bundle.
