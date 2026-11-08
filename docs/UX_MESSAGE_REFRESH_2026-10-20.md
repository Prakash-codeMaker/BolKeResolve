# BolKeResolve — UX and Support Message Refresh

**Prepared:** 20 October 2026  
**Scope:** Homepage hierarchy, new-case details step, organisation-facing message draft, comparative UX review.

## Executive summary

BolKeResolve had a visually distinctive style, but the home page placed too many large photographic and promotional sections before the practical action. The second intake step depended on a native select for issue type, even though users need help recognizing the closest problem. The case message was a generic paragraph in a large textarea; it repeated the user story but asked no specific questions relevant to the issue, and it included an internal disclaimer which was useful in the application but inappropriate in a message to a merchant.

The implementation therefore does three things:

1. **Homepage:** simplify to a clear value proposition, one primary CTA, common issue shortcuts, and a compact three-step explanation. The issue shortcuts carry their selection into the intake.
2. **Intake:** replace the basic-details select with eight visual issue choices, then use a consistent two-column details grid for merchant, amount, and date; unknown details remain optional.
3. **Support message:** add a visible case-context strip and editor label, and replace the generic draft with issue-specific requests for refunds, failed/pending UPI, duplicate charges, incorrect amounts, undelivered orders, possible fraud, and other payment problems. The message uses only facts stored in the case and omits unknown fields. Internal verification/safety explanation remains outside the copied message.

## Comparative review: 22 product/pattern references

This is a targeted review of 26 product pages/pattern references across form UX, grievance services, payment disputes, support case-management and design systems. It is not a claim that 22 full products were usability-tested with participants. Recommendations below are based on published flow documentation and patterns, and need real-user validation.

| # | Product / reference | Pattern observed | Application to BolKeResolve |
|---:|---|---|---|
| 1 | [GOV.UK Design System — Question pages](https://design-system.service.gov.uk/patterns/question-pages/) | Ask only for information needed at that stage; reuse information already provided; offer a clear Back path. | Keep story, issue classification and action details in distinct stages. Do not ask for merchant/date again if confidently extracted. |
| 2 | [GOV.UK Design System — Check answers](https://design-system.service.gov.uk/patterns/check-answers/) | Review collected answers before the user commits to the next action. | Keep a fact review point before saving or sharing any action pack. |
| 3 | [GOV.UK Design System — Error summary](https://design-system.service.gov.uk/components/error-summary/) | Put an error summary at the top and link errors to the relevant field; preserve entered answers. | On validation failure, show a useful, field-linked issue without wiping the user's story. |
| 4 | [GOV.UK Design System — Form structure](https://design-system.service.gov.uk/get-started/structure/) | Semantic hierarchy and predictable grouping. | Group issue choice separately from optional case facts; use logical headings and field labels. |
| 5 | [Tally — Conditional logic](https://tally.so/help/conditional-logic) | Show/hide questions and jump past irrelevant questions based on responses. | Later, reveal payment-network reference fields only for UPI cases; do not burden merchant-delivery cases with them. |
| 6 | [Tally — Progress bar](https://tally.so/help/progress-bar) | Show users where they are in a longer flow. | Keep an honest three-stage indicator and use concise stage names. |
| 7 | [Typeform — Multiple questions on one page](https://help.typeform.com/hc/en-us/articles/38099463383188-How-to-add-multiple-questions-to-a-form-page) | Balance one-question focus with grouped questions when they make sense together. | One decision per step, but group merchant/amount/date because they are a natural set of case facts. |
| 8 | [Jotform — Continue forms later](https://www.jotform.com/help/495-setting-up-the-continue-forms-later-feature-in-card-forms/) | Allow a user to pause and continue rather than forcing completion in one sitting. | Preserve progress as a future priority; case facts/evidence can take time to gather. |
| 9 | [PayPal India — Resolution Center status](https://pep.paypal.com/in/cshelp/article/how-do-i-check-the-status-of-my-dispute-or-claim-help181) | The user can check case state and see/respond to messages; escalation is a distinct phase. | Make a case useful after the first draft by tracking what the user did, what response arrived, and what is next. |
| 10 | [Wise — Disputing a card transaction](https://wise.com/help/articles/2977995/how-do-i-dispute-a-wise-card-transaction) | Check transaction state before choosing a dispute route; differentiate pending from completed. | Ask about status and payment type before recommending a route. Do not confuse a pending transaction with a missing refund. |
| 11 | [National Consumer Helpline (NCH)](https://consumerhelpline.gov.in/) | Official multichannel grievance support, including portal and WhatsApp; references/docket and tracking are central. | Prepare the user for the real route, keep the official reference when they provide it, and make return visits worthwhile through action updates. |
| 12 | [NPCI — Register a complaint](https://www.npci.org.in/register-a-complaint) | Route depends on product/transaction facts; the site asks for transaction identifiers and notes that unauthorised transactions should go to the bank. | Use the right route and clarify that BolKeResolve has not checked NPCI or bank records. Do not imply that a merchant is always the right contact for UPI fraud. |
| 13 | [RBI Complaint Management System](https://cms.rbi.org.in/) | Official regulated-entity complaint route with eligibility boundaries. | Present RBI escalation only where appropriate, after the complaint route and eligibility are understood. |
| 14 | [e-Jagriti](https://e-jagriti.gov.in/) | Formal consumer commission filing and case-history/status are separate from informal support. | Clearly distinguish merchant contact, NCH pre-litigation grievance, and formal consumer-commission proceedings. |
| 15 | [Meta — WhatsApp Business Platform](https://developers.facebook.com/docs/whatsapp/cloud-api/overview) | Official business messaging platform with configured numbers, messages and webhooks. | Replace a dead link with an actual service: inbound and outbound messages, case linkage, consent, status and failure logging. |
| 16 | [Meta WhatsApp — Webhook payload reference](https://www.postman.com/meta/whatsapp-business-platform/folder/tduohwq/webhook-payload-reference) | Webhooks require a publicly reachable HTTPS endpoint and subscription/configuration. | Localhost can’t receive platform webhooks; live integration needs deployed HTTPS, Meta credentials, webhook verification and operational monitoring. |
| 17 | [Microsoft Fluent 2 — Accessibility](https://fluent2.microsoft.design/accessibility) | Clear structure, hierarchical headings, visible focus, responsive reflow, and concise language support usability. | Align field spacing and headings, improve mobile reflow, and avoid relying on colour alone for selection. |
| 18 | [Microsoft Fluent 2 — Design principles](https://fluent2.microsoft.design/design-principles) | “Built for focus”: reduce visual noise, stay predictable, adapt to device and context. | Keep one hero image and reduce redundant home-page cards/sections. The page should help people act, not showcase every feature at once. |
| 19 | [Nielsen Norman Group — Homepage design](https://www.nngroup.com/articles/homepage-design/) | Homepages should answer what the product is, what users can do, and where to begin; clutter obscures the task. | Primary CTA plus common issue chooser is the front-page hierarchy. Avoid duplicated CTAs, redundant promo cards and repeated imagery. |
| 20 | [Nielsen Norman Group — Visual hierarchy](https://www.nngroup.com/articles/visual-hierarchy-ux-definition/) | Scale, placement, contrast, grouping and whitespace guide attention. | Use consistent field groups, aligned columns, clear issue-card selected state, and a compact metadata strip in the message editor. |
| 21 | [Intercom — Assign conversations](https://www.intercom.com/help/en/articles/6561699-assign-conversations-to-teammates-and-teams) | Conversations need ownership/routing to be reliably handled, not merely stored. | Future organisation-contact support should include a human/partner handoff, clear owner, next response deadline, and a visible status rather than only an AI reply. |
| 22 | [Zendesk — Ticket lifecycle/statuses](https://support.zendesk.com/hc/en-us/articles/8263915942938-About-the-ticket-lifecycle-and-ticket-statuses) | Explicit statuses communicate where work stands and what needs to happen next. | Use states such as Draft ready, User contacted organisation, Awaiting response (user-reported), Follow-up due, Resolved (user-reported); never present user reports as verified company status. |
| 23 | [Stripe — Disputes API/reference](https://docs.stripe.com/api/disputes) | Dispute is a structured object with reason, evidence, status and deadlines. | Use issue-specific evidence packs and reminders; deadlines/required evidence should be sourced, not invented. |
| 24 | [Stripe — Evidence examples](https://docs.stripe.com/disputes/visual-evidence) | Evidence requirements differ by issue, such as credit-not-processed versus product-not-received. | Tailor the checklist to issue type rather than giving the same document list to everyone. |
| 25 | [Airbnb — Resolution Centre requests](https://www.airbnb.co.in/help/article/3590) | Users can find past requests, read status and respond to requests in the resolution centre. | One stable case page should preserve prior messages and next action instead of requiring the user to reconstruct history each time. |
| 26 | [Freshdesk — Ticket fields/status](https://support.freshdesk.com/support/solutions/articles/50000010094-understand-and-customize-ticket-fields) | Status is part of a lifecycle, while source/channel can be tracked alongside the ticket. | Record whether an update came from the website, WhatsApp, or a user note; keep its provenance visible. |

## Implementation details

### Homepage

- Removed the original run of large photo cards, three more photographic scenarios, oversized WhatsApp promo, evidence promo and bottom CTA from the first-visit path.
- Kept a single hero, then a grid of common issue shortcuts and a concise three-step explanation.
- Issue shortcuts open the new-case flow with the chosen issue preselected, and the visual issue radio cards share the same hidden source select so the choice is consistent with the existing backend payload.
- Retained the cream/forest/mint visual identity and the existing primary illustration instead of introducing a new brand system.

### Intake form

- The second stage now exposes the eight supported issue types as accessible radio cards rather than making the user decode a dropdown.
- Merchant, amount and date are grouped in a two-column details grid; the unknown values remain optional.
- A short side rail reassures users that details can be corrected, evidence can be added later, and nothing is sent without approval.
- Desktop collapses to a single-column layout on small screens and reflows the option grid to keep tap targets large enough.

### Support message

- Generator now uses case-specific requests, including: refund initiation/reference/credit date; UPI outcome and reversal status; duplicate charge review; amount discrepancy; undelivered order; and urgent treatment of a suspected unauthorised transaction.
- It adds amount, payment date, status and previous-support contact only when the stored case contains those facts.
- Whole-number amounts render as `₹850`; non-whole amounts keep two decimals. Dates are formatted for people rather than copied as ISO values.
- The internal BolKeResolve case ID and “independently verified” disclaimer are not inserted into a merchant-facing draft as if they were the merchant's reference or part of the customer's request.
- The UI shows issue, amount and app case reference separately, keeps the message fully editable, provides copy/save/read-aloud actions, and warns that changing language replaces the draft.
- English, Hindi and Hinglish drafts are rule templates, not machine-certified legal translations. Native-speaker QA remains necessary before calling all templates production-ready.

## Product choices and next steps

### This pass (implemented)

1. Reduce homepage choice overload.
2. Make issue selection visual and carry selection into intake.
3. Improve field alignment and responsive spacing.
4. Make organisation-facing drafts more specific without inventing missing facts.
5. Add regression tests for homepage structure, issue-card wiring, missing-fact omission and three-language draft behavior.

### Next engineering milestone

1. Add browser-based end-to-end tests that start a case from each homepage issue shortcut, check the selected issue, save the case and generate a draft.
2. Run visual regression screenshots at desktop, tablet and mobile widths after deploying to a browser environment that permits local/preview navigation.
3. Add real save/resume with explicit privacy controls instead of storing sensitive story text in browser local storage by default.
4. Establish an “action provenance” event schema for each case update (user-entered, imported from official portal with consent, received from WhatsApp webhook, or staff-reviewed), plus source URL and timestamp.
5. Only build direct organisation contact where there is an official, permissioned integration or a clearly labelled user-approved handoff. Where it is merely an external link, record “opened by user” instead of “contacted”.
6. Pilot with 20–30 consenting users; measure completion, extraction corrections, actions actually taken, follow-up completion, user understanding of unverified states, and whether the product helped them reach the next official step.

## Validation status

The backend and frontend regression suite is run locally for this build. Chromium is installed, but the runtime environment blocks direct navigation to `127.0.0.1` with `ERR_BLOCKED_BY_ADMINISTRATOR`, so I could not truthfully complete a visual browser sign-off here. Live Gnani transcription and live Meta WhatsApp delivery are also not verified by this UX pass. Use the provided ZIP with a local browser on your own Windows laptop for final visual confirmation.
