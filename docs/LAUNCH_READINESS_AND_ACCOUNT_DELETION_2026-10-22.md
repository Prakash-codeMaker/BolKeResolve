# Launch-readiness hardening — 22 October 2026

This increment preserves BolKeResolve's focused voice-first payment/refund helper flow. It does not add complaint filing, a new case dashboard, or automatic contact with banks/merchants.

## Account and data deletion

When production authentication is enabled, a signed-in user can open **My cases → Account & privacy → Delete account and saved data**. The user must re-enter the current password and check an irreversible-action acknowledgement. The endpoint `DELETE /api/auth/account` then:

- deletes the account and revokes its sessions;
- deletes owned cases and their case-linked timeline, checklist, follow-up, outcome, and evidence metadata through SQLite foreign keys;
- deletes linked active WhatsApp contact/session records for contacts owned by that account and webhook records associated with the account's contacts or owned cases;
- attempts to remove evidence files from the active evidence directory after the database transaction commits.

It does **not** recall copies the user previously downloaded/exported, data already sent to third-party providers, or copies in hosting backups. A deletion request is not secure-media erasure of the SQLite volume. The operator must disclose backup/provider retention and ensure the documented policy is followed. If evidence-file cleanup fails due to an operating-system error, the server logs a cleanup warning for operator follow-up; the database records are still removed.

The route is unavailable when authentication is disabled. It is CSRF-protected by the app's existing same-origin request check and requires password re-authentication. Do not treat password re-entry as a replacement for email verification, password reset, MFA, or a complete privacy/legal review.

## API caching

All `/api/` responses now receive `Cache-Control: no-store, max-age=0` and `Pragma: no-cache` centrally. This is an additional safeguard; it does not replace authentication, per-owner access checks, secure transport, or edge/proxy configuration.

## Production preflight

Run from the repository root:

```bash
python scripts/check_release_readiness.py
```

For `BOLKE_ENV=production`, the script requires a bare public HTTPS origin, a configured HTTPS privacy URL, a monitored support route, authentication, a present writable data directory, and a bundled `frontend/privacy.html` with no known draft banner/operator placeholders. It reports email verification/password recovery as a known gap and prints operator checks for persistent storage, backups/restore, security/privacy review and end-to-end testing. Passing the script is not a security certification.

### Before inviting real users

1. Replace every placeholder in `frontend/privacy.html` with the operator's truthful legal identity, privacy/support contact, retention and deletion details, third-party processing/location details, age policy and incident route; obtain appropriate legal/privacy review.
2. Configure real HTTPS, an exact public origin, authenticated sessions and persistent storage; test data restoration.
3. Decide and implement an acceptable verified-email/account-recovery baseline before broad public registration.
4. Set a shared gateway rate/quota for paid Gnani STT/TTS endpoints; in-process throttles are not shared across workers.
5. Choose and test a malware-scanning/content-disarm strategy for evidence files. File-signature checks and text redaction are not malware scanning or complete DLP.
6. In a normal desktop and mobile browser, test registration/sign-in, the two-step intake, case save/edit/delete, evidence upload/delete, account deletion, export/print, keyboard navigation and focus behavior.
7. Verify live Gnani requests with the operator's own credentials and synthetic audio. Automated tests use mocked provider replies.

## Automated checks

```bash
python -m pytest -q
node --check frontend/app.js
python -m compileall -q backend tests scripts
```

Current verified local suite after this increment: 176 tests and 69 subtests. Live services, hosted TLS/persistence, browser visual QA, backups/restore, and independent security review are not verified by those tests.
