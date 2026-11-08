# BolKeResolve Live Room — Acceptance tests

## A. No repeated stale advice

1. Open an existing overdue Zepto refund case.
2. Say “Like.” then “आई”.
3. Confirm the app does not append or speak the previous long refund plan again. It may keep the short utterance in the transcript, but it must remain listening.
4. Say “I contacted support but still haven't got a reply.”
5. Confirm the next action changes to following up on the existing support conversation and asks for the earlier complaint/reference and written status.
6. Reload the case and confirm the new workflow stage remains. Previous identical assistant paragraphs should not be repeated in the visible transcript.

## B. Camera intent

1. Say “Can you open the camera? I want to show you a receipt.”
2. Confirm the app displays an “Open camera” action and an alternative to choose an existing photo.
3. Confirm the camera does not start until the user clicks Open camera and grants the browser permission.
4. Close the camera and confirm the microphone/case session remains available.

## C. Screen share and recording

1. Say “I want to share my screen.”
2. Confirm the app offers “Choose screen to share” and a “Not now” action.
3. Choose a tab/window and grant browser permission.
4. Say “Record the screen I shared.”
5. Confirm the app offers recording of the already-shared screen.
6. Stop recording/sharing and confirm the resulting evidence is attached only after it has been finalized/uploaded.

## D. Evidence and layout

1. Open Evidence & documents with one or more photos, then with audio/video/document items.
2. Confirm All / Photos / Documents / Audio / Video filters appear horizontally and wrap on narrow screens; they must not become tall vertical pills.
3. Confirm evidence cards align at their top edge and fill the available grid without large empty gaps.
4. Confirm long filenames, support drafts and transcript lines wrap without horizontal page scrolling.
5. At a 320 CSS-pixel viewport, verify the page reflows to a single column, controls remain reachable, and no two-dimensional scrolling is needed.

## E. Notes

Camera/screen permissions, actual audio pause detection, provider transcription and media recording need testing in the target Chrome/Edge browser with the user's Gnani account. The build's automated tests do not simulate physical devices or grant browser permissions.
