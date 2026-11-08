# BolKeResolve — Product Audit, Competitor Scan, and Competition Roadmap

**Audit date:** 17 October 2026  
**Target:** Great Indian AI Internship Challenge by Gnani AI  
**Submission deadline:** 10 November 2026, 11:59 PM IST

## Executive recommendation

BolKeResolve has a working local application shell: voice capture and an STT client are wired, cases can be stored in SQLite, evidence can be uploaded, notes can be added, and English/Hindi support-message drafts can be generated. The local CRUD flow passed a smoke test.

It is not yet the complete product we intend to demonstrate. The main missing capability is the product's promise: turn a person’s messy, spoken payment story into a **safe, source-backed, issue-specific next-step plan**, then help them prepare the right evidence and keep track of follow-up. Today's draft is a template, the in-site “WhatsApp-style” flow is scripted, and the app does not check transaction status or contact a bank/merchant.

**Recommended positioning:** “A voice-first Indian-language payment-resolution companion that turns a confusing payment story into a documented, source-backed next step—without asking for sensitive credentials or pretending to verify a payment.”

Do not rewrite the frontend stack or build a real WhatsApp Cloud API integration before the core journey works. Make one golden scenario excellent, test it with real Gnani calls, and document exactly what is real versus simulated.

## 1. What is already implemented

| Area | Current state | What remains |
|---|---|---|
| Public site and page flow | HTML/CSS site with home, intake, case list, case detail, and WhatsApp-style intake views | Consolidate the two stylesheets and test key mobile/accessibility states |
| Voice capture | Browser records audio, encodes WAV and posts it to the backend | Live API test, amount/date transcription tests, better audio worklet/resampling, cancellation and error states |
| Speech-to-text | Prisma v2.5 REST request wired in `backend/main.py` | Verify credentials, request schema, supported languages, errors and real output |
| Text-to-speech | Timbre v2.5 endpoint wired for speaking drafts | Verify a live call; make selected language and voice consistent |
| Case storage | SQLite tables for cases, evidence, and timeline | User/session ownership if deployed, lifecycle status, richer transaction details |
| Evidence | Upload/download for PNG/JPG/WEBP/PDF, size and basic file-signature checks | Access control, malware scanning, retention/deletion policy, safer hosting |
| Support message | Template-based English/Hindi draft | Issue-specific next steps and a source-grounded recommendation before the draft |
| In-site chat | Canned prompts, heuristic issue classification, saves a case | Multi-turn guided intake; it is not currently AI-powered dialogue |
| WhatsApp | Opens a prefilled `wa.me` message; in-app flow is a simulated WhatsApp-style UI | No live two-way WhatsApp Business API/webhook exists |
| Test/production readiness | Windows launcher and README | Automated test suite, rate limits, observability, secure public deployment |

### Local smoke-test result

Using the extracted application and a temporary database, these local flows passed: `GET /api/health`, homepage response, case creation (`201`), case list, support draft (`200`), timeline note (`201`), evidence upload (`201`), evidence retrieval (`200`). This did **not** verify a live Gnani request or a real browser-rendered responsive experience.

### Practical maturity assessment (judgement, not a measured score)

- **As a prototype website:** around 6/10 — the main pages and local case mechanics are present.
- **Against the full product vision:** around 3–4/10 — contextual resolution guidance, source-grounded decisions, secure user-level case ownership and testing are still missing.

The interface is further along than the decision-making product logic.

## 2. Important code findings

Start with `README.md`, then `backend/main.py`, `frontend/app.js`, `frontend/index.html`, and both CSS files.

1. **No user authentication or per-user authorisation.** `/api/cases` lists every stored case and the evidence endpoint is not authenticated. This is acceptable only for a local synthetic-data prototype; do not expose the current build publicly with real case data.
2. **The current “assistant” is largely scripted.** In `frontend/app.js`, the WhatsApp-style flow returns fixed responses, classifies issues with keyword regexes and estimates language from English word matches. It does not use a model to conduct contextual follow-up questions.
3. **The next-step panel is generic.** The support draft uses a string template in `make_support_draft()`; it does not retrieve official guidance or choose a different workflow based on transaction type and status.
4. **Case statuses do not represent a full real lifecycle.** Statuses are updated for evidence/draft creation, but there is no user action or endpoint to mark “submitted,” “awaiting reply,” “needs more info,” or “resolved.” The open-case counter filters for a “Resolved by user” value that the current API does not set.
5. **The WhatsApp button is a handoff, not an integration.** It opens a generic prefilled message. The case intake conversation is not sent along as a live WhatsApp session.
6. **`DraftRequest` accepts `hinglish`, but `make_support_draft()` only has a distinct Hindi branch; other values fall through to the English template.** The UI currently exposes English/Hindi, but the API's accepted schema and implementation should agree.
7. **Storage configuration order needs correcting.** `BOLKE_DATA_DIR` is read before `load_dotenv()` is called, so setting it only in `.env` will not select that directory on import. Environment variables set in the shell do work.
8. **The JS is hard to maintain.** Many functions are compressed onto long single lines and all browser logic lives in `app.js`. Format it and split by responsibility only after the golden flow is stable; do not do a risky full rewrite.
9. **The two CSS files overlap.** `styles.css` and `design-v2.css` are both loaded, making selector precedence harder to reason about. Consolidate design tokens and duplicated media queries gradually.
10. **No project test suite is shipped.** Add repeatable tests around case data, drafts, transcript handling, source selection and status transitions before adding more features.

## 3. Competitive scan

These are public GitHub repositories whose READMEs identify them as Gnani challenge projects or use the challenge’s models. A public repository is not proof that the owner has submitted an official entry or that every advertised feature works. Repository size is a weak proxy for quality; the notes below rely on public descriptions, file structures, and selected tests, not a full clone-and-run evaluation.

| Project | Approx. repository size returned by GitHub | Problem and visible strengths | What BolKeResolve should learn |
|---|---:|---|---|
| [Kural](https://github.com/Mirdumurugesan/kural) | 8.3 MB | Tamil-first voice helpline for government schemes. README describes Prisma STT, Timbre TTS, Evon, source-grounded retrieval, escalation tickets, noisy-phone simulation, PII redaction, rate limiting, budget guard and admin routes. Public test files cover API, voice, escalation, privacy, rate limit and budget behavior. README claims 20/20 on a 20-question retrieval benchmark; that result is author-reported, not independently reproduced here. | The strongest engineering pattern in this scan: grounded answers, honest escalation, privacy controls, an evaluation harness and an actual demo. Use the pattern, not their code. |
| [SunoAI](https://github.com/neha-tanti/sunoai) | 773 KB | B2B call-quality tool for food-delivery/quick-commerce support calls. Product/technical documents are unusually detailed; report design includes red flags, checklist scores and exact transcript quotes, plus coaching audio. The README explicitly says pre-production/scaffold and that features are being built, so do not assume the full workflow is complete. | Make every recommendation provable: show the user’s facts and the exact official source behind each next step. Great example of documentation and defined non-goals. |
| [Kirana Voice Orders](https://github.com/sagar-grv/kirana-voice-orders) | 151 KB | Hinglish voice order flow: Prisma → deterministic parser → calculated total → Timbre confirmation. Contains parser tests with Hindi, English, native digits and multiple language samples. Catalog/data are described as synthetic; test presence is visible, but coverage claims are not independently measured here. | Keep financial fields deterministic and testable. Confirm extracted amounts and important details with the user instead of letting a free-form model invent them. |
| [KisanSetu](https://github.com/aniket25042005/kisan_setu_gnani_ai_challenge) | 54 KB | Vernacular farmer voice desk. README describes mandi prices, crop-health guidance, government schemes, acoustic test modes and Prisma/Timbre; backend separates Gnani client, reasoner and audio processing and includes a test script. “Live” data and agricultural recommendations were not independently verified. | Strong Real Deal story; narrow the promised workflow and be clear about data freshness and source. Avoid unsupported domain claims. |
| [Kavach](https://github.com/abhishek-pandey7/Kavach-Realtime-Voice-Threat-Intelligence) | 239 KB | Multilingual voice scam-threat detection intended to warn someone during a call, notify family and prepare a report. README calls it a working prototype in active development and describes staged/synthetic data. This is ambitious and high-impact, but it also has significant privacy, safety and real-time audio complexity. | A sharp problem story matters; keep scope realistic and make safety constraints explicit. |
| [gnani-voice-ops-line](https://github.com/Sivadheeraj5356/gnani-voice-ops-line) | 11 KB | Small Hinglish voice line for daily field-worker reports. One Python file, standard-library web server, mock mode for offline testing and deterministic report parser. The code intentionally leaves unmentioned fields empty rather than hallucinating operational numbers. | A compact, complete and safe journey is more convincing than many partially finished features. |
| [Samasya](https://github.com/DreadVoice/samasya) | 26 KB | Six voice-driven puzzle games with a proposed TypeScript/Cloudflare/D1 architecture. Its README explicitly says core `src` is a scaffold with signatures/TODOs and no implementations. | Do not judge competitors by architecture diagrams alone; working behavior matters more than breadth on paper. |
| [JeevanRaksha AI](https://github.com/aasutoshsony/jeevanraksha-ai) | 78 MB | Voice-based disaster-relief needs intake and request dashboard. README says it is an MVP and is not connected to live emergency services. The large repository size does not by itself indicate maturity. | Show what actually happens after a voice report; clearly distinguish a prototype from a live emergency service. |

### The main competitor lesson

The best public examples are not simply voice input plus an LLM. They turn speech into a useful, structured result and add trust: a source, an escalation route, a follow-up ticket, a human review, a deterministic field extraction or a repeatable test.

## 4. Market/product positioning risk: UPI support already exists

NPCI issued an official October 2025 circular introducing UPI HELP as a pilot for digital-payment questions, transaction grievance tracking and UPI mandate management. NPCI’s February 2026 publication says FiMI powers UPI Help and describes dispute handling and multilingual support. Sources:

- [NPCI official UPI HELP pilot circular](https://www.npci.org.in/uploads/UPI_OC_No_227_FY_2025_26_Introduction_of_UPI_HELP_Assistant_pilot_an_AI_powered_support_for_UPI_payments_cd501de8f3.pdf)
- [NPCI article on FiMI and UPI Help](https://www.npci.org.in/blog/fimi-engineering-indias-first-domain-specific-language-model-for-the-payments-ecosystem)

Recent secondary regulatory-update sites also report a September 2026 addendum expanding the platform under the name “MyUPI,” with transaction replay, payee-context information, user controls and automated chargeback processing. I did not locate that addendum on an NPCI-hosted page in this research pass, so treat the specific addendum details as secondary-source-reported rather than fully verified from the primary circular.

**Strategic response:** Do not pitch BolKeResolve as “another UPI support chatbot.” Pitch it as a user-controlled, voice-first **resolution case companion across payment and commerce problems**: UPI/card/wallet payment issues, order-not-received complaints, delayed refunds and duplicate charges. It helps people who do not know which party to contact by organising facts, assembling evidence, explaining a sourced next step, preparing the message and tracking what the user did. For supported UPI tasks, link users to official bank/UPI/NPCI routes rather than pretending to replace transaction rails.

Official guidance must be maintained as versioned information, not guessed from a model. NPCI directs users toward their UPI app/participating bank for transaction grievances and distinguishes fraud/unauthorised issues. RBI’s current 2026 Ombudsman scheme has maintainability and timing conditions, so do not show a generic “go to RBI now” instruction without checking current, issue-specific rules. For suspected cyber financial fraud, the National Cyber Crime Reporting Portal says to call 1930 promptly.

Sources:
- [NPCI UPI FAQs](https://www.npci.org.in/what-we-do/upi/faqs)
- [NPCI complaint portal](https://www.npci.org.in/register-a-complaint)
- [RBI Integrated Ombudsman Scheme 2026 FAQs](https://old.rbi.org.in/commonman/english/scripts/faqs.aspx?id=3407)
- [National Cyber Crime Reporting Portal](https://cybercrime.gov.in/Webform/Crime_NodalGrivanceList.aspx)

## 5. The product to build next

### Golden user journey

1. The person taps **Speak my problem** or types. The default example is natural Hinglish; the user can select a tested language.
2. Prisma transcribes the user’s words. Show an editable transcript and explicitly ask the person to confirm amounts/dates before using them.
3. A guided intake asks only the missing follow-up facts. For example: payment method, whether money left the account, recipient/merchant outcome, approximate date, app/bank and whether they already contacted support. Never ask for a UPI PIN, OTP, password, full card details or Aadhaar/PAN.
4. A deterministic case router chooses a reviewed playbook; retrieve only from a small curated knowledge base of official sources. Show **recommended action + why + source link + last verified date**. If the situation is unclear, say so and ask one question or provide a human/official escalation route.
5. BolKeResolve produces a case summary and evidence checklist, plus an editable complaint draft in the chosen language. Any recommendation must be tied to what the user actually said and an official source.
6. Save a case with honest statuses: `Details collected` → `Draft ready` → `User says submitted` → `Awaiting response` → `More information needed` → `Resolved / Not resolved`. These are user-reported statuses, not confirmation from a bank.
7. Add a follow-up date and personal notes. Keep “open official support channel” separate from “submit a complaint”; do not claim that a message has been sent when it has not.

### Four first issue playbooks

- UPI transfer failed / beneficiary not credited.
- UPI merchant payment failed or merchant says payment not received.
- Online order cancelled / refund not received.
- Suspected unauthorised payment or scam (prioritise official bank and cybercrime reporting guidance).

Do not attempt to support every possible financial problem in v1. A few well-tested paths are more impressive than a long list of unreliable labels.

## 6. Engineering priorities

### Frontend and design

- Keep the existing cream/forest-green visual direction; do not redesign the entire app from scratch.
- Keep the photo-led storytelling on the landing page, but make the working intake calmer and more functional: the main voice button, live transcript state, privacy note and next question should dominate.
- Design the result around three clear blocks: **What we understood**, **What to do next (with sources)**, **Prepare your message/evidence**.
- Clearly label the in-app experience “WhatsApp-style chat” and the external button “Open WhatsApp with a draft” until the real Cloud API is built.
- Consolidate styles carefully, define CSS tokens, remove duplicated responsive rules, format JavaScript, and avoid a framework migration unless a concrete need appears.
- Check keyboard use, visible focus, reduced motion, live status/error announcements, contrast, large tap targets, slow mobile connection and narrow viewport. Keep inputs labeled and errors adjacent to the fields.

### Backend and AI

- Split responsibilities over time: `routers`, `schemas`, `services/gnani`, `services/intake`, `services/resolution`, `knowledge`, and `repositories/db`.
- Keep numeric/financial extraction and workflow state transitions deterministic where possible. Use a model for understanding natural-language phrasing, not for inventing amounts or regulatory facts.
- Add a curated, versioned source register with URL, publisher, update/effective date, issue category and verified-on date. Every recommendation should record the source version used.
- Create a clear `resolution_plan` response schema: issue category, missing fields, recommended actions, source IDs, warning/escalation flag, evidence checklist, draft language and confidence/needs-review flag.
- Distinguish `/api/health` (process alive) from `/api/ready` (configured and upstream connectivity check). Record request IDs, latency, provider errors and estimated credit usage without logging user transcripts or credentials.
- Prisma and Timbre endpoints are wired today; make one live synthetic request to each and save a repeatable manual/API smoke-test procedure. Evon v3.3 is described by the challenge page as open weights by request, not a hosted API-platform endpoint; don't block the MVP on self-hosting a large model.
- Fix `BOLKE_DATA_DIR` dotenv initialization order, reconcile the unsupported `hinglish` draft option, and add a real status-transition endpoint.
- SQLite is fine for a local demo. A public multi-user app needs authentication, owner checks on every case/evidence route, safe private file storage, rate limits, retention/deletion controls and a reviewed privacy/security design.

## 7. Testing and evidence of quality

Build a synthetic evaluation set of at least 30 short prompts: Hinglish, Hindi and one regional language you can personally demonstrate well; mix amounts, dates, numerals, noisy clips and ambiguous scenarios. Never use real payment records or personal phone/account details in the demo.

Measure:

- STT transcript correctness, especially amount/date fields.
- Issue-routing accuracy and whether the agent asks for missing facts instead of guessing.
- Whether every recommended route links to the correct official source and effective date.
- Unsupported-claim rate (target: zero on the fixed test set).
- Case-create-to-next-step completion rate.
- API latency/failure rate and TTS success rate.
- Correct behaviour when a service is unavailable or the situation is unclear.

Tests needed: schema validation, amount/date extraction, classification, every playbook, unsafe/fraud flow, recommendation source selection, upload validation, evidence access control, status transitions, and end-to-end journey. Test mock mode freely; use live API credits only for a smaller final benchmark and the recording.

## 8. Competition strategy and final demo

The official challenge asks for a working app using at least one Gnani model/API, a public demo post on LinkedIn and/or X with `#GnaniAI` and `#GreatIndianAIInternshipChallenge`, nomination of the post link, a written project explanation, models used and individual contributions. The official brief says verified engagement influences interview shortlisting, the interview is individual, and purchased engagement, bots, paid promotion, engagement swaps and misleading demos are disallowed. The public demo should be live before final submission.

### Recommended schedule

- **17–19 Oct:** lock scope; fix obvious correctness issues; confirm live Prisma and Timbre calls with synthetic data.
- **20–24 Oct:** build the guided intake, structured case fields and the first two verified resolution playbooks.
- **25–29 Oct:** add sourced recommendation cards, evidence checklist, editable complaint draft and real case status workflow.
- **30 Oct–2 Nov:** run the synthetic test set, fix failures, test mobile/keyboard states and tighten security boundaries.
- **3–5 Nov:** capture a real, uncut golden journey for the video; prepare the write-up and screenshots.
- **6–8 Nov:** publish the public demo early, collect authentic feedback and make only safe fixes.
- **9 Nov:** verify the post URL, hashtags, model names, contribution description and submission fields. Keep 10 Nov as the deadline buffer.

### 60-second demo structure

- **0–5 s:** hook: “Paise kat gaye, refund nahi aaya—ab kya karun?”
- **5–15 s:** speak a natural Hinglish problem; show Prisma transcription and the user correcting/confirming the amount.
- **15–27 s:** answer one precise follow-up question instead of filling a long form.
- **27–40 s:** show the recommended next step with an official source and a short evidence checklist.
- **40–52 s:** generate an editable support message and save it to a case timeline.
- **52–60 s:** show the named Gnani models, the follow-up state and the product promise.

Show only what the application truly does live. Use synthetic data, and clearly label any mock or simulated component.

## 9. What not to spend time on before the deadline

- Do not rewrite everything in React/Next.js solely for stack prestige.
- Do not build live WhatsApp Business webhooks before the core workflow is complete.
- Do not self-host Evon unless access, hardware and latency are practical.
- Do not add ten more issue categories before the first two or four are tested.
- Do not claim that funds are verified, a complaint is submitted, or money is recovered when the user still has to act.
- Do not use unverified regulatory rules or unsupported claims about competitors. Learn from public architectures and tests; do not copy source code or designs without checking licenses and attribution.

## Research links

### Challenge and official technology
- [Great Indian AI Internship Challenge — official page](https://www.gnani.ai/internship)
- [Gnani developer docs](https://docs.gnani.ai/)
- [Prisma STT documentation](https://docs.gnani.ai/api/STT/speech-to-text)
- [Timbre TTS documentation](https://docs.gnani.ai/api/TTS/tts-inference)

### Public GitHub projects reviewed
- [Kural](https://github.com/Mirdumurugesan/kural)
- [SunoAI](https://github.com/neha-tanti/sunoai)
- [Kirana Voice Orders](https://github.com/sagar-grv/kirana-voice-orders)
- [KisanSetu](https://github.com/aniket25042005/kisan_setu_gnani_ai_challenge)
- [Kavach](https://github.com/abhishek-pandey7/Kavach-Realtime-Voice-Threat-Intelligence)
- [Voice Ops Line](https://github.com/Sivadheeraj5356/gnani-voice-ops-line)
- [Samasya](https://github.com/DreadVoice/samasya)
- [JeevanRaksha AI](https://github.com/aasutoshsony/jeevanraksha-ai)

### Payment resolution references
- [NPCI UPI FAQs](https://www.npci.org.in/what-we-do/upi/faqs)
- [NPCI complaint portal](https://www.npci.org.in/register-a-complaint)
- [RBI Integrated Ombudsman Scheme 2026 FAQs](https://old.rbi.org.in/commonman/english/scripts/faqs.aspx?id=3407)
- [National Cyber Crime Reporting Portal](https://cybercrime.gov.in/Webform/Crime_NodalGrivanceList.aspx)
