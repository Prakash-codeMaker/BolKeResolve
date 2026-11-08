# BolKeResolve — Deep Product Research, Differentiation & Challenge Upgrade

**Updated:** 22 October 2026  
**Purpose:** Upgrade the product, prioritise the next builds, and prepare a credible demonstration for the Great Indian AI Internship Challenge by Gnani AI.  
**Research method:** Desk research across official contest/API documentation, Indian payment and grievance systems, competing help journeys, accessibility standards, human–AI interaction guidance, security references and Indic-language speech resources. A 180+ item reference library is included below. It is a curated starting corpus, not a systematic academic review; authority and freshness vary by source type.

## Executive recommendation

BolKeResolve should not compete on “AI writes a complaint.” That is easy to copy and a close competitor, RefundPe, already publicly advertises complaint drafting, approved sending, follow-up and escalation-pack features. Nor should it claim to replace NPCI, banks, merchants, the National Consumer Helpline (NCH), RBI CMS or e-Jagriti.

**The product thesis:** BolKeResolve is an evidence-to-resolution companion for people who cannot tell which payment/refund process applies or who lose continuity while moving between support channels.

The defensible direction is a connected workflow:

1. Understand the user’s story in their natural language, including code-mixed speech.
2. Classify the situation with an explainable, testable playbook; ask a clarifying question where the path may change.
3. Preserve a user-confirmed fact ledger and show provenance (user-reported, extracted from document, user-confirmed, or verified through an authorised integration).
4. Explain one next action, why it applies, the official source and what facts remain missing.
5. Produce a portable evidence index and editable support message.
6. Read replies, update the timeline and only then recalculate the next action.
7. Integrate directly with a merchant or provider only when a real partner approves the integration and the user consents.

This is a stronger product than a chat window because it makes follow-through and factual traceability the centre of the experience.

## What changed in this build

### New interactive, read-only “Try a fictional case” demo

Added a public homepage module with two selectable scenarios:

- **UPI payment failed:** fictional Hinglish story; amount ₹1,200.
- **Merchant refund delayed:** fictional Hinglish story; amount ₹850.

On click, the frontend calls the same deterministic `/api/resolution/preview` endpoint used for a first-pass intake. It displays the recommended first action, a short next step, what additional information may matter, and official-source links with review dates. The user can inspect the result without signing in or providing personal details.

The UI deliberately says that the story is fictional; no payment is checked; no case is saved; no complaint is submitted. It also labels the likely classification and confidence, explains why the next step was selected, and offers a collapsed rationale so visitors can inspect the rule logic. The sample is a view into the product’s decision path, not a success animation or a fake bank integration. This makes a judge-facing demonstration safer, faster and easier to understand.

### Regression protection

- Added static frontend checks for the sample-demo controls, live result region, disclaimers and responsive styles.
- Added API tests for both scenarios and verifies that previewing them does not increase persisted case count.
- Bumped the public-shell service-worker cache version to `bolkeresolve-shell-v8`. `/api/` remains deliberately network-only so user/case data is not cached offline.
- Refreshed the rules-source review date in `backend/resolution.py` to 22 October 2026. A review date means a human review timestamp, not proof of a legal opinion or future freshness; source monitoring still needs to be implemented.

### Verification performed

The full test suite passes **140 tests and 58 subtests**. The live Gnani API has not been independently called with the owner’s key during this build. That must be checked before describing a public voice demo as a verified live Gnani run.

## 1. What existing systems already do

The competitive picture has to be stated honestly. BolKeResolve’s gap is not the absence of official help; it is the fragmented hand-off and limited continuity across channels.

| Existing system | Already useful for | Gap BolKeResolve should target |
|---|---|---|
| UPI app/bank help | Transaction history, selected status/complaint flows and the provider’s own support | Users may need to work out which entity or path fits the actual situation; BolKeResolve should not pretend to see bank state. |
| NPCI complaint facility | Certain supported payment-system member complaints and status checks | Help the user assemble the correct facts; keep the reference number and later replies together. NPCI itself notes that unauthorised/fraudulent transactions should be raised with the respective bank. |
| National Consumer Helpline | Pre-litigation consumer grievance access via portal, phone, WhatsApp and other channels; convergence organisations | Help the consumer decide whether this is the right route, prepare clean evidence, and carry a record of what was submitted. NCH is itself a real route and must be linked, not imitated. |
| RBI Complaint Management / Ombudsman | Eligible grievances against covered regulated entities subject to current scheme rules | Correctly determine eligibility and sequence; explain the rule and show the missing prerequisite. Never use a generic delay period for every refund. |
| e-Jagriti | Consumer-commission filing and case lifecycle workflows | Organise evidence and the chronology before the user leaves the assistant; do not represent this as a substitute court portal. |
| Merchant/platform support | Platform-specific order, transaction, refund and complaint routes | Make the handoff prepared, traceable and updateable instead of creating another generic FAQ. |
| RefundPe | Publicly advertises AI-assisted grievance, approved sending, reminders and escalation packs | Do not claim message drafting or reminders alone are unique. Differentiate through verified rule provenance, document-to-fact traceability, reply-aware routing and partner-authorised two-way status integrations. |

Sources to verify before release: Gnani contest rules, NPCI UPI FAQ/complaint page and UPI HELP pilot circular, RBI Integrated Ombudsman Scheme 2026 FAQ, RBI failed transaction framework, NCH official page and convergence programme, e-Jagriti, consumer-protection rules, and competitors’ live product claims. The 130+ link appendix identifies these references.

## 2. The five best differentiation opportunities

### A. Explainable resolution routing engine — build now

Build versioned decision playbooks for at least:

1. UPI transfer failed / beneficiary not credited.
2. Merchant-side UPI payment debit with no confirmation.
3. Merchant order cancellation / delayed refund.
4. Wrong amount or duplicate charge.
5. Unrecognised/unauthorised payment (urgent safety route).
6. Order paid but not received.

These are not interchangeable categories. Each playbook should define: required clarifying facts; why a source applies; applicable entity; user action; expected proof; possible next route; date/effective period; review owner; and tests. Put rules in structured code/data, not only an LLM prompt. If important facts are missing, the product should ask one question or state uncertainty.

**Important:** RBI’s failed-transaction framework distinguishes (a) UPI transfer where the account is debited but the beneficiary is not credited, and (b) a merchant-side payment where confirmation is not received. The specified TATs differ (commonly T+1 and T+5 respectively under that framework). These timelines do not automatically apply to a separate merchant order refund. Do not publish a universal refund timer. Ask the question that identifies the transaction type first and show the exact source next to the applicable rule.

### B. Provenance ledger — build alongside routing

Every important fact should carry a provenance label:

- **You told us:** captured from speech/text; not independently checked.
- **Found in your document:** OCR/extraction candidate; not yet accepted as fact.
- **You confirmed:** the user reviewed and accepted it.
- **Verified through authorised connection:** available only after a real partner API response, with timestamp and provider identifier.

The consumer can tap a fact and see its origin. Corrections propagate to the draft and Resolution Passport. The final export includes a source index, event chronology, missing-evidence checklist and uncertainty notes. Do not add bank account access just to call facts “verified.”

### C. Reply-aware case state — phase 2

Provide an email-forward or document-upload entry point for a support reply. Start with a transparent assistive classifier that produces a suggestion: acknowledgement, request for documents, promised refund, rejected request, closed case, or ambiguous. Always show a quoted excerpt and ask the user to confirm before it changes the case status. Then recalculate the playbook using confirmed information.

This is different from a static reminder because a new reply changes the next action. Keep initial ingestion manual and user-controlled; full email connectors need granular scopes, token security, deletion behaviour and clear consent.

### D. Partner Resolution Bridge — phase 3, only with a real partner

A genuine integration could send a user-approved structured complaint to a willing merchant’s ticketing system and receive an authenticated acknowledgement/status. The case should then display ticket ID, partner, event time and origin. Start with a small online merchant or a consumer-support organisation willing to pilot a documented API. Do not imply NPCI, a bank, NCH or a merchant has partnered without a written agreement and deployed connection.

### E. Learn from outcomes without inventing “success rates” — phase 3

Offer a clear, optional close-out: resolved, partly resolved, still pending, withdrawn or unable to proceed. Separate self-reported outcome from document-backed and integration-verified outcome. Over time, a carefully labelled dataset may improve the playbooks. Avoid publishing recovery rates until cohort definition, denominator, follow-up window, duplicate handling, missing outcomes and verification standards are well-defined and independently reviewable.

## 3. Better integration strategy — feasible vs conditional

| Integration / connection | MVP route | Prerequisites for deeper connection |
|---|---|---|
| NPCI / UPI | Official guidance link, transaction facts checklist, user-entered complaint/reference number | Participating provider or NPCI-approved interface, formal permissions, user consent, security review and documented response semantics. Public complaint web page does not mean open API access. |
| NCH | Link to official portal/1915/WhatsApp routes; create an editable, reviewable case summary | Officially supported submission method or agreement. Do not automate CAPTCHA or scrape login-protected flows. |
| RBI CMS | Eligibility checklist and a prepared document pack linking to the official CMS | Any direct submission/status integration must be expressly authorised and technically supported. Scheme eligibility must remain rule-versioned. |
| e-Jagriti | Chronology, evidence index, exportable pack and official link | Formal supported handoff/API if available; court filing remains the user’s decision. |
| Email / user-uploaded reply | User manually adds a reply or pastes content, with redaction and preview | Mailbox connector requires explicit scopes, secure tokens, scoped read-only access first, deletion and incident handling. |
| Calendar reminder | User-clicked `.ics` file or reminder text | Browser/push reminders need opt-in, permission and dependable scheduling infrastructure. A date saved to a database is not an active reminder. |
| Account Aggregator | Not in MVP; do not request bank login/PIN | The AA framework relies on explicit consent and participation of regulated Financial Information Users. The product’s legal role and eligibility must be confirmed before pursuing. |
| Merchant/ticketing API | Structured draft and user-controlled handoff | Real partner, authorised API contract, data-sharing terms, authentication, audit logs, retention/deletion policy and a disclosed pilot status. |

## 4. Why the current demo is the right product improvement

The sample case does four things for a visitor or evaluator in under one minute:

1. Gives them a tangible scenario without asking for real financial details.
2. Shows that a UPI failure and merchant refund are routed as different categories.
3. Provides actionable language and official-source links, not only an AI paragraph.
4. Makes limits explicit: no transaction check, no case created, no complaint sent.

The new public demo is intentionally powered by the deterministic resolution playbooks, not claimed to be generated by Gnani. The separate spoken path is where the actual configured Gnani speech model must be demonstrated. If Prisma v2.5 is used for live voice-to-text, say that accurately. Current Gnani material also lists Timbre v3.0, while the existing `hi-en`/Poorvi support in the app is tied to the v2.5 catalog; don't change the TTS model blindly or claim v3.0 is used unless the endpoint, voice catalogue and live response were tested.

### Suggested 60-second demo

- **0–7 s:** “A voice assistant alone won’t get you a refund. The hard part is choosing the right process and proving what happened.”
- **7–18 s:** Record a real, fictional Hinglish utterance with the configured Gnani Prisma v2.5 service. Show the service is configured and the transcript arrives live. Keep credentials hidden.
- **18–27 s:** Correct the transcript and confirm the amount/status. Point out that speech output is user-reported until confirmed.
- **27–38 s:** Open the read-only sample demo; compare “UPI payment failed” vs “refund delayed” and show how the next step and official sources change.
- **38–49 s:** Show a Resolution Passport with chronology, missing evidence and editable message. Do not show a claimed submitted complaint or fake refund outcome.
- **49–56 s:** Show a fictional response requiring more evidence and how the next step would be reviewed (only demo this if implemented and tested; otherwise say it is roadmap).
- **56–60 s:** Explain one measured user problem and the next validation milestone.

Before publishing, live-test API credentials, transcript quality, failure paths, and current official route links. Use a screen capture of the actual build—not an edited mock presented as live functionality.

## 5. Align with the Gnani AI challenge without chasing award badges blindly

The official Great Indian AI Internship Challenge page describes an open brief and requires a working app built on at least one Gnani AI model/API, naming the model/API and each team member’s contribution. It asks for a public demo on LinkedIn or X with `#GnaniAI` and `#GreatIndianAIInternshipChallenge`, tagging Gnani AI and nominating the post in the submission. Published final deadline: 10 November 2026, 11:59 PM IST. Eligibility, current rules and submission instructions must be rechecked on the official page before submission.

Relevant angles for this product:

- **Mixed Vibes:** a real Hinglish voice example, corrected transcript and meaningful code-mixed journey.
- **Real Deal:** help an actual consumer understand and organise a payment/refund process. Back this with a small, ethical usability study, not invented impact numbers.
- **Main Character:** only claim this angle if the product works well in the selected regional/low-resource language and has been tested by fluent speakers; adding a language dropdown alone is not enough.
- **Noisy voice / accessibility:** demonstrate natural speech under realistic, consented conditions only if the live API handles it reliably.

The challenge’s authenticity restrictions mean no bought engagement, bots, paid promotion, engagement exchanges, plagiarism or misleading live-demo claims. Strongest path: genuine functionality, a crisp 60-second public demo, explicit Gnani model attribution, repeatable tests and an honest account of what is still a prototype.

## 6. Security, legal and trust release gates

This product processes potentially sensitive financial stories and evidence. Before any public launch, make these gates explicit:

- Private cases/evidence are owner-isolated; API access tests cover anonymous, member and admin tiers.
- Uploaded files are size-limited, extension/MIME/signature-checked, stored out of webroot, safely named and scanned before any future OCR pipeline. Treat text inside documents as untrusted input, not model instructions.
- Logs do not retain full speech transcripts, identifiers, uploaded evidence or API credentials by default. Use retention limits and redaction tests.
- User consent specifies purpose, external processor, storage, retention and deletion. Implement export/delete and incident handling with legal review against the DPDP Act/Rules’ phased commencement timetable.
- Public preview is rate-limited and data-minimised. It never persists the fictional scenario and is network-only in the service worker.
- No bank transaction is called “verified” without an authorised live response and timestamp.
- No complaint is called “submitted” until an actual submission response or reference has been received.
- Suspected fraud short-circuits to the official urgent route (bank and India’s 1930 cyber-fraud channel) and does not wait for a normal intake.
- Keep legal routing rules versioned with `source_url`, `applicable_to`, `effective_from`, `reviewed_on`, `reviewer`, `last_checked`, `rule_id`, `test_id`, `supersedes` and `next_review_due`.
- RBI scheme details and e-commerce rule changes must be reviewed as law/regulation changes. For example, the 2026 Consumer Protection (E-Commerce) Amendment Rules are described as taking effect from 1 January 2027; add their future effective date to monitoring rather than applying them early.

This is product engineering guidance, not legal advice or a certification of compliance. Get a qualified Indian privacy/security/legal review before processing real consumer evidence at scale.

## 7. Roadmap and validation gates

### P0 — before challenge demo (next 1–3 days)

- [x] Add a no-login, fictional sample-case demo with official source links.
- [x] Show explicitly that the demo does not check a bank, save a case or submit a complaint.
- [x] Add regression checks for both sample scenarios and non-persistence.
- [ ] Run the actual Gnani speech endpoint with owner-provided credentials and record the exact configured model/version; keep secrets out of recording.
- [ ] Have two or more fluent Hinglish speakers rate transcript corrections and task comprehension; save only consented, minimal test data.
- [ ] Validate each source URL and exact text in current official routing playbooks.

### P1 — next 2 weeks

- Add structured provenance for case facts and evidence; propagate corrections into all generated outputs.
- Add the “why this path?” panel that identifies rule, source, applicability and one unanswered question.
- Build a regression dataset of 50–100 fictional utterances: Hindi, Hinglish, English, common typo/noise cases, negatives (money not debited), merchant order refund vs UPI reversal, duplicate charge and fraud. Have a human review expected labels.
- Report classification confusion matrix, unsafe-route failures, false urgency, unsupported claims, transcript edit rate, completion and mobile accessibility. Don't optimise only for model latency.
- Add an exportable chronology and case summary that includes only selected/redacted data.

### P2 — weeks 3–6

- User-reviewed reply import / paste with quoted evidence and suggestion-only status classification.
- Active reminders using a reliable, opted-in channel; timezone, snooze, cancellation and deletion behaviour.
- Source-rule management with effective-date alerts and regression reruns.
- Usability study with 10–20 real people who have recently faced a supported problem. Measure unaided next-step understanding, time to a complete first-contact pack, confidence and completion; obtain consent and avoid collecting unnecessary account/transaction details.

### P3 — weeks 7–12

- Pilot one documented, authorised merchant/support integration.
- Receive authenticated acknowledgement/ticket updates with consent, timestamp and provider proof.
- Collect optional outcomes; distinguish self-reported vs document-supported vs integration-verified outcomes.
- Publish measured results only with defined denominator, cohort, observation window, missing outcomes and independent verification.

### Example launch-quality metrics (targets to test, not achieved results)

- ≥90% accuracy on the curated fictional routing set for the categories included at launch.
- 0 critical unsafe routing failures in the release suite (especially fraud and unauthorised debit).
- ≥80% of usability participants can explain their next action without coaching.
- ≥80% of generated packs contain all required evidence fields for the supported scenario, after user confirmation.
- 100% of substantive recommendation steps have visible sources or an explicit “no reliable source found” state.
- 0 false “live transaction verified” / “complaint submitted” states.
- Track how many users edit the transcript; don't treat low edits as success if transcription silently omits details.

## 8. 180+ reference library

**How to read this library:** primary government/regulator/product documentation should govern route rules. Company help articles describe that company’s own flow and may not override an RBI/NPCI rule. Human–AI, accessibility and security references are implementation guidance. User forums are anecdotal signal, not prevalence data. Link availability and content should be rechecked before release.

### A. Official challenge and Gnani AI technology

1. [Great Indian AI Internship Challenge — official rules and award categories](https://www.gnani.ai/internship)
2. [Gnani AI challenge registration / nomination information](https://www.gnani.ai/great-indian-ai-internship-registration-form)
3. [Gnani API documentation — introduction](https://docs.gnani.ai/api/introduction/introduction)
4. [Gnani Prisma speech-to-text REST API](https://docs.gnani.ai/api/STT/speech-to-text)
5. [Gnani text-to-speech available voices](https://docs.gnani.ai/api/TTS/available-voices)
6. [Gnani Timbre TTS audio tags](https://docs.gnani.ai/api/TTS/tts-audio-tags)
7. [Gnani AI Hugging Face organisation](https://huggingface.co/gnani)
8. [Gnani SDK/model guide on Hugging Face](https://huggingface.co/gnani/gnani)
9. [Gnani Evon v3.3 model card](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B)
10. [Gnani developer API service documentation](https://gnani-ai.github.io/API-service/)
11. [Gnani AI API platform](https://app.gnani.ai/voice)
12. [Gnani AI official website](https://www.gnani.ai/)
13. [Gnani AI official developer documentation home](https://docs.gnani.ai/)
14. [Gnani AI official Hugging Face model collection](https://huggingface.co/collections/gnani)
15. [Gnani Prisma STT realtime WebSocket guide](https://docs.gnani.ai/api/STT/stt-websocket)
16. [Gnani batch speech-to-text guide](https://docs.gnani.ai/api/STTBatch/Introduction)
17. [Gnani Timbre TTS REST guide](https://docs.gnani.ai/api/TTS/tts-inference)
18. [Gnani Timbre TTS streaming guide](https://docs.gnani.ai/api/TTS/tts-sse)
19. [Gnani Timbre TTS realtime WebSocket guide](https://docs.gnani.ai/api/TTS/tts-websocket)
20. [Gnani Speech APIs quick start](https://docs.gnani.ai/api/introduction/quick-start)
21. [Gnani podcast transcription use case](https://docs.gnani.ai/api/use-cases/podcast-transcription)
22. [Gnani call analytics use case](https://docs.gnani.ai/api/use-cases/call-analytics)
23. [Gnani realtime compliance monitoring use case](https://docs.gnani.ai/api/use-cases/real-time-compliance)

### B. NPCI, UPI, transaction disputes and payment rules

24. [NPCI UPI FAQs](https://www.npci.org.in/what-we-do/upi/faqs)
25. [NPCI Register a Complaint / complaint status](https://www.npci.org.in/register-a-complaint)
26. [NPCI official UPI HELP pilot circular (FY 2025–26)](https://www.npci.org.in/uploads/UPI_OC_No_227_FY_2025_26_Introduction_of_UPI_HELP_Assistant_pilot_an_AI_powered_support_for_UPI_payments_cd501de8f3.pdf)
27. [NPCI UPI product page](https://www.npci.org.in/what-we-do/upi/product-overview)
28. [NPCI BHIM product page](https://www.npci.org.in/product/bhim)
29. [BHIM UPI official FAQs](https://www.bhimupi.org.in/faq-s.html)
30. [RBI failed-transaction TAT circular / auto-reversal framework](https://www.rbi.org.in/commonman/Upload/English/Notification/PDFs/CIRCULAR677EC931A7A65E4D99AA957D8E85BC0A2A.PDF)
31. [RBI Integrated Ombudsman Scheme 2026 — FAQ](https://old.rbi.org.in/commonman/english/scripts/faqs.aspx?id=3407)
32. [RBI Complaint Management System](https://cms.rbi.org.in/)
33. [RBI official website](https://www.rbi.org.in/)
34. [RBI circulars and notifications index](https://www.rbi.org.in/Scripts/NotificationUser.aspx)
35. [RBI payment system information](https://www.rbi.org.in/Scripts/PaymentSystems.aspx)
36. [RBI Master Directions on Prepaid Payment Instruments (index)](https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12051)
37. [RBI Digital Payment Security Controls for non-bank PSOs](https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12088&Mode=0)
38. [RBI Bharat Bill Payment System directions (searchable official source)](https://www.rbi.org.in/Scripts/NotificationUser.aspx)
39. [NPCI UPI site map / products index](https://www.npci.org.in/what-we-do/upi)
40. [NPCI official complaint page — eligibility and disclaimers](https://www.npci.org.in/register-a-complaint)
41. [NPCI product and service list](https://www.npci.org.in/what-we-do)
42. [RBI consumer education and protection](https://www.rbi.org.in/commonman/English/Scripts/ConsumerAwareness.aspx)
43. [RBI Ombudsman annual-report / publication index](https://www.rbi.org.in/Scripts/AnnualReportPublications.aspx)

### C. Consumer protection, NCH, consumer commissions and cyber safety

44. [National Consumer Helpline — official overview](https://consumeraffairs.gov.in/pages/nch)
45. [National Consumer Helpline portal](https://consumerhelpline.gov.in/)
46. [NCH convergence programme and partner process](https://www.consumerhelpline.gov.in/public/convergenceprogram)
47. [NCH consumer rights guide](https://consumerhelpline.gov.in/public/index.php/consumerrights)
48. [NCH Consumer Protection Act 2019 knowledge base](https://consumerhelpline.gov.in/public/knowledgebasedetails/Consumer%20Protection%20Act%202019)
49. [Consumer Handbook (NCH, PDF)](https://consumerhelpline.gov.in/public/assets/docs/consumerhandbooks/Consumer_Handbook.pdf)
50. [Department of Consumer Affairs — Consumer Protection Acts and Rules](https://consumeraffairs.gov.in/index.php/pages/consumer-protection-acts)
51. [Central Consumer Protection Authority guideline index](https://www.ccpa.doca.gov.in/guidelines)
52. [e-Jagriti official portal](https://e-jagriti.gov.in/)
53. [NIC — e-Jagriti unified digital platform for consumer justice](https://www.nic.gov.in/project/e-jagriti-a-unified-digital-platform-for-consumer-justice/)
54. [Department of Consumer Affairs — official website](https://consumeraffairs.gov.in/)
55. [National Cyber Crime Reporting Portal](https://cybercrime.gov.in/)
56. [Cybercrime portal — 1930 and nodal grievance information](https://cybercrime.gov.in/Webform/Crime_NodalGrivanceList.aspx)
57. [Indian Cyber Crime Coordination Centre (I4C)](https://i4c.mha.gov.in/)
58. [Ministry of Home Affairs](https://www.mha.gov.in/)
59. [Consumer Protection (E-Commerce) Rules, 2020 — official rules page](https://consumeraffairs.gov.in/)
60. [PIB — Consumer Protection (E-Commerce) Amendment Rules, 2026 notice](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2308759&lang=1&reg=48)
61. [PIB — Digital Personal Data Protection Rules 2025](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2190014&lang=1&reg=3)
62. [India Code — legal acts and notifications](https://www.indiacode.nic.in/)
63. [UMANG official government services app](https://web.umang.gov.in/)
64. [MyGov India — official government service announcements](https://www.mygov.in/)
65. [PIB — Press Information Bureau](https://pib.gov.in/)

### D. Payment-app / merchant support competitors and alternatives

66. [RefundPe — public product and feature claims](https://refundpe.com/)
67. [Paytm — failed or pending UPI transaction help](https://paytm.com/support/upi/steps-for-resolving-failed-or-pending-upi-transactions)
68. [Paytm — how to raise a UPI complaint](https://paytm.com/support/upi/how-to-raise-upi-complaint-paytm)
69. [Paytm — UPI support hub](https://paytm.com/support/upi)
70. [Paytm help and FAQs](https://paytm.com/faqs)
71. [Google Pay India — merchant order/payment issue guide](https://support.google.com/pay/india/answer/9494510?hl=en)
72. [Google Pay India — support centre](https://support.google.com/pay/india/)
73. [Google Pay — report a problem / contact help](https://support.google.com/pay/india/answer/7644078?hl=en)
74. [PhonePe support](https://support.phonepe.com/)
75. [PhonePe official website](https://www.phonepe.com/)
76. [BHIM official site](https://www.bhimupi.org.in/)
77. [Amazon India customer service — official explanation](https://www.aboutamazon.in/news/operations/contact-amazon-india-customer-service)
78. [Amazon order/refund help topic](https://digprjsurvey.amazon.com/csad/help/node/GMP8PC8KBY5FCPM2)
79. [Amazon support options](https://digprjsurvey.amazon.com/csad/help/node/GSD587LKW72HKU2V)
80. [Flipkart Help Centre](https://www.flipkart.com/helpcentre)
81. [Flipkart — official guide to contacting support](https://stories.flipkart.com/get-help-contact-flipkart-support)
82. [Myntra](https://www.myntra.com/)
83. [PayPal Help Centre](https://www.paypal.com/in/cshelp/home)
84. [Razorpay customer help](https://razorpay.com/support/)
85. [CRED help centre](https://cred.club/)
86. [IRCTC official website / transaction-related support](https://www.irctc.co.in/)
87. [Consumer court filing portal — e-Jagriti](https://e-jagriti.gov.in/)

### E. Account Aggregator, privacy, security and safe document processing

88. [Department of Financial Services — Account Aggregator framework](https://www.financialservices.gov.in/account-aggregator-framework)
89. [Sahamati — Account Aggregator ecosystem](https://sahamati.org.in/)
90. [Reserve Bank of India — NBFC Account Aggregator Directions](https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=10598)
91. [PIB — DPDP Rules 2025 announcement](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2190014&lang=1&reg=3)
92. [MeitY — Digital Personal Data Protection (DPDP) ecosystem](https://www.meity.gov.in/)
93. [India Code — Digital Personal Data Protection Act, 2023](https://www.indiacode.nic.in/)
94. [CERT-In — official website](https://www.cert-in.org.in/)
95. [CERT-In Directions under section 70B (PDF)](https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf)
96. [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
97. [OWASP Cheat Sheet Series home](https://cheatsheetseries.owasp.org/)
98. [OWASP Prompt Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
99. [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
100. [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
101. [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
102. [OWASP API Security Top 10](https://owasp.org/API-Security/)
103. [OWASP Application Security Verification Standard](https://asvs.owasp.org/)
104. [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
105. [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
106. [OWASP REST Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html)
107. [OWASP Cross Site Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
108. [OWASP Content Security Policy Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)
109. [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
110. [OWASP Error Handling Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html)
111. [OWASP Data Protection Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
112. [Mozilla Observatory security header checker](https://observatory.mozilla.org/)
113. [MDN Content Security Policy guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
114. [MDN Web security](https://developer.mozilla.org/en-US/docs/Web/Security)

### F. Human–AI interaction, user research and accessibility

115. [Google PAIR Guidebook](https://pair.withgoogle.com/guidebook-v2/)
116. [Google PAIR — Feedback and Controls](https://pair.withgoogle.com/guidebook-v2/chapter/feedback-controls/)
117. [Google PAIR design patterns](https://pair.withgoogle.com/guidebook-v2/patterns)
118. [Microsoft HAX Toolkit](https://www.microsoft.com/en-us/haxtoolkit/)
119. [Microsoft HAX Guidelines for Human-AI Interaction](https://www.microsoft.com/en-us/haxtoolkit/ai-guidelines/)
120. [GOV.UK Service Standard](https://www.gov.uk/service-manual/service-standard)
121. [GOV.UK — Understand user needs](https://www.gov.uk/service-manual/service-standard/point-1-understand-user-needs)
122. [GOV.UK — Make the service simple to use](https://www.gov.uk/service-manual/service-standard/point-4-make-the-service-simple-to-use)
123. [GOV.UK — making prototypes](https://www.gov.uk/service-manual/design/making-prototypes)
124. [W3C WCAG 2.2 standard](https://www.w3.org/TR/WCAG22/)
125. [W3C WCAG overview](https://www.w3.org/WAI/standards-guidelines/wcag/)
126. [W3C — Target Size Minimum (WCAG 2.2)](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)
127. [WAI ARIA Authoring Practices — Accordion pattern](https://www.w3.org/WAI/ARIA/apg/patterns/accordion/)
128. [MDN HTML details element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details)
129. [MDN Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
130. [MDN MediaDevices getUserMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)
131. [Nielsen Norman Group — usability heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/)
132. [Nielsen Norman Group — user interviews](https://www.nngroup.com/articles/user-interviews/)
133. [Nielsen Norman Group — task analysis](https://www.nngroup.com/articles/task-analysis/)
134. [Nielsen Norman Group — progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/)
135. [Nielsen Norman Group — error prevention](https://www.nngroup.com/articles/slips/)
136. [Nielsen Norman Group — form design](https://www.nngroup.com/articles/web-form-design/)
137. [Nielsen Norman Group — mobile usability](https://www.nngroup.com/articles/mobile-usability/)
138. [Nielsen Norman Group — accessibility](https://www.nngroup.com/articles/accessibility-101/)
139. [W3C Web Content Accessibility Guidelines quick reference](https://www.w3.org/WAI/WCAG22/quickref/)

### G. Indian-language speech, datasets and developer tooling

140. [AI4Bharat](https://ai4bharat.iitm.ac.in/)
141. [AI4Bharat IndicVoices dataset](https://huggingface.co/datasets/ai4bharat/IndicVoices)
142. [AI4Bharat Kathbath speech dataset](https://huggingface.co/datasets/ai4bharat/Kathbath)
143. [AIKosh — IndiaAI datasets platform](https://aikosh.indiaai.gov.in/)
144. [ULCA — Unified Language Contribution API (GitHub)](https://github.com/ULCA-IN/ulca)
145. [Bhashini official portal](https://bhashini.gov.in/)
146. [Bhashini APIs platform](https://www.bhashini.ai/)
147. [Bhashini TTS API documentation UI](https://tts.bhashini.ai/openapi/ui/)
148. [Sarvam AI documentation](https://docs.sarvam.ai/)
149. [Sarvam speech-to-text product](https://www.sarvam.ai/speech-to-text)
150. [Sarvam model overview](https://docs.sarvam.ai/api/getting-started/models)
151. [Sarvam Translate model documentation](https://docs.sarvam.ai/api/getting-started/models/sarvam-translate)
152. [Sarvam — building for India](https://docs.sarvam.ai/api-reference-docs/building-for-india)
153. [AI4Bharat IndicTrans2](https://github.com/AI4Bharat/IndicTrans2)
154. [Mozilla Common Voice](https://commonvoice.mozilla.org/)
155. [Hugging Face documentation](https://huggingface.co/docs)
156. [Hugging Face Transformers documentation](https://huggingface.co/docs/transformers/index)
157. [Hugging Face Evaluate library](https://huggingface.co/docs/evaluate/index)
158. [PyTorch documentation](https://pytorch.org/docs/stable/index.html)
159. [FastAPI documentation](https://fastapi.tiangolo.com/)
160. [Pydantic documentation](https://docs.pydantic.dev/latest/)
161. [pytest documentation](https://docs.pytest.org/en/stable/)
162. [Playwright documentation](https://playwright.dev/python/)
163. [MDN Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
164. [Python security considerations](https://docs.python.org/3/library/security_warnings.html)

### H. Evaluation, testing, engineering and public-discussion starting points

165. [OWASP Top 10 for LLM Applications — project page](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
166. [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
167. [NIST AI RMF Playbook](https://airc.nist.gov/AI_RMF_Knowledge_Base/Playbook)
168. [NIST Generative AI Profile (AI 600-1)](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf)
169. [Google Responsible AI practices](https://ai.google/responsibility/responsible-ai-practices/)
170. [Google Model Cards](https://modelcards.withgoogle.com/about)
171. [Hugging Face model cards documentation](https://huggingface.co/docs/hub/model-cards)
172. [Hugging Face dataset cards documentation](https://huggingface.co/docs/hub/datasets-cards)
173. [GitHub Actions documentation](https://docs.github.com/actions)
174. [GitHub security best practices](https://docs.github.com/code-security)
175. [Python unittest documentation](https://docs.python.org/3/library/unittest.html)
176. [HTTPX documentation](https://www.python-httpx.org/)
177. [SQLite security and database documentation](https://www.sqlite.org/docs.html)
178. [OWASP threat modeling](https://owasp.org/www-community/Threat_Modeling)
179. [OWASP Juice Shop (security-testing education project)](https://owasp.org/www-project-juice-shop/)
180. [W3C WebDriver standard](https://www.w3.org/TR/webdriver2/)
181. [web.dev accessibility](https://web.dev/learn/accessibility/)
182. [web.dev performance](https://web.dev/learn/performance/)
183. [Chrome DevTools documentation](https://developer.chrome.com/docs/devtools/)
184. [Lighthouse documentation](https://developer.chrome.com/docs/lighthouse/)
185. [Google Search Central — spam policies](https://developers.google.com/search/docs/essentials/spam-policies)
186. [Reddit — example discussion about failed UPI payment (anecdotal, not authoritative)](https://www.reddit.com/r/CreditCardsIndia/comments/1kc7rgo/money_debited_but_upi_transaction_failed_via_bhim/)
187. [Reddit India discussion search: failed UPI payment](https://www.reddit.com/search/?q=failed%20UPI%20payment%20refund)
188. [Reddit India discussion search: delayed merchant refund](https://www.reddit.com/search/?q=merchant%20refund%20delayed%20India)
189. [Reddit India discussion search: consumer complaint experience](https://www.reddit.com/search/?q=National%20Consumer%20Helpline%20experience)

**Count:** 189 numbered references (181 distinct URLs after de-duplicating exact repeats). This is a starting library of primary rules, product help, tooling and tutorials/posts. Before relying on any entry for legal routing or model claims, confirm that the page still exists and that its content applies to the specific scenario and effective date.