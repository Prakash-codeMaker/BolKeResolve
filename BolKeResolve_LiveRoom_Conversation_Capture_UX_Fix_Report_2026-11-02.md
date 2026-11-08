# BolKeResolve Live Room — Conversation, capture and presentation fix

**Release date:** 2 November 2026  
**Scope:** Live Resolution conversation handling, evidence capture requests, transcript restoration, evidence filters and responsive layout.

## What was wrong

The latest user-provided transcript showed the same Zepto refund paragraph repeating after unrelated turns: filler speech (“Like”, “आई”), requests to open the camera, requests to record/share the screen, a new description of the delivery/refund issue, and a report that support had not replied. The app treated these as if they were all ordinary updates to the existing overdue-refund action. The screenshots also showed duplicated historical guidance, a tall transcript with nested scrolling, and evidence filters occupying narrow vertical capsules.

## What changed

1. **Filler/noise:** short filler utterances are kept visible if transcribed, but they do not trigger fact saving, a model/guidance call, automatic workflow advancement or repeated text-to-speech.
2. **Capture intents:** camera, photo/file upload, screen share, screen recording and stop requests are identified before guidance generation. The user gets a contextual action card. Browser permissions still require an explicit click.
3. **No duplicate advice:** the current workflow is fingerprinted. If the stage/question/action/evidence/facts have not changed, the transcript gets a short acknowledgement instead of repeating the same long recommendation; TTS is suppressed for the duplicate.
4. **Restored transcript:** repeated historical assistant guidance is collapsed to one visible occurrence. Original timeline events remain intact for audit/history.
5. **Support-no-reply branch:** reporting that support was contacted but did not reply changes the refund workflow to an existing-ticket follow-up action, asks for the earlier reference/status and requests proof of that previous contact.
6. **Message formatting:** chat guidance uses short labeled sections, while transcript bubbles preserve line breaks and wrap long text.
7. **Evidence and responsive layout:** filters are horizontal wrapping controls; the evidence grid auto-fits cards; support drafts have readable bounded text areas; capture prompt cards wrap safely; service-worker cache is now v36.

## Verification results

| Check | Result |
|---|---:|
| Automated tests | **323 passed** |
| Additional subtests | **129 passed** |
| JavaScript syntax (`node --check frontend/app.js`) | Passed |
| Python compile (`python -m compileall -q backend tests`) | Passed |
| ZIP integrity and fresh extraction | Passed |

The tests include an API-level follow-up case that confirms a no-reply update produces a new case-specific action and remains correct after a reload, plus frontend regression assertions for capture/filler auto-advance suppression and duplicate-guidance suppression.

## What is not claimed as verified

- A local Chromium visual pass could not be completed because Chromium blocked navigation to the local app with `net::ERR_BLOCKED_BY_ADMINISTRATOR`. The CSS and frontend asset rules are in the test suite, but final desktop/mobile appearance needs visual confirmation in the user's browser.
- No physical microphone/camera/browser screen-share test or authenticated Gnani provider session was available here. Device permissions, actual pause detection, transcript quality and recording/playback must be checked on the target machine.
- Camera, screen share and recording do not begin from voice recognition alone; the user must approve the relevant browser permission/action.

## Install

1. Extract the ZIP into a new folder.
2. Copy the existing `.env` into the new folder; do not share it.
3. Run `run_windows.bat`.
4. Open `http://127.0.0.1:8000` and hard-refresh with `Ctrl + F5`.
5. Test the acceptance checklist with the same sequence in the screenshots.
