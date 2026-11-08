# BolKeResolve: Deep Differentiation, Integration and Resolution Strategy

**Research cut-off:** 22 October 2026  
**Scope:** Current Indian consumer/payment grievance journey; direct and adjacent competitors; actionable product differentiation; official integration feasibility; rules and safety boundaries; a demo and validation plan.  
**Project basis:** Review of the supplied BolKeResolve project bundle and its existing docs, especially `IMPLEMENTATION_STATUS.md`, `RESOLUTION_PASSPORT_AND_NO_API_HANDOFF.md`, `ACTION_PACK_AND_FOLLOWUP.md`, `PRODUCT_STRATEGY_RESET_AND_COMPETITIVE_RESEARCH_2026-10-21.md`, voice/WhatsApp guides, and the current frontend/backend feature descriptions.

> **Scope note:** This is product research, not a legal opinion or a guarantee that every current portal, API or workflow has been independently tested. Official rules and eligibility depend on the payment rail, transaction facts, the regulated entity involved, the date, and any later circular. Public competitor pages establish what they advertise, not whether every feature works as advertised. Have qualified Indian consumer/payment counsel review rules before public launch.

---

## 1. Executive decision

### Do not compete as “another AI complaint writer”

A direct India-focused competitor, **RefundPe**, currently advertises complaint drafting, sending grievance emails with user approval, follow-ups, reply tracking and regulator complaint packs. That substantially overlaps with a generic “AI that gets your refund” proposition. Its public homepage describes a Day 4 follow-up and a Day 7 regulator pack; the service's terms say the customer must review AI drafts and no outcome is guaranteed. See its [homepage](https://refundpe.com/), [terms](https://refundpe.com/terms), and [privacy policy](https://refundpe.com/privacy).

Government and ecosystem systems also cover important parts of the journey:

- **UPI HELP** is an NPCI pilot for digital-payment queries, supported transaction-status checks, complaint logging/tracking and UPI mandate management for users of participating members. Its circular describes API integration for participating members—not a generic public API that any startup can simply call. ([NPCI circular, 8 October 2025](https://www.npci.org.in/uploads/UPI_OC_No_227_FY_2025_26_Introduction_of_UPI_HELP_Assistant_pilot_an_AI_powered_support_for_UPI_payments_cd501de8f3.pdf))
- **National Consumer Helpline (NCH)** already has multi-channel intake in 17 languages, docket numbers, document upload and a company-convergence model. In a 17 February 2026 release, the government said NCH facilitated ₹52 crore in refunds across 31 sectors for 79,521 refund-related grievances over the previous nine months. ([NCH](https://www.consumerhelpline.gov.in/public/convergenceprogram), [PIB result](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2229099&lang=1&reg=3))
- **e-Jagriti** provides online consumer-commission filing, case management, document handling, tracking and virtual proceedings. ([National Informatics Centre](https://www.nic.gov.in/project/e-jagriti-a-unified-digital-platform-for-consumer-justice/))
- **RBI's Integrated Ombudsman Scheme 2026** provides a formal, free route for eligible grievances about covered regulated entities, with new maintainability and timing rules effective 1 July 2026. ([RBI FAQ](https://old.rbi.org.in/commonman/english/scripts/faqs.aspx?id=3407))
- **ConsumerComplaints.in** operates a public-facing consumer complaint and company-response platform. ([site](https://www.consumercomplaints.in/), [about](https://www.consumercomplaints.in/about-us.html))

So BolKeResolve should not claim that AI chat, drafting, reminders, a case history, or complaint tracking are individually unique. Several are already provided by competitors or official services, and parts are already in the current BolKeResolve code.

### Recommended position

> **BolKeResolve is the consumer's evidence-to-resolution workspace: it works out which process fits the facts, shows the rule and source behind the next step, prepares a complete user-approved evidence pack, and keeps the case together as the user moves between support channels.**

The differentiator is not one isolated feature. It is the *quality and continuity of the entire resolution journey*:

1. **Correct case classification** rather than treating every “refund problem” alike.
2. **A versioned, evidence-backed routing and deadline engine** rather than a generic AI response or one-size-fits-all Day 4/Day 7 schedule.
3. **Evidence-to-claim traceability**: each material statement in the draft is marked as user-reported, extracted from a document, user-confirmed, or externally verified.
4. **A living case timeline** that understands the meaning of a reply, deadline, promise, request for information or rejection—not merely that a reminder date has arrived.
5. **A careful handoff to real official channels** without pretending BolKeResolve is a bank, regulator, court or refund processor.
6. **Outcome learning** based only on consented and correctly labelled outcomes, to improve future workflows over time.

This is a **differentiation hypothesis**, not a verified exclusivity claim. Validate it through hands-on competitor trials and user research before using claims such as “first”, “only” or “no other platform”.

---

## 2. What the current BolKeResolve project already does—and what is still missing

The current project is not starting from zero. Its documentation describes:

### Existing foundation

- Text and voice-first intake with a confirm/correct step for extracted details.
- Issue-specific deterministic resolution plans and official source links.
- Editable support-message drafts and safety reminders.
- Evidence checklist and file inventory.
- A Resolution Passport export in JSON plus a printable case view.
- A case timeline, user-entered follow-up date/notes, and user-reported outcomes.
- User-controlled email and WhatsApp draft handoffs.
- Optional WhatsApp integration for user-initiated conversations with the same case engine.
- Static/PWA shell caching while sensitive `/api/` resources are kept network-only.

These features are a good foundation. The project documentation explicitly states that the passport does not prove a payment occurred, a message was sent or read, a refund arrived, or an external complaint was filed. The current email/WhatsApp handoffs open editable drafts; they do not give BolKeResolve delivery or reply visibility. The follow-up date is persisted, but automatic reminders are not yet implemented. The evidence flow does not currently OCR/classify files, and uploaded evidence is not fully embedded in the Passport export. The app does not query payment systems or submit grievances to NPCI, NCH, RBI or e-Jagriti.

These are meaningful boundaries. Product language must match them.

### The most valuable gaps to close next

| Gap in the current project | Why it matters | Next meaningful increment |
|---|---|---|
| Evidence is a checklist plus uploaded file metadata | User still has to manually understand which screenshot proves which part of the story | Extract key fields from uploads; let the user confirm them; map claims to evidence pages/files; generate a clean evidence index |
| Follow-up date is visible only in the case | Users may forget to return to the site | Opt-in reminders with a user-visible reason, safe timing, cancel controls and correct time-zone handling |
| External handoffs are not tracked | Opening `mailto:` or WhatsApp does not show whether anything was sent | Track an explicit “I sent this” user event, recipient, timestamp and reference number; distinguish user-reported from provider-confirmed events |
| Replies do not update case logic | A generic reminder can be wrong after a partial answer or information request | Let a user upload/forward a reply; classify response type; ask the user to confirm; recalculate the next step and timeline |
| Rules can be mistaken for a static guidance page | Payment, consumer, regulator and fraud processes are different, and regulations change | Versioned case decision rules with effective dates, sources, conditions, test cases and a visible “why this route” explanation |
| Passport export mostly contains case facts and evidence metadata | A receiving support team may still need the files and exact chronology | A user-reviewed, redacted “Complaint-ready Pack” with chronology, evidence index, referenced documents, draft, source list and clear provenance labels |
| No authorised transaction-status connection | The app cannot claim to have verified a transaction | Explicit “user supplied / user-confirmed / source-backed / externally verified” labels and partnerships only where approved access exists |

**Priority:** close the route accuracy, evidence quality and action follow-through gaps before expanding issue categories or adding more visible sections.

---

## 3. Competitive map: what people can already do

### 3.1 Direct and official alternatives

| Service | Existing value | What BolKeResolve must not pretend to replace | Possible BolKeResolve role |
|---|---|---|---|
| **RefundPe** ([site](https://refundpe.com/), [terms](https://refundpe.com/terms)) | Markets AI-generated complaint letters, user-approved email dispatch, follow-ups, reply tracking and escalation packs across shopping, quick commerce, travel, UPI/banking, insurance and telecom. Its homepage describes Day 4/Day 7 actions; public pages advertise optional automated dispatch/follow-up. | Complaint drafting, grievance emails, reminders, broad category coverage, or “AI recovery agent” wording alone will not differentiate BolKeResolve. | Outperform through a more rigorous, transparent case/rule engine and an evidence trail where every recommendation and factual statement can be audited. This is a hypothesis to test against a live RefundPe flow, not a claim that its product lacks those features. |
| **NPCI UPI HELP** ([circular](https://www.npci.org.in/uploads/UPI_OC_No_227_FY_2025_26_Introduction_of_UPI_HELP_Assistant_pilot_an_AI_powered_support_for_UPI_payments_cd501de8f3.pdf)) | Payment-related conversational help, eligible transaction-status checks, supported UPI complaint logging/tracking and UPI mandate management through participating channels. | A general claim that nobody offers AI payment support, UPI status help or complaint tracking. | Prepare a clear, portable case and guide users to the supported flow; explore participation with NPCI/member institutions instead of scraping/private API assumptions. |
| **NPCI complaint portal** ([portal](https://www.npci.org.in/register-a-complaint)) | Customer can lodge or track complaints for NPCI-operated systems through member institutions and reference data; it notes that fraudulent/unidentified/unauthorised transaction complaints should be raised with the user's bank. | Any suggestion that BolKeResolve is already filing with NPCI or has direct transaction records. | Explain when the NPCI/member route is relevant, gather the required facts, and provide a reviewed handoff pack. |
| **National Consumer Helpline** ([site](https://www.consumerhelpline.gov.in/), [convergence](https://www.consumerhelpline.gov.in/public/convergenceprogram)) | Official pre-litigation consumer grievance access through web, app, UMANG, phone and WhatsApp; 17 languages; docketing/document upload; a convergence model for company responses. | A generic “one place for consumer complaints” claim without explaining the extra value. | Help prepare a complete complaint, maintain a private evidence chronology, explain the handoff, and preserve context after the NCH docket is created. Explore a formal relationship only after confirming what integration is available. |
| **RBI CMS / RB-IOS 2026** ([FAQ](https://old.rbi.org.in/commonman/english/scripts/faqs.aspx?id=3407), [CMS](https://cms.rbi.org.in/)) | Formal complaint path and tracking for eligible matters against covered regulated entities; a centralised portal and defined admissibility checks. | A claim that every shop, marketplace or merchant refund dispute can go to RBI. | Check route fit and prerequisites, organise the first representation and evidence, calculate the applicable next step from the current Scheme, and prepare a handoff. |
| **e-Jagriti** ([NIC description](https://www.nic.gov.in/project/e-jagriti-a-unified-digital-platform-for-consumer-justice/), [portal](https://e-jagriti.gov.in/)) | Formal consumer-commission filing and case-management processes, document management, online status, hearing and case information. | “Replace courts” or “solve any complaint in chat.” | Help users assess whether a formal consumer case may be a later route, prepare a consistent chronology/documents, and export what they need. Complex eligibility/questions need human or qualified legal review. |
| **ConsumerComplaints.in** ([site](https://www.consumercomplaints.in/)) | Public complaint visibility, company responses, public user experience and company information. | A claim that there is no consumer complaint community or any way to publish a complaint. | Default to a private case file. Make public sharing an explicit, separately consented, later-stage choice—not the basic workflow. |
| **Bank/payment app support** | The bank or PSP is the party that can check relevant records, follow internal complaint processes and make appropriate decisions. | “BolKeResolve has verified your payment” or “we can release your refund.” | Make it easier to contact the right party with a clean, complete, corrected case record. |

**Market implication:** there are already real alternatives and strong public infrastructure. A compelling product cannot merely put all the logos on one page. It must remove the *cognitive and evidence overhead between destinations* and correctly distinguish which process applies.

### 3.2 One strong public outcome signal

The Department of Consumer Affairs reported that NCH facilitated **₹52 crore in refunds across 31 sectors and 79,521 refund-related grievances** from 25 April 2025 through 31 January 2026. That shows the official pre-litigation channel can be useful. It also tells BolKeResolve to integrate well with existing resolution routes instead of treating official systems as competition. This is a government-reported aggregate, not an independent causal evaluation and not a promise that a given complaint will resolve. ([PIB release, 17 February 2026](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2229099&lang=1&reg=3))

---

## 4. The highest-value differentiated product: an “Evidence-to-Resolution Engine”

The Resolution Passport already exists as a case export concept. Keep it, but make the engine underneath more useful than a static summary and draft.

### Pillar A — Case-type precision before route selection

The first step should not ask “Which regulator do you want?” It should work out what *actually happened*, through a few short discriminating questions. At minimum, distinguish:

1. **Failed UPI fund transfer:** the sender's account was debited but the beneficiary did not receive the funds.
2. **UPI merchant-payment failure/unknown status:** the payer was debited, but the merchant did not receive transaction confirmation.
3. **Merchant refund after cancellation/return:** the original payment may have succeeded and the merchant owes or has promised a separate refund. This is not the same as an auto-reversal for a failed payment.
4. **Unauthorised/fraudulent debit or suspected scam:** speed and incident reporting are more important than the normal complaint flow.
5. **Paid but goods/services not supplied, defective or not as described:** this may involve a merchant/service complaint or a supported payment dispute reason, not just a bank reversal.
6. **Other / facts unclear:** ask one clarifying question or direct to the appropriate human/official help rather than guessing.

The route engine must also consider: payment rail; who the counterparty is; displayed transaction status; whether debit occurred; transaction vs return/cancellation date; whether an official complaint already exists; who received that complaint; the response and timestamp; any relevant docket/reference; and whether the user suspects fraud.

**Why this is differentiated:** a generic AI can write a fluent letter for the wrong process. A deterministic decision tree with uncertainty handling can prevent a user from being told to wait for an auto-reversal when the real issue is a merchant refund, or to wait through normal intake when an alleged fraud needs immediate reporting.

### Pillar B — Versioned “rule + clock” engine

Every actionable recommendation should show:

- **Action:** what to do next, with one main button.
- **Why:** the facts that make this step relevant.
- **Rule/source:** official URL and the exact policy/circular/Scheme, plus checked-on/effective-from dates.
- **Conditions:** what must be true for the rule to apply.
- **Missing facts:** what is still unknown, and how the user can confirm it.
- **Deadline:** how the date was calculated, which event starts the clock and what could change it.
- **Fallback:** what to do if the facts do not match, a source is unavailable or the confidence is too low.

Use a versioned policy table, not only an LLM prompt. Each rule needs: `rule_id`, issue class, payment rail/entity scope, predicates, rule text, authoritative source URL, effective date, superseded date, source-checked date, action, deadline function, required evidence, exceptions, reviewer, and test cases. Store the version used on each case so a future rule update does not silently rewrite history.

#### Examples of why this matters

**RBI failed-transaction TAT (2019 circular, as accessed for this research):** the official table differentiates UPI fund transfer where the beneficiary is not credited (auto-reversal by the beneficiary bank latest by **T+1 day**, with ₹100/day compensation beyond T+1 under the prescribed conditions) from a merchant UPI payment where the payer is debited but merchant confirmation is not received (auto-reversal within **T+5 days**, with ₹100/day beyond T+5 under the prescribed conditions). These rules refer to defined failed-transaction scenarios, not every ordinary merchant refund or cancellation. The product must not calculate compensation eligibility without establishing the applicable scenario and current instructions. ([RBI notification and annex](https://m.rbi.org.in/commonman/English/Scripts/Notification.aspx?Id=3074); [PDF table](https://rbi.org.in/commonman/Upload/English/Notification/PDFs/CIRCULAR677EC931A7A65E4D99AA957D8E85BC0A2A.PDF))

**RBI–Integrated Ombudsman Scheme 2026:** the RBI's current FAQ says the customer must first approach the concerned covered Regulated Entity. If no reply is received within **30 days or the period specified by applicable RBI/NPCI/card-network guidelines, if any, whichever is higher**, or the customer is unsatisfied with the reply, the customer may approach the RBI Ombudsman; the Scheme FAQ then specifies a **90-day filing window** calculated from the expiry of the applicable waiting period or the last communication, whichever is later. The first representation must itself be within the relevant limitation period. The Scheme came into force on **1 July 2026**. This is materially different from relying on old generic summaries of the 2021 Scheme. Product logic must cite and follow the current Scheme and check all maintainability conditions. ([RBI RB-IOS 2026 FAQ](https://old.rbi.org.in/commonman/english/scripts/faqs.aspx?id=3407))

**E-commerce grievance handling:** the Department of Consumer Affairs' public summary of the Consumer Protection (E-Commerce) Rules states that e-commerce entities must display grievance-officer details, acknowledge complaints within 48 hours, and redress grievances within one month. That is a grievance-handling obligation in the applicable e-commerce context; it is not a universal guarantee that every refund must be paid within 48 hours or a month. Eligibility and the exact legal rule should be checked against the rules and subsequent amendments before applying it to a live case. ([Department of Consumer Affairs rules page](https://consumeraffairs.gov.in/pages/consumer-protection-acts); [department report summary](https://consumeraffairs.gov.in/public/upload/files/1617263115_AR2020-21_1733218509.pdf))

**Unauthorised digital-payment fraud:** the official National Cyber Crime Reporting Portal directs victims of cyber financial fraud to call **1930 immediately**; it is available 24/7. BolKeResolve should surface the emergency route before asking for nonessential case details, and it must not imply that reporting guarantees recovery. ([National Cyber Crime Reporting Portal FAQ](https://cybercrime.gov.in/Accept.aspx/Webform/images/Webform/Webform/Webform/Webform/Webform/FAQ.aspx))

These examples demonstrate why the differentiator should be *scenario-specific, versioned route logic*, not generic AI text. The rule engine needs qualified review and a regression corpus before being relied on for live user guidance.

### Pillar C — Evidence-to-claim graph (high-value feature)

Make every generated claim traceable to its origin. Example case facts:

- “₹2,000 was debited” — source: uploaded statement screenshot, user-confirmed; not a direct bank verification.
- “The app displays Failed” — source: UPI screenshot, extracted text, user-confirmed.
- “The merchant promised a refund on 18 October” — source: support email screenshot, user-confirmed; no inference about payment status.
- “Reference ID” — source: receipt/OCR, user-confirmed; mask part of it in general views.
- “The refund has not arrived” — current user report, not inferred from an incomplete document.

Every draft paragraph should be able to answer “where did this fact come from?” If evidence is missing, use a placeholder or ask the user—not hallucinate it. Display conflicting facts and ask the user to resolve them before finalising the letter.

#### Proposed upload flow

1. Upload screenshot, PDF, invoice, message export or email.
2. Scan the file type, enforce size limits, malware-scan server-side, and store outside public/static directories.
3. Extract likely dates, merchant, amount, status, transaction/order/reference number and promised date.
4. Show a side-by-side **original vs extracted** review. Ask the user to confirm high-impact details.
5. Offer redaction of Aadhaar numbers, full account/card numbers, addresses or unrelated transactions before sharing externally.
6. Link each confirmed fact to its source file and page/region (where technically available); store a file hash and upload timestamp for audit/consistency, not as proof that the document is authentic.
7. Build an evidence index, date-ordered chronology and recipient-specific attachment checklist.
8. Generate a **Complaint-ready Pack** (PDF/print view and downloaded attachments) that the user reviews and downloads or shares themselves.

Do not call a file “verified proof” just because OCR extracted text or its hash is stored. A file hash shows whether the stored bytes changed; it does not prove the original event was true or that the issuer created the file.

### Pillar D — Reply-aware case tracking, not just scheduled reminders

The system should model the *meaning* of each event:

- Complaint sent by user (user-reported or provider-confirmed, depending on connection)
- Acknowledgment received
- Reference/docket assigned
- More information requested
- Resolution promised for a specific date
- Complaint rejected/closed
- Partial resolution offered
- No response by the next expected event
- Refund credited (user-reported, document-supported, or externally verified—clearly distinguished)

After a reply arrives, the product should ask the user to forward/upload it or paste it in, extract the sender/date/reference/request/decision, and display a plain-language summary plus the exact source paragraph. The user confirms the classification. Then the state machine recalculates the next task and deadline. If the organisation asked for extra evidence, don't send the same old follow-up on schedule. If the user received a resolution, don't continue escalating automatically.

A low-permission starting point is **manual forwarding to a per-case secure address** or upload/paste. It avoids asking for broad Gmail/Outlook inbox scopes at the first step. A dedicated case inbox alias, signed routing token, safe attachment scanner, and visible consent step are needed if built. Never let any sender update a private case solely because it guessed a case ID.

### Pillar E — Cross-channel “handoff kit”

Do not scrape every portal or pretend there is one API for all institutions. Give the user a more coherent process:

- Open the official channel in a new tab.
- Provide a field-by-field copy/paste assistant with the relevant confirmed facts.
- Attach the correct evidence pack and show which documents are required/missing.
- Track the handoff only after the user says they completed it or an approved integration returns a receipt.
- Prompt for the reference/docket number and record it.
- For RBI or a consumer commission, run an eligibility/prerequisite check first and prominently show the official portal's source and deadline.
- After the user returns, ask “What happened?” with choices such as reference received, more information requested, rejected, unresolved, resolved.

It is acceptable for the first version to require a user click and manual confirmation. It is safer than unofficial web automation and more honest than pretending that a draft was submitted.

### Pillar F — Real outcome intelligence, privacy-first

Every resolved case can improve the guidance only if outcome labels are trustworthy. Offer an optional post-resolution question: “Did this action help?” with “money credited / partial refund / explanation only / still pending / stopped / other.” Ask if the user wants to share a minimal, anonymised outcome for improving future recommendations.

Separate four data quality levels:

- `user_reported` — user selected the outcome.
- `document_supported` — user supplied a receipt/statement that appears consistent with the report, but it is not independently verified.
- `integration_verified` — a specific approved integration confirmed the event.
- `unknown` — no outcome evidence.

Do not present a user-reported outcome as a verified recovery statistic. Do not create a public “worst companies” board from raw complaint volume. A crowd dataset can be biased by company size, selection effects, different case complexity and which users return to report. Minimum cohort sizes, disclosure, consent, retention controls and moderation are necessary.

**Potential long-term moat:** a reviewed mapping between incident patterns, required evidence, official process, event sequence and observed outcomes. That is much harder to create than an AI chat interface—but only valuable if the underlying labels and legal route are accurate.

---

## 5. Unique integrations: what is realistic, what requires permission, and what to postpone

### Build now / low to medium integration effort

| Integration | User value | Feasibility / guardrail | Priority |
|---|---|---|---|
| **Official-source rule registry** | Each recommendation carries a current source, applicability conditions, as-of date and next-step calculation. | Build in-house with version control, reviewer sign-off and scenario tests. This is rules/data engineering, not a regulatory API. | **P0** |
| **Evidence intake + OCR + redaction** | One upload produces a structured, confirmed timeline rather than another checklist the user must interpret. | Use document/image processing with strict file limits, private storage and source mapping. Have fallback manual entry when extraction confidence is low. | **P0** |
| **Complaint-ready evidence pack** | User can take one coherent file bundle to a bank, company, NCH, RBI or e-Jagriti instead of retelling the case. | Export must be user-reviewed and clearly labelled; do not claim submission. Protect shared/downloaded sensitive files. | **P0** |
| **Opt-in reminder engine** | A case can remind the user of a correctly calculated next date and explain why it matters. | Existing case date/notes are not a scheduler. Add a job queue or reliable reminder integration; consent, timezone, frequency limits, STOP/cancel, deletion and delivery status need testing. Do not blindly use “Day 4/Day 7” for every case. | **P0** |
| **Reply upload/forward and semantic update** | A real reply can change what the user needs to do next; case context is preserved. | Start with user-directed forwarding/upload and confirmation. Inbound mail requires secure aliasing, anti-spoof controls, attachment scanning and deletion rules. | **P1** |
| **Assisted official portal handoff** | Structured text and attachments are easy to transfer without repeatedly filling information from memory. | Link to official route, map supported form fields, copy-to-clipboard and track user confirmation. No bots, bypassing logins/CAPTCHAs, or automatic filing without an authorised API and explicit consent. | **P1** |
| **Local-language review of the final draft** | User explains the issue naturally but submits a clear formal message; can show original-language summary plus English/Hindi output as appropriate. | Native/qualified reviewer evaluations for each language and code-mix. Preserve user meaning; never silently translate a critical amount, date, negation or transaction status. | **P1** |

### Explore only after access/partner approval

| Integration opportunity | Why it could materially increase value | Reality check / dependency |
|---|---|---|
| **Merchant “Resolution Bridge” API** | The case pack enters a participating merchant's support queue as a structured case; merchant returns acknowledgement/reference/status through an authenticated webhook; the customer sees the status in their private case. This is the clearest path to an actual two-way resolution loop. | Requires willing merchant/CRM partners, data-sharing terms, technical agreements, support SLAs, privacy/security review and a transparent conflict-of-interest policy. Start with a small willing D2C merchant or service provider, not every major platform. |
| **NCH / consumer-organisation partnership** | Validate the pack format and handoff with people who handle real consumer grievances; potentially improve handoff if the programme offers an approved mechanism. | NCH's public convergence programme is described as a scheme for companies to receive and resolve consumer grievances. Public material does **not** establish a general third-party consumer-app submission API. Contact the Department/partner team; until approved, use the official user-facing channels and record the user-entered docket number. |
| **NPCI UPI HELP / bank / PSP integration** | Potentially query supported transaction status, deep-link the right bank/app flow or track a complaint through authorised systems. | NPCI's circular describes access through participating members and API integration for participating members. It is not an open API promise. Seek a formal member/partner path; do not scrape private endpoints or claim live transaction verification without it. |
| **Regulated financial-data access (Account Aggregator)** | With appropriate user consent, financial data could help reconcile debits/credits and detect whether a reported refund appears in a supplied period. | Under India's AA framework, AAs operate under RBI directions; a Financial Information User must be enrolled/eligible under the regulated framework. A normal app cannot assume it may access arbitrary bank data. Explore only with legal/compliance advice and an authorised partner; this is not an MVP shortcut. ([DFS framework](https://www.financialservices.gov.in/account-aggregator-framework), [RBI master direction](https://systemhealth.rbi.org.in/Scripts/BS_ViewMasDirections.aspx_id%3D10598%281%29.html)) |
| **Email provider APIs** | A case could track sent/delivered email status and retrieve case-specific replies with less user effort. | Start with manual forwarding. Later use narrow scopes, separate consent per mailbox/action, easy revoke, minimal storage, explicit recipient review and strong account isolation. SMTP acceptance is not proof that the recipient read the email. |
| **Human review network** | Ambiguous or high-value cases can be reviewed by trained consumer advocates or qualified legal professionals. | Separate general information from legal advice; define escalation, fees, supervision, disclaimers and professional requirements with counsel. Do not represent unqualified staff as lawyers. |

### What not to build yet

- A new social network/WhatsApp clone: it does not improve routing or case follow-through and creates a large network-effects/moderation burden.
- Bank-account scraping or screen-scraping of private apps: fragile, risky, and misleading if the user assumes real authorisation.
- Full Gmail inbox access as the default: high privacy cost when user-directed forwarding may solve the first use case.
- Automated form submission to RBI/NCH/e-Jagriti without documented permission/API and user approval.
- A “guaranteed refund”, “AI gets your money back”, or “official/government-backed” claim without actual authorised basis. A case tool cannot decide a refund, reverse funds, or promise an official result.
- A public case wall by default; evidence often contains sensitive account, order, address, phone or other personal details.
- Features in ten issue categories before the most important two or three routes are accurate and complete.

---

## 6. The most differentiated near-term feature bundle

Name it internally: **Resolution Passport 2.0 — Evidence, Rules and Follow-through**.

### User experience

**Step 1 — Tell the story.** Voice or text. Ask no more than a few high-value questions first. Fraud/suspicious debit gets an immediate safety route.

**Step 2 — Confirm the facts.** Show a short editable fact card: amount/date, counterparty, payment type, status, what was already tried. Each fact says whether it came from the user or a supplied file. Ask the user to correct uncertainties.

**Step 3 — Understand the path.** One recommended next action, one primary button and a concise explanation. Expandable “Why this step?”, “What to prepare?” and “Official rule/source” sections. Always display the effective date/source, not just an AI confidence badge.

**Step 4 — Prepare once.** Upload or paste a receipt/reply. The system proposes extracted facts with review. Build a chronology, evidence checklist, recipient-specific draft and redacted attachment pack.

**Step 5 — Handoff.** Open the official channel or user-reviewed email/WhatsApp draft. Tell the user what the app did and did not do. The user completes the submission and records the reference.

**Step 6 — Follow through.** A correct, opt-in reminder triggers on the appropriate date. If a reply arrives, upload/forward it, confirm its meaning and update the action plan. Do not auto-send a threatening/escalation letter just because a timer fired.

**Step 7 — Close the loop.** The user can record resolution, partial resolution, information-only response, no response or stopped. If they voluntarily provide a redacted supporting document, label it document-supported rather than bank-verified. Ask permission before using a minimally sufficient anonymised outcome for learning.

### Why someone would use BolKeResolve instead of going directly to the official site

Because it handles the *work around the official site*:

- explains which official destination fits this case;
- avoids forgetting the facts and references between destinations;
- catches missing documents before a submission;
- turns a vague story into a concise, recipient-specific request;
- keeps the reply and next step attached to the case;
- reminds the user without falsely claiming the institution is being monitored;
- provides an exportable case file if they stop using BolKeResolve.

It should not create friction or hide official routes behind sign-up. Let people try a sample case, see the next-step logic and export a basic pack before requiring an account, where practical.

---

## 7. Website positioning: demonstrate the value, don't sell a chatbot

### Suggested hero copy

**Your payment or refund is stuck. Know exactly what to do next.**

“Tell us what happened in your own words. BolKeResolve helps organise the facts, find the relevant official route, prepare a message you can review, and keep track of what happens next.”

Primary CTA: **Build my resolution plan**  
Secondary CTA: **Try a sample case**

Trust line: **Independent guidance. You control what is shared. We do not verify bank transactions or guarantee refunds.**

### Homepage hierarchy

1. **Hero with an actual product interface**, not three interchangeable stock-photo cards. Show the sample case fact card and the one recommended action.
2. **A real interactive demo** with fictional, visibly labelled data.
3. **“Why this recommendation?”** as a clickable source/rule explanation.
4. **“Your evidence, organised”** with a before/after chronology and redaction preview.
5. **“Take it to the official channel”** showing a user-controlled handoff—not a fictitious integration.
6. **“Keep your place”** showing response tracking and a due-date reminder that updates after a response.
7. **Limits and privacy in plain language**: not a bank/regulator/law firm, no direct account access, no guaranteed refund, never enter OTP/UPI PIN/password.
8. **Verified outcomes, only when real.** If no user-reviewed case outcomes exist yet, don't invent statistics, testimonials, logos or “₹ recovered” counters. Say the product is in a pilot and recruit pilot users transparently.

### A 90-second demo script

Use fictional data such as “₹2,000 paid; the payment app shows failed; debit appears in a redacted sample screenshot.” Label it **Sample case — fictional data** on every frame.

1. User says in Hinglish: “₹2,000 kat gaye, app says failed.”
2. BolKeResolve asks one critical clarifier: transfer to a person, or merchant payment? Show why the answer changes the route.
3. The app reads sample evidence, proposes extracted facts, and asks the user to confirm the status/date/amount.
4. It shows one next action, the official source, the facts that make the rule applicable, what is still missing, and how the deadline is calculated.
5. It prepares a message tied to the confirmed facts and displays any uncertain/missing facts as explicit prompts.
6. The user reviews the final draft and opens the official support route. **Do not simulate a successful submission or verified refund.**
7. The user records a fictional reference number, later imports a sample reply, confirms its meaning and sees a recalculated next step.
8. End with a portable pack: chronology, evidence list, user-approved draft, official-source links, handoff history and clear user-reported/externally verified labels.

This demo proves the actual differentiated workflow: not “AI can write,” but “the process remains correct and coherent from first story to next action.”

### Website trust details that matter

- Make official source links visible before account creation and show the date checked.
- Distinguish official/independent clearly; do not use government/NPCI/RBI marks in a way that implies endorsement.
- Keep sensitive case content private by default. Sharing/export is a user action with a preview.
- Show the recipient, message contents, attachments and action before anything is sent.
- State if a reminder is only an in-app date, browser notification, calendar item, or verified scheduled message.
- Make correction, export, deletion and account closure easy.

---

## 8. Rules, regulations and safeguards to bake into product design

### 8.1 RBI–Integrated Ombudsman Scheme 2026

The new Scheme took effect on 1 July 2026. Current RBI FAQ describes the initial representation to the covered Regulated Entity, the no-reply threshold of 30 days **or a longer applicable RBI/NPCI/card-network guideline period, whichever is higher**, the unsatisfactory-reply branch, the subsequent 90-day filing window, maintainability requirements and tracking through CMS. It is not a general route for every retailer/merchant dispute. Check the current Scheme and legal counsel before turning the FAQ into production code. Do not carry over older RB-IOS 2021 timelines without confirming whether they still apply to the case. ([RBI 2026 FAQ](https://old.rbi.org.in/commonman/english/scripts/faqs.aspx?id=3407), [CMS](https://cms.rbi.org.in/))

### 8.2 RBI failed-transaction deadlines are not ordinary refund deadlines

The RBI 2019 TAT circular specifies separate timelines for defined failed payment scenarios and related compensation beyond the relevant time. E.g., UPI sender debited/beneficiary not credited vs payer debited/merchant confirmation not received are separate entries. The circular says the framework applies to domestic transactions and defines failure as not fully completed for reasons not attributable to the customer. Do not use a “T+5” rule for all post-cancellation merchant refunds. ([RBI notification](https://m.rbi.org.in/commonman/English/Scripts/Notification.aspx?Id=3074))

### 8.3 E-commerce grievance handling

The Consumer Protection (E-Commerce) Rules are linked from the Department of Consumer Affairs. The Department's own report summary states an e-commerce entity must display grievance-officer information, acknowledge a grievance within 48 hours, and redress it within one month. Applicability depends on the relevant entity and facts. Those timelines should not be presented as a universal promise to refund within that period. Check the actual rule text, amendments and relevant commercial terms for each flow. ([rules page](https://consumeraffairs.gov.in/pages/consumer-protection-acts))

### 8.4 National Consumer Helpline and e-Jagriti are different stages

NCH is a pre-litigation grievance mechanism and offers a variety of channels. e-Jagriti is the formal consumer-commission platform. A product flow should not jump every user straight to a formal case nor imply NCH is a court. Provide stage-appropriate routes. ([NCH](https://www.consumerhelpline.gov.in/public/convergenceprogram), [e-Jagriti](https://www.nic.gov.in/project/e-jagriti-a-unified-digital-platform-for-consumer-justice/))

### 8.5 Unauthorised digital-payment fraud

The product needs a separate urgent path with a persistent warning, immediate official cybercrime reporting direction at 1930 and direction to contact the bank/payment issuer through official channels. Do not force a fraud victim to finish routine intake first. Do not guarantee funds will be recovered. Avoid asking for OTPs, UPI PINs, passwords, full card numbers or unrelated identity information. ([National Cyber Crime Reporting Portal FAQ](https://cybercrime.gov.in/Accept.aspx/Webform/images/Webform/Webform/Webform/Webform/Webform/FAQ.aspx))

### 8.6 DPDP Act and Rules 2025: build for the requirements now

MeitY notified the Digital Personal Data Protection Rules, 2025 and described a phased implementation timeline, including an 18-month transition for important core obligations. As of this report date, do not assume every operational provision is already commenced; confirm the commencement schedule in the Gazette for each obligation as of deployment. But design from the start for clear purpose-specific notices, data minimisation, consent and withdrawal, security, retention/deletion, rights handling and breach response. Do not advertise “DPDP compliant” solely because a privacy page exists. ([PIB notification summary](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2190014&lang=1&reg=3), [MeitY explanatory note](https://www.meity.gov.in/writereaddata/files/Explanatory-Note-DPDP-Rules-2025.pdf))

### 8.7 Account Aggregator access is not a simple bank-login integration

The Government's Account Aggregator framework page states that financial information moves only with explicit customer consent and explains that an FIU is an entity enrolled and regulated by a financial-sector regulator. BolKeResolve should not promise automatic bank-statement import through AA until eligible structure, provider terms and purpose are cleared. Do not ask users to provide internet-banking credentials or use unofficial screen scraping. ([DFS Account Aggregator framework](https://www.financialservices.gov.in/account-aggregator-framework))

### 8.8 Safe product language

Prefer:
- “We help you identify and prepare the next step.”
- “Based on the facts you confirmed and the source shown…”
- “Open the official complaint channel.”
- “You marked this as sent.” / “Email provider accepted the message” (only if technically true).
- “You reported the refund as received.” / “Document-supported” where appropriate.

Avoid unless supported by a genuine authorised integration and evidence:
- “We checked your bank transaction.”
- “We filed the complaint.”
- “Your case is approved.”
- “Your refund is guaranteed.”
- “The bank must return the money” without checking the specific rule conditions.
- “Government-approved/official” without documented authorisation.

Legal disclaimers help but do not replace correct design, source review, privacy/security controls or counsel.

---

## 9. How BolKeResolve can actually improve refund outcomes

No software outside the authorised institution's workflow can force the refund to be paid. The controllable levers are reducing the user's errors, shortening time to the correct channel, making a request actionable, preserving the record and ensuring the user does not miss a valid next step.

### The practical path to actual value

**A. Correct first destination.** Prevent a user from bouncing among app, bank, merchant and regulator by identifying the actual transaction state and responsible party.

**B. Complete evidence before contact.** A concise first complaint that has dates, amount, reference, requested remedy, prior attempt and attachments can reduce avoidable follow-up for missing information.

**C. Make next actions specific.** “Contact support” is weak. “Open this official route; have this transaction reference ready; attach these two files; ask this specific status question; record the docket number” is actionable.

**D. Preserve the counterparty's response.** A reply can change what should happen next. The system should read/summarise it only when the user provides it or a permitted integration retrieves it, show the source and ask the user to confirm the interpretation.

**E. Follow up by the right clock.** Do not use a universal timer. Tie every reminder to an applicable rule or a user-selected expected response date, and explain the reason.

**F. Enable real two-way partner integrations eventually.** The most direct path to materially reducing elapsed time is to have willing merchants/financial institutions accept a structured case and return an authenticated acknowledgement/status into the user's case. A human-approved merchant/CRM pilot is more credible than a fake claim of API access to banks.

### What to measure

- Time from case creation to first correct action.
- Proportion of cases with a high-confidence, human-reviewed route recommendation.
- Percentage of users who can explain why the next step is appropriate.
- Evidence completeness before first contact.
- Percentage of handoffs where a docket/reference is recorded.
- Number of repeat explanations / duplicate submissions reported by users.
- Response classification accuracy on a review set.
- Reminder accuracy: timely, justified and stopped when the case changes or closes.
- User-reported resolution/partial resolution/no response, with evidence-quality label.
- Time to reported resolution among comparable case categories, with cohort size and methodology disclosed.
- **Safety measure:** critical misroutes, false claims of verification/submission and privacy incidents. The target for those is zero.

Do not market a refund recovery rate until enough cases are complete, outcomes are honestly labelled, and the denominator, time window, category mix, exclusions and evidence standard are published.

---

## 10. A focused 30/60/90-day plan

### Days 0–30 — prove the smallest differentiated workflow

1. Pick two launch workflows: (a) failed/pending UPI with debit, clearly split into transfer vs merchant-payment scenarios; (b) delayed refund after a merchant order cancellation/return. Keep unauthorised/fraud as a high-visibility safety path, not a normal wizard.
2. Create a legally reviewed, machine-readable rules pack with a source registry and version history. Do not attempt every sector yet.
3. Ship evidence extraction preview, user confirmation, redaction, and an evidence-index export.
4. Add route-specific due-date logic. The visible due date must say which user event starts it and why it is relevant. Add opt-in reminders only after a real scheduler and cancel behaviour work.
5. Build the public sample case with only fictional data, source citations and an honest “not externally submitted” state.
6. Run 15–20 usability tests; include people who recently had a stuck UPI payment or delayed refund and ask them to use the real flow, not rate a Figma mockup.

### Days 31–60 — close the loop

1. Add user-directed reply upload/forward, sender/date/reference extraction, response classification and user confirmation.
2. Add “I sent it” and reference-number events; explicitly differentiate user-reported from provider-confirmed delivery.
3. Add field-by-field assisted handoff for NCH and the relevant official route; record the docket number after user confirmation.
4. Create a reviewed test suite of at least 100 scenarios across the two workflows plus urgent fraud, including missing, contradictory and adversarial facts.
5. Have a qualified reviewer examine generated messages and routes for the scenario set. Do not launch a category just because one happy-path test passes.

### Days 61–90 — validate distribution and one real integration

1. Recruit 3–5 potential pilot partners among smaller D2C merchants/service providers or a consumer-support organisation. The pitch is: structured complaints, fewer missing details, more visible consumer updates—not preferential treatment in exchange for payment.
2. Explore, but do not promise, an approved NCH/programme, NPCI/member or regulated-entity integration.
3. If a merchant partner commits, build one authenticated ticket/acknowledgement integration with a disclosed data-sharing agreement and explicit customer approval.
4. Test an opt-in anonymous outcome loop and publish only sufficiently large, accurately labelled aggregates.
5. Decide whether to expand categories based on first-action accuracy, completion and outcome evidence—not traffic or number of features.

### Proposed pilot gates (targets, not current results)

- At least 90% correct route selection on a reviewed test set for the supported scenarios, with separate measurement for each scenario.
- 100% of critical fraud scenarios surface immediate official safety guidance.
- At least 80% of participants can explain their next step after seeing the recommendation, unaided.
- At least 75% of pilot cases leave with a user-approved, complete first-contact pack.
- Zero instances of fabricated transaction verification, fabricated filing confirmation, or a false guaranteed-refund promise.

A reviewer should stop expansion if a critical route or safety miss remains unresolved.

---

## 11. User and expert research plan

### Interview 12–15 people with a recent real case

Aim for a mix of:
- failed/pending UPI with debit;
- marketplace refund after cancellation/return;
- payment made but merchant claims not received;
- people who already contacted one or more support channels;
- people who are comfortable with English and people who prefer Hindi/Hinglish or another supported language.

Ask them to reconstruct the last incident from memory and available records:
1. What happened first?
2. What did the app/bank/merchant show?
3. What was the first thing they tried?
4. What did support ask them for?
5. What information or receipt was hard to find?
6. Did anyone give a deadline or reference number? What did they do with it?
7. Did they receive a reply that was difficult to understand?
8. What did they do next, and what caused delays?
9. What would they trust a tool like BolKeResolve to do, and what would they refuse to share?
10. What would make them stop using it?

Avoid asking “Would you use our app?” as the main validation; stated intention is weak. Ask participants to perform the task with the prototype or real MVP.

### Interview 4–6 domain experts

A mix of bank/payment grievance operations, consumer helpdesk/consumer advocate, D2C merchant support, and a qualified lawyer familiar with the relevant consumer/payment process. Ask where tickets are commonly incomplete, what routes are often confused, what a good first representation needs, and what integrations they would legally/operationally permit.

### Competitor test

Run the same fully fictional set of scenarios on BolKeResolve, RefundPe, the relevant official support path and NCH. Compare:
- classification of the incident;
- correctness and freshness of the cited rule;
- appropriateness of first destination;
- completeness of evidence request;
- whether timing logic adapts to the case;
- ability to preserve external references and incoming replies;
- privacy and sharing controls;
- whether the interface represents submission/reply/transaction status honestly.

Have the output reviewed by a domain expert. Do not conclude a competitor is inaccurate or inferior from marketing copy alone. Public evidence currently shows RefundPe advertises many features that overlap; practical benchmark testing is required to find where BolKeResolve can meaningfully outperform it.

---

## 12. Main risks and mitigation

| Risk | Mitigation |
|---|---|
| Wrong rule, stale deadline or incorrect forum | Versioned source registry; legal/domain review; regression tests; no confident recommendation when conditions are missing; clearly date rules and display sources. |
| User believes AI verified transaction or filed complaint | Provenance labels everywhere; separate UI states for drafted/opened/user-reported/provider-confirmed; no fake success animation. |
| Sensitive evidence leaks | Data minimisation, private storage, least privilege, deletion/retention policy, redaction preview, attachment scanning, access isolation, encryption and breach plan. |
| Fraud victim loses time in routine intake | Persistent emergency path; immediate 1930/official bank route; avoid asking nonessential questions first. |
| Automation sends unsuitable or repeated messages | User approval for every consequential outgoing message; event-based stop conditions; no auto-escalation on timer alone. |
| Monetisation damages trust | Do not take a share of the refund. If merchant/B2B monetisation is introduced, disclose it; prohibit paid placement in routing; preserve consumer independence and make partner relationships obvious. |
| Competitor copies surface features | Invest in rule quality, evidence linkage, correct deadline transitions, partner workflow and outcome measurement. These are deeper than CSS or one prompt, although not impossible to copy. |
| Regulatory/data change | Scheduled official source checks; effective-date history; change-review and rollback; deployment gate for materially changed rules. |
| Unfair public claims or “recovery rate” marketing | Publish only real, well-defined, representative-enough outcome metrics; never treat user-reported data as independently verified. |

---

## 13. Strategic choices: what I would do and what I would not

### Do

- Position as an **evidence-to-resolution workspace** with a source-backed rules engine.
- Launch with two robust workflows and one emergency fraud route.
- Use a “Why this step?” explanation and effective-dated sources.
- Make every fact in an outgoing draft traceable to user input or a specific document.
- Automate reminders and reply-aware transitions, but make sending/filing a deliberate user action until an approved integration exists.
- Use a complaint-ready pack to reduce repeated explanation across channels.
- Pursue one real partner integration only after the end-to-end manual workflow is useful and safe.
- Measure correct actions and user-reported resolution, not chat volume.

### Do not

- Claim “no other platform offers this” without complete competitive validation—RefundPe is already a close public competitor.
- Treat all refund problems as the same legal/payment scenario.
- Use generic 30-day / Day 4 / Day 7 reminders for every route; current RBI Scheme rules are more conditional, and different rails have separate TATs.
- Promise that a complaint pack will force a refund or that a refund will happen by a specific date.
- Claim direct access to payment records or official portals without permission and real technical evidence.
- Build a social feed, public complaint database, broad mailbox integration or 10-category issue catalogue before the core cases work.
- Present the app as a lawyer, regulator, bank, official portal or government-backed service without a true basis.

## Final recommendation

**The next meaningful build should be a route-and-evidence engine that can show its work.** Make two common cases genuinely complete from the user's first words to a reviewed official-channel handoff, a correct rule-specific clock, a case pack and a reply-aware next step. Add one partner integration only when there is a real institution/merchant willing to support it.

The key proposition is: **“You don't have to understand the entire complaint system. BolKeResolve explains the next valid step, shows why, organises the proof, and remembers the case with you.”**

The product cannot itself make a bank or merchant issue a refund. It can make the user's process more correct, complete and persistent—and partner integrations may eventually shorten the route from a complete complaint to an actual decision.

---

## Sources reviewed

### Official systems and regulations

1. NPCI, *Introduction of UPI HELP pilot*, 8 Oct 2025 — https://www.npci.org.in/uploads/UPI_OC_No_227_FY_2025_26_Introduction_of_UPI_HELP_Assistant_pilot_an_AI_powered_support_for_UPI_payments_cd501de8f3.pdf
2. NPCI, *Register a Complaint* — https://www.npci.org.in/register-a-complaint
3. RBI, *Harmonisation of Turn Around Time (TAT) and customer compensation for failed transactions*, 20 Sep 2019 — https://m.rbi.org.in/commonman/English/Scripts/Notification.aspx?Id=3074
4. RBI, *RB-IOS 2026 FAQ*, updated 1 Jul 2026 — https://old.rbi.org.in/commonman/english/scripts/faqs.aspx?id=3407
5. RBI Complaint Management System — https://cms.rbi.org.in/
6. National Consumer Helpline, Convergence Programme — https://www.consumerhelpline.gov.in/public/convergenceprogram
7. PIB / Department of Consumer Affairs, NCH facilitated ₹52 crore in refunds across 31 sectors, 17 Feb 2026 — https://www.pib.gov.in/PressReleasePage.aspx?PRID=2229099&lang=1&reg=3
8. Department of Consumer Affairs, Consumer Protection Acts and rules — https://consumeraffairs.gov.in/pages/consumer-protection-acts
9. National Informatics Centre, e-Jagriti description — https://www.nic.gov.in/project/e-jagriti-a-unified-digital-platform-for-consumer-justice/
10. e-Jagriti official portal — https://e-jagriti.gov.in/
11. National Cyber Crime Reporting Portal FAQ — https://cybercrime.gov.in/Accept.aspx/Webform/images/Webform/Webform/Webform/Webform/Webform/FAQ.aspx
12. PIB / MeitY, DPDP Rules notification summary, 14 Nov 2025 — https://www.pib.gov.in/PressReleasePage.aspx?PRID=2190014&lang=1&reg=3
13. MeitY, explanatory note on DPDP Rules 2025 — https://www.meity.gov.in/writereaddata/files/Explanatory-Note-DPDP-Rules-2025.pdf
14. Department of Financial Services, Account Aggregator framework — https://www.financialservices.gov.in/account-aggregator-framework
15. RBI, Account Aggregator Master Directions — https://systemhealth.rbi.org.in/Scripts/BS_ViewMasDirections.aspx_id%3D10598%281%29.html
16. Central Consumer Protection Authority — https://ccpa.doca.gov.in/

### Direct/adjacent competitor sources

17. RefundPe homepage — https://refundpe.com/
18. RefundPe terms — https://refundpe.com/terms
19. RefundPe privacy policy — https://refundpe.com/privacy
20. RefundPe grievance-contact directory — https://refundpe.com/emails
21. ConsumerComplaints.in — https://www.consumercomplaints.in/
22. ConsumerComplaints.in, About — https://www.consumercomplaints.in/about-us.html

### Project sources reviewed

- `IMPLEMENTATION_STATUS.md`
- `docs/RESOLUTION_PASSPORT_AND_NO_API_HANDOFF.md`
- `docs/ACTION_PACK_AND_FOLLOWUP.md`
- `docs/PRODUCT_STRATEGY_RESET_AND_COMPETITIVE_RESEARCH_2026-10-21.md`
- `docs/WHATSAPP_LAUNCH_PLAYBOOK.md`
- `docs/WHATSAPP_INTEGRATION_GUIDE_2026-10-21.md`
- `docs/DEEP_RESEARCH_AND_PRODUCT_BLUEPRINT.md`
