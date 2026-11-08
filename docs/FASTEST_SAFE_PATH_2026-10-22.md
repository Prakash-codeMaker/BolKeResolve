# Fastest Safe Path — 22 October 2026

## What changed

BolKeResolve now returns a structured `fastest_path` summary and at most one decision-changing `next_question` from the deterministic resolution preview.

- For failed/pending UPI-like scenarios with an unknown status, the first question offers direct choices for **Failed**, **Pending**, **Successful**, or **Not sure**. The selected answer is sent back to the preview without rerunning extraction over the story, preventing a previously extracted suggestion from silently overriding the user's choice.
- Where the story says a UPI payment failed but the selected status says **Successful**, classification is deliberately lowered to an unclear general payment issue and a conflict question appears. The system does not present a confidently specific failed-payment route until the mismatch is resolved.
- A confirmed **Pending** selection on a transaction-like story routes to the pending/not-credited playbook rather than the failed-payment playbook. A confirmed **Failed** selection on an UPI-like story routes to the failed-payment playbook.
- For non-urgent cases, the system may ask whether support has already been contacted. A “yes” answer shifts failed UPI, pending UPI and delayed-refund guidance toward continuing the existing support thread and using its reference rather than starting over.
- Helpful missing fields remain in `missing_information`, but are not converted into a chain of additional prompts. Amount, merchant and date remain optional details; the first-pass flow asks only questions likely to change the first action.
- Suspected unauthorised/fraud cases show the immediate safety route without blocking the user with intake questions.
- The preview uses short inline answer buttons, with keyboard focus styling and a two-column mobile arrangement. Choosing an answer refreshes the result and keeps the user on the same screen.
- Static shell cache incremented to `bolkeresolve-shell-v10`. API responses remain network-only and are not cached by the service worker.

## Safety constraints

- All payment facts remain user-reported unless an authorised external integration verifies them. No live bank/UPI query, refund action or complaint submission was added.
- The path is guidance, not a refund guarantee. Official sources and time limits must be checked for the specific transaction and current rules.
- Urgent fraud instructions take precedence over the Fastest Safe Path question flow.
- A saved/selected app status can change the playbook; contradictory narrative/status information is not silently promoted to high confidence.

## Validation

Run from the repository root:

```bash
node --check frontend/app.js
python -m py_compile backend/resolution.py
python -m unittest discover -s tests -q
```

The test suite includes cases for structured status choices, pending-vs-failed routing, conflicting status/story information, following up on an existing refund thread, and no blocking question in the urgent-fraud route. These automated checks do not constitute live Gnani API, bank, merchant, or public-deployment verification.

## Saved-case clarification loop

The saved-case overview renders the same decision-changing question and response chips as the intake preview when the saved resolution contains a supported question. Answers update the saved case through the existing case-details endpoint, which recalculates the plan; the user is then shown the next applicable question (for example, payment status first, whether support was already contacted second). The helper preserves all other saved facts, labels answers as user-provided, and explicitly notes that the update does not query bank/provider records.

The status clarification intentionally does not provide a "Not sure" answer chip, because choosing unknown would repeat the same question without progress. Users may still continue to the primary support-message action or review/edit case details without answering it.
