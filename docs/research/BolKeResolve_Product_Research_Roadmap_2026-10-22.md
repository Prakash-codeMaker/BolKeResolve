# BolKeResolve: Product Research, Audience Strategy, and Next-Step Roadmap

**Research date:** 22 October 2026  
**Project reviewed:** `BolKeResolve_Homepage_Photo_Refresh_2026-10-22.zip` and its included product-strategy, research, implementation-status, README, and UX documents.  
**Purpose:** Decide what BolKeResolve should be, whom it should serve first, where it can create differentiated value, and what to prioritise across product, website, trust, and validation.

> **Research scope and limitations.** This combines a source/code-document review, current public-source desk research, and a small qualitative scan of public user discussions. It is not a statistically representative customer study, a legal opinion, a live test of every official portal, or an independently verified evaluation of competitors. Reddit posts and review sites below are anecdotes, not prevalence estimates. All proposed product targets are hypotheses to test.

---

## 1. Executive recommendation

### The product should be a resolution companion—not another chatbot

**Recommended positioning:**

> **Tell BolKeResolve what happened. Get the next appropriate step, a message you can review, and one case record you can carry across support channels.**

The long-term product is a **Resolution Passport**: a user-owned, source-backed record that turns a messy story into confirmed facts, a clear next action, the right official route, a prepared message, a record of what the user did, and a sensible follow-up.

The strategic goal is not to promise that BolKeResolve can force a refund. It cannot currently view a user's bank/payment-network records, make decisions for an institution, submit a complaint through every authority, or guarantee a resolution. Its job is to make the user's next move easier, safer, more accurate, and harder to lose track of.

### Why this is the strongest direction

1. **The channel is not the moat.** NPCI's UPI HELP pilot already targets digital-payment questions, transaction-status checks, supported complaint logging/tracking, and UPI mandate management for participating members. The Government of India also launched Samadhan Didi, a multilingual voice grievance chatbot in May 2026. Voice, Hindi/Hinglish, or a chat interface are valuable access features, but are not unique on their own. ([NPCI UPI HELP circular](https://www.npci.org.in/uploads/UPI_OC_No_227_FY_2025_26_Introduction_of_UPI_HELP_Assistant_a_pilot_an_AI_powered_support_for_UPI_payments_cd501de8f3.pdf); [PIB: Samadhan Didi](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2266985&lang=2&reg=48))
2. **The official system already has many destinations and channels.** The National Consumer Helpline offers web, app, UMANG, phone, SMS and WhatsApp grievance registration in 17 languages; its convergence programme says more than 2,000 organisations have joined. BolKeResolve should help people prepare for and navigate these destinations, not imply it replaces them. ([NCH](https://consumeraffairs.gov.in/index.php/pages/nch); [NCH Convergence Programme](https://consumerhelpline.gov.in/public/convergenceprogram))
3. **The hard part is follow-through across disconnected steps.** Public anecdotes include users being bounced between a UPI app and a bank, and consumer-helpline cases with very different outcomes—some quick resolutions, other cases remaining pending. The design implication is to keep the context, evidence, reference numbers, source, and next follow-up together. These anecdotes suggest hypotheses; they do not quantify how common the problem is. ([UPI user discussion](https://www.reddit.com/r/CreditCardsIndia/comments/1kc7rgo/money_debited_but_upi_transaction_failed_via_bhim/); [NCH outcome discussion](https://www.reddit.com/r/india/comments/1oruh6n/national_consumer_helpline_works_and_swiggy_sucks/); [pending NCH case discussion](https://www.reddit.com/r/swiggy/comments/1v82ovl/is_the_national_consumer_helpline_india_actually/))
4. **The current project already has much of the right foundation.** The inspected ZIP describes voice/text intake, user confirmation of extracted facts, deterministic resolution playbooks, source links, evidence checklist, editable support drafts, a timeline, follow-up fields, and portable Resolution Passport export. The next improvement should focus on proving this whole journey works for real users, not adding more top-level sections.

### The differentiator to build

**One story → one source-backed next action → one portable case record → continued follow-through.**

The defensible value is the combination of:
- decision-quality routing with an explanation and dated official sources;
- a clear distinction between user-reported, AI-suggested, source-confirmed, and externally verified information;
- a message and evidence pack the user controls;
- a history that survives switching from merchant to app/bank to official channel;
- opt-in, privacy-preserving learning about which steps users report as helpful over time.

Do not advertise this as “the only service that does X” before validating the competitive market further. Differentiate with the complete workflow and measurable execution quality, not with an unsupported uniqueness claim.

---

## 2. What current evidence says about the opportunity

### High-volume payment behaviour creates meaningful stakes

The Government's April 2026 UPI decade release reports **24,161.69 crore transactions in FY 2025–26**, worth approximately **₹314 lakh crore**, across 700+ banks. That scale means even infrequent confusion around a payment can affect a very large user base; it does **not** imply that every failed transaction becomes a dispute or that every user needs BolKeResolve. ([PIB / Ministry of Finance, 30 April 2026](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2257087&lang=1&reg=1))

RBI's 2024–25 Annual Report records **2.96 lakh complaints** received by RBI Ombudsman offices in that year, with complaints mainly against banks and many relating to loans/advances and digital banking products. This is evidence that formal grievance handling is an active need, but the total is not a market-size estimate for BolKeResolve and is not all UPI complaints. ([RBI Annual Report 2024–25, Consumer Education and Protection](https://www.rbi.org.in/scripts/AnnualReportPublications.aspx?Id=1436))

### Local-language access matters—but trust is essential

The IAMAI/Kantar *Internet in India 2024* report says 870 million users accessed the internet in Indic languages in 2024, and 57% of urban internet users said they preferred Indic-language internet content. The same report says 15% of internet users used voice-based commands for online activities; it also reports that 36% said they did not trust AI-bot answers and 49% said they struggled with AI tools. Voice and language support should therefore be optional and well reviewed, not a substitute for clarity, correction, and evidence. ([IAMAI/Kantar report PDF, especially pp. 13–17](https://wearesocial.com/uk/wp-content/uploads/sites/3/2025/10/Kantar_20IAMAI20report_2024_.pdf))

**Implication:** Hindi, Hinglish, Marathi, and other languages can reduce friction, but the experience must allow people to type, correct speech transcripts, and switch to a human or official channel when uncertain. Do not claim equal accuracy in all languages without a reviewed evaluation set.

### A crucial shift in the regulatory landscape

The RBI's **Reserve Bank–Integrated Ombudsman Scheme 2026** took effect on **1 July 2026**, replacing the 2021 scheme for applicable new cases. Its official FAQ states that eligibility and prior-approach requirements matter. Therefore, BolKeResolve must not show a generic “go to RBI after 30 days” instruction for every payment or merchant issue. Routing should depend on the kind of entity, the complaint, the prior grievance, and the current official guidance. ([RBI scheme FAQ, updated 1 July 2026](https://old.rbi.org.in/commonman/english/scripts/faqs.aspx?id=3407))

### Consumer support already has strong alternatives

- **NPCI UPI HELP:** pilot support for transaction queries/status, supported complaint workflows, and mandates for participating members; decisions remain with the customer and/or issuer bank. [Official circular](https://www.npci.org.in/uploads/UPI_OC_No_227_FY_2025_26_Introduction_of_UPI_HELP_Assistant_a_pilot_an_AI_powered_support_for_UPI_payments_cd501de8f3.pdf).
- **National Consumer Helpline:** official pre-litigation route, multilingual, omni-channel, and connected to a large set of participating organisations. [Official convergence programme](https://consumerhelpline.gov.in/public/convergenceprogram).
- **RBI Complaint Management System / Ombudsman:** formal route for eligible complaints against regulated entities, subject to scheme conditions. [RBI public complaint information](https://www.rbi.org.in/Scripts/Complaints.aspx).
- **National Cyber Crime Reporting Portal:** the official portal directs users to 1930 for online financial fraud. Suspected unauthorised payment needs a prominent, immediate safety route, not a lengthy onboarding. [Official portal](https://cybercrime.gov.in/).
- **Voxya:** publicly presents consumer complaint preparation, brand outreach/social campaigns, and legal support as parts of its offering. It is a private alternative, so BolKeResolve should not assume all users want legal escalation first. [Voxya](https://voxya.com/).
- **Grahak-Nyay:** an academic system using LLMs/RAG for Indian consumer grievance assistance, with sectoral datasets and annotated conversations. This shows that a generic consumer-law chatbot is also not a defensible wedge by itself. [ACL Anthology paper](https://aclanthology.org/2025.justnlp-main.7/).

**Competitive conclusion:** official services are endpoints to help people reach; private complaint platforms focus on escalation; generic AI answers explain. BolKeResolve should own the *continuity layer* between explanation, preparation, handoff, and follow-up.

---

## 3. The audience to serve first

Do not target “everyone in India with any consumer problem.” That makes routing, content, trust, and usability impossible to optimise.

### Primary early adopter segment — a behavioural definition

**A mobile-first consumer with a stuck payment or delayed refund who has already tried one support path, still does not know the correct next step, and needs to keep proof and follow-ups organised.**

Common behaviours worth testing in interviews:
- They have a screenshot, order/reference number, SMS, or chat transcript scattered across apps.
- They are unsure whether to contact the merchant, UPI app, bank, NCH, or RBI.
- They may know what happened but do not know how to express it in a concise, complete complaint.
- They dread repeating the same story or losing the latest reply.
- The amount may be personally meaningful, while hiring a lawyer or navigating a formal case feels disproportionate.

Treat these as hypotheses, not assumed facts about age, income, education, or digital literacy.

### Start with two core flows and one emergency path

**Flow A — Merchant refund delayed**
- Collect: merchant/order, cancellation or return state, promised refund date if known, previous support attempt and reference number if any.
- Produce: a concise recipient-specific message, the minimal evidence checklist, the official first route, and a clear follow-up event.
- Later: conditionally show the relevant NCH or consumer-commission path when appropriate; never suggest RBI merely because a refund is delayed.

**Flow B — UPI/payment failed, pending, or status unclear**
- Collect: payment app/bank, approximate date/time, amount, visible status, whether money was debited, whether the recipient received it, and whether the user already raised a dispute.
- Produce: the correct first contact based on the scenario, official source, details to keep, and a reviewed draft.
- Boundary: do not imply access to transaction status or bank/network confirmation unless an authorised integration actually returns it. NPCI's UPI FAQ routes many grievances through participating UPI apps/banks, and UPI HELP's pilot may cover supported flows. [NPCI UPI FAQs](https://www.npci.org.in/what-we-do/upi/faqs).

**Emergency path — suspected unauthorised payment or cyber fraud**
- Surface the user's bank and official 1930/cybercrime reporting route immediately.
- Offer a compact optional case record after showing the urgent action.
- Never request an OTP, UPI PIN, password, full card number, or full account credentials.
- Do not make the user finish the ordinary intake before seeing the emergency guidance.

Other complaint categories should remain discoverable, but if a flow has not been evaluated and reviewed, clearly say that the app has limited guidance and direct users to an appropriate official/help channel.

---

## 4. The website should communicate value, not feature count

The current site should stop making the visitor infer why the chat widget is worth using. Show the useful output and the limits plainly.

### Recommended above-the-fold content

**Headline:** “Refund or payment stuck? Know what to do next.”

**Subheadline:** “Explain it in your own words. Get a source-backed next step, a message to review, and a case record you can take across support channels.”

**Primary CTA:** “Tell us what happened”  
**Secondary CTA:** “See a sample case”

**Trust line:** “Independent guidance—not a bank or government helpline. We do not access your payment account, send a complaint automatically, or guarantee a refund.”

This is clearer and more credible than broad claims about resolution or a headline that only highlights a chat interaction.

### What the homepage needs

1. **Show the real output.** Replace or supplement generic lifestyle stock photography with an interactive/demo Resolution Passport using conspicuously fictional data: confirmed facts, one next action, official source/date, editable message, evidence list, and follow-up. The hero should let visitors see the product's actual value without starting a case.
2. **Use examples based on concrete problems.** Two primary entry cards: “Refund hasn't arrived” and “UPI payment is stuck.” An always-visible emergency option: “I don't recognise this payment.” Keep everything else under “Another issue.”
3. **Make the process feel small.** Three short steps: Explain → Review the next step → Keep track. Do not add more icon cards or process steps to the first screen.
4. **Make boundaries part of the value proposition.** A small “What we do / don't do” section should explain that drafts are user-reviewed, actions are not sent until the user opens/sends them, and progress statuses are user-reported unless clearly identified otherwise.
5. **Show proof without fake social proof.** Use a demo case, transparent source links, a “last checked” date, and a security/privacy summary. Do not make up success rates, average refund times, case counts, or testimonials.
6. **Make imagery product-specific.** Keep photos as supporting human context, but use the actual case interface, a safe fictional evidence bundle, and a clear visual of the user's next step as the main visual language. Never use scraped personal/social-media photos without permission. Stock photography cannot prove the service works.
7. **Make it mobile-first and low-friction.** One prominent CTA; large touch targets; text and voice options; transcript confirmation; preserve work if the user navigates; usable at low bandwidth; no required account before the user sees an initial recommendation, where the security model permits it.

### Recommended case screen

The default saved-case view should have only two visible zones:

- **Do this next** — one action, the reason, source link, and one primary button.
- **Your case record** — concise facts and the current user-reported state.

Everything else can appear only when relevant through a single secondary entry point such as **“Update case”**: prepare/edit message, attach proof, log a reference number, record a reply, set a follow-up. Do not turn the case into three tabs that contain all six old tabs' worth of panels.

### Copy examples

Prefer:
- “Suggested next step” over “Resolution” if the outcome is not yet known.
- “You marked this as sent” over “Message sent.”
- “You reported that the refund arrived” over “Refund verified.”
- “Source checked 22 Oct 2026” over an unqualified “Official guidance.”
- “Open official support” over “We contacted support” if the user is handing off manually.

Avoid:
- “Get your refund guaranteed.”
- “We filed your complaint” when the user only copied a message or opened a portal.
- “Verified payment” based only on a transcript or screenshot.
- “Go to RBI” for a merchant dispute without establishing scope and eligibility.

---

## 5. The product loop that creates real value

### The core journey

1. **Tell the story** in text or voice; offer issue chips but don't force a form.
2. **Reflect back the facts**: a small editable summary, with unconfirmed transcript fields clearly marked.
3. **Ask only for critical missing facts**. Use adaptive follow-ups, not a long list of form fields.
4. **Explain one next action**: what to do, why, where, what to prepare, and what happens next.
5. **Make the handoff easy**: an editable message tailored to the recipient plus copy/open official route.
6. **Record the handoff**: let the user enter the destination, date, ticket/docket/reference, and a copy or summary of any reply.
7. **Follow through**: opt-in follow-up date/reminder, then next conditional step when the user returns.
8. **Close the loop**: user-reported result and optional consent to share anonymised outcome signals.

### The most important feature additions

**P0 — Source-backed next-step card**
- Every instruction has an applicability rule, official source, last-reviewed date, and “why this applies” explanation.
- Distinguish official requirements from BolKeResolve's suggested organisation.
- If key facts are missing or sources conflict, abstain from confident routing and offer official/human help.

**P0 — Fact provenance and uncertainty**
- Each important field is labelled as user-provided, voice transcript awaiting confirmation, user-confirmed, extracted from uploaded evidence but unconfirmed, or independently verified by an authorised integration.
- Show conflicting amounts/dates instead of silently choosing one.
- Keep the user in control of edits and deletion.

**P0 — Two narrow, complete playbooks**
- Finish refund-delay and failed/pending payment flows end to end before expanding categories.
- Make emergency fraud routing a separate safe shortcut.
- Maintain a reviewed corpus of at least 50 realistic scenarios; include missing facts, contradictory stories, Hindi/Hinglish/code-switching, typo-heavy input, and out-of-scope cases.

**P1 — Follow-up that actually helps**
- The current project documentation says follow-up dates are stored in the case, but reminders are not automatically sent. That is a gap between a “saved date” and actual help.
- Start with an explicit opt-in calendar file/link or browser reminder where supported. Do not claim notifications exist until tested. Keep reminder content discreet to protect users sharing devices.
- When someone returns, ask “Did you get a reply?” and let them paste/attach the reply; update the next action based on what happened.

**P1 — Carry-anywhere export**
- Provide a compact printable/PDF case summary and an editable message. Keep structured JSON for power users/integrations.
- Use a clear, readable first page: story, dates/amount if supplied, relevant reference numbers, action already taken, desired outcome, next action, evidence list, source links.
- Avoid exposing unnecessary sensitive fields in exports; include a preview before download/share.

**P2 — Anonymous outcome intelligence**
- Only after real usage and explicit opt-in, aggregate which types of evidence and next steps users report as useful.
- Label sample size, time range, and provenance; suppress small cohorts; never publish raw stories or identify complainants.
- Do not create public company rankings or a public complaint wall in the MVP.

---

## 6. How BolKeResolve can become meaningfully different

There is no credible way to guarantee that any interface feature is unavailable anywhere else. The stronger strategy is to deliver a distinctive combination and then demonstrate its outcomes.

| Layer | Most services already do | BolKeResolve should do better |
|---|---|---|
| Explain | FAQs, bots, help articles | Let people tell the story naturally and correct the facts once |
| Route | Point to one official channel or institution | Explain which route applies to this specific issue, why, with official source and review date |
| Prepare | Ask user to fill a portal or form | Reuse confirmed facts to prepare a correct, editable, recipient-specific message and checklist |
| Handoff | User switches apps and repeats context | Keep the same case record and evidence summary across the handoff |
| Follow up | Destination has its own ticket/status view | Record what the user actually sent/received, a reference number, and the next follow-up date |
| Learn | Public complaints or generic FAQs | With consent, learn from structured, privacy-preserving outcome events to improve the playbooks |

**Defensibility over time:** not a larger language model and not a longer chatbot. It is a high-quality source registry, a tested routing/evaluation corpus, a clean case-provenance model, and a longitudinal dataset of consented outcomes that improves the next action without exposing private case details.

---

## 7. Distribution: how to reach people at the moment they need help

Do not start with broad social-media awareness or a generic “AI for consumers” campaign. Meet people when they search for a specific problem.

### Content and acquisition tests

- Build high-intent, source-maintained landing pages for “UPI payment failed money deducted,” “refund not received after cancellation,” and “support says payment successful but app says failed.” Each page gives useful immediate guidance and links to official sources, not a thin SEO page that only funnels to a bot.
- Create a 30–45 second demo: one anonymised/synthetic story becomes confirmed facts, the next action, a support message, and a follow-up record.
- Pilot with 2–3 trusted distribution partners: a college/student support office, consumer-awareness group, community organisation, or worker association. Provide the tool at no cost during discovery and disclose any sponsor relationship.
- Use shareable but privacy-safe case exports; never make public sharing the default.
- Consider QR cards or a lightweight PWA after the core task works, rather than building an expensive native app first.

### What not to build yet

- A WhatsApp clone or new social network.
- A public “worst companies” leaderboard.
- An all-category legal advisor.
- Direct bank/payment integrations before you have a partner and real API access.
- Automatic filing claims based on opening a URL or copying a message.
- Push/email/WhatsApp notifications before consent, delivery, privacy, and failure handling are implemented.
- Monetisation that creates a conflict of interest with the user's complaint.

---

## 8. User research to run before adding more features

### Recruitment: first 10–15 interviews

Recruit people who have had a real delayed refund or failed/pending payment in the last 90 days. Include a range of language preferences and levels of comfort with online support. Recruit 3–5 additional practitioners if possible: consumer counsellors, support agents, legal aid/consumer advocates, or community workers. Do not ask people to disclose full financial credentials, OTPs, PINs, or unredacted account information.

### Interview questions (ask about the last real event)

1. “Walk me through the last time a payment or refund went wrong. What happened next?”
2. “Which channels did you try, and what did each one tell you?”
3. “Where did you get stuck or repeat yourself?”
4. “What proof or reference numbers did you need? Where were they stored?”
5. “What did you believe the next step was, and how confident were you?”
6. “How did you decide the issue was resolved—or not?”
7. Give a synthetic case and ask the participant to use the prototype without coaching. “What would you do next, and why?”
8. “Which information would you refuse to enter into a tool like this?”
9. “Would you use the case record later? What would make you trust—or distrust—it?”

Avoid asking “Would you use this app?” in isolation. Observe the task, where users hesitate, what they correct, and whether they can explain the next action afterward. An interview or click-through is not evidence that the product gets refunds; it is evidence about usability and perceived value.

### Decision gate after interviews

- If users value the draft only, simplify to a focused complaint-message helper.
- If they value route clarity and reusing details across channels, prioritise source-backed routing and the Resolution Passport.
- If they primarily want a human advocate to contact organisations on their behalf, test a small supervised human-assistance pilot before promising automation.
- If people do not understand the distinction between a draft, a submitted complaint, and a resolution, fix that before acquisition.

---

## 9. Metrics that reflect the real goal

A consumer problem-solving tool is episodic; **do not optimise daily active use or time spent in the chat**. Success means the user can take the right next step with less confusion and less repetition.

### North-star candidate: Action-ready case rate

Share of supported cases where the user:
1. confirms the key facts;
2. receives a route judged appropriate by the reviewed rules;
3. can explain the next action unaided;
4. gets a usable message/checklist or opens the correct official destination; and
5. knows what to do if there is no reply.

Instrument the stages, but minimise analytics on the story itself. Never count a generated answer as a successful resolution.

### Pilot scorecard

Initial thresholds below are **proposed pilot goals**, not evidence-backed industry benchmarks:
- At least 80% of usability-test participants can explain the next step in their own words after using the flow.
- Median time from story entry to a user-approved next action under 3 minutes for supported scenarios.
- At least 70% of cases produce a user-approved usable message or an intentional official-channel handoff.
- 100% of high-risk fraud scenarios show the urgent safe route before ordinary form completion.
- Zero unsupported claims of bank/payment verification, complaint submission, delivery, or refund success in the reviewed evaluation set.
- Expert-reviewed route accuracy target of at least 95% on supported scenarios, with any error that could materially misroute a user treated as a release blocker.
- Track 7-day follow-through (did the user send/contact/log a response?) and user-reported outcomes, but do not label those outcomes “verified” without an authorised integration or independent proof.

Also track abandonment at every step, voice transcript correction rate, missing-fact questions, incorrect-route reports, opt-out/deletion, and source freshness.

---

## 10. Product and engineering roadmap

### Next 72 hours — focus and trust

1. Freeze feature expansion; decide that the first pilot supports the two core flows and an emergency safety path.
2. Update the hero, CTA, sample case, and “what we do/don't do” copy.
3. Create one excellent sample Resolution Passport and use it in the website's main product visual instead of relying on generic photos.
4. Audit every routing recommendation for source, applicability, reviewed date, and clear uncertainty handling.
5. Recruit the first 10–15 interviews and prepare five synthetic test cases.

### Week 1–2 — complete the core workflow

1. Make the home → story → confirm facts → next action → draft/handoff → follow-up path seamless on mobile.
2. Remove duplicate panels from the case workspace; keep one primary action and one secondary “Update case” path.
3. Finish refund-delay and UPI-pending playbooks first; keep unauthorised-payment safety guidance immediate.
4. Add source registry metadata and a review process so an outdated regulatory instruction cannot silently stay in the product.
5. Make provenance labels consistent across the chat, case, export, and activity timeline.
6. Test 50 realistic scenarios plus keyboard, screen-reader, low-bandwidth, and shared-device privacy basics.

### Week 3–4 — supervised pilot

1. Test with 20–30 target users recruited through trusted communities, using synthetic demo data until the privacy/security gates are ready for real information.
2. Observe five end-to-end sessions without coaching; log hesitation, wrong assumptions, and repeated-entry points.
3. Review route accuracy with a consumer-support practitioner and a lawyer/regulatory expert for applicable advice boundaries.
4. Ship only changes that improve correct action completion, clarity, or trust.

### Before a public launch — hard gates

The current project's implementation notes flag gaps such as live provider verification, durable production data storage/backups, malware scanning for uploads, account deletion/retention controls, and a comprehensive security review. Before real consumers upload financial evidence, verify:
- authentication and ownership isolation for every case/evidence route;
- encrypted transit and storage where appropriate, controlled logs and secrets;
- tested deletion, backup/restore and retention policy;
- file malware scanning and image/PDF content handling policy;
- abuse/rate limits and monitoring;
- privacy notice and consent appropriate to the data collected;
- real live STT/TTS/provider flows, not just mocked tests;
- production deployment, TLS, backup recovery, and incident response.

The Indian Digital Personal Data Protection Act has a phased commencement schedule in the November 2025 Gazette notification; use this to plan with counsel rather than assume all provisions commence at once. Data minimisation and safe handling should be product requirements regardless of commencement timing. ([MeitY Gazette notification, 13 November 2025](https://www.meity.gov.in/static/uploads/2025/11/c56ceae6c383460ca69577428d36828b.pdf)).

---

## 11. The most useful single product bet

If there is only enough time to make **one** important improvement, build the **source-backed next-action card plus carry-forward case summary**, not another navigation tab.

A sample result should answer, on one mobile screen:
- **What happened?** The facts the user confirmed.
- **What should I do now?** One practical, specific action.
- **Why this route?** One or two official citations, checked date, and relevant conditions.
- **What do I need?** Only the evidence/details required for this step.
- **Use this message.** A ready-to-edit draft.
- **What next if nothing happens?** A conditional follow-up and reminder option.

A user should finish the first session thinking: *“I know what to do next, I have the words and proof ready, and I won't have to reconstruct this story later.”* That is the value proposition worth testing.

---

## 12. Source list

### Official and institutional sources
- [NPCI, UPI HELP pilot circular, 8 October 2025](https://www.npci.org.in/uploads/UPI_OC_No_227_FY_2025_26_Introduction_of_UPI_HELP_Assistant_a_pilot_an_AI_powered_support_for_UPI_payments_cd501de8f3.pdf)
- [NPCI UPI Help / FiMI engineering overview](https://www.npci.org.in/blog/fimi-engineering-indias-first-domain-specific-language-model-for-the-payments-ecosystem)
- [Government of India / PIB, Samadhan Didi voice chatbot, 30 May 2026](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2266985&lang=2&reg=48)
- [National Consumer Helpline](https://consumeraffairs.gov.in/index.php/pages/nch)
- [National Consumer Helpline Convergence Programme](https://consumerhelpline.gov.in/public/convergenceprogram)
- [NCH complaint tracking](https://consumerhelpline.gov.in/user/track-complaint.php)
- [RBI Integrated Ombudsman Scheme 2026 FAQ](https://old.rbi.org.in/commonman/english/scripts/faqs.aspx?id=3407)
- [RBI Annual Report 2024–25](https://www.rbi.org.in/scripts/AnnualReportPublications.aspx?Id=1436)
- [RBI complaints information](https://www.rbi.org.in/Scripts/Complaints.aspx)
- [NPCI UPI FAQs](https://www.npci.org.in/what-we-do/upi/faqs)
- [NPCI register a complaint](https://www.npci.org.in/register-a-complaint)
- [National Cyber Crime Reporting Portal](https://cybercrime.gov.in/)
- [PIB UPI usage data, FY 2025–26](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2257087&lang=1&reg=1)
- [MeitY Gazette commencement notification for DPDP Act, 13 November 2025](https://www.meity.gov.in/static/uploads/2025/11/c56ceae6c383460ca69577428d36828b.pdf)

### Research and product references
- [IAMAI/Kantar, Internet in India 2024 report](https://wearesocial.com/uk/wp-content/uploads/sites/3/2025/10/Kantar_20IAMAI20report_2024_.pdf)
- [Grahak-Nyay: Consumer Grievance Redressal through Large Language Models, ACL Anthology 2025](https://aclanthology.org/2025.justnlp-main.7/)
- [Voxya](https://voxya.com/)
- [Public UPI dispute discussion, Reddit, May 2025](https://www.reddit.com/r/CreditCardsIndia/comments/1kc7rgo/money_debited_but_upi_transaction_failed_via_bhim/)
- [Public NCH refund discussion, Reddit, November 2025 with 2026 updates](https://www.reddit.com/r/india/comments/1oruh6n/national_consumer_helpline_works_and_swiggy_sucks/)
- [Public NCH pending-case discussion, Reddit, July 2026](https://www.reddit.com/r/swiggy/comments/1v82ovl/is_the_national_consumer_helpline_india_actually/)

---

## Final decision

**Keep the current technical foundation. Narrow the target audience, make the homepage sell the outcome, and make the case screen deliver one source-backed next action with a record that survives every handoff.** Test the workflow with real people before adding more channels, issue categories, community features, or monetisation. The product should be measured by the user's ability to act correctly and follow through—not by chat length, AI novelty, or promises of guaranteed refunds.
