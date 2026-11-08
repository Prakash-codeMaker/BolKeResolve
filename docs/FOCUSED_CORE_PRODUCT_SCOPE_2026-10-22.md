# BolKeResolve — Focused Core Product Scope

## The product we are building

BolKeResolve is a voice-first helper for everyday Indian payment and refund problems. A user explains what happened in a familiar language, reviews the facts, receives one clear source-backed next step, and may save a concise case record to help carry the story into the relevant support channel.

## Preserve these fundamentals

1. Voice and text are equally valid ways to describe the problem; review the transcript before using it.
2. Give a useful first-pass next step before forcing a long data-entry flow.
3. Ask only questions that can change the recommended route or the case record. Unknown values may remain unknown.
4. Keep the saved-case view concise: one next action up front; evidence, message and progress tools remain secondary.
5. Distinguish user-reported facts, document-supplied details, official guidance and any truly verified partner event.
6. Link to official guidance; the user reviews and sends any message.

## Initial problem focus

Primary paths: (a) failed/pending UPI payment, (b) delayed or missing merchant refund, and (c) unrecognised/suspected unauthorised payment. Other payment problems remain available as secondary options; the user can always describe a different issue. Fraud guidance must be surfaced immediately and must not wait for a normal intake sequence.

## Explicitly out of scope for this phase

- A broad complaint-filing marketplace or social network.
- Automatic filing or contacting merchants, banks, NPCI, NCH, RBI, e-Jagriti or law enforcement without an approved integration and user confirmation.
- A bank-data aggregation product, lawyer marketplace, public merchant ratings, or promises to obtain a refund.
- Additional dashboards/tabs simply to expose more features.

## Release increment in this branch

- The intake is now two steps: tell the story/get the first suggestion; then review the useful details and save the case. Payment status, support-contact status and evidence stay optional unless a relevant route requires clarification.
- The homepage presents three common entry paths up front: missing refund, failed payment and unrecognised payment. Other issue types remain available in a disclosure rather than being removed.
- The review step keeps all prior issue types, merchant/amount/date inputs, safety acknowledgement, optional evidence, and case creation behavior.
- The existing concise case detail design, Resolution Passport, source-backed deterministic resolution logic, Gnani voice adapter, and optional guided chat remain intact.

## Success measures

Measure median time to first useful recommendation, correct-route rate on reviewed test cases, percentage of users completing a case without help, first-contact completeness, and user-reported/verified outcomes separately. Do not optimise solely for fewer clicks if it makes a route less accurate.
