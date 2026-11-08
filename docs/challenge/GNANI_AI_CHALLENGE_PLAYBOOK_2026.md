# BolKeResolve — Great Indian AI Internship Challenge (Gnani AI), 2026

**Challenge-aligned project title:** BolKeResolve: Hinglish Voice-to-Resolution Passport  
**One-line pitch:** Turn a naturally spoken Hinglish payment problem into a reviewed case, a source-backed next step, and a portable evidence passport.

> Official challenge reference: https://www.gnani.ai/internship and official participation terms: https://www.gnani.ai/great-indian-ai-internship-registration-form. Recheck both before submission in case terms change.

## 1. What this project does

BolKeResolve helps people who are stuck with failed/pending UPI payments or delayed refunds explain the problem in their own words. The app uses Gnani AI Prisma v2.5 to transcribe spoken audio when configured. The user reviews the transcript; a conservative extraction layer proposes facts such as amount, merchant and issue type; the user confirms or corrects those details. A deterministic playbook then presents an issue-specific next step with links to official sources. Users can create a case, prepare an editable support message, organise an evidence checklist, track user-reported events, and export/print a Resolution Passport they can carry to another support channel.

The useful outcome is not “AI writes a complaint.” It is **voice → reviewable facts → appropriate next step → evidence-backed case record**.

## 2. Target user and real-world problem

Primary user: an Indian consumer who speaks naturally in Hindi/Hinglish or another supported Indian language and has a failed/pending payment or delayed refund, but is unsure which facts matter and which support route applies.

The user may not know the formal vocabulary, may have transaction evidence spread across apps, and may need to repeat the story when moving from a merchant to a payment app or bank. BolKeResolve lowers the first-step burden while remaining explicit that it does not independently verify bank records or force/guarantee a refund.

## 3. Why Gnani AI is central, not a decorative add-on

- **Prisma v2.5 (speech-to-text):** the app records up to 60 seconds in the browser, submits audio to the server after the user stops, calls Gnani's documented STT endpoint, then displays an editable transcript before the user sends/saves anything.
- **Timbre v2.5 (text-to-speech):** the backend has a server-side read-aloud adapter. The app may use it for supported read-aloud flows. Show a real successful Timbre call in the demo only after confirming this endpoint with the registered API account.
- **No API key in the browser:** secrets remain server-side in `GNANI_API_KEY`; never commit `.env`, expose the key, or put it in a screen recording.
- **Downstream logic:** current issue/fact extraction is conservative and the resolution playbooks are deterministic/curated. Do not claim that Prisma determines refund eligibility or that Gnani independently checks transactions.

Documented endpoints implemented in `backend/main.py`:

- STT: `POST https://api.vachana.ai/stt/v3`, header `X-API-Key-ID`, multipart `audio_file` and `language_code`.
- TTS: `POST https://api.vachana.ai/api/v1/tts/inference`, header `X-API-Key-ID`, `model: timbre-v2.5`.

Current contract tests use mocked responses. **The project still needs a live smoke test using the participant's own valid key before we may say the live integration was verified.**

## 4. Recommended challenge positioning

**Primary award lens to lean into: Mixed Vibes Award.** The strongest match is a real code-mixed voice interaction—ordinary Hinglish into a useful structured result—not simply a multilingual selector. Show a single naturally code-mixed utterance and demonstrate the actual Prisma output, correction/confirmation, and final case record.

**Real-world impact is the product's wider story.** Failed payments and delayed refunds are relatable, practical problems. Keep that impact tangible, but avoid diluting the 60-second demo with every feature. The official rules state that an entry/team can win no more than one award, so make the demo's primary story clear rather than pitching five award categories at once.

Possible alternate lens: Real Deal Award, if user testing shows the clearest proof is helping a real consumer take the correct next step. Decide deliberately before publishing.

## 5. What is implemented now

- Voice recording and a language selector for 10 configured speech locales.
- Real HTTP adapter paths for Prisma STT and Timbre TTS, behind server-side configuration.
- Editable transcript before use.
- Conservative extraction of candidate facts, with explicit review/confirmation and ambiguity handling.
- Deterministic first-pass resolution playbooks with links to official support/rule sources.
- Editable support-message drafts and an exportable/printable Resolution Passport.
- A local test suite for API request/response contracts, rate limits, extraction, auth and frontend assets.
- This challenge pack: project narrative, demo script, post draft, checklist and interview prep.

## 6. What is not currently proven or should not be claimed

- The live Prisma/Timbre APIs have not been tested with the applicant's account credentials in this packaging environment.
- The app does not independently verify payment/refund transactions and does not guarantee successful recovery.
- The app does not automatically submit complaints to NPCI, RBI, NCH, a merchant or a bank.
- It does not have unrestricted access to UPI, bank, NPCI or regulator case databases.
- The provided mock-based tests are not evidence of live transcription quality, production availability or a refund outcome.
- Do not claim a real user saved money or recovered a refund unless there is authentic, permissioned evidence.

## 7. Official challenge rules checklist (as reviewed 22 October 2026)

Official page: https://www.gnani.ai/internship

- Open brief: build a **working app** that uses at least one Gnani AI model/API for a practical need.
- Eligibility: currently enrolled in a degree/course at a college/university in India and at least 18 years old when registering.
- Solo or team of two only. Every member must independently meet the conditions and participate/accept terms.
- Name the Gnani model(s)/API(s), describe the problem and users, and state each member's real contribution.
- Publish a public video of the working app on LinkedIn and/or X **before** final submission; explain the build and Gnani technology, tag Gnani AI's official account, and include both `#GnaniAI` and `#GreatIndianAIInternshipChallenge`.
- Nominate the public post link(s) in the submission. Posting/tagging by itself does not complete entry.
- Deadline: **10 November 2026 at 11:59 PM IST**, as shown on the official page reviewed on 22 October 2026. Do not rely on a later deadline unless the official page changes.
- The challenge page says verified reactions, comments and reshares on nominated posts affect shortlisting; interview skill and performance affect internship offers.
- Bought engagement, bots, paid promotion, engagement swaps, plagiarism and misleading demos are prohibited. Do not use them.
- Use synthetic data in the demo. Do not show real phone numbers, bank/account numbers, Aadhaar/PAN, private documents, or recorded calls from real people.
- Each entry/team may receive at most one of the ten ₹50,000 award categories; awards are separate from internship selection.

## 8. Demo acceptance test (must pass before recording)

1. Deploy/run with a valid Gnani API key in the server environment. Confirm the key never appears in JS, page source, browser requests, errors, logs shared in the video, or Git history.
2. Record a new synthetic Hinglish utterance; do not play back an already typed transcript and imply it came from speech.
3. Confirm the network request reaches the Gnani endpoint and a real transcript returns. Keep the returned transcript visible and editable.
4. Fix any mistaken transcription manually and show the corrected facts before saving.
5. Confirm the app distinguishes the actual scenario (e.g. transfer pending vs merchant refund delayed), displays the relevant official source/route, and does not present a guessed date or amount as verified.
6. Save the case and show the generated message/Resolution Passport.
7. If demonstrating Timbre, make a real request and play its generated audio. If not live-tested, leave it out of the claim/video.
8. Check fallback, errors, request quotas and remaining programme credits. A missing/invalid provider key must not be presented as working voice service.
9. Use synthetic data, hide credentials and avoid government/merchant logos that could imply partnership or endorsement.
10. Run `python -m pytest -q` and `node --check frontend/app.js` after final changes.

## 9. Team contribution declaration

Replace the template below with accurate details before submission; do not claim work another person performed.

- Primary participant: `[name]` — `[specific work personally completed]`.
- Teammate (if any): `[name]` — `[specific work personally completed]`.
- Gnani AI APIs integrated by the team: Prisma v2.5 STT; Timbre v2.5 TTS only if the live adapter is demonstrated and verified.
- Other tools/frameworks: FastAPI, vanilla JavaScript, SQLite and browser APIs, plus the packages listed in `requirements.txt`.

## 10. Suggested submission description

**BolKeResolve: Hinglish Voice-to-Resolution Passport** is a voice-first consumer-support prototype for people dealing with failed/pending UPI payments or delayed refunds. A user can explain the issue naturally in Hinglish, review a transcript produced by Gnani AI Prisma v2.5, confirm extracted case facts, and get a practical next step grounded in a deterministic playbook and official-source links. The user can prepare an editable support message and save or export a Resolution Passport containing the case facts, evidence checklist and follow-up history.

The design treats voice as an accessibility path into a useful workflow, not an end in itself. It keeps the transcript editable, labels facts as user-reported until confirmed, avoids requesting sensitive authentication secrets, and does not claim to verify payment records or guarantee a refund. The current prototype uses Gnani AI's Prisma v2.5 speech-to-text API and includes an adapter for Timbre v2.5 text-to-speech. Live provider behavior must be validated with the registered account before the submission claims successful live calls.

## 11. Interview framing

Be ready to explain:
- Why speech-first entry lowers form friction for code-mixed speakers.
- Exactly where the Gnani request is made, how the key is protected, how rate limiting works, and what happens on provider errors.
- How ambiguity is handled and why extracted amounts, dates and issue types are suggestions until the user confirms them.
- Why the routing engine uses deterministic, source-linked rules instead of asking an LLM to improvise legal/regulatory timelines.
- Which parts are mocked in tests vs checked through live APIs.
- What product/security gaps remain before public production use.
- What you personally built and what you learned from the integration.
