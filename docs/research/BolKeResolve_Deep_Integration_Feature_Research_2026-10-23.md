# BolKeResolve — Deep Integration Feature Research

**Research date:** 23 October 2026  
**Product baseline inspected:** `BolKeResolve_Frontend_Visual_Alignment_2026-10-22.zip`  
**Purpose:** Find unusually valuable, deeply integrated features that can be added incrementally to the existing voice-first product without turning it into a sprawling complaint-management platform.

> **Recommendation in one sentence:** Build a **Living Resolution Passport**—a case that continuously connects the user's spoken story, documents, support replies, official rules and next action—starting with a local evidence compiler and a case-specific inbound email bridge, not direct bank access or a new microservice architecture.

---

## 1. Executive decision

BolKeResolve should preserve its original job: make it easy for an Indian consumer to explain a payment or refund problem, understand a sensible next step, prepare what they need, and retain a concise case record. The next significant improvement should not be more tabs or a general-purpose complaint bot. It should make the *existing case materially smarter* by connecting its inputs and outputs.

The largest product opportunity is a single case object that can answer:

1. **What do we know?** Facts extracted from the user's story, files, and replies.
2. **Where did each fact come from?** User-reported, extracted from a particular page/message, confirmed by the user, or verified by a permitted external integration.
3. **What is missing or inconsistent?** E.g. the order email says ₹850 but a screenshot says ₹580; a refund is described as initiated but not credited; the merchant reply requests an invoice that has not been attached.
4. **What is the correct next step for this issue type?** Select from a dated, source-backed rulebook, not a free-form legal guess.
5. **What happened after the user acted?** A draft is not a sent message; a provider delivery receipt is not a recipient acknowledgement; a user-reported refund is not independently verified.

Call this the **Living Resolution Passport**. It is a product experience and data model—not another product area in the navigation. Keep the user's screen concise; put the complex logic behind one recommended action.

### Why this is the best fit

The current code already gives BolKeResolve a strong starting point:

- FastAPI modular monolith, vanilla JS frontend, SQLite storage.
- Gnani speech-to-text path and optional text-to-speech path.
- Editable transcription and confirmation of extracted facts.
- Deterministic, source-linked issue playbooks in `backend/resolution.py`.
- Evidence upload endpoint in `backend/main.py` with file-type signature and size checks, but no actual OCR pipeline in that endpoint.
- Evidence metadata and case timeline.
- Reply-review preview/confirm flow which stores a confirmed interpretation instead of the pasted raw support reply.
- Action-pack generation, Resolution Passport export, follow-up fields, WhatsApp provider adapters and status events.

This means the easiest path is to connect what is already present, rather than rewrite the app or add agents, microservices, bank connections, a legal-services marketplace, or a new social network.

---

## 2. Product and competitive facts that affect the opportunity

### Existing products already cover many isolated features

- **UPI HELP:** NPCI's October 2025 pilot describes payment queries, transaction-status checks and complaint tracking for supported scenarios/participants; it also discusses mandate management. This means “voice chatbot for UPI” alone is not sufficiently differentiated, and a general developer should not assume open unrestricted access to the pilot's underlying integrations. Source: [NPCI UPI HELP pilot circular](https://www.npci.org.in/uploads/UPI_OC_No_227_FY_2025_26_Introduction_of_UPI_HELP_Assistant_pilot_an_AI_powered_support_for_UPI_payments_cd501de8f3.pdf).
- **National Consumer Helpline (NCH):** already offers registration through web, app, UMANG, phone, SMS and WhatsApp across 17 languages, plus complaint docketing and a convergence program with 2,000+ organisations. BolKeResolve should prepare users for this system and eventually hand off through approved routes, not claim it has replaced NCH. Sources: [NCH](https://consumeraffairs.gov.in/pages/nch), [NCH Convergence Program](https://consumerhelpline.gov.in/public/convergenceprogram).
- **e-Jagriti:** supports consumer-commission filing and case management, document management, status tracking and notices. BolKeResolve should focus on getting the user and their evidence ready, and only later integrate if an approved interface exists. Source: [NIC e-Jagriti overview](https://www.nic.gov.in/project/e-jagriti-a-unified-digital-platform-for-consumer-justice/).
- **RefundPe:** publicly advertises complaint drafting, user-approved sending, follow-up and regulator packs. Therefore those features alone are not a defendable unique advantage. Source: [RefundPe](https://refundpe.com/).
- **Nyaykar:** publicly advertises authority routing, Indian-language-to-formal-letter conversion, a complaint strength score and follow-ups. “AI router” or a numeric “strength score” alone is not enough. Source: [Nyaykar](https://www.nyaykar.in/).
- **Voxya:** provides consumer complaint escalation services. Source: [Voxya](https://voxya.com/).

### A current policy shift creates a future integration opportunity, but not an open API

The Department of Consumer Affairs announced that the Consumer Protection (E-Commerce) (Amendment) Rules, 2026 take effect on **1 January 2027** and require e-commerce entities to partner in the NCH convergence process. The release says NCH received 5,11,196 e-commerce grievances during 2025. This is a strong reason to explore merchant-side resolution handoffs as a long-term business opportunity—but it does **not** mean a student project can access NCH's internal case system automatically. NCH's partner registration asks for company identity, senior contacts, company-domain email, authorization and undertaking documents. Sources: [PIB announcement](https://www.pib.gov.in/newsite/erelcontent.aspx?lang=2&reg=48&relid=294532), [NCH partner registration requirements](https://consumerhelpline.gov.in/public/convergencepartnersreq).

### Official routing needs version control

The RBI's **Integrated Ombudsman Scheme 2026** took effect on 1 July 2026 and replaces the 2021 scheme for new matters, while specified older matters remain under prior rules. Coverage and admissibility are conditional; it is not a universal refund route. Source: [RBI Scheme FAQ, updated 1 July 2026](https://old.rbi.org.in/commonman/english/scripts/faqs.aspx?id=3407).

The RBI's failed-transaction framework distinguishes a UPI funds transfer where a beneficiary is not credited from a merchant payment where confirmation is not received. The referenced framework specifies T+1 and T+5 timelines for those respective categories, not for every merchant refund. Source: [RBI failed-transaction TAT circular](https://www.rbi.org.in/commonman/Upload/English/Notification/PDFs/CIRCULAR677EC931A7A65E4D99AA957D8E85BC0A2A.PDF).

This is why the rulebook should become testable data with effective dates and scenario predicates, not just prose in a prompt.

---

## 3. Six features ranked by value and buildability

Scores are relative product estimates, not measured user outcomes. “Buildability” is higher when the first version can ship without a third-party approval or direct financial integration.

| Rank | Feature | Consumer value | Differentiation | First version buildability | Requires partner? | Recommendation |
|---:|---|---|---|---|---|---|
| 1 | **Living Resolution Passport / Evidence Graph** | Very high | High when connected end-to-end | Medium | No for MVP | Core technical direction |
| 2 | **Case Inbox Bridge** (forward/CC support replies to a case) | High | Medium-high when paired with state updates | Medium-high | Email provider + domain, not a bank | Build after the evidence pipeline foundation |
| 3 | **Source rules as code + eligibility checks** | Very high for trust/accuracy | High when tested and kept current | Medium | No | Build alongside #1 |
| 4 | **Case Preflight / missing-evidence checker** | High | Medium | High | No | First visible part of #1 |
| 5 | **One-click official-channel handoff** | Medium-high | Medium | High with copy/open/export only | No for a safe first version | Add after packet reliability |
| 6 | **Merchant Resolution Bridge** with acknowledgements/status | Potentially very high | Very high if real two-way integration is obtained | Low without partner | Yes | Partnership track, not MVP blocker |

### Avoid for now

- **Direct account aggregation / automatic bank statement access:** the Government's Account Aggregator framework says financial information is shared with explicit customer consent, but Financial Information Users must be registered and regulated by a financial-sector regulator. This is not an easy “just add an API” feature for a generic consumer app. Use user-uploaded statements first; investigate an authorised partner only if the product has demonstrated need. Source: [Department of Financial Services — Account Aggregator Framework](https://www.financialservices.gov.in/account-aggregator-framework) and [Sahamati participation steps](https://sahamati.org.in/fip/).
- **DigiLocker transaction-receipt imports:** DigiLocker requester access requires onboarding, agreements, technical vetting, testing and approval; most payment screenshots and merchant emails will not be DigiLocker-issued documents anyway. Not a first integration. Sources: [DigiLocker partner API onboarding](https://api.apisetu.gov.in/), [DigiLocker implementation model](https://www.digilocker.gov.in/web/implementation-model).
- **Full Gmail mailbox reader:** Gmail read-only scope is a restricted OAuth scope and can trigger verification and a security assessment when restricted data is stored/transmitted. The more direct first step is an explicit forward/CC case address. Sources: [Gmail API scopes](https://developers.google.com/workspace/gmail/api/auth/scopes), [restricted-scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification).
- **“AI refund probability” or “complaint strength 0–100”:** without trustworthy labelled outcome data and validation this could create false confidence. Prefer an explainable “ready / missing information / conflicting facts” check, which can be directly justified.
- **Automatic filing or contacting authorities without a real approved integration:** opening a portal or generating a draft is not submission. Preserve a human review and action receipt.
- **Microservices / Temporal in the first step:** the present FastAPI + SQLite application can add a couple of clearly bounded modules. Durable workflow infrastructure such as Temporal is powerful for multi-month workflows, callback retries and recovery, but it adds operational overhead. Add it only when actual partner callbacks and reliable scheduling outgrow a simple tested worker. Source: [Temporal delayed-callback pattern](https://github.com/temporalio/documentation/blob/main/docs/design-patterns/delayed-callback.mdx).

---

## 4. Feature 1 — Living Resolution Passport: one case that understands all its inputs

### What it is

Every important claim in a case becomes a structured fact linked to its origin. Example:

```json
{
  "fact_key": "amount",
  "value": 850,
  "currency": "INR",
  "source_type": "uploaded_document",
  "source_id": "evidence_123",
  "source_locator": {"page": 1, "text_span": "Total paid ₹850"},
  "status": "extracted_needs_confirmation",
  "confirmed_by_user_at": null
}
```

The displayed record remains simple. The internal structure supports:

- facts from the spoken story;
- facts extracted from PDFs/images/emails;
- facts the user explicitly confirms or edits;
- official rules and source versions used to select an action;
- support replies and user-confirmed response classifications;
- action receipts (drafted, user marked sent, provider delivered, recipient acknowledged, user reported resolved, integration verified).

It should be a small graph of `fact ↔ source ↔ event ↔ rule ↔ next action`, not a graph database product. Start with relational tables and JSON metadata inside the current modular monolith.

### Why it is hard—and how to make it easy

The hard part is not OCR. The hard part is safely preserving provenance as information flows from speech to documents to rule evaluation to export. Implement the pipeline in small steps:

1. Create a common internal `FactCandidate` schema.
2. Let existing text extraction populate it.
3. Add PDF text extraction first; only OCR when the PDF/image has no usable text layer.
4. Present candidate facts in a confirmation panel with the document name and source location.
5. When two values disagree, show the conflict instead of silently choosing one.
6. Recalculate the resolution plan only from the user's confirmed values plus versioned rules.
7. Export the provenance labels and unresolved conflicts in the Resolution Passport.

### Example interaction

User says: “Merchant ne bola ₹850 refund initiate ho gaya.”

They upload an email that reads “Refund initiated: ₹850” and a bank screenshot with no matching credit visible.

BolKeResolve should say:

- **Merchant response:** the uploaded email says the refund was initiated — source: email, user to confirm.
- **Credit status:** not yet confirmed by a bank record — source: user report / provided screenshot.
- **Conflict:** none on amount, but “initiated” is not the same as “credited.”
- **Next step:** record the stated refund date/reference and select the correct merchant/payment route before creating a follow-up.

It must not claim the email is authentic, the transaction has been verified, or a refund is guaranteed.

### Implementation choices

- For native digital PDFs, use text extraction before OCR.
- For scanned PDFs and images, prototype an OCR adapter. Options include [OCRmyPDF/Tesseract](https://github.com/ocrmypdf/OCRmyPDF) for searchable PDFs and [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) or [Docling](https://github.com/docling-project/docling) for broader document parsing. Docling supports diverse file formats and local execution; PaddleOCR has active document parsing and multilingual OCR work. Benchmark against real redacted Indian payment screenshots before choosing a model; do not accept vendor benchmark numbers as your product's accuracy. Sources: [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF), [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR), [Docling](https://github.com/docling-project/docling).
- Store extracted text with minimum retention; prefer source pointer + candidate facts over duplicating the entire document text in several tables.
- Treat OCR output, emails and PDF text as **untrusted data**, never as instructions for the application or an AI agent. Tool access and state changes must be validated in code, and high-impact actions require user approval. Sources: [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html), [OWASP LLM Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html).

### Acceptance criteria

- User can inspect what value was extracted and where it came from.
- No fact silently overwrites a user-confirmed value.
- Conflicting values produce a conflict item, not a hidden auto-resolution.
- Each recommended route has source ID, source URL, review/effective date and explicit applicability predicates.
- Upload rejection covers extension, magic bytes, file size, ownership, storage outside public web root, and malware scanning/quarantine before extraction.
- Export shows which facts are user-reported, document-extracted, user-confirmed or verified through a specific integration.

---

## 5. Feature 2 — Case Inbox Bridge: connect real support replies without reading the user's whole mailbox

### The user problem

Today, a user gets a reply in email, returns to BolKeResolve, pastes the message into reply review, confirms an interpretation, and then updates their next step. That is a reasonable privacy-first first version, but it creates friction and the case can go stale.

### The smallest genuinely useful integration

Give each case a unique, opaque inbound email address. Example format only: `case-<random-token>@reply.example.com`.

When preparing a support email, the app can optionally display “CC this case address to keep replies together.” The user can also forward a received reply to the address. The address should map to a stored hash/token—not embed a predictable case ID. An inbound email service converts email/MIME content and attachment metadata into a JSON webhook; Postmark documents this flow and supports parsed messages and attachments. Source: [Postmark inbound webhook](https://postmarkapp.com/developer/webhooks/inbound-webhook), [email parsing](https://www.postmarkapp.com/developer/user-guide/inbound/parse-an-email).

### Safe flow

1. User explicitly enables email reply intake for a chosen case and sees what will be captured.
2. BolKeResolve creates a random per-case alias and states that emails sent/forwarded there will be processed for this case.
3. The inbound webhook validates a secret/shared-auth mechanism, checks the alias token, applies quotas and deduplicates by provider message ID.
4. The service extracts body text and allowlisted attachment metadata; files go to a private quarantine/scan path.
5. The user sees a review screen: “This reply appears to request an invoice” / “This says refund initiated” / “This appears to reject the request.”
6. Only after confirmation is the short interpretation added to the timeline, relevant missing evidence updated, and a next action recalculated.
7. Raw inbound email is deleted according to an explicit retention policy unless the user deliberately saves the original as case evidence.

### Why forwarding is easier than Gmail OAuth

Postmark-style inbound processing can be added with one provider adapter, a public HTTPS webhook, DNS/domain setup and careful token design. It avoids reading the user's entire mailbox. Full Gmail API access requires sensitive/restricted scopes, app verification, and potentially security assessment for stored/transmitted restricted data. Sources: [Postmark inbound webhook](https://postmarkapp.com/developer/webhooks/inbound-webhook), [Gmail scopes](https://developers.google.com/workspace/gmail/api/auth/scopes), [Google restricted-scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification).

### Don't do these things

- Don't auto-classify a reply as “refund paid” based on a single phrase.
- Don't trust sender display names or email subject lines as proof of sender identity.
- Don't execute instructions contained in inbound email or attachments.
- Don't save the full email in the event timeline by default.
- Don't attach or distribute files before validation/scanning.
- Don't imply an acknowledgement from BolKeResolve is acknowledgement from the merchant.

### Acceptance criteria

- Inbound alias token is unguessable, revocable and not the case database ID.
- Webhook is HTTPS-only, authenticated, rate-limited, deduplicated, size-limited and replay-safe.
- Inbound messages are untrusted input and do not change a case without review.
- Duplicate webhook deliveries never create duplicate timeline events.
- Attachments pass type/signature/size and malware/quarantine controls before parsing or opening.
- Raw message retention and deletion are visible to the user and tested.

---

## 6. Feature 3 — Resolution Rulebook as Code

Currently the deterministic resolution module includes source metadata and `reviewed_on`, which is a good foundation. Evolve it into a registry that supports effective dates, issue predicates, jurisdiction/organisation coverage, official sources, and scenario tests.

### A rule record should specify

- unique rule ID and version;
- issue type and exact scenario predicates;
- excluded/ambiguous scenarios;
- action and user-facing rationale;
- official source title, URL and relevant section;
- publication/effective date and “last reviewed” date;
- who approved the wording internally;
- test examples for positive matches, negative matches, missing data, and date boundaries.

### Avoid a hallucinated deadline engine

For example, the RBI 2026 Ombudsman route is for covered regulated entities and has admissibility rules; it is not the generic answer to every unreceived merchant refund. The failed-UPI-transfer and merchant-payment-confirmation situations also have distinct TATs under the relevant RBI framework. Treat those as separate testable rules. Sources: [RBI Scheme 2026 FAQ](https://old.rbi.org.in/commonman/english/scripts/faqs.aspx?id=3407), [RBI failed-transaction TAT](https://www.rbi.org.in/commonman/Upload/English/Notification/PDFs/CIRCULAR677EC931A7A65E4D99AA957D8E85BC0A2A.PDF).

### Lowest-overhead implementation

Use YAML/JSON files or relational tables first. Add tests that compare the old and new rules on a fixed case suite. Make the source registry a data layer read by the existing resolution engine. Do not build a web crawler that changes rules automatically. A monitor may alert the maintainer when a source changed, but a human must review the change before the production rule changes.

---

## 7. Feature 4 — Case preflight and one-click handoff

This feature becomes powerful after the first three exist.

Before the user contacts support or opens an official portal, compile a **ready-to-contact packet**:

- short chronology with exact dates and provenance;
- what the user is asking the organisation to do;
- missing information that is actually relevant to the route;
- attachment list with labels and redaction review;
- draft message with editable placeholders omitted unless confirmed;
- official destination and why it fits;
- next follow-up rule with its source and event that starts the clock;
- one compact status distinction: “draft prepared”, “user says submitted”, “email provider reports delivered”, “recipient acknowledges”, “status verified by authorised integration”, or “user reports resolved.”

For NCH/e-Jagriti/RBI portals in the first version, use **open official portal + reviewed/copyable field values + download packet**. Don't automate submission unless an authorised supported integration exists and the user sees/approves the complete submission. NCH already offers multiple official channels and docket tracking; e-Jagriti already offers filing and case management, so BolKeResolve should be a bridge into those systems, not a shadow copy of them. Sources: [NCH channels](https://consumeraffairs.gov.in/pages/nch), [NCH Convergence](https://consumerhelpline.gov.in/public/convergenceprogram), [e-Jagriti](https://www.nic.gov.in/project/e-jagriti-a-unified-digital-platform-for-consumer-justice/).

---

## 8. The deeply integrated architecture—without overengineering

Keep the current modular monolith. Introduce four modules behind existing API boundaries:

```text
Voice / text / uploaded file / forwarded reply
                    |
                    v
       Intake adapters (untrusted inputs)
                    |
                    v
     Extraction -> candidate facts + source locators
                    |
                    v
       User confirmation / conflict resolution
                    |
                    v
  Case event log + fact/provenance relationships
                    |
                    v
     Versioned, deterministic rulebook evaluator
                    |
                    v
  One recommended action + readiness/missing evidence
                    |
                    v
  User-reviewed draft / official handoff / follow-up
                    |
                    v
  User report or authenticated provider/partner event
                    |
                    └──────── updates the same case ────────┘
```

### Proposed modules

- `backend/evidence_ingestion.py`: MIME/type validation, document adapter selection, OCR/text extraction, candidate fact schema.
- `backend/case_intelligence.py`: merge confirmed facts, detect contradictions, compute missing information, label provenance.
- `backend/rule_registry.py`: versioned rule retrieval and tests; can initially wrap `resolution.py`.
- `backend/inbound_email.py`: validate inbound webhook, map opaque per-case alias, deduplicate, scrub, preview reply and route attachments to quarantine.
- Keep `backend/action_pack.py`, `backend/passport.py`, `backend/messaging.py`, and `backend/resolution.py` as the existing downstream services; refactor only where required.

### Data model sketch

- `facts`: fact ID, case ID, field key, typed value, status, created/updated times.
- `fact_sources`: fact ID, source type, evidence/event ID, page/text locator, extraction method, confidence if measured, user-confirmed timestamp.
- `case_events`: append-oriented events with idempotency key, event type, actor, channel, source/provenance, minimal metadata.
- `source_rules`: rule ID/version, applicability predicate, effective date range, source URL, reviewed timestamp, status.
- `inbound_aliases`: case ID, hash of random alias token, created, expiry/revoked state, retention setting.
- `inbound_messages`: provider ID, dedupe key, case ID, minimal metadata, preview/deletion state; avoid retaining raw body by default.
- `evidence_processing_jobs`: queued/running/completed/failed state, safe error, retry count, model/tool versions.

Do not require a graph database. SQLite can support an early pilot. Before public scale, move to a durable managed database and object storage with private access, backups, restoration tests and deletion semantics.

---

## 9. The genuinely ambitious partner idea: a Merchant Resolution Bridge

The long-term moat is not only consumer-side AI. It is a structured two-way handoff with one participating merchant or support provider:

1. BolKeResolve compiles a user-approved case packet.
2. A partner endpoint receives the packet in an agreed schema.
3. The partner returns an authenticated ticket ID and acknowledgement.
4. Later webhook events return state changes.
5. BolKeResolve updates the timeline and chooses the next action from a controlled event/state model.

This could reduce copying and lost reference numbers. However, the publicly available NCH Convergence programme currently describes organisation registration and company documents rather than an open public consumer-complaint API. The e-commerce amendments take effect on 1 January 2027 and require e-commerce entities to join NCH convergence; they do not grant an arbitrary startup direct access to the convergence system. Sources: [PIB E-Commerce Rules amendment](https://www.pib.gov.in/newsite/erelcontent.aspx?lang=2&reg=48&relid=294532), [NCH registration](https://consumerhelpline.gov.in/public/convergencepartnersreq), [NCH partner list](https://consumerhelpline.gov.in/public/convergencepartners).

**Practical way to start:** find one willing merchant, university consumer-support office, or small service platform. Agree on one use case, one ticket-creation endpoint and three event types: received, additional-information-requested, resolved/rejected. Don't build a generalized integration marketplace before one partner works end to end.

---

## 10. Build order: the easiest path to the deeply integrated result

### Sprint 0 — Freeze scope and define events (2–3 days)

- Preserve the current simple user flow and three issue starts.
- Define precise status semantics and event IDs.
- Add fixed test fixtures for failed transfer, merchant payment failure, delayed refund, unauthorised payment and duplicate charge.
- Add schema for source-linked facts; do not redesign the navigation.

### Sprint 1 — Case preflight / Resolution Compiler MVP (1–2 weeks)

- Parse digital PDF text first; expose extraction adapter for images.
- Map extracted candidates to fact schema and let user confirm.
- Highlight amount/date/reference conflicts.
- Render “ready to contact” with three states: ready, missing required information, conflict to review.
- Export the source/provenance and missing-evidence status in the Resolution Passport.
- Start with redacted synthetic files; benchmark against at least 50 representative screenshots/PDFs before calling it reliable.

### Sprint 2 — Case Inbox Bridge (1–2 weeks plus provider setup)

- Choose an inbound email service and configure DNS/domain.
- Generate a random per-case alias and store only a secure token hash.
- Add authenticated webhook, size/attachment limits, rate limit, dedupe and quarantine.
- Inbound email -> preview -> user confirms interpretation -> timeline event -> recompute next step.
- Test duplicate webhook, wrong alias, forwarded reply, malicious attachment, oversized email, spam and revocation.

### Sprint 3 — Source rules and workflow state (about 1 week)

- Move source metadata and predicates into versioned rules.
- Add a manual review queue/CLI report for stale links or rules overdue for review.
- Re-run scenario tests on every rule update.
- Keep actions deterministic; LLMs may extract/interpret but cannot determine legal eligibility without a rule predicate.

### Sprint 4 — User pilot and one partner discovery track (2–4 weeks)

- 15–20 observed usability sessions with people who recently had a stuck payment/refund.
- Use synthetic test data first; handle any real data only with clear consent, secure storage and a reviewed retention policy.
- Measure correct route rate, fact-correction rate, first-contact completeness, task completion and reported outcomes.
- Separately speak to a possible merchant partner. No partner? Keep the consumer product valuable without it.

Estimated time ranges assume one developer familiar with the current code and do not include provider onboarding delays, production legal/security review or external partnership timelines.

---

## 11. Security, privacy and model-boundary requirements

The deeper the integrations, the more important these become:

- Treat PDF text, screenshots, email bodies, OCR output and user prompts as untrusted data. A document can contain malicious prompt instructions; extraction output never gets tool execution privileges. OWASP recommends layered prompt-injection controls, permission enforcement outside the model, and approval for consequential actions. Source: [OWASP prompt-injection prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html).
- Validate file type by content signature as well as extension; cap sizes and quotas; create app-generated names; keep uploads outside the public web root; scan/quarantine before parsing; authorize every file access. Source: [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html).
- Minimise raw data retained. Don't request a whole Gmail inbox when forwarding one relevant reply is enough. Google treats Gmail read-only as a restricted scope and may require verification and a security assessment for stored/transmitted restricted data. Sources: [Gmail scopes](https://developers.google.com/workspace/gmail/api/auth/scopes), [restricted-scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification).
- India’s DPDP Act/Rules have phased commencement dates. Build to data minimisation, purpose limitation, notice/consent, deletion and security now; have qualified counsel confirm the obligations effective on the actual launch date. Sources: [DPDP Rules 2025 Gazette](https://egazette.gov.in/WriteReadData/2025/267647.pdf), [PIB summary](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2190014&lang=2&reg=3).
- Distinguish draft created, email accepted by provider, delivery reported, recipient acknowledgement, and user-reported resolution. Do not treat any one of these as another.
- Never ask for OTPs, UPI PINs, passwords, or full card credentials. Keep suspected fraud on a separate urgent route.
- Ensure users can revoke an inbound email address and delete case data; document provider copies, backups and retention limitations honestly.

---

## 12. Metrics and acceptance tests

Do not measure success by number of features or AI words generated. Use tests that show the integrated loop works.

### Product metrics

- Median time from start to a correct, user-approved next action.
- Percentage of cases with all facts needed for the recommended route confirmed.
- OCR/extraction precision for transaction reference, amount, date and party; user correction rate for each field.
- Contradiction detection precision (especially different amounts/dates/references).
- Share of support replies correctly classified after user confirmation.
- First-contact completeness as rated by a trained reviewer or user.
- Follow-up completion and case state transition reliability.
- User-reported resolution and, separately, provider-/partner-verified resolution.

### Technical acceptance tests

- Duplicate inbound email webhook does not duplicate a timeline event.
- An alias that is revoked/expired cannot add events.
- An email or file cannot mutate a case without an explicit user confirmation.
- OCR extraction links each candidate to the correct evidence item/page; if not, it marks it as unlocated.
- If a document contradicts a user-confirmed fact, preserve both sources and ask the user; do not silently overwrite.
- Rule tests cover effective-date boundaries, unsupported entities, missing facts and emergency fraud routing.
- If a source is stale/unavailable, show the last reviewed date and avoid presenting the route as freshly verified.
- Raw email body and unconfirmed extraction candidates expire under the disclosed retention policy.
- An exported passport distinguishes reported facts from independently verified events.

### First pilot success criteria

Set the baseline first. As a provisional target, at least 80% of test participants should be able to explain their next step unaided; no critical test scenario should route suspected fraud through the routine refund flow; and any material extraction error should remain visible until corrected. Do not claim the tool increases refund rate or reduces resolution time until a real comparison supports it.

---

## 13. Official and technical source library

The following are the most decision-relevant pages reviewed for this recommendation. Vendor documentation describes available capabilities; it does not independently prove production suitability for BolKeResolve.

### India payments and grievance system

1. [NPCI UPI HELP pilot circular (8 Oct 2025)](https://www.npci.org.in/uploads/UPI_OC_No_227_FY_2025_26_Introduction_of_UPI_HELP_Assistant_a_pilot_an_AI_powered_support_for_UPI_payments_cd501de8f3.pdf)
2. [RBI — Integrated Ombudsman Scheme 2026 FAQ](https://old.rbi.org.in/commonman/english/scripts/faqs.aspx?id=3407)
3. [RBI — failed transaction turnaround time framework](https://www.rbi.org.in/commonman/Upload/English/Notification/PDFs/CIRCULAR677EC931A7A65E4D99AA957D8E85BC0A2A.PDF)
4. [National Consumer Helpline](https://consumeraffairs.gov.in/pages/nch)
5. [NCH Convergence Program](https://consumerhelpline.gov.in/public/convergenceprogram)
6. [NCH Convergence partner registration](https://consumerhelpline.gov.in/public/convergencepartnersreq)
7. [NCH partner directory](https://consumerhelpline.gov.in/public/convergencepartners)
8. [PIB — 2026 e-commerce amendment effective 1 Jan 2027](https://www.pib.gov.in/newsite/erelcontent.aspx?lang=2&reg=48&relid=294532)
9. [e-Jagriti — NIC overview](https://www.nic.gov.in/project/e-jagriti-a-unified-digital-platform-for-consumer-justice/)
10. [e-Jagriti help documents](https://e-jagriti.gov.in/help-docs)
11. [National Cyber Crime Reporting Portal](https://cybercrime.gov.in/)

### Competitor/adjacent product references

12. [RefundPe](https://refundpe.com/)
13. [Nyaykar](https://www.nyaykar.in/)
14. [Voxya](https://voxya.com/)
15. [Consumer Protection UK](https://www.consumerprotection.org.uk/tools)

### Email, identity and integration primitives

16. [Postmark inbound webhook](https://postmarkapp.com/developer/webhooks/inbound-webhook)
17. [Postmark inbound email parsing](https://www.postmarkapp.com/developer/user-guide/inbound/parse-an-email)
18. [Google Gmail API scopes](https://developers.google.com/workspace/gmail/api/auth/scopes)
19. [Google restricted-scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification)
20. [Microsoft Graph mail change notifications](https://learn.microsoft.com/en-us/graph/outlook-change-notifications-overview?tabs=http)
21. [DigiLocker API Setu partner onboarding](https://api.apisetu.gov.in/)
22. [DigiLocker implementation model](https://www.digilocker.gov.in/web/implementation-model)
23. [Account Aggregator framework — Department of Financial Services](https://www.financialservices.gov.in/account-aggregator-framework)
24. [Sahamati — AA FIP participation steps](https://sahamati.org.in/fip/)
25. [Temporal delayed-callback design pattern](https://github.com/temporalio/documentation/blob/main/docs/design-patterns/delayed-callback.mdx)

### Document processing, security and trustworthy AI

26. [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF)
27. [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
28. [Docling](https://github.com/docling-project/docling)
29. [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
30. [OWASP LLM Prompt Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
31. [DPDP Rules 2025 — Gazette notification](https://egazette.gov.in/WriteReadData/2025/267647.pdf)
32. [PIB — DPDP Rules overview](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2190014&lang=2&reg=3)
33. [Gnani AI challenge page](https://www.gnani.ai/internship)

---

## Final recommendation

**Build one connected system: the Living Resolution Passport.** Start by turning evidence into confirmed, source-linked facts and a useful preflight. Then add an opt-in case-specific inbound email route so real support replies update the same case after user review. Both feed the existing deterministic source rulebook and concise next-action card. After this works for a real pilot, seek one merchant-side integration.

This is ambitious because it integrates multiple data sources, state changes and external workflows. It remains easy to build incrementally because it reuses the current FastAPI, SQLite, evidence, timeline, action-pack, reply-review and Passport modules. It does not require direct UPI/bank access, Gmail-wide permissions, a new frontend framework or a microservice platform to begin.

The product should be judged by whether it eliminates repetition, prevents missing/conflicting facts from being hidden, and helps users take the correct next action—not by how autonomous or complex the system appears.
