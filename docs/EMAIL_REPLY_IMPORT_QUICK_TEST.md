# Email reply import — quick test (29 October 2026)

This tests the working manual fallback. Automatic forwarding remains off until a real inbound-email domain/provider is configured.

1. Extract the project and run `run_windows.bat`. Open `http://127.0.0.1:8000`.
2. Create a fictional test case and open its saved case page.
3. Expand **More case tools → Forward a support reply into this case**.
4. If no provider is configured, check that the warning is followed by the manual form. Paste this synthetic message:

   `Subject: Refund update\n\nYour refund has been initiated. Please allow 5 business days.`

5. Click **Review email reply**. Confirm the preview says initiation is not proof of credit. No case timeline event should be created by preview alone.
6. Add an optional synthetic reference such as `TEST-REF-12` and click **Save interpretation to timeline**.
7. Open the case history. It should show a brief user-confirmed interpretation and optional reference, not the original message body.
8. Repeat and click **Discard review** instead; no timeline update should be added.

Never use a real customer's message or paste an OTP, PIN, password, full card number, or unnecessary personal information during this test. Sensitive-text redaction is best-effort.

## What this does not test

This fallback does not receive email automatically or create a forwarding alias. To activate automatic forwarding, configure a receiving domain/subdomain and DNS/MX routing, a stable `BOLKE_INBOUND_EMAIL_ENCRYPTION_KEY`, a strong webhook token or supported Basic credentials, a public HTTPS URL, provider webhook delivery and a synthetic end-to-end message. See `LIVING_RESOLUTION_PASSPORT_AND_CASE_INBOX_BRIDGE_2026-10-23.md`.
