# Resolution Completion Loop — 29 October 2026

## Why
The saved case previously kept a mostly static first-step recommendation even after the user reported contacting support, receiving no response, or resolving the issue. This made the case feel like a record rather than a workflow that helps the user finish the job.

## Implemented
- Added `backend/completion_loop.py`, deterministic state-aware next-action logic (`completion-loop-v1`).
- Every case response now includes `completion_loop` with a state, recommended action, destination tab, next milestone, follow-up status, preparation percentage, most recent recorded update and an explicit verification boundary.
- The primary action card now reflects the case state: prepare the first contact, review/send the user's own message, track a response, follow up, or check a user-reported resolution.
- The CTA routes to the relevant existing area (`prep`, `draft`, or `progress`) without adding a new dashboard or changing the product's core navigation.
- Added a compact progress/state strip in the existing palette and a reduced-motion-aware pulse indicator.
- Bumped the service-worker shell cache to v20.
- Added regression tests for new case, contacted-support, no-response, resolved and frontend rendering states.

## Important limits
- This is a deterministic recommendation based on user-reported case stage, outcome, checklist and follow-up fields.
- It does not verify bank/merchant status, submit complaints, guarantee refunds, or send notifications.
- A `resolved` outcome remains explicitly user-reported. The app recommends checking the actual account before treating the matter as complete.
