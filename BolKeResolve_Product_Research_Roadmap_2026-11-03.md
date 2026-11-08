# BolKeResolve — Product Research & Improvement Roadmap

**Research date:** 3 November 2026  
**Purpose:** Turn BolKeResolve from a generic advice chatbot into a reliable, evidence-first, continuously updated case-resolution workspace.

## Executive recommendation

The product should be built around a persistent **case state machine**, not around a chatbot response generator. The chatbot is an interface for collecting and explaining information. A workflow engine should decide which state the case is in, what facts are confirmed, what is still unknown, what evidence is relevant, and which next action is justified.

A reliable loop is:

1. Hear or receive a user turn.
2. Classify the turn's intent: answer, new fact, correction, contradictory fact, new issue, request to use a capture tool, question, status update, resolution confirmation or low-information filler.
3. Update the case's fact ledger with exact supporting text, source, confidence and time.
4. Reconcile conflicts without silently replacing earlier facts.
5. Select the next workflow state and only the next useful question/action.
6. Request only evidence relevant to that state.
7. Present a short action card and official source.
8. Record what the user did and what the organisation replied.
9. Continue, escalate or close based on a user-confirmed outcome.

A model can interpret language and propose structured facts, but reviewed workflow rules should control money-flow classification, safety-critical actions, official routes and final state transitions. The system must clearly label user-reported information separately from independently verified information.

---

## 1. Financial issue taxonomy: classify the money flow before the brand

Merchant name alone is not a sufficient classifier. The same brand can be involved in distinct types of money movement.

| Flow | Example | Correct workflow |
|---|---|---|
| Consumer order refund | Meesho cancelled an order; refund not received | Order outcome → refund initiated? → refund reference → promised date → merchant support |
| Merchant gateway settlement | Customers paid the business through Razorpay; collections have not reached the business bank | Payment captured? → settlement ID/status → scheduled date → UTR or failure/hold reason → bank/provider trace |
| Gateway refund issued to a buyer | A business issued a refund through Razorpay; its customer has not received it | Original Payment ID → refund ID/status → ARN/RRN/reference where applicable → customer payment method/provider trace |
| Outbound merchant payout | A business used a payout product to send funds to a vendor/recipient | Payout ID → recipient → payout status → bank reference → reversal/failure handling |
| Failed UPI debit | User's account was debited but the UPI transfer failed | UPI transaction ID → status → account debit → bank/app complaint |
| Pending UPI / recipient not credited | Sender sees pending; beneficiary has not received funds | Current transaction status → recipient confirmation → app/PSP/bank route |
| Unauthorised payment | User does not recognise a debit | Immediate bank/provider safety path; cyber-fraud reporting where appropriate |

**Razorpay-specific improvement:** distinguish Payment Gateway merchant settlements from RazorpayX payouts and from refunds that a merchant sends to its customers. The current code now correctly handles the demonstrated customer-collections-to-business-bank settlement scenario. A separate RazorpayX payout playbook should be added before claiming all Razorpay money-flow issues are covered.

### Razorpay settlement route verified in official documentation

- Dashboard: Transactions → Payments → select the affected Payment ID → view settlement details → open `settlement_id` for the detailed breakdown. [Razorpay Dashboard documentation](https://razorpay.com/docs/payments/payments/dashboard/?preferred-country=IN)
- Razorpay's FAQ describes settlement as customer money transferred to the merchant's bank account; each settlement has a settlement ID and UTR. It describes a standard domestic T+2 working-day cycle from capture, while noting that bank approval, business vertical and risk factors can change the actual cycle. Bank holidays are not working days. [Razorpay settlement FAQ](https://tfs.np.razorpay.in/docs/payments/settlements/faqs)
- For a settlement marked processed, the UTR is the bank-traceable reference. For failed settlements, inspect the registered Razorpay email and the official support process. Do not tell every merchant that T+2 is a guaranteed deadline.

**Next product improvement:** add separate question graphs for `Processed`, `Failed`, `On hold`, `Created/Initiated` and `No record`. For example, a processed settlement should lead to UTR/bank tracing; a failed one should lead to the provider's failure email/reason; a no-record state should check whether the underlying payment was captured.

## 2. Conversation intelligence and workflow engine

### A. Turn intent layer

Every new turn should be classified before it can advance a workflow:

- `answer_to_current_question`
- `new_case_fact`
- `correction`
- `contradiction`
- `new_issue_or_topic_switch`
- `capture_tool_request` (camera, upload, screen share, clip)
- `support_reply_update`
- `user_question`
- `resolution_confirmation`
- `filler_or_incomplete_utterance`

A capture request must launch a user-approved tool prompt, not regenerate the refund paragraph. A correction must update the fact ledger and recalculate the affected branch. An unrelated new issue should be offered as a separate linked case rather than corrupting the current one.

### B. Case fact ledger with provenance

Each fact should include:

- `fact_id`, canonical field, value and normalised value;
- exact evidence quote and conversation turn ID;
- who supplied it (user, model candidate, verified integration, official document);
- confidence and whether user confirmation is required;
- `observed_at`, `valid_from`, and supersedes/retracts links;
- redaction/sensitivity tags.

Do not overwrite “merchant promised 4 days” with “12 days elapsed”. Store both facts independently. The same applies to amount, order date, promised date, actual elapsed time, reference number and status.

### C. Dynamic state graph, not generic paragraph regeneration

For each supported issue, define:

- entry conditions and disqualifying conditions;
- required/optional facts;
- high-value questions in order;
- evidence needed at each state;
- branch transition rules;
- official support action;
- follow-up condition;
- escalation eligibility and required evidence;
- closure conditions.

The engine should never reuse an old question when its field is already answered. It should not generate the same action card if the case-state signature has not changed. A model should explain the selected state and next action, not invent a different state on every turn.

### D. Uncertainty and topic switch handling

If a user says “this is not an order; I run a payment gateway”, the engine should revise the issue family and show what changed. If the message is ambiguous between Razorpay Gateway and RazorpayX, ask that narrow distinction before giving account-specific instructions. If the user is just testing the microphone or says a filler word, save the transcript if appropriate but do not advance the case.

---

## 3. Speech and multilingual interaction

1. Use provider-side language identification where supported; never silently label a session Hindi or English before a transcript exists.
2. Show partial transcript text, but do not treat each provider segment as a finished user turn.
3. Use voice activity detection plus a configurable end-of-utterance pause. Let the user edit/review the transcript before committing if recognition confidence is low.
4. Preserve original audio only with clear consent, retention limits and a visible stop control.
5. Handle English/Hindi/Hinglish code-switching, Romanized Hindi, number words and dates with a separate normalisation layer; preserve original text alongside normalised facts.
6. Use idempotent commit IDs to prevent duplicate transcript turns and repeated assistant responses.
7. If speech service fails, show a clear error and let the user retry, record a voice note or type; never show “microphone detected” as proof that transcription succeeded.

**Metrics:** time from pause to transcript commit, commit failure rate, duplicate-turn rate, language correction rate, transcript edit rate and voice-to-next-action latency.

---

## 4. Camera, screen share and evidence capture

The camera is useful only when it helps the case. It should be optional and contextual.

- “Show my receipt” → offer camera, upload and screen-share options.
- “I want to show this order screen” → user chooses the tab/window; show an explicit preview and capture button.
- “Record a clip” → explain what will be recorded, require a click to start, show visible recording state, stop/save/discard controls.
- “Read this document” → show image/document preview, extract candidate fields, ask the user to confirm before those fields change the case.
- Allow “Not now”, cancel, retake, redact and remove from case.
- Do not automatically turn on the camera, record the screen or upload a document from inferred intent without user approval.

The original evidence must remain immutable. Derived OCR/transcript/AI observations should be separate artefacts linked to the original and to the claim they support.

### Evidence data model

Each exhibit should store a unique ID, original file name/type, byte size, cryptographic hash, MIME/signature result, timestamp, source action (upload/camera/screen/audio), user description, linked fact/claim, preview reference, verification status, redaction status and retention/deletion policy. Maintain an audit trail for changes. Never label user-supplied evidence as independently verified.

### Document processing

- Validate file extension, MIME type and file signature; enforce size/count limits.
- Scan uploads for malware and store outside executable/public web roots.
- Use authenticated access and short-lived signed URLs; verify case ownership for every upload, preview, download and export.
- Preserve the original; create a redacted working copy for sharing.
- OCR/extraction should show field-level confidence and exact source region/page; user confirmation is required before using extracted facts.
- Detect obvious mismatches such as a screenshot from a different merchant or amount and ask the user instead of silently attaching it as proof.

OWASP's file-upload guidance warns that extension or Content-Type checks alone are insufficient. OWASP logging guidance also says to mask or exclude credentials, access tokens, financial-account and payment-card information from logs.

---

## 5. Case workspace and presentation system

### Recommended desktop hierarchy

1. **Case title + status:** “Razorpay settlement not credited” / “Awaiting settlement status”.
2. **One primary next action:** one concise card, one CTA and a one-sentence reason.
3. **Conversation:** bounded scroll area; distinguish user, assistant, tool prompt and system status visually.
4. **Evidence needed now:** only the 1–3 items relevant to the current state; other evidence categories remain collapsed.
5. **Case facts:** amount, merchant, promise date, elapsed time, reference, current status and confidence/provenance.
6. **Progress timeline:** intake → evidence → official support → response → follow-up → resolved/escalated.
7. **Support draft:** generated for the current branch, editable, copyable, with an explicit “not sent” notice.

### Mobile hierarchy

Use a single-column layout with simple tabs/segments for Conversation, Next step and Evidence. Keep the composer accessible. Do not shrink the entire desktop two-column layout to fit a phone.

### Typography and accessibility

- Body copy around 16px; important instructions 15–16px; supporting metadata at least 12px.
- Use a readable text measure. USWDS recommends 45–90 characters per line and around 66 characters for long-form text. [USWDS typography](https://designsystem.digital.gov/components/typography/)
- WCAG 2.2 reflow expects ordinary content to fit a 320 CSS-pixel viewport without two-dimensional scrolling. [W3C reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html)
- WCAG text-spacing criterion requires the content to remain usable with line height at least 1.5×, paragraph spacing 2×, letter spacing 0.12× and word spacing 0.16× when those overrides are applied. [W3C text spacing](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing)
- WCAG AA normal text contrast target: at least 4.5:1. [W3C contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum)
- WCAG 2.2 target-size minimum is 24×24 CSS px or permitted spacing/equivalent exceptions. Prefer 40–44px for primary touch actions. [W3C target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum)
- Avoid all-caps micro-labels for important instructions; use consistent sans-serif UI typography and reserve display serif for a few page titles.
- Test keyboard focus, screen-reader labels, text zoom to 200%, reflow at 320 CSS px, reduced motion and high-contrast settings.

---

## 6. Support routes and escalation

Build a versioned source registry rather than hard-coded links scattered across templates. Each route should carry:

- organisation / legal entity / country;
- issue family and product (consumer app, payment gateway, banking, lending, insurance etc.);
- first support channel and exact user action;
- official source URL, reviewed date, last checked date and route owner;
- required identifiers/evidence;
- escalation conditions, response-time rules and scope limitations;
- retirement/expiry status when a route changes.

Do not add the National Consumer Helpline to business gateway settlement cases. RBI Ombudsman routes should only appear when the respondent is a covered RBI-regulated entity and scheme conditions fit. Consumer-commission routes should not be the default first answer for an ordinary payment issue.

Build a safe “unlisted organisation” fallback: ask for the exact organisation and use the support section within its verified official app/site. Never invent a phone number, email or contact.

---

## 7. Integrations that can make this a genuinely useful product

### Short term

- Email import/forwarding with explicit consent and sender verification; extract ticket IDs and reply dates.
- Calendar/reminder provider for user-approved follow-up dates.
- One-click export of a shareable case pack with redaction controls.

### Medium term

- Read-only OAuth integrations for payment gateways/banks where official APIs permit, with minimal scopes and revocable access.
- Webhook-based status updates for supported payment/settlement events, with signature verification, event replay protection and idempotent processing.
- User-authorised upload/import of settlement reports and bank transaction CSV/PDF, with reconciliation assistance and confirmation.

### Longer term

- Merchant support integrations that create/continue an authenticated support ticket only after the user reviews and approves the exact message and attachments.
- Multi-channel reminders (in-app, email, WhatsApp/SMS only where the user explicitly opts in) with quiet hours, frequency caps and unsubscribe controls.
- Partner/merchant case handoff with case reference and minimal evidence sharing, revocable consent and audit.

Do not ask users to paste gateway API secrets into chat. Keep credentials server-side or use OAuth, least privilege and short-lived tokens.

---

## 8. Privacy, security and trust requirements before production

- Authentication and per-case authorisation for every read, update, upload, preview, export and delete route.
- Encryption in transit and at rest; key rotation and restricted access.
- Private object storage, short-lived signed links, separate original/derivative storage and backups with restore tests.
- File allow-lists, magic-byte validation, malware scanning, size limits and safe image/PDF processing.
- Mask account numbers, Aadhaar, card numbers, CVV, OTPs, UPI PINs, API keys, passwords and session tokens before model input or logs.
- Do not send raw uploaded documents to an external model unless the user has consented and the purpose/retention is explained.
- Per-case retention period, user export, deletion request workflow and audit log.
- Prompt-injection defense for uploaded text/screenshots: treat document content as evidence, never as instructions to the agent or application.
- Keep model output untrusted; validate structured outputs and all links/actions server-side.
- Pen test IDOR/access-control, upload endpoints, archive exports, stored XSS, CSRF, SSRF and malicious PDFs/images.

No new visual treatment should imply that a document, bank entry, merchant status or AI-extracted field has been independently verified when it has not.

---

## 9. Quality system and metrics

### Automated journey matrix

Test every supported issue across:

- merchant/product/provider;
- user role (consumer vs business merchant);
- amount/date/promise/elapsed-time combinations;
- statuses and contradictory statements;
- English, Hindi, Hinglish, Romanized Hindi and code-switching;
- one utterance vs segmented speech, pauses, interruptions and retries;
- camera/photo/PDF/screen/audio evidence;
- new facts, corrections, filler, topic switching and resume;
- desktop/mobile and 200% zoom;
- provider/model unavailable fallback.

Create synthetic “gold” scenarios with expected facts, correct issue family, next question, evidence and official route. Regression tests must assert the entire case journey, not only isolated regex/helper functions.

### Product metrics

- repeated-question rate;
- incorrect-issue-family rate and user correction rate;
- percent of extracted facts accepted/rejected by users;
- speech commit failures and pause-to-response latency;
- time to first useful action;
- evidence request completion rate;
- percent of users who return after a support reply;
- action completion and user-reported resolution rate;
- export/share usage;
- route freshness and broken-link rate;
- privacy opt-out rate and user trust feedback.

Do not optimise only for “resolved” counts; users must be able to report no progress or an organisation's refusal without being nudged into a false success state.

---

## 10. Prioritised execution plan

### P0 — correctness and trust (before external pilot)

1. Finish the core taxonomy: gateway settlement vs RazorpayX payout vs refund issued to a buyer vs failed/pending UPI.
2. Make every turn intent-aware and keep the state graph/fact ledger authoritative.
3. Implement question-skip rules, correction/contradiction handling and new-case handoff.
4. Verify voice capture/commit/segmentation on actual Chrome/Edge devices with English, Hindi and code-switching.
5. Complete camera/screen/clip stop/cancel/preview/save flows with user consent.
6. Secure uploads and verify per-case authorisation, storage, encryption, redaction, backups and retention.
7. Complete browser-based visual and accessibility verification at desktop, mobile, 320px reflow, 200% zoom and keyboard-only usage.

### P1 — usefulness and continuity

1. Add more reviewed playbooks: Meesho/Flipkart delayed refund, missing/damaged delivery, UPI pending, failed debit, duplicate charge, gateway settlement and support non-response.
2. Build support reply import/review and evidence-to-claim linking.
3. Add reminder delivery with explicit opt-in and reliable channel configuration.
4. Add polished PDF dossier with a timeline, confirmed facts, disputed facts, evidence index and attachments.
5. Add multilingual support drafts and voice read-back of the selected next action.

### P2 — integration and scale

1. Read-only OAuth payment integrations, where providers permit.
2. Signed webhook ingestion and idempotent settlement/payment updates.
3. Merchant support ticket integration and approved handoff.
4. Organisation/source review dashboard and broken-link monitoring.
5. Case analytics and privacy-preserving product-quality dashboards.

## Bottom line

BolKeResolve's defensible product advantage will not be a prettier chatbot. It will be a trustworthy case graph that remembers the user's story, understands the type of money flow, knows exactly what evidence matters, chooses a relevant official route, and helps the user continue when a new reply or document arrives. The interface should make that next action obvious in one glance.
