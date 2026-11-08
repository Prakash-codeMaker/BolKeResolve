# BolKeResolve WhatsApp integration — 21 October 2026 release note

## What changed from the 20 October milestone

- Added retryable webhook-processing leases and attempt/error-type tracking. Stale processing claims can be recovered. If the case command already committed but sending failed, the stored reply is reused instead of reapplying the command.
- Kept the consent check ahead of `LINK <CODE>` so a pairing token cannot silently reactivate a contact after `STOP`; first-time link attempts now explain how to opt in without consuming the one-time code.
- Recognised common, explicit opt-out phrases beyond `STOP` and added regression tests for this behavior.
- Added a helpful START-first reply for a first-time `LINK <CODE>` attempt, preserving the one-time code for retry after opt-in.
- Expanded opt-out command recognition to common explicit phrases (`STOP`, `UNSUBSCRIBE`, `OPT OUT`, `QUIT`, and related specific phrases).
- Made privacy URL and support escalation settings explicit launch gates. `.env.example` now leaves these fields blank so example values cannot accidentally pass readiness checks.
- Added a draft privacy-notice page, a safe configuration-preflight script, Docker/Render starting files, an India timezone setting for follow-up reminder queries, and a deep integration/launch guide.
- Updated the case-link screen instructions and tests for retry recovery, opt-out state and START-first linking.

## Verification performed in this build environment

- `python -m unittest discover -s tests -q`: passed (104 tests; the existing suite includes additional subtest assertions).
- `python -m py_compile backend/main.py backend/whatsapp.py scripts/send_whatsapp_reminders.py scripts/check_whatsapp_config.py`: passed.
- `node --check frontend/app.js`: passed.
- Network integrations remain mocked in automated tests. No live Meta/Gnani delivery was performed from this build environment.

## Still required before launch

- Configure the actual Meta app, WABA, number, token, app secret, verify token and public HTTPS webhook.
- Publish a final accurate privacy notice and monitored support channel; complete retention/deletion and incident procedures.
- Verify a live Meta test-number flow and Gnani speech service with your own account/credits.
- Complete mobile/accessibility, rate-limit, backups/restore and security review.
- Keep reminders disabled until a matching Meta-approved utility template is configured and its cost is accepted.

See `docs/WHATSAPP_INTEGRATION_GUIDE_2026-10-21.md` for the full setup and release checklist.
