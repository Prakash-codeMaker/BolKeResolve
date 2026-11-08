# Live Room conversation, capture-intent and evidence UX fix — 2 November 2026

## Problems reproduced from the user's latest screenshots and transcript

- The same Zepto overdue-refund paragraph was appended and read aloud after filler speech, a camera request, a screen-share/record request and a later support-no-reply update.
- Requests to show evidence were treated like ordinary case answers, so the guidance generator could replay the old resolution instead of handing off to the requested capture control.
- The transcript accumulated duplicate historical assistant guidance, making it difficult to tell what had changed.
- The evidence filter controls were laid out as tall, narrow pills rather than compact horizontal filters.
- Support-message drafts and long transcript turns needed clearer wrapping, spacing and bounded scrolling.

## Implementation changes

### Conversation and decision flow

- Added low-information utterance handling for common filler/noise (`like`, `um`, `hmm`, `okay`, Hindi fillers) so these turns do not save new case facts, trigger guidance generation, auto-advance intake or speak the same recommendation again.
- Added a structured workflow signature. If a user message does not change the workflow stage, question, action, evidence request or relevant facts, the Live Room acknowledges that the update was saved without replaying the full previous action paragraph or reading it aloud again.
- Added a structured chat response format with distinct headings for `CASE UPDATED`, `ONE DETAIL NEEDED`, `WHY I'M ASKING`, `YOUR NEXT STEP`, `WHAT TO DO`, and `EVIDENCE TO ADD`.
- On restore, identical historical assistant guidance paragraphs are shown once in the conversation. The underlying timeline and audit events remain untouched.

### Capture intent and permissions

- Recognises requests to open the camera, choose an existing image, upload a file, share a screen, record the already-shared screen, or stop a recording/share.
- A capture request saves the user's utterance, presents the matching action and suppresses ordinary workflow guidance/auto-advance for that turn.
- Camera and screen capture still require a user click and browser permission. The app does not start recording or share a screen merely because the user said so.
- After the user has explicitly shared a screen, the app offers a separate record-clip action. Stop controls remain available.

### Evidence and page presentation

- Evidence filters now render as compact, wrapping horizontal controls across the full evidence-list width, not as tall grid cards.
- Evidence cards use responsive auto-fit columns and align at the top of the grid.
- Support drafts use a readable bounded text area with line-height and safe wrapping.
- Capture-intent cards and transcript text wrap long content rather than pushing the layout sideways.
- The service-worker shell cache is bumped to `v36` so stale front-end assets are invalidated on the next load.

### Case workflow

- The refund adaptive workflow now advances to an `existing_support_no_response` action when the user reports prior contact and no reply. The action continues the existing order-specific support thread, asks for a complaint reference and written refund status, and requests evidence of the earlier contact. It explicitly discourages opening a duplicate ticket while the old one may still be active.
- Adaptive workflow engine version updated to `adaptive-intake-2026-11-02.7`.

## Validation

- Full pytest suite: **323 passed, 129 subtests passed**.
- `node --check frontend/app.js`: passed.
- `python -m compileall -q backend tests`: passed.
- API regression covers the Meesho/Flipkart-style follow-up pattern: prior support contact plus no reply produces a new existing-support action and survives a case reload.
- Frontend static regression checks that filler/capture turns suppress auto-advance, identical guidance is not spoken again, and evidence filters/layout rules stay responsive.
- Browser screenshot QA could not be completed in this environment: local Chromium navigation was blocked with `net::ERR_BLOCKED_BY_ADMINISTRATOR`. Therefore responsive appearance still needs a visual check in the user's Chrome/Edge installation.
- No authenticated Gnani session or physical microphone/camera/screen-share hardware test was available. Browser permission prompts and provider timing still require device-level acceptance testing.

## UX research basis

- GOV.UK design guidance recommends asking only questions that are necessary, explaining why they are asked and avoiding questions already answered. See https://www.gov.uk/service-manual/design/form-structure.
- WCAG 2.2 Reflow requires content to work at a 320 CSS-pixel viewport without two-dimensional scrolling for ordinary vertically scrolling content. See https://www.w3.org/WAI/WCAG22/Understanding/reflow.html.
