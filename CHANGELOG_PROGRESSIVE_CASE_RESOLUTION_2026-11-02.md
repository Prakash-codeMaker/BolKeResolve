# Progressive Case Resolution — 2026-11-02

## Product change

BolKeResolve Live Resolution now uses a progressive, evidence-led workflow instead of regenerating a generic recommendation after every speech segment.

## What changed

- Added `backend/adaptive_workflow.py`, a conservative, staged workflow engine.
- Separates order merchants from payment apps (for example, a Meesho order paid using Google Pay remains a merchant refund case unless the facts indicate a UPI transaction dispute).
- Saves user-reported facts and uncertainty across turns, including merchant, issue type, amount, order outcome, refund scope, item count, refund status, reason given by the merchant, promised time, support contact and ticket reference.
- Parses common spoken English amounts when nearby text establishes payment/refund context.
- Asks one route-changing question at a time. Incomplete stories and reopened-case updates do not generate resolution advice until the user explicitly finishes the story/update.
- Supports staged paths for refunds, missing/not-delivered/wrong/damaged orders, UPI transfer issues and suspected unauthorised transactions.
- Adds curated official support routes for selected merchants. Unlisted merchants receive a safe in-app/official-site fallback; the app does not invent telephone numbers or claim a route is verified.
- Keeps support drafts editable and user-sent; the application does not automatically contact a merchant, bank, NPCI, NCH or regulator.
- Preserves adaptive workflow state when loading cases and when evidence is confirmed, including when the legacy recommended-step list is empty.
- Restores prior conversation history when reopening a case and keeps the same case ID while collecting an update.
- Requests microphone access for live speech but does not request camera access at session start. Camera, screen sharing and clip recording are user-initiated.
- Suppresses legacy generic advice/checklists during active story or update collection.

## Official route handling

Selected support routes are based on official sources reviewed for this release. Merchant terms and help pages change; the app should display the route as a source to check, not as a guarantee of eligibility or outcome. Unknown or unlisted merchants are not assigned guessed support contacts.

## Data/provenance principles

- User statements remain user-reported facts.
- AI-extracted observations from documents or images require user review before being promoted to confirmed facts.
- Original evidence remains distinct from extracted text or generated summaries.
- A suggested support message is not sent by BolKeResolve.
- The platform does not claim to access merchant, bank or payment-provider internal records.

## Known boundaries

- This release does not establish a live integration with merchant or bank systems.
- A physical microphone/camera/screen-share test and authenticated provider test must be run on the deployment device with the operator's credentials.
- Camera OCR/visual extraction still depends on the existing evidence review flow; this release does not claim continuous autonomous interpretation of a live camera stream or automatic video understanding.
- Browser security requires a user gesture and permission for file picker, camera and screen sharing.
- Reminder dates are persisted as case data; push/WhatsApp/SMS delivery requires a separately configured and consented provider.
- Deployment security, encryption at rest, TLS, persistent storage, backups, malware scanning, privacy notice, authentication and deletion/retention operations require operator verification before public production use.


## 2 November 2026 — Start Live Resolution launch fix

- Fixed the Start Live Resolution click listener passing the browser `MouseEvent` into `startLiveRoom(existingCaseId)`. The function interpreted the event as an existing case ID and attempted to load `/api/cases/[object MouseEvent]` instead of creating a new draft case.
- The click listener now invokes `startLiveRoom()` without arguments; the function also defensively ignores non-string values for `existingCaseId`.
- Start failures are now surfaced through a visible toast as well as the in-workspace feedback area, so an error cannot be hidden behind the workspace that has not opened yet.
- Bumped the public shell service-worker cache to v30 so clients fetch the corrected frontend.
- Added a regression test for the click-handler argument and defensive guard.
