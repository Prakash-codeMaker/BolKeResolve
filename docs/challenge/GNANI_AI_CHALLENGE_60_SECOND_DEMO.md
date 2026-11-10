# 60-second public demo: BolKeResolve

Goal: make the problem, the actual Gnani model integration, and the useful outcome undeniable in one minute. Record the working app—not a slide deck. Use synthetic case details only.

## Shot-by-shot plan

**0–5s — The hook**  
On screen: `A failed payment shouldn't mean a confusing support journey.`  
Say: “People often explain a payment problem in the language they use every day. BolKeResolve turns that story into a case they can act on.”

**5–18s — Real code-mixed voice**  
Show the live app's voice recorder and say naturally, in one take:  
`Mere ₹850 UPI se kat gaye, app failed dikha raha hai, aur saamne wale ko paise nahi mile.`  
Stop recording. Keep the actual response wait in the cut only if the transcription really completed. Show `Gnani AI Prisma v2.5` attribution and the transcript returned from the live API. Do not use a typed substitute while implying it was transcribed.

**18–28s — Review, don't blindly trust AI**  
Show the editable transcript and the suggested issue/amount. Say: “Prisma gives us the words; the user still reviews the transcript and confirms the facts. A spoken claim is not a bank verification.” Correct one field only if needed.

**28–42s — From words to a useful action**  
Show the scenario-specific next step, official-source link and missing-detail prompt. Say: “The resolution logic distinguishes the payment scenario and points to the relevant official route. It doesn't invent a bank status or promise a refund.”

**42–53s — Reply changes the next move**  
For a pre-prepared fictional case (or only if the click path stays clear), review and confirm the synthetic reply: “Your refund has been initiated. Please allow 5 business days.” Show the main action change to getting the reference and checking actual credit. Say: “A reply changes the next step—but a message is not proof that money arrived.” If this cannot fit cleanly or it requires a cut that hides the actual flow, use this section in the longer technical walkthrough instead.

**53–60s — Close with a truthful attribution**  
Show project title and `Built with Gnani AI Prisma v2.5` (add Timbre v2.5 only if you made a live successful TTS call on camera). Say: “BolKeResolve: your next correct step, and the case stays with you.”

## Recording rules

- Record the real app after setting a valid `GNANI_API_KEY` on the server. Never show the key or `.env`.
- Use synthetic data (₹850 is fictional). Do not include real phone numbers, bank identifiers, Aadhaar/PAN, private messages or real recordings.
- Prefer one unbroken screen recording with voice narration. Add captions for accessibility; do not edit a failure to look like a successful API call.
- Do not show a fake “refund successful” state. If a provider call fails, fix it and rerecord.
- If a real TTS call is not verified, do not claim Timbre works live in the video; the code adapter alone is not evidence.
- Keep a longer 2–3 minute walkthrough available for technical questions, even if posting the 60-second cut.

## Optional 2–3 minute technical walkthrough (not the competition's 60-second cut)

If judges ask for more detail, show the reply-aware follow-through after the 60-second story:

1. Open a saved fictional case and expand **Understand a support reply**.
2. Paste a safe synthetic response such as “Your refund has been initiated. Please allow 5 business days.”
3. Click **Review reply**. Show the classification and next step; point out that it is a conservative rule-based interpretation, not proof of credit.
4. Confirm saving. Show the timeline contains a short category/interpretation but not the pasted raw reply.
5. Optionally export the Resolution Passport and show that source/provenance labels remain present.

Do not include a real customer support message or personal/financial details. Do not imply that BolKeResolve verified a bank account, filed a complaint, or used Gnani AI to classify the support reply. Only attribute Prisma to the actual live transcription shown in the video.

## Optional 2–3 minute Promise-to-Proof walkthrough

Use this after the core voice-to-case demo. It showcases the existing commitment reconciliation engine without implying that a bank or merchant was contacted.

1. Open a **synthetic refund case** and go to its **Prep** tab, then expand **Commitments & conditions**.
2. Click **Load fictional ₹850 refund example**. The app previews this support-chat statement: “We will initiate your ₹850 refund within five business days from today.”
3. Inspect the candidate: refund initiation, ₹850, five business days and a statement date of **20 October 2026**. The source label identifies it as synthetic. Confirm that no condition was invented and the clock starts from the statement date.
4. Read the estimate: five working days after 20 October gives **27 October 2026**, excluding weekends only. Since this walkthrough is dated **10 November 2026**, the app should say **“The stated period may have passed”**. This is an estimate, not a legal deadline; Indian public holidays and company-specific calendars are not checked.
5. Check the review box and save the commitment. Show the preserved source excerpt, amount, date, estimate and current interpretation.
6. Expand **Add a later reply or proof** and click **Load fictional 10 Nov follow-up note**. Review the prefilled report, keep its relation as **“I'm not sure yet”**, and record the update. Show that it is labelled **user-reported**, not independently verified.
7. Open **Change history** and the Resolution Passport export. Point out that the original promise and the later report remain separate entries.

The example is deliberately synthetic. It does not look up a UPI transaction, inspect a bank account, verify the speaker or prove that a refund did or did not arrive. The follow-up is a user report; a message saying a refund was initiated is not proof of credit.

## Optional advanced feature walkthrough — commitment reconciliation

**Do not add this to the 60-second submission clip until you have completed local browser/mobile smoke testing and can reproduce the sequence reliably.** It may work better as an additional 2–3 minute technical walkthrough.

Using synthetic data, open a case and expand **Commitments & conditions**. Paste:

`Once the return is scanned at the warehouse, we will initiate the ₹1,200 refund within five business days.`

Show the candidate, correct its condition/action/timeframe if needed, check the explicit confirmation box, then save it. Point out that the clock is initially unset. Add a reviewed trigger event dated 29 October 2026 and show the estimated date (5 November 2026 with the current weekend-only business-day approximation). Then record a contradictory update and show that both statements stay in the case history and the state becomes “Conflicting information to review.”

Explain the boundaries accurately: extraction is deterministic/rule-based; audio transcription uses the configured Gnani route if used live; the app does not verify the speaker, the company, any source file, or the refund. Business-day calculations exclude weekends only, not public holidays/company-specific calendars; the date is an estimate, not a legal deadline.
