# BolKeResolve — Voice-to-Proof Consumer Resolution Workspace

**Great Indian AI Internship Challenge 2026**  
**Tagline:** Your words. Your evidence. Your next move.

## Problem

A failed UPI payment, pending transfer or delayed refund can leave people juggling screenshots, SMS messages, reference numbers and support conversations. When stressed, many users would rather explain the issue aloud—in familiar Hinglish—than complete a long English form. The details then remain scattered and the next step is unclear.

## Solution

**BolKeResolve turns a spoken consumer complaint into a user-reviewed, evidence-linked case.** It brings the conversation, supporting files, timeline, support commitments and suggested next steps into one portable record.

## How it works

1. **Speak:** Describe the payment or refund issue naturally in Hinglish or text.
2. **Review:** Gnani speech-to-text produces a transcript; the user checks and confirms key details.
3. **Organise:** The app structures the case, keeps evidence with its source, provides issue-specific next-step guidance and records support commitments.
4. **Follow through:** The Promise-to-Proof ledger preserves the original wording, amount, condition and timeframe of a support promise. Later updates are recorded separately, with user-reported information clearly distinguished from independently verified facts.
5. **Take it forward:** Export a Resolution Passport with the case summary, timeline, evidence index and file hashes.

## Gnani AI integration

- **Gnani Prisma v3.0 — Speech-to-text (STT):** powers spoken complaint transcription.
- **Gnani Timbre v2.5 — Text-to-speech (TTS):** powers spoken responses.

The Promise-to-Proof extraction, estimated-date calculations and reconciliation are application logic. This project does not claim to use Evon.

## What makes it different

- Voice-first intake for everyday Indian payment and refund problems.
- A case workflow rather than a generic chatbot response.
- Original support statements and later updates remain traceable instead of being overwritten.
- Source-aware records distinguish user statements, extracted suggestions, user-confirmed facts and independently verified facts.
- A portable case export helps the user continue with the relevant support channel.

## Trust boundaries

BolKeResolve organises user-provided information and suggests next steps. It does **not** access bank accounts, verify UPI transactions, contact merchants, initiate payments or refunds, or claim that a refund has been independently confirmed. File hashes can help detect file changes; they do not prove who created a file or whether its contents are true. Demo data is synthetic.

## Implementation and links

- **Live application:** https://bolkeresolve.vercel.app
- **Source code:** https://github.com/Prakash-codeMaker/BolKeResolve
- **Primary challenge fit:** Real Deal
- **Additional strength:** Mixed Vibes (Hinglish voice interaction)

**Demo:** The public 2–3 minute recording shows the real voice intake, transcript review, next-step guidance, Promise-to-Proof follow-up and Resolution Passport. Model attribution in the recording is limited to the Gnani API calls actually shown working.
