# BolKeResolve: Defensibility Research and Final-Polish Strategy

**Research cut-off:** 29 October 2026  
**Purpose:** find a hard-to-reproduce product advantage that fits the current build and the Gnani AI Great Indian AI Internship Challenge deadline.  
**Method:** review current official challenge requirements, the latest code snapshot and changelog, prior BolKeResolve product research, and public sources on direct competitors, Indian consumer-resolution systems, AI product defensibility and service design.

## Executive decision

Do not add a flashy AI feature just to make the site look more complicated. Keep the user experience extremely simple: **tell us what happened → check the facts → take one next step → bring back the reply → get the next step.** The hard work belongs in the product logic beneath that simple journey.

No interface, prompt or feature can honestly be described as impossible to copy. A competitor can imitate a screen or call the same model. More durable defensibility comes from owning the end-to-end workflow, learning from exception cases and corrections, maintaining a source-versioned rule system, becoming the user's persistent case record, and building distribution or authorised integration advantages over time. This aligns with Microsoft for Startups' warning that public information or uploaded documents alone do not constitute a data moat and with a16z's focus on workflow, permissioning, generated outcome data and real-world execution as defensible layers:

- Microsoft for Startups, *Building a moat in the AI age*: https://www.microsoft.com/en-us/startups/blog/building-a-moat-in-the-ai-age-patterns-from-top-startups-in-the-microsoft-for-startups-program/
- a16z, *Is Software Losing Its Head?*: https://a16z.com/is-software-losing-its-head/
- McKinsey, *From AI table stakes to AI advantage: Building competitive moats*: https://www.mckinsey.com/capabilities/quantumblack/our-insights/from-ai-table-stakes-to-ai-advantage-building-competitive-moats/

The current final-polish increment therefore focuses on a real product gap: **a confirmed support reply now changes the next action according to what the reply appears to say**. This is a meaningful improvement over a generic chat and reminder loop, and the regression suite verifies its main paths.

## 1. Challenge identity and submission constraints

The challenge matching this project in the prior records and the current official page is Gnani AI's **Great Indian AI Internship Challenge — “Build Sovereign AI for India.”** Its published requirements include a working app using at least one Gnani AI model/API, naming the model/API and each person's contribution, posting a public working demo on LinkedIn and/or X, tagging Gnani AI, using `#GnaniAI` and `#GreatIndianAIInternshipChallenge`, and nominating the live post link. The currently published deadline is **10 November 2026 at 11:59 PM IST**. It prohibits purchased engagement, bots, paid promotion, engagement exchanges, plagiarism and misleading demonstrations. Recheck the official page immediately before submission in case the organiser changes the terms.

Official page: https://www.gnani.ai/internship  
Official terms: https://www.gnani.ai/great-indian-ai-internship-registration-form

I did not find a Canon AI challenge that matches the project records and requirements; this report proceeds on the documented Gnani AI challenge. If “Canon” refers to a separate event, its rules must be checked separately before submission.

## 2. The competitive reality: the obvious product is already copyable

### Direct and adjacent alternatives

- **RefundPe** currently advertises AI complaint drafting, user-approved email sending, follow-up and regulator complaint packs. A product pitched only as “AI writes and tracks a refund complaint” is not a strong differentiator. https://refundpe.com/ and https://refundpe.com/terms
- **NPCI UPI HELP** describes digital-payment queries, supported transaction-status/complaint flows and mandate management for users of participating members. Access to transaction/member data is not an open capability that a new app should assume. https://www.npci.org.in/uploads/UPI_OC_No_227_FY_2025_26_Introduction_of_UPI_HELP_Assistant_pilot_an_AI_powered_support_for_UPI_payments_cd501de8f3.pdf
- **National Consumer Helpline (NCH)** is an established government resolution route. BolKeResolve should direct people to the appropriate official service rather than imitate it or imply that it has filed a grievance. https://consumerhelpline.gov.in/public/convergenceprogram
- **Grahak-Nyay**, a 2025 research system, already presents an LLM/RAG-based consumer grievance assistant and introduces curated datasets for evaluation. This is further evidence that “a consumer-law chatbot with retrieval” is not itself defensible. https://aclanthology.org/2025.justnlp-main.7/

These alternatives establish what they publicly provide, not independent proof that their outcomes are accurate or superior. The strategic implication is nevertheless clear: do not claim to be first or only based on the current desk research.

## 3. The defensible product thesis

**BolKeResolve should own continuity between the user's story and the eventual resolution—not the complaint letter.** The user should not have to understand the organisational maze, learn legal terminology, repeat the story across channels, or infer the next move from a vague reply.

The internal engine should preserve a compact, traceable chain:

1. **User story** — typed or spoken in the user's own language, with a transcript that remains editable.
2. **Confirmed fact ledger** — value, origin and status for each important fact: user reported, extracted from a document, confirmed by the user, or verified through a specifically authorised integration.
3. **Versioned resolution rule** — issue predicates, applicable/excluded conditions, source URL, rule/source version and human review date.
4. **Evidence map** — the document or field that may support each case fact, including mismatches and missing information.
5. **User-controlled handoff** — official destination, reviewed draft and exported Resolution Passport; no invented claim that it was submitted or delivered.
6. **Response-aware state transition** — interpret a new reply only as a provisional candidate, ask the user to review it, then change the recommended action when confirmed.
7. **Outcome label** — still pending, no response, partially resolved, resolved (user-reported), or otherwise stopped; never confuse user-reported status with bank/merchant verification.

This is a **Resolution Intelligence Graph** as an internal product architecture, not a claim that a complex graph database is needed. A modular monolith, typed case events, a source registry and regression tests are sufficient at this stage.

## 4. What changed in the current build

### Reply-aware Resolution Completion Loop

Before this increment, the reply classifier could tell users that a message appeared to say “refund initiated,” “send documents,” “rejected,” or “under review,” but confirmation wrote the case to a generic follow-up stage. The completion loop did not reliably make the next action fit the actual reply category.

The 29 October increment connects those existing pieces. After user confirmation, the next action now branches to:

- **Potentially unsafe request:** do not disclose OTP/UPI PIN/password, install remote-access software or pay an unsolicited release fee; independently verify the support route.
- **More information requested:** review and supply only the exact relevant evidence through the verified official route.
- **Refund initiation claimed:** obtain a reference/expected date and later check for actual credit; initiation is not credit.
- **Refund credit claimed:** check the user's own account; a message does not mark the issue resolved.
- **Under review / waiting period / acknowledgement:** preserve the reference, track a stated update date and avoid duplicate complaints without reason.
- **Rejected/closed:** inspect the rejection reason and check the current eligibility/prerequisite rules before escalation.
- **Mixed or ambiguous message:** pause for human review or written clarification rather than choosing a route automatically.

The action card remains the single primary interface. Extra details are disclosed only where useful. The raw pasted reply remains outside the ordinary reply-review persistence path; only the brief, confirmed interpretation/category and optional user-provided reference are recorded. The sender's identity and claims are not independently authenticated.

### Test results

The latest source snapshot passes **227 automated tests and 77 subtests**, JavaScript checks and Python compilation. The regression tests cover response categories, action destinations, safety language, the distinction between initiated and credited refunds, raw-reply non-retention and supersession by a later user action. This is code-level regression evidence, **not** proof of live Gnani inference, public deployment readiness, actual user comprehension or improved recovery rates.

## 5. Why this is more defensible than a one-off feature

The reply-aware action itself can be copied. The compounding assets are the parts that take repeated operational work to build well:

### A. A resolution ontology with difficult exceptions

Create a reliable, testable map from issue type + confirmed facts + available evidence + current case stage + response interpretation to the next safe action. Keep exceptional conditions explicit. Examples include “failed UPI debit” versus “merchant refund,” “refund initiated” versus “credit confirmed,” “received an acknowledgement” versus “rejected,” and “under review” versus “requested more evidence.” The rules are not an LLM's hidden judgement: each material branch should be reproducible and cite an applicable official source.

### B. A source-versioned rulebook

For every supported route, record rule ID/version, jurisdiction and scenario scope, positive and exclusion predicates, official source, published/effective date where available, last human review, and tests for edge cases. Do not automatically change the advice because a webpage changed; alert a maintainer to review it. Public source text is not a moat by itself; reliable interpretation, exception handling and regression coverage are more costly to reproduce.

### C. A resolution replay corpus

Build and keep a synthetic benchmark of case journeys, not just isolated chatbot prompts. Each test scenario should contain a fictional user story, transcript variants, confirmed fields, evidence gaps, the simulated support reply, expected category, expected next action, disallowed claims and the correct official source. Include Hinglish/code-mixed phrasing, negation, OCR errors, quoted previous emails, conflicting statements, unsafe messages, partial credit and date-boundary conditions.

Measure at least:

- critical fact accuracy after user confirmation (amount, date, issue type, provider/merchant, transaction status);
- issue and reply category accuracy on the fixed benchmark;
- next-action correctness reviewed by a human;
- unsupported legal/regulatory or verification claims (target zero on the fixed set);
- whether required clarification is asked instead of guessed;
- percentage of plans whose source and scope match the scenario;
- time to the first correct next action in a small, consented usability study.

Do not state that the system has “X% accuracy” until a defined benchmark has actually been run. The current automated test count is a regression count, not a model accuracy rate.

### D. A privacy-preserving outcome feedback loop

Over time, ask users to record only structured milestones such as “information provided,” “support replied,” “refund not yet visible,” “partially resolved,” or “I verified the credit.” If future product analytics are added, use clear opt-in consent and retain the minimum data required. Do not treat a user's raw case or voice transcript as free training data. Do not store raw complaint text or private documents for a purported moat when a structured label is enough. Only analyse aggregate trends after a minimum cohort size, suppress rare merchants/categories, and offer a visible delete/export path. Do not use an outcome to change production rules automatically; review it as a candidate test or insight.

This loop produces hard-to-reconstruct learning only if it actually changes the product, is collected with lawful permission, and is measured. Until BolKeResolve has real opt-in case volume, describe this as the planned moat—not an existing proprietary dataset.

### E. Real-world integration and distribution

A partner-approved, user-consented handoff into an organisation's case workflow would be more defensible than adding another generic AI interface. Do not attempt banking/NPCI integration or automated government complaint filing without authorised access and the required technical/legal arrangements. In the meantime, the portable Resolution Passport and stable case ID minimise repeated explanation across official routes.

## 6. Final-polish plan before 10 November

### P0 — Must complete

1. Run a fresh real Prisma v2.5 STT test using a synthetic Hinglish recording and the applicant's own key. Keep the transcript editable. Do not use a typed script as a fake transcription.
2. Walk through at least one full synthetic case with both branches: first action → saved Passport → confirmed “refund initiated” reply → action changes to get reference/check credit. Then test a second safety case that asks for an OTP and ensure the warning wins.
3. Do manual Chrome/Edge desktop and mobile checks. Confirm the service-worker v21 delivers the updated JS/CSS; the browser automation environment previously could not perform visual QA.
4. Complete the preflight blockers before any public deployment: HTTPS origin, production auth, a real privacy notice, monitored support channel, persistent storage, backup/restore checks, upload scanning strategy, shared rate limits, security/privacy review and deletion verification.
5. Publish a truthful working demo with both official hashtags and tag the official Gnani AI account. Publish early enough for authentic organic engagement to accumulate, and nominate the actual public post link in the submission.

### P1 — Do if the P0 journey is reliable

- Add 30–50 fixed synthetic case journeys to the resolution replay benchmark and publish the methodology, not just a headline score.
- Ask 5–8 consenting people to complete the core flow with fictional data; observe whether they can explain their next action without help. Report results honestly, including small sample size.
- Use at most one language expansion that can be checked by a fluent speaker. Ten language options are not evidence of ten-language quality.

### Explicitly do not attempt now

- a full Gmail OAuth integration;
- live bank/UPI transaction verification;
- automatic complaint filing to official portals;
- a new dashboard, public complaint marketplace, autonomous general-purpose agent or flashy animation layer;
- extra API providers unless they materially strengthen the single demonstrated journey.

These would increase risk and scope without establishing defensibility before the deadline.

## 7. Challenge demo positioning

The strongest technical narrative is a real code-mixed voice-to-resolution path built around Gnani Prisma v2.5. The consumer problem makes the scenario concrete; the response-aware completion loop makes the result more than transcription or letter generation. If the live Hinglish interaction is reliable, **Mixed Vibes** is the most directly demonstrable award lens. Treat real-world impact as the product motivation, but do not claim reduced recovery time or successful refunds without measured user evidence. The official challenge lists ten award categories and says an individual/team can win no more than one category; focus the public demo on one exceptional journey rather than a menu of unfinished features.

### Revised 60-second story

- **0–4s:** “A complaint draft is easy. Knowing what to do after support replies is the hard part.”
- **4–16s:** record a fresh synthetic Hinglish story; show the actual Prisma result and attribution.
- **16–24s:** correct/confirm the amount, payment type and merchant as user-reported facts.
- **24–34s:** show the official-source-backed first move and save the case.
- **34–49s:** paste a synthetic support reply: “Your refund has been initiated. Please allow 5 business days.” Review and confirm it; show the next action change to get the reference and check actual credit—never mark it resolved from the reply alone.
- **49–56s:** briefly show that the new action states the interpretation is user-confirmed and the sender/credit is not independently verified.
- **56–60s:** “BolKeResolve: your next correct step, and the case stays with you.” Show `Built with Gnani AI Prisma v2.5` only if the real call is demonstrated.

If it is not feasible to record the reply loop clearly within 60 seconds, show it in the 2–3 minute technical walk-through and keep the public cut focused on the real voice call and source-backed next step. Never fake live API output.

## 8. Summary

The product should be **simple on the outside, rigorous underneath**. The final code increment is a real move in that direction: a reply does not merely become another timeline entry; it now changes the guidance in a way that matches the content and preserves safety boundaries. The hard-to-copy asset should be built over the coming months from a tested resolution protocol, a carefully maintained source/rule corpus, privacy-respecting structured outcomes, and actual user trust—not from pretending that a new feature cannot be copied.
