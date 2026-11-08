# BolKeResolve — Case Workspace Visual Refresh

**Date:** 20 October 2026  
**Scope:** Home issue picker, Preparation Kit and Activity timeline

## What changed

### Home page and issue picker
- Replaced the remaining generic issue glyphs with consistent, inline SVG line icons so that every common payment issue has a recognizable visual treatment.
- Added a consistent icon frame, better alignment between icon/title/description/arrow, clearer hover/focus states and restrained movement.
- Preserved the issue-first path: selecting a common issue preselects it in the case intake, avoiding a second selection.
- Kept the existing warm-neutral / deep-forest visual identity; the change is hierarchy and consistency, not a wholesale brand rewrite.

### Preparation Kit
- Reorganized the information into a clear reading order: first action + progress, evidence checklist, follow-up controls, then official sources.
- The first action and preparation progress now share a balanced desktop row.
- The checklist uses a two-column layout on desktop and one column on smaller screens, with status labels (“Needed” and “Helpful”), larger click targets and clear descriptions.
- Follow-up controls and official sources are distinct cards, with more consistent field alignment and action buttons.
- The progress bar exposes an accessible `role="progressbar"` and updates `aria-valuenow` when checklist items change.

### Activity timeline
- Added a compact two-column desktop layout: event feed as the main column; case snapshot and honesty note in the side column.
- Timeline events are now sorted by parsed timestamp in the browser, newest first, instead of relying on the API/database ordering.
- Added filters for All updates, Progress, Files & messages, and Notes; the selected state is reflected with `aria-pressed`.
- Each event uses a consistent inline SVG icon, event title, timestamp, explanatory copy, and optional source-channel label.
- Added a visible empty-filter message and retained the private-note form.
- Mobile uses a compact three-column / two-row tab layout, avoiding a clipped Message tab. The detail content and side summary collapse into a single column without horizontal page overflow.

## Research reviewed

This is a targeted desk review of official design documentation and product/help surfaces, not a claim that each entire product was usability-tested end to end. It included more than 15 distinct products/patterns:

1. **GOV.UK Design System — Task list** — [Task list component](https://design-system.service.gov.uk/components/task-list/). Uses concise task labels, short hints, and clearly separated status; also cautions to simplify a service before adding more task-list complexity.
2. **GOV.UK — Complete multiple tasks** — [Pattern](https://design-system.service.gov.uk/patterns/complete-multiple-tasks/). Useful for saved progress across separate tasks and sessions.
3. **US Web Design System (USWDS) — Step indicator** — [Component](https://designsystem.digital.gov/components/step-indicator/). Reinforces a clearly visible current step, concise step labels and accessible progress semantics.
4. **Tally — Conditional logic** — [Help](https://tally.so/help/conditional-form-logic). Shows the value of revealing only questions relevant to a user's answer.
5. **Tally — Progress bar** — [Help](https://tally.so/help/progress-bar). Useful for keeping multi-page forms short and communicating progress.
6. **Typeform** — [Product](https://www.typeform.com/). Conversational intake reference: one main decision/question at a time, generous whitespace, restrained secondary content.
7. **Jotform** — [Help centre](https://www.jotform.com/help/). Reference for form completion, draft retention and file-upload patterns.
8. **Material Design** — [Cards](https://m3.material.io/components/cards/overview). Related information should be grouped; cards need a clear hierarchy rather than card-for-everything clutter.
9. **Radix UI** — [Primitives](https://www.radix-ui.com/primitives). A useful reference for accessible, keyboard-aware component interactions and tab semantics.
10. **Intercom** — [Conversation events in the Inbox](https://www.intercom.com/help/en/articles/13334840-conversation-events-in-the-inbox). Consistent event names and concise metadata make histories easier to scan.
11. **Intercom Inbox** — [Inbox overview](https://www.intercom.com/helpdesk/inbox). Shows the value of keeping conversation context near the current action.
12. **Zendesk** — [Ticket lifecycle and statuses](https://support.zendesk.com/hc/en-us/articles/8263915942938-About-the-ticket-lifecycle-and-ticket-statuses). Explicit state transitions give users and agents a shared understanding of progress.
13. **Freshdesk** — [Viewing ticket activity history](https://support.freshdesk.com/support/solutions/articles/37589). Provides a ticket-history model where replies and status changes are preserved together.
14. **Wise** — [Dispute a card transaction](https://wise.com/help/articles/2977995/how-do-i-dispute-a-wise-card-transaction). Evidence and next steps depend on the specific dispute path, not a universal checklist.
15. **PayPal** — [How long dispute resolution takes](https://www.paypal.com/us/cshelp/article/how-long-does-it-take-to-resolve-a-dispute-or-claim-help257). Useful reference for explaining state, waiting period and follow-up.
16. **Airbnb** — [Resolution/help process](https://www.airbnb.co.in/help/article/3590). Reference for a resolution-centred process and keeping relevant case details together.
17. **Stripe** — [Dispute visual evidence](https://docs.stripe.com/disputes/visual-evidence?locale=en-GB). Reinforces tailoring supporting evidence to the issue category.
18. **e-Jagriti** — [Government of India platform](https://e-jagriti.gov.in/). Formal consumer-commission workflow; it should be distinguished from informal/consumer-helpline escalation.
19. **National Consumer Helpline (NCH)** — [Official portal](https://consumerhelpline.gov.in/). Relevant consumer grievance route and follow-up reference point.
20. **NPCI** — [Register a complaint](https://www.npci.org.in/register-a-complaint). Relevant source for eligible payment-system / UPI complaint routes.
21. **RBI Complaint Management System** — [CMS portal](https://cms.rbi.org.in/). Relevant to eligible RBI-regulated entities and complaint handling; not a catch-all merchant complaint destination.

### Design decisions distilled from the research
- Make the current action obvious; don't give all parts of a workflow equal visual weight.
- Use a task checklist only when users benefit from gathering items over time; show status and helpful hints alongside each task.
- Give each card one purpose and use consistent padding, headings and metadata.
- Make activity history chronological, scannable and filterable, but ensure the displayed order matches the claim “newest first”.
- Keep case context and follow-through controls near each other on desktop, then collapse intentionally on mobile.
- Differentiate official routes by problem type and never state that an external party has verified a case unless an integration actually returned that result.

## QA performed

- `python -m pytest -q`: **91 passed, 34 subtests passed**.
- `node --check frontend/app.js`: passed.
- `python -m compileall -q backend scripts`: passed.
- Offline Chromium visual QA rendered a mocked case at a 1440 px desktop viewport and a 390 px mobile viewport. It checked that Prep Kit and Activity panels were visible, that the activity filter buttons changed the visible items, that no JavaScript errors occurred during rendering, and that mobile `scrollWidth` equalled the viewport width (no horizontal page overflow).
- Timeline was verified to render newest first even if the supplied sample array was oldest first.

### QA limitations
- Browser QA used static embedded HTML/CSS and a mocked case object because this runner blocks navigation to its local HTTP service. This is not a live authenticated browser run against the actual app.
- External images/font delivery, live Gnani speech services and live WhatsApp/Meta delivery were not verified by this visual pass.

## Files changed
- `frontend/index.html`
- `frontend/app.js`
- `frontend/design-v2.css`
- `tests/test_frontend_assets.py`

## Suggested next step
Run the project locally and check the existing case on a real browser. Specifically verify that a real timeline shows newest activity first, all 5 tabs are reachable on mobile, checklist changes persist after reload, and the selected home issue remains selected throughout intake. Only then move on to real user testing or WhatsApp live integration.
