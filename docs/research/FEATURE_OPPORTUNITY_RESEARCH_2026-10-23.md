# BolKeResolve — High-Value Feature Opportunities & Integration Research

**Research date:** 23 October 2026  
**Product baseline inspected:** `BolKeResolve_Frontend_Deep_Alignment_Polish_2026-10-23.zip`, including the Living Resolution Passport, evidence-review and case-inbox code paths.  
**Goal:** Find the next technically meaningful features that reduce the time and effort between a consumer having a payment/refund issue and taking the correct next action—without expanding BolKeResolve into a sprawling complaint-management platform.

> **Executive recommendation:** Build the next release around a **Share-to-Case + Official Route Intelligence + Rule-backed Timeline** trio. These features fit together, reduce friction at the exact moment a user has evidence in another app, and improve the accuracy of what the existing product recommends. Keep bank/account integrations and automatic complaint submission out of the critical path until formal access and privacy/security reviews are possible.

---

## 1. What the current project already has

This research is not starting from zero. The inspected code already includes:

- Voice/text intake and a guided case-creation flow; a Gnani speech integration path exists, but live API use must be separately configured and verified.
- A deterministic source-linked resolution module in `backend/resolution.py`.
- A curated official support directory in `backend/support_directory.py`.
- Authenticated case creation, case listing, saved facts, timeline, outcome updates, follow-up dates and checklist state.
- Evidence upload with file type/signature/size controls; PDF/image text extraction and user-confirmed candidate facts through the Evidence Review pipeline.
- Provenance metadata and JSON/printable Resolution Passport exports.
- Reply-review preview/confirm logic that stores a short user-confirmed interpretation instead of raw pasted support reply text.
- A case-specific inbound email bridge that is **disabled until domain, encryption and webhook configuration is supplied**.
- WhatsApp provider adapters and link flows that require actual provider configuration to be operational.
- A PWA manifest and service worker with a public-shell-only cache.

Therefore, the best next additions should connect these existing capabilities and expose them at the moment users need them. Avoid adding more tabs or rebuilding existing functions under new names.

### Current limitations worth addressing

1. Evidence review starts after the user has already opened BolKeResolve and uploaded a file. This is avoidable friction: users often have the receipt in email, a screenshot in Photos, or order information in another app.
2. Support routing is curated and static. It can be strengthened by a dated official merchant/grievance directory and a verified match to the National Consumer Helpline (NCH) Convergence Partners list.
3. The source registry is manually reviewed and the resolution logic is largely deterministic, but source review dates alone are not a versioned legal/policy rules system with effective-date predicates and explicit scenario tests.
4. The Case Inbox Bridge code exists but has not had its receiving domain, DNS/MX, provider retention, live webhook and deletion lifecycle verified in a production environment.
5. Neither the current app nor a proposed new feature should imply that a bank transaction has been independently checked unless an authorised live integration genuinely performed that check.

---

## 2. Competitive reality: what not to rebuild

### NPCI / UPI HELP

NPCI’s October 2025 UPI HELP pilot describes digital-payment queries, transaction status and complaint logging/tracking for supported scenarios and participating members, plus mandate management. A generic UPI chatbot or a promise of live transaction checking would not be distinctive—and access to NPCI/member systems cannot be assumed to be open to every startup. [NPCI pilot circular](https://www.npci.org.in/uploads/UPI_OC_No_227_FY_2025_26_Introduction_of_UPI_HELP_Assistant_pilot_an_AI_powered_support_for_UPI_payments_cd501de8f3.pdf).

### National Consumer Helpline (NCH)

NCH already accepts grievances in 17 languages across phone, web, app, UMANG, SMS and WhatsApp. Its Convergence Program says that more than 2,000 companies/organisations participate, with grievances forwarded in real time and responses expected within 30 days. The official partners list publishes brand and legal-entity names. [NCH channels](https://consumeraffairs.gov.in/pages/nch) · [NCH Convergence](https://www.consumerhelpline.gov.in/public/convergenceprogram) · [Official partner directory](https://consumerhelpline.gov.in/public/convergencepartners).

### e-Jagriti

The National Informatics Centre describes e-Jagriti as supporting consumer-commission filing, case progress, documents and case-management workflows. BolKeResolve should help users prepare and organise their facts, not pretend to replace a formal case portal. [NIC e-Jagriti overview](https://www.nic.gov.in/project/e-jagriti-a-unified-digital-platform-for-consumer-justice/).

### Direct competitors

- [RefundPe](https://refundpe.com/) advertises complaint drafting, user-approved sending, follow-ups and regulator packs.
- [Nyaykar](https://www.nyaykar.in/) advertises authority routing, Indian-language input, formal complaint drafting, a complaint-strength score and follow-up letters.
- [Voxya](https://voxya.com/) offers consumer complaint and escalation services.
- Large merchants already provide their own refund status portals; for example, [Amazon's refund-status help](https://digprjsurvey.amazon.com/csad/help/node/GMP8PC8KBY5FCPM2) directs users to their Returns area and confirmation email.

**Implication:** Complaint letters, an AI chatbot, a dashboard, or reminders are not defensible differentiators on their own. BolKeResolve needs a better way to get evidence into the case, select the correct process, and keep the case accurate as new information arrives.

---

## 3. Feature ranking

Scores are strategic estimates based on the reviewed product and public documentation, not measured user outcomes. Buildability means the first useful version can be built without privileged banking, merchant or government API access.

| Rank | Feature | User value | Differentiation potential | MVP buildability | External approval required? | Decision |
|---:|---|---|---|---|---|---|
| 1 | **Share-to-Case** from Android/PWA share sheet | Very high | High for friction reduction | Medium | No, but browser/platform support is limited | Build first |
| 2 | **Official Route Intelligence**: merchant contacts + dated NCH convergence match | High | High when combined with correct next step | Medium | No API required for public directory snapshot; do not claim official integration | Build in parallel |
| 3 | **Rules-as-code + milestone timeline** | Very high | High for correctness and trust | Medium | No for public-source rules; domain/legal review required | Build alongside #2 |
| 4 | **Policy Snapshot / mismatch check** | High for merchant refunds | Potentially high | Medium | Not for user-supplied public-policy capture; arbitrary automated crawling needs careful controls | Pilot after top three |
| 5 | **Reply-delta / evidence-request detector** | High | Medium-high | Medium | No | Extend existing reply review, not a new tab |
| 6 | **NCH-ready portable action pack** | Medium-high | Medium | High | No for manually submitted pack | Improve existing Passport export |
| 7 | **Merchant-side Resolution Bridge** with status acknowledgement | Potentially very high | Very high if genuine | Low without a willing partner | Yes | Partnership track |
| 8 | Full Gmail mailbox sync | Medium | Low-medium | Low | Google OAuth verification; restricted scope may require security assessment | Do not start here |
| 9 | Automatic bank/UPI transaction verification | Potentially high | High | Very low | Authorised scheme member / regulated partner access | Do not promise; partner track |
| 10 | Bank account data aggregation | Potentially high | Low for initial consumer use case | Very low | Account Aggregator framework and regulated FIU participation | Not an MVP feature |

---

## 4. Build first: Share-to-Case

### The consumer problem

A user notices a failed payment, opens a UPI app, sees the transaction or takes a screenshot, then must leave that app, open BolKeResolve, navigate to the correct case/form, upload the file and explain it again. Every extra step increases friction, especially for voice-first and mobile users.

### Proposed interaction

1. The user taps **Share** on a transaction screenshot, order confirmation, merchant email text or PDF in an app that supports sharing.
2. BolKeResolve appears as a share destination when installed as a compatible PWA.
3. BolKeResolve opens a small **Review shared item** screen. It shows the file/text/URL and clearly says nothing has been attached or saved to a case yet.
4. The user chooses **Add to an existing case** or **Start a new case**.
5. The app validates the file type and size, places it in the normal evidence-review flow, and asks the user to confirm extracted facts before updating any case.

### Technical approach

- Add a `share_target` definition to `frontend/manifest.webmanifest` using `POST` and `multipart/form-data` for supported image/PDF files. The MDN `share_target` documentation describes this mechanism, including file parameters and form encoding. [MDN share_target](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Manifest/Reference/share_target).
- Implement a tightly scoped FastAPI receive endpoint, e.g. `/share-target`, using the existing session and request-security rules. Validate authentication, ownership, allowed MIME types and magic bytes, file counts, size limits and quota before staging anything.
- Store new shared files in a private, non-public temporary staging area with an opaque short-lived token tied to the authenticated user; do not use shared content to infer the case ID.
- Expire unclaimed staging files quickly (e.g. 30–60 minutes). Redirect to a confirmation view using HTTP 303. Never automatically attach to a case or persist extracted facts without user confirmation.
- Reuse the existing evidence review and provenance pipeline after the user chooses a case.
- Keep a conventional upload/paste route for browsers or platforms that do not support PWA share targets. MDN marks this capability as not universally available, so treat it as progressive enhancement—not the only way to upload. [MDN Web Share API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Share_API).

### Why this is stronger than adding another form

It removes the context-switching step at the moment the user already has the relevant evidence. It connects the real phone workflow to the existing evidence pipeline and can be demonstrated quickly in a competition demo. It does not require credentials to a bank, UPI app or mailbox.

### Acceptance tests

- Shared text, URLs and allowlisted image/PDF files reach a preview screen, not a saved case automatically.
- Unauthenticated users are prompted to sign in; no private upload is attached to an anonymous or guessed account.
- Tampered MIME headers, invalid signatures, oversized files, too many files and path-like filenames are rejected safely.
- A shared file is not placed in a public/static directory.
- Temporary files are deleted on completion, cancellation and expiry.
- Share-target requests are replay-safe and do not duplicate evidence on page refresh.
- If the browser does not expose Share-to-Case, the ordinary upload flow remains available.

OWASP recommends allowlisted extensions, validation of file signatures rather than trusting Content-Type, generated filenames, size limits, private/out-of-webroot storage and careful upload handling. [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html).

---

## 5. Build in parallel: Official Route Intelligence

### What the feature does

When the user names a merchant or provider, the case displays a concise route card that answers:

- What is the official customer-support or grievance route?
- Is the organisation currently listed in the public NCH Convergence Partners directory?
- What is the legal entity name associated with that listing?
- What is the source, and when was the directory last checked?
- What is the next appropriate route if the merchant response does not resolve the problem?

This must be integrated into the existing **one recommended next step** card, not become a new dashboard.

### Data source and feasibility

NCH publishes a searchable company/brand directory. Examples in the current public list include Amazon.in / Amazon Seller Services Private Limited, Zomato / ETERNAL LIMITED and Flipkart.com / Flipkart Internet Private Limited. Listing should be recorded exactly as observed, alongside the directory URL and retrieval date. [NCH official convergence-partner list](https://consumerhelpline.gov.in/public/convergencepartners).

The Department of Consumer Affairs says the 2026 e-commerce rule amendments take effect on **1 January 2027** and require every e-commerce entity to become a partner in NCH's convergence process. It reported 511,196 e-commerce grievances among 1,771,622 total NCH grievances in 2025. This is a reason to strengthen correct routing and explore approved merchant-side integrations, not evidence of an open NCH API. [PIB announcement](https://www.pib.gov.in/newsite/erelcontent.aspx?lang=2&reg=48&relid=294532).

### Implementation

- Create a versioned, locally stored directory snapshot from the public source. Do not scrape it on every user request.
- Normalize known aliases, brand names and legal entities; retain the original official names for display.
- Match conservatively. If multiple possible matches exist, ask the user to confirm the merchant rather than fuzzy-match automatically.
- Store `source_url`, `retrieved_at`, `brand_name`, `legal_entity`, and a `match_confidence`/matching method.
- Include a visible label such as **“Listed in the NCH Convergence Partners directory (checked 23 Oct 2026)”**, not “BolKeResolve is partnered with NCH” or “your complaint has been filed”.
- If no match exists, say “No matching entry found in the snapshot last checked on [date]” rather than claiming the organisation is not a partner.
- Refresh on a planned cadence; diff changes for a human to review before publishing.
- Use the directory to improve first-party support links and the user-controlled NCH handoff.

### Why it matters

Correct destination choice is directly related to whether the user's initial effort is wasted. It improves the existing support-directory and case guidance with public evidence, without needing a privileged government integration.

### What not to claim

NCH's Convergence Program is a route for grievances to be forwarded to participating organisations. A public partner listing is not proof that BolKeResolve itself has a partnership, that a particular case was registered, or that a refund will be approved. The official partner registration form requests organisation identity, contact roles, company-domain email and authorisation/undertaking documents; a product integration would require the appropriate formal route. [NCH registration form](https://consumerhelpline.gov.in/public/convergencepartnersreq).

---

## 6. Build alongside it: Rules-as-code + a milestone timeline

### The issue

A support recommendation can be visually clear yet still be wrong if it applies a deadline to the wrong scenario. The product needs to separate:

1. **Suggested next check** — a practical recommendation to the user.
2. **Official outer limit / turnaround time** — only when a current rule directly applies to the classified transaction scenario.
3. **Organisation's own stated timeline** — from the user's receipt/email or an official merchant policy.
4. **User-set reminder** — a personal reminder, not a regulatory deadline.

### Verified examples

- RBI's failed-transaction framework distinguishes a UPI transfer where the beneficiary is not credited from a merchant payment where confirmation is not received. The referenced circular states T+1 and T+5 turnaround limits for those respective categories; these must not be generalized to all merchant refunds. [RBI failed-transaction TAT circular](https://www.rbi.org.in/commonman/Upload/English/Notification/PDFs/CIRCULAR677EC931A7A65E4D99AA957D8E85BC0A2A.PDF).
- The RBI Integrated Ombudsman Scheme 2026 came into force on 1 July 2026 and applies only to covered regulated entities, subject to its maintainability requirements. A merchant refund by itself is not automatically an RBI Ombudsman matter. [RBI Scheme 2026 FAQ](https://old.rbi.org.in/commonman/english/scripts/faqs.aspx?id=3407).
- NPCI's UPI FAQ describes contacting the bank if a failed debited transaction refund is not received within one hour; this initial-contact advice is not the same thing as the RBI's outer reversal timelines. [NPCI UPI FAQ](https://www.npci.org.in/what-we-do/upi/faqs).

### Rule record shape

Every rule should have:

- `rule_id` and `version`;
- issue/scenario predicates and explicit exclusions;
- required confirmed fields;
- user-facing recommendation;
- source title, URL and cited section;
- source publication date, rule effective-from date and last-reviewed date;
- internal reviewer and review status;
- positive, negative and boundary tests.

### Implementation plan

- Move rules out of free-form prompt logic and into JSON/YAML or a small DB table used by the current deterministic resolver.
- Add test fixtures covering failed transfer, failed merchant payment, delayed merchant refund, unrecognised debit/fraud and ambiguous/missing status.
- Label any computed date with the facts and rule used. Do not compute a deadline when the transaction scenario, date or applicable entity is unknown.
- If a source changes, alert the maintainer; never silently publish automatically generated regulatory advice.
- Keep the display simple: a single “Next step” card with a “Why this step?” disclosure.

---

## 7. After the first three: Policy Snapshot and mismatch detection

For e-commerce/food-delivery refunds, let the user share or upload the order-confirmation email, cancellation confirmation and the merchant's refund-policy page. BolKeResolve can compare user-confirmed facts against the supplied policy and correspondence and produce a compact table:

- what the merchant policy says (quoted/short excerpt + URL + date captured);
- what the order/cancellation email says;
- whether the support reply says “initiated” or “credited”;
- which dates or amounts are missing or inconsistent;
- the next action supported by the facts.

**Important limitation:** a policy captured today is not proof of what was in force on the purchase date. Label the capture date and do not backdate or state legal entitlement if the evidence does not support it.

Start with a user-supplied URL, screenshot or saved page. If the product later fetches policy URLs server-side, use a strict allowlist or safe network fetch layer to prevent server-side request forgery (SSRF), reject private/internal IPs, cap redirect chains and response sizes, and treat fetched content as untrusted. E-commerce rule amendments and merchant policies can change; preserve source snapshots with dates.

---

## 8. Extend existing reply review rather than building another module

BolKeResolve already has preview/confirm reply review and a case-specific email bridge. The next useful iteration is to improve the existing review classification to detect:

- acknowledgement only;
- request for a specific document;
- refund initiated versus refund credited;
- partial refund / amount mismatch;
- rejected / closed / needs more information;
- unclear or non-responsive message;
- dangerous credential requests.

Use the reply to suggest a change, but require the user to confirm the interpretation and the case update. Never treat an email sender display name as verified identity, and never execute instructions in email bodies/attachments. OWASP specifically notes that emails, documents and retrieved web pages can contain prompt-injection instructions; content must remain untrusted data and permissions/actions must be enforced in application code. [OWASP LLM Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html) · [OWASP AI Agent Security](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html).

### Provider-retention concern

The current code's Case Inbox Bridge is optional and not live until configured. Before launching it publicly, account for the email provider's own retention. Postmark says messages and related metadata are retained for 45 days by default, adjustable from 7 to 365 days with its retention add-on, and that attachment bytes may appear in the Raw Source view. Application-level deletion does not erase a third-party provider's retained copy immediately. [Postmark retention documentation](https://postmarkapp.com/support/article/how-long-are-inbound-and-outbound-messages-stored-in-activity).

Full Gmail reading is not the easier alternative: Google documents restricted scopes such as `gmail.readonly`, with OAuth verification requirements and security assessment possible when restricted data is stored/transmitted. Avoid requesting access to the entire mailbox when case-specific forwarding or an explicit file share can do the job. [Google Gmail API scopes](https://developers.google.com/workspace/gmail/api/auth/scopes).

---

## 9. Integrations to postpone

### Direct UPI/bank transaction verification

Do not promise a status check from a transaction ID alone. NPCI describes UPI HELP as a pilot routed through participating members and their user-facing channels. Direct status checks or complaint tracking must use supported, authorised integrations. In the near term, use user-provided screenshots and transaction details with explicit provenance. [NPCI UPI HELP pilot](https://www.npci.org.in/uploads/UPI_OC_No_227_FY_2025_26_Introduction_of_UPI_HELP_Assistant_pilot_an_AI_powered_support_for_UPI_payments_cd501de8f3.pdf).

### Account Aggregator

The Government of India's Account Aggregator framework transfers financial information only with explicit consent; Financial Information Users have regulatory participation requirements. This should not be treated as an ordinary API key integration for a generic early-stage consumer app. [Department of Financial Services AA framework](https://www.financialservices.gov.in/account-aggregator-framework) · [Sahamati FIU/FIP materials](https://sahamati.org.in/).

### Browser extension with broad website permissions

A browser extension could capture order/refund data, but broad host permissions on arbitrary shopping/banking sites raise privacy risk and increase Chrome Web Store review burden. Start with a limited PWA share target, file upload and user-provided links. [Chrome Web Store review guidance](https://developer.chrome.com/docs/webstore/review-process).

### Automatic filing or sending

Do not automatically submit a complaint, send emails to a guessed grievance officer, or label a draft “sent”. If a submission integration is ever added, it must be authorised, destination-verified and user-approved with a clear receipt.

---

## 10. Proposed 30-day build plan

### Week 1 — Design and groundwork

- Add Share-to-Case to the PWA manifest and a private staging/confirmation flow.
- Implement server-side validation, one-use staging IDs and short expiry.
- Keep ordinary upload working for unsupported platforms.

### Week 2 — Official Route Intelligence

- Build a dated snapshot of the NCH convergence directory and alias matching for the existing priority merchants.
- Expand the support directory to include source date, exact official brand/legal entity, first-party support contact and route confidence.
- Add an explicit “no match found in last-checked snapshot” state and human-reviewed update workflow.

### Week 3 — Rules-as-code

- Introduce rule IDs, effective dates, predicates and source metadata.
- Add test cases for UPI transfer versus merchant-side payment, delayed merchant refund, fraud/unauthorised debit and missing facts.
- Add a timeline that separates next-check suggestions from actual official deadlines.

### Week 4 — Test with real workflows

- Run at least 15 usability sessions using fictional examples first and consenting real cases only after security/privacy review.
- Measure time from “I have a problem” to correct first action, missing-document rate at first support contact, correct-route rate, successful Share-to-Case capture and user comprehension of the deadline labels.
- Do not use “refund recovery rate” as an early headline metric until outcomes are independently defined and enough cases are observed.

---

## 11. Success metrics

| Metric | Definition | Why it matters |
|---|---|---|
| Time to first useful action | Start of intake to a source-backed recommended action | Measures friction and speed |
| Share-to-case completion | Shared items that reach a user-confirmed case/evidence attachment | Measures the integration's actual adoption |
| First-contact completeness | Cases where the relevant required fields/evidence are present before first support contact | Measures avoidable back-and-forth |
| Correct-route rate | Reviewer-validated cases routed to the appropriate channel | Measures system correctness |
| Uncertain facts correctly labelled | Sampled facts that preserve unverified/user-reported status | Measures trustworthy provenance |
| Follow-up completion | Users completing a suggested next action after a user-controlled reminder | Measures follow-through |
| Verified resolution rate | Separate self-reported outcomes from outcomes supported by an authorised source | Avoids overstating results |

## Final decision

Build **Share-to-Case**, **Official Route Intelligence**, and **Rules-as-code** next. These are technically substantial, fit the current FastAPI/PWA architecture, and improve the original value proposition without adding an extra product layer. The first removes friction, the second improves destination choice, and the third prevents the app from recommending the wrong process or displaying an incorrect timeline.

The Case Inbox Bridge is already implemented in code but requires a real inbound domain/provider and a privacy/retention review. Merchant/bank connections should remain a formal partnership objective, not an assumed capability. No feature can guarantee a refund; the product can only shorten avoidable delay and improve the user's ability to take the correct next step.

---

## Research sources

The following public pages were used to ground this assessment. Official sources take precedence for regulatory/payment claims. Competitor websites describe their own advertised features and are not independently verified outcome data.

### Indian payment and grievance systems
1. [NPCI — UPI HELP pilot circular](https://www.npci.org.in/uploads/UPI_OC_No_227_FY_2025_26_Introduction_of_UPI_HELP_Assistant_pilot_an_AI_powered_support_for_UPI_payments_cd501de8f3.pdf)
2. [NPCI — UPI FAQ](https://www.npci.org.in/what-we-do/upi/faqs)
3. [RBI — Failed transaction TAT / compensation circular](https://www.rbi.org.in/commonman/Upload/English/Notification/PDFs/CIRCULAR677EC931A7A65E4D99AA957D8E85BC0A2A.PDF)
4. [RBI — Integrated Ombudsman Scheme 2026 FAQ](https://old.rbi.org.in/commonman/english/scripts/faqs.aspx?id=3407)
5. [Department of Consumer Affairs — National Consumer Helpline](https://consumeraffairs.gov.in/pages/nch)
6. [National Consumer Helpline — Convergence Program](https://www.consumerhelpline.gov.in/public/convergenceprogram)
7. [National Consumer Helpline — Convergence Partners](https://consumerhelpline.gov.in/public/convergencepartners)
8. [National Consumer Helpline — Company registration requirements](https://consumerhelpline.gov.in/public/convergencepartnersreq)
9. [PIB — Consumer Protection (E-Commerce) Amendment Rules, 2026](https://www.pib.gov.in/newsite/erelcontent.aspx?lang=2&reg=48&relid=294532)
10. [NIC — e-Jagriti overview](https://www.nic.gov.in/project/e-jagriti-a-unified-digital-platform-for-consumer-justice/)
11. [National Government Services Portal — postal-service complaint](https://services.india.gov.in/service/detail/lodge-your-complaint-for-postal-services-1)
12. [India Post — contact and complaint routes](https://www.indiapost.gov.in/contactus)
13. [Government of India — Account Aggregator Framework](https://www.financialservices.gov.in/account-aggregator-framework)
14. [Sahamati — Account Aggregator ecosystem](https://sahamati.org.in/)
15. [PIB — DPDP Rules 2025](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2190014&lang=1&reg=3)
16. [DigiLocker / API Setu — partner API access](https://api.apisetu.gov.in/)

### Competitors and current consumer refund workflows
17. [RefundPe](https://refundpe.com/)
18. [Nyaykar](https://www.nyaykar.in/)
19. [Voxya](https://voxya.com/)
20. [Amazon — check refund status](https://digprjsurvey.amazon.com/csad/help/node/GMP8PC8KBY5FCPM2)
21. [NCH — Consumer App](https://consumerhelpline.gov.in/apps/consumerapp/)

### Platform and integration documentation
22. [MDN — PWA `share_target` manifest member](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Manifest/Reference/share_target)
23. [MDN — Web Share API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Share_API)
24. [Android Developers — receive shared content](https://developer.android.com/develop/ui/compose/sharing/receive)
25. [Postmark — inbound email webhook](https://postmarkapp.com/developer/webhooks/inbound-webhook)
26. [Postmark — inbound/outbound retention behaviour](https://postmarkapp.com/support/article/how-long-are-inbound-and-outbound-messages-stored-in-activity)
27. [Google — Gmail API scopes](https://developers.google.com/workspace/gmail/api/auth/scopes)
28. [Microsoft Graph — email change notifications](https://learn.microsoft.com/en-us/graph/change-notifications-delivery-webhooks)
29. [Chrome Web Store — extension review process](https://developer.chrome.com/docs/webstore/review-process)

### Security and responsible AI
30. [OWASP — File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
31. [OWASP — LLM Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
32. [OWASP — AI Agent Security](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)
33. [OWASP — RAG Security](https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html)
34. [PIB — DPDP framework principles and phased implementation](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2294910&lang=1&reg=3)

### Product design and UX
35. [GOV.UK Design System — Summary list](https://design-system.service.gov.uk/components/summary-list/)
36. [W3C — Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/)

**Limitations:** This is a source-based product and integration review, not legal advice, a security audit, or proof that third-party integrations are approved. Provider API capabilities, regulatory rules and merchant contact details must be rechecked before implementation/launch. Feature scores and expected outcomes are hypotheses to validate with users.
