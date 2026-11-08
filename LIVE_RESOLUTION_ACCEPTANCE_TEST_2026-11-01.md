# BolKeResolve Live Resolution — manual acceptance test

Run against the updated ZIP on the target Windows machine with its real Gnani API key. Use a disposable test account and synthetic order/payment records. Do not upload real passwords, OTPs, UPI PINs, full card numbers or unrelated personal documents.

## A. Provider configuration

- [ ] Copy `.env.example` to `.env` (or merge the relevant settings into the existing `.env`).
- [ ] Set `GNANI_API_KEY` to the intended key.
- [ ] Set `GNANI_STT_MODEL=prisma-v3.0` for consistency. Auto mode explicitly requests Prisma v3.0 regardless of the value in this setting.
- [ ] Confirm the API key is enabled for Prisma v3.0 Auto-LID. If the provider rejects it, resolve entitlement with the provider; do not try to mask that with a forced language selection.
- [ ] Keep `BOLKE_AUTH_REQUIRED=true` for a private/production deployment. Run local-only testing on localhost with no public exposure.

## B. Speech test without selecting a language

- [ ] Start the app with `run_windows.bat` and open `http://127.0.0.1:8000` in Chrome or Edge.
- [ ] Start a new Live Resolution session. Leave the language control on **Detect automatically**; do not open the optional language selector.
- [ ] Speak a short English sentence, pause, then use **Finish speaking** if needed. Confirm the transcript appears and the language label reflects the provider's detected language when supplied.
- [ ] Start another session and test Hindi. Repeat with a natural Hinglish sentence containing English product/order terms.
- [ ] Repeat with a different mic profile only if the meter or transcript indicates the microphone is too quiet/noisy.
- [ ] Confirm the exact words are saved as a user-reported timeline turn, and correct any number/date/name before sharing.
- [ ] Simulate an unavailable/unauthorized Prisma v3.0 key. Confirm the UI gives an explicit provider/model compatibility message and leaves the case available for typing/evidence; do not claim auto detection worked.
- [ ] Confirm a speech segment that gets no transcript triggers the timeout/retry message rather than leaving a permanent listening state.

## C. Saved recording fallback

- [ ] Use **Add or show evidence → Record voice note**.
- [ ] Speak for 5–10 seconds and stop. Confirm the original recording is saved as evidence before transcript review.
- [ ] Confirm the transcription request uses Auto-LID when the language selector is still in automatic mode.
- [ ] Review/edit the transcript, add it only after confirmation, then reopen the case and verify the original audio and confirmed transcript remain linked.
- [ ] Force a transcription error and verify the original audio remains available.

## D. Flipkart refund scenario

Use this synthetic story:

> We have not got the refund back or ₹6,000 from Flipkart yet. We ordered something three weeks ago and have already contacted support, but we have got no response to date. Please help us get it back.

- [ ] Confirm the case classifies as **Refund not received**.
- [ ] Confirm the case shows Flipkart, ₹6,000, the three-week delay and support already contacted.
- [ ] Confirm neither chat nor the side panel asks again whether support has already been contacted.
- [ ] Confirm the first step tells the user to continue the existing refund complaint rather than open a duplicate ticket.
- [ ] Confirm the Flipkart route is order-specific: Account → Orders → select the order → Help → Chat with us (or desktop 24x7 Customer Care → select the order → Chat with us).
- [ ] Confirm the editable support message asks for a traceable status, refund reference/ARN/UTR/RRN, acknowledgement and expected credit date.
- [ ] Confirm the checklist asks for relevant material (for example, order/refund confirmation or prior support chat) without demanding every possible document at once.

## E. Voice-led capture flow

- [ ] Confirm the default control row is uncluttered and evidence modes are collapsed under **Add or show evidence**.
- [ ] Say "I want to upload a screenshot". Confirm one contextual **Choose a file** action appears; select a synthetic screenshot and verify the original is saved to the active case.
- [ ] Say "I want to show you this document". Confirm the contextual camera capture action appears; capture, review and save the photo.
- [ ] Say "I want to share my screen". Confirm a contextual screen action appears, browser permission is requested, and only the user-selected screen/tab is shared.
- [ ] Stop screen sharing and confirm the preview closes; previously saved evidence remains.
- [ ] Say "record a short video clip". Start and stop the clip; verify the original video is saved and playable.
- [ ] Dismiss a capture prompt with **Not now** and confirm no media is captured.
- [ ] Confirm visual AI analysis is separately consented to and produces unverified candidate observations only.

## F. Continue an existing case and export

- [ ] End the Live Room and open the saved case.
- [ ] Select **Continue live**. Confirm the same case ID is shown.
- [ ] Add a new reply/update and one supporting file. Confirm both are appended to the same case timeline/dossier.
- [ ] Print/save the case passport. Confirm summary, user-reported facts, chronology, actions and evidence references are present.
- [ ] Download the full case + evidence bundle. Reopen the ZIP and verify the originals are included.
- [ ] Confirm the report labels user-provided claims and AI-extracted candidate facts appropriately; it must not describe the report as independently verified or legally certified.

## G. Follow-up and privacy

- [ ] Set a follow-up date and note, reopen the case and verify they persist.
- [ ] Confirm that a saved follow-up date is not described as an actual push notification unless a reminder delivery channel is configured.
- [ ] For WhatsApp delivery, separately configure the approved provider, credentials, business number, approved message template and user opt-in; test with a non-sensitive sample.
- [ ] Confirm production is served over HTTPS and authentication is enabled before real user data is uploaded.
- [ ] Confirm uploaded records are in a private persistent directory with access control, backups, encryption-at-rest at the storage/volume layer and retention/deletion controls suitable for your deployment.

## Known manual-only checks

Automated tests cannot verify microphone hardware, Windows privacy settings, a real Gnani account's model entitlement, browser permission dialogs, live camera rendering, screen selection or actual WhatsApp delivery. Complete these checks on the deployment device before treating the workflow as production-ready.
