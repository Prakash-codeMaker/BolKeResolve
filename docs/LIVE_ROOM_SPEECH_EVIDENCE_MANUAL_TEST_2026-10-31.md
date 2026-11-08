# Live Room manual test — 31 October 2026

Use fictional payment details only. Do not record a real customer-service call or expose OTPs, UPI PINs, passwords, full card numbers, Aadhaar or PAN.

## Before opening
1. Extract this ZIP into a new folder.
2. Add a valid `GNANI_API_KEY` to the server-side `.env`.
3. Keep `GNANI_STT_MODEL=prisma-v2.5` unless your Gnani account has confirmed access to another model.
4. Restart `run_windows.bat` and open `http://127.0.0.1:8000`.
5. Hard-refresh Chrome/Edge with `Ctrl+F5` so the new service-worker cache (`v28`) and stylesheet load.

## Test A — live speech
1. Open **Live resolution** and select Hindi/Hinglish or Detect language.
2. Click **Start live resolution** and allow microphone/camera permissions as desired.
3. Confirm the microphone meter moves when you speak.
4. Say: “Mera ₹1,200 ka UPI payment debit hua, lekin merchant ko payment nahi mila.”
5. Pause. If the transcript doesn't arrive, click **Finish speaking** once. This sends an explicit end-of-utterance signal to Gnani.
6. Check that your words appear in the conversation, are saved as a case turn, and update the guidance panel.

## Test B — voice note fallback
1. In the Live Room, click **Record voice note**.
2. Speak a short fictional issue for 5–15 seconds.
3. Click **Stop voice note**.
4. Confirm that the original recording appears in the evidence list.
5. Review the transcription preview and click **Add transcript to case** only after checking it.
6. Open the case. Confirm the original audio appears as an audio player and the confirmed transcript appears in the case history.

## Test C — camera, screen and clip
1. Click **Take photo** and capture a synthetic receipt/screenshot. Wait for the “saved” confirmation.
2. Click **Share screen**, explicitly choose a window/tab or screen, and confirm the first frame is saved. Capture another frame if needed.
3. Click **Record clip**, record 5–10 seconds, then click **Stop clip**. Wait for the saved confirmation.
4. Open **My cases**, reopen the case and confirm that each original item can be viewed or played.

## Test D — case overview and exports
1. In the reopened case overview, find **Evidence attached**. Open an item directly or choose **View all**.
2. In **Prepare & contact → Evidence & receipts**, check the image/video/audio/PDF previews and the separate **Download original** link.
3. Use **Print / Save as PDF** and download the full case + evidence ZIP. Confirm the ZIP includes the case JSON, exhibit manifest and original files.
4. Reopen the case once more. Evidence should still be present.

## What a failure means
- **No mic meter movement:** browser/Windows microphone permission or wrong input device. Open Mic settings and select the correct input.
- **Meter moves but live transcript does not:** click Finish speaking. If still unavailable, use Record voice note; this uses the existing REST transcription path after storing the original.
- **Voice note saved but no transcript:** the original is still evidence; check the displayed transcription error and verify the Gnani key/account supports the REST STT request.
- **Camera placeholder remains:** close other apps using the camera, check its privacy shutter, or upload a photo.
- **Video won't play:** use the inline preview in the evidence area; if the browser cannot play the codec, use Download original.

A passing automated test suite is not a substitute for this physical browser/provider test.
