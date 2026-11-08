# Progressive Case Resolution

## Goal

Live Resolution is a guided case workflow, not a one-shot chatbot. It must understand the user's account of events, preserve uncertainty, ask for facts that change the route, request relevant evidence, and continue from the same case after a response or later update.

## State model

1. `collecting_story`: preserve interim turns; do not display resolution advice.
2. `question`: ask one material question; retain the answer and advance only after it is saved.
3. `action`: show a specific next action, why it matters, the required evidence, a source-backed route and what outcome/reference to record.
4. `collecting_update`: reopened cases collect one or more new turns without replacing the prior case history or prematurely rebuilding the plan.
5. `resolved`/closed: only mark resolved when the user reports the outcome; do not infer success from elapsed time or a generated report.

The user explicitly finishes an initial story or a resumed update. A completed intake can then advance one question/action stage at a time.

## Fact model

The workflow keeps separate fields for:
- merchant/order platform and payment app/provider;
- complaint category and order outcome;
- amount, currency and relevant dates/durations;
- full-order vs partial-item refund scope and item count;
- refund initiation/status and merchant-stated reason;
- promised refund/response timeline;
- previous support contact, ticket/reference and response;
- evidence requested, attached and user-confirmed.

Absence of a fact is not proof of its opposite. For example, "refund not received" does not prove that the merchant initiated a refund. The engine asks rather than guessing.

## Routing rules

- A marketplace/merchant refund remains a merchant-order case even when the user paid through a UPI app.
- A payment dispute is selected when the issue concerns the transfer itself (for example, failed/debited/not credited, an unknown transfer or an incorrect transfer).
- Suspected unauthorised transactions trigger an urgent safety route. The user is told to contact the bank/payment provider immediately and never share OTPs, UPI PINs, passwords or remote-access codes.
- Unknown merchants receive an official in-app/site fallback. Do not invent a customer-care number, email or deep link.
- Consumer/regulatory escalation is conditional on the entity, complaint history, elapsed time, eligibility and current official process.

## Evidence interaction

Offer one contextually relevant action at a time: upload an order/invoice, show a screenshot, use camera to capture a physical document, share a selected screen, or record a short clip. Always make the action user-initiated, explain what is being captured, allow stop/cancel/review, preserve the original, and require confirmation before extracted observations become case facts. Avoid requesting credentials, OTPs, UPI PINs or full identity/account details unless an official process truly requires them; default to redaction/minimisation.

## Case continuity

A case ID is stable. New speech, files, replies and support outcomes append to the same timeline. Reopening restores the earlier conversation and current workflow. Rebuilds of legacy resolution summaries must not overwrite the adaptive workflow, especially during `collecting_story` or `collecting_update`.

## Trust boundaries

BolKeResolve does not see merchant/bank internal records, does not send a complaint automatically, and cannot guarantee a refund. Official links are references for the user to open and verify. Drafts are editable and user-sent. User-reported facts, AI observations and externally verified facts must remain distinguishable.


## Semantic conversation understanding (optional, explicit consent)

The deterministic workflow remains responsible for selecting issue stages, evidence requests and official support destinations. Where the user explicitly enables case-understanding AI, the server may send redacted saved text and minimum relevant facts to the configured AI provider to interpret mixed-language answers, corrections and genuinely new issues. Raw microphone audio and images are excluded from this semantic text feature; image processing has separate per-image consent.

The interpreter returns a strict structured object with intent, issue family, a concise summary and candidate fact updates. Every candidate fact must include an exact quote from the saved user conversation; the backend rejects unsupported quotes, low-confidence updates, out-of-enum values and invalid amounts/statuses. A different issue may reset the issue-specific fact set only when a newly quoted issue-family update is accepted. This prevents a new UPI issue from remaining trapped in an old merchant-refund workflow.

A separate response composer may explain the rule-selected question/action in simple language. It is not permitted to choose a different support route, invent a deadline or contact, claim an external check, or send a complaint. If the provider is not configured, consent is off, or the call fails, the reviewed deterministic workflow remains available. The Live Room exposes a reversible in-session consent control and shows whether semantic interpretation was used for the latest response.

The AI provider's API data controls apply. Do not describe this as zero retention; users should avoid including passwords, OTPs, UPI PINs, full card numbers or other credentials. The app continues to redact sensitive-looking text before storing user turns.
