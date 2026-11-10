# BolKeResolve — Voice-to-Proof Consumer Resolution Workspace

**Great Indian AI Internship Challenge 2026**  
**Primary category fit:** Real Deal  
**Additional strength:** Mixed Vibes (Hinglish voice interaction)  
**Tagline:** Speak the issue. Keep the proof. Know the next step.

## The problem

A failed UPI payment, pending transfer or delayed refund can leave someone juggling screenshots, reference numbers, SMS messages and support replies. The person may receive a message saying a refund was initiated, but that message does not establish that the money was actually credited. Important facts become fragmented across conversations and files, and the next step is often unclear.

## The solution

**BolKeResolve turns a spoken or typed consumer complaint into a user-reviewed, evidence-aware case.** It brings the user's account, supporting records, issue-specific guidance, support commitments and follow-up history into one portable workspace.

## How the workflow works

1. **Speak or type.** Describe the issue naturally, including in Hinglish. The voice intake uses Gnani speech services when configured.
2. **Review the transcript and facts.** The user checks or corrects the transcript and key case details. Missing values remain missing rather than being guessed.
3. **Organise the case.** The application keeps evidence with source/provenance information, shows relevant next-step guidance and helps prepare a support message.
4. **Track the promise.** The Promise-to-Proof ledger preserves the original wording of a support commitment, amount, condition and stated timeframe.
5. **Record what happened next.** A later reply, contradiction or user report becomes a separate event. It does not overwrite the original statement or silently become independently verified fact.
6. **Take the record forward.** The Resolution Passport exports a structured summary, timeline, user-confirmed facts and evidence index for the user's next interaction.

## The differentiator: Promise-to-Proof

A support message can say, “We will initiate your ₹850 refund within five business days.” BolKeResolve lets the user review that statement and save its amount and timeframe. A later report is recorded separately, with its provenance visible.

This matters because **a promise to initiate a refund is not proof that a refund was credited**. The case history should preserve that distinction rather than marking a case resolved simply because a message sounded reassuring.

## Gnani AI integration

- **Prisma — speech-to-text:** used for spoken complaint transcription. The repository template currently defaults to `prisma-v3.0`; verify the successful live request before naming the version because the public challenge page currently lists Prisma v2.5.
- **Timbre v2.5 — text-to-speech:** used for spoken responses/readback in the current server configuration.

The case workflow, deterministic guidance, evidence relationships and Promise-to-Proof reconciliation are application logic. This submission does not claim to use Evon. Model attribution in the final video should match the exact successful calls shown during recording.

## What makes it different

- A case workflow rather than a generic voice chatbot.
- A traceable link between statements, evidence, commitments and later updates.
- Explicit distinction between user-reported information, user-confirmed facts and independently verified facts.
- Preservation of the original support statement instead of silently overwriting it.
- A portable case record that can be taken to the relevant support channel.

## Trust boundaries

BolKeResolve organises user-provided information and suggests next steps. It does **not** access bank accounts, independently verify UPI transactions, contact merchants, initiate payments or refunds, or automatically file complaints. A user-reported outcome remains labelled as user-reported. File hashes can help detect changes to exported files; they do not prove authorship, origin or truth. The demo uses synthetic case details.

## The evaluator's path

Open the live application, create or open a synthetic case, speak a Hinglish payment complaint, review the actual transcript, inspect the next-step guidance, save the fictional ₹850 refund commitment, add a later synthetic user-reported update, then inspect the timeline and Resolution Passport.

- **Live application:** https://bolkeresolve.vercel.app
- **Source code:** https://github.com/Prakash-codeMaker/BolKeResolve
- **2–3 minute submission demo:** publish a public video and link it in the challenge form.
- **Demo walkthrough:** [GNANI_AI_CHALLENGE_60_SECOND_DEMO.md](GNANI_AI_CHALLENGE_60_SECOND_DEMO.md)

**A good outcome is not a confident-sounding answer. It is a case record that helps the user take the next step without losing what was said or what remains unverified.**
