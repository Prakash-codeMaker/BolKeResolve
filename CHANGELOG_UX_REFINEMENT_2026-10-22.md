# UX refinement release — 22 October 2026

## User-facing changes
- Homepage now communicates the outcome (one clear next action) with a floating value card and refined visual hierarchy.
- Guided chat is explicitly labelled as a private in-app experience, not a live WhatsApp connection.
- Four common issues are shown first; less common paths live under “Another issue”.
- The chat surface is wider and calmer, with clearer voice controls and responsive layouts.
- Saved-case overview focuses on the recommended action and official support destinations.
- Progress tracking, outcomes, exports and supporting history are grouped into a dedicated Progress destination.
- Service worker cache version bumped to v4 so installed clients fetch the updated shell.

## Follow-up refinement — 22 October 2026
- Reduced the saved-case workspace from six top-level tabs to three: **Next step**, **Prepare & contact**, and **Progress**.
- Combined evidence upload and the editable support draft in Prepare & contact; the checklist remains at the top, with evidence and message details revealed only when opened.
- Combined progress updates, outcomes, exports and case history in Progress; history is collapsed until needed.
- Kept existing buttons working by routing their actions into the relevant destination and opening the relevant disclosure automatically.
- Added responsive styling and explicit tab/panel accessibility relationships; changed the nested case-column landmark to a `div` so the page has a single main landmark.
- Bumped the public service-worker shell cache to v4.

## Validation
- `python -m unittest discover -s tests -v`: 136 tests passed.
- `node --check frontend/app.js`: passed.
- Browser smoke check with a mocked API: confirmed three top-level tabs, action-to-disclosure navigation, visible Progress panel, and no JavaScript/page-console errors.
- Real-deployment browser QA remains recommended; voice-provider calls and external integrations were not exercised by this UI smoke check.

## Scope boundary
No automatic complaint submission was added. Official links, editable drafts and user-controlled handoff remain the supported model until a real organisation API or partnership is available.


## Follow-up visual and simplification pass
- Fixed support-route cards collapsing into narrow vertical columns by enforcing two balanced columns on desktop and one column on mobile, with robust text wrapping.
- Reworked the guided-chat page into a clear intro/chat split on desktop and a stacked layout on smaller screens, with responsive heading sizes and compact supporting imagery.
- Replaced plain “How it works” boxes with image-led cards using the project’s local image assets, subtle hover motion, and responsive cropping.
- Kept the primary case actions visually dominant while reducing duplicate emphasis; the three destinations remain, but the page is easier to scan.

## Guided resolution flow refinement

- Reworked the saved-case default screen around one recommended next action and a single primary button to prepare or review the support message.
- Moved message, evidence, and progress destinations under a collapsed **More case tools** disclosure, which closes again after a destination is chosen.
- Collapsed the full resolution plan and editable case details by default so the first screen no longer repeats every tool from the older six-section workspace.
- Moved official support routes to **Prepare & contact**, ahead of the optional checklist/reminder/export pack; collapsed that pack unless the user needs it.
- Added clear return navigation, responsive spacing and compact case-tool layouts for mobile.
- Bumped the service worker shell cache to v5.
- Updated frontend regression tests for the guided one-action-first flow.


## Homepage photography and image-row refinement

- Replaced the repeated “How it works” photographs with three distinct, publicly sourced Pexels images matching story intake, transaction review and support follow-through.
- Added descriptive alt text, lazy loading, async image decoding, and separate local fallbacks for each card.
- Standardised the desktop photo heights and crop positions to align the three cards.
- Turned the small-screen row into a horizontally swipeable, snap-aligned image strip instead of a long stack of large cards.
- Added the photo source URLs and attribution notes to `ASSET_CREDITS.md`; bumped the public shell cache to v6.

## Challenge showcase update — 22 October 2026

- Added a public sample-case explorer to the homepage for failed UPI payment vs delayed merchant refund.
- Both fictional scenarios call the same read-only `/api/resolution/preview` rules endpoint; the UI displays official sources and review dates and explicitly says no payment is checked, no case is saved and no complaint is submitted.
- Added responsive, accessible controls and live result announcements.
- Added frontend asset tests and API regression tests confirming both paths return relevant official sources without creating cases.
- Bumped service-worker shell cache to v8; API responses remain network-only.
- Added `docs/PRODUCT_RESEARCH_AND_CHALLENGE_UPGRADE_2026-10-22.md`, a product strategy/implementation report and 180-link research library.

## Fastest Safe Path — 22 October 2026

- Added structured next questions that can be answered in one tap when the answer changes the route (payment status, or whether support was already contacted).
- Rendered compact inline choice buttons with an explanation of why the answer matters. Choosing an answer re-runs the read-only preview using the explicit field value and does not re-run extraction over it.
- Added a `fastest_path` response summary that describes whether the user should act now, clarify one detail, or continue an existing support thread.
- Made the current support-contact answer change the first step for failed UPI, pending UPI, and delayed-refund cases: existing cases are followed up rather than duplicated.
- Made explicit pending status route to the pending/not-credited UPI playbook; detected a failed-story vs successful-status contradiction and ask the user to resolve it before a specific route is selected.
- Removed chains of questions about helpful-but-not-essential fields. Amount, date, merchant and references remain listed as missing details but do not block the first useful recommendation.
- Urgent suspected-fraud routing does not wait for a clarification answer.
- Added mobile/keyboard styling for quick-answer controls, bumped shell cache to v10, and added regression coverage.
- See `docs/FASTEST_SAFE_PATH_2026-10-22.md`.

## Fastest Safe Path — saved cases

- Made the status/support-contact clarifications interactive after a case has been saved, not only in the initial preview.
- Answers now update the saved facts and recalculate the resolution plan, so the user sees the next relevant question or a changed next step without re-creating the case.
- Removed the non-progressing "Not sure" status chip; users can still proceed with the primary action or edit their case details.
- Added frontend and API regression coverage for the two-question flow and existing-thread recommendation.
