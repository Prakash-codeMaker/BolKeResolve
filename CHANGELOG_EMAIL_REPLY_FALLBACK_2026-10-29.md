# Case email-reply fallback — 29 October 2026

## User problem
The Case Inbox Bridge panel displayed only a configuration warning when the deployment lacked an inbound email domain, provider webhook, stable encryption key or webhook credential. This made the whole panel look unusable, even though the existing reply-review endpoints work without automatic email infrastructure.

## Implemented
- Replaced the dead-end unconfigured state with a manual email-reply paste form embedded directly in the Case Inbox Bridge panel.
- Reuses the existing `POST /api/cases/{case_id}/reply-review/preview` and `/confirm` routes; no new raw-email storage has been introduced.
- Allows an optional user-provided ticket/reference field.
- Shows the same first-pass interpretation and limitations as the existing support-reply tool.
- Confirming saves only a short interpretation and optional reference to the case timeline; the raw reply text is not stored by these endpoints. Discard clears the in-browser form state.
- Keeps automatic forwarding explicitly unavailable until an operator configures a receiving domain, provider/MX routing, stable Fernet encryption key and authenticated webhook over HTTPS. No fake alias is shown and no claim of actual email reception is made.
- Added accessible, responsive styles and bumped the public shell cache to `bolkeresolve-shell-v23`.

## Verification
- `python -m pytest -q`: 254 passed, 90 subtests passed.
- `node --check frontend/app.js`: passed.
- The automated test suite validates the fallback markup and shared preview/confirm routes. Live provider email delivery is not tested because no real receiving domain/provider credentials were supplied. Browser interaction QA still needs to be run on the target deployment.

## How to test
1. Start the application with `run_windows.bat` and open `http://127.0.0.1:8000`.
2. Open a saved case and expand **Forward a support reply into this case**.
3. With inbound email environment variables absent, verify the page shows the provider warning and paste form.
4. Paste a fictional support reply, click **Review email reply**, inspect the suggested interpretation, then confirm.
5. Verify that only the short interpretation appears in the timeline and the raw email text is not retained by the confirmation route.
