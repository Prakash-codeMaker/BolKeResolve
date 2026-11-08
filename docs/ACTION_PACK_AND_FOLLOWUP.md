# Resolution Prep kit — implementation guide

## Product behavior

The case workspace now has five views: Next steps, Prep kit, Evidence, Message and Activity. The Prep kit is meant to answer three questions quickly: what do I do first, what information should I gather, and when should I follow up?

### Evidence checklist

`backend/action_pack.py` contains deterministic templates for refund-not-received, failed/pending UPI, duplicate charge, incorrect amount, undelivered order, suspected fraud and a general fallback. Each item has a stable task key, description and required/helpful marker. Checked state is stored per case in SQLite. The score is the fraction of required checklist items marked as ready. It is a user assertion, not file verification. Uploaded evidence count is displayed separately.

### Action pack

`GET /api/cases/{case_id}/action-pack` returns case-specific summary, first action, checklist and readiness, follow-up state, official sources, disclaimer and `export_text`. The UI supports copying or downloading the plain-text pack. No external submission happens.

### Follow-up

`PUT /api/cases/{case_id}/follow-up` saves `{due_date, note, completed}`. The due date is an ISO `YYYY-MM-DD` value. An empty date and note with `completed: false` clears the reminder. The app shows the due state when the case is opened; there is currently no OS/browser push notification, background task, email or WhatsApp reminder.

### Draft editing

`POST /api/cases/{case_id}/draft` generates an initial draft. `PUT /api/cases/{case_id}/draft` stores a user-edited draft after best-effort sensitive-text scrubbing. Both operations are local case actions; neither sends a message.

## API additions

- `GET /api/cases/{case_id}/action-pack`
- `PATCH /api/cases/{case_id}/checklist/{task_key}` with `{ "checked": true }`
- `PUT /api/cases/{case_id}/follow-up` with `{ "due_date": "YYYY-MM-DD", "note": "...", "completed": false }`
- `PUT /api/cases/{case_id}/draft` with `{ "text": "..." }`

Every route uses the case access check; checklist task keys are allowlisted. New tables are created by the regular initialization migration, preserving old case rows.

## Source hierarchy

- Failed/pending UPI transfer guidance uses NPCI's UPI FAQs.
- Suspected unauthorized/online financial fraud directs the user to the bank/payment provider and official cybercrime reporting route (1930 / cybercrime.gov.in).
- Consumer/merchant complaints can consider the National Consumer Helpline as a pre-litigation mechanism.
- Formal consumer-commission filing is shown as a later option with e-Jagriti help docs, not as a guaranteed or automatically eligible next step.
- RBI's Ombudsman scheme is relevant only for eligible RBI-regulated-entity complaints after the required first approach and applicable conditions.

Sources are public guidance links; BolKeResolve does not certify a user's eligibility, inspect transactions, submit a complaint, or guarantee an outcome.

## Local test commands

```powershell
python -m pytest -q
node --check frontend/app.js
python -m compileall -q backend tests
```


## Reminder delivery states

The case timeline distinguishes a reminder accepted by the Cloud API from provider-reported `sent`, `delivered`, `read`, or `failed` states. Provider receipts are signature-validated, deduplicated, and applied monotonically; a repeated or older receipt does not add another timeline event or downgrade the current state. These are provider-reported delivery states, not proof that a person read or acted on the message. Reminder runs use a short per-follow-up lease to prevent duplicate sends from overlapping scheduler invocations.
