# Interview prep — BolKeResolve

## 30-second explanation

“BolKeResolve is a voice-first consumer-resolution prototype for failed UPI payments and delayed refunds. A user can explain the issue naturally in Hinglish; Gnani AI Prisma v2.5 turns speech into an editable transcript. We propose structured facts for the user to confirm, use a deterministic source-linked playbook to identify the next step, then save a support draft and portable Resolution Passport. The point isn't to claim that a model can verify a bank transaction—it's to reduce confusion and repeated explanation.”

## Likely questions

**Why use a voice model instead of a normal form?**  
The first barrier is often translating a lived experience into formal complaint fields. Voice is an accessible entry path for people who naturally code-switch. The transcript remains editable so speech recognition does not become authoritative evidence.

**What is uniquely yours beyond calling speech-to-text?**  
The downstream workflow: conservative fact extraction with review, scenario-specific routing to official sources, a user-controlled support draft, and a portable case record with user-reported timeline. Prisma is the voice input; the output is a workflow, not just a transcript.

**Why not let an LLM decide the applicable RBI/NPCI rule?**  
The current prototype uses curated deterministic playbooks for first-pass guidance. Regulatory timing is consequential and varies by scenario; rules need a source, version/date, eligibility conditions and review. A probabilistic response should not invent a deadline.

**Does the app check a bank or guarantee a refund?**  
No. It does not independently verify a transaction, submit a complaint to an institution by itself, or guarantee recovery. Facts remain user-reported unless supported by a clearly identified document or an authorised integration.

**How is the API key protected?**  
The browser uploads audio to the app backend; the backend calls Gnani with the key stored in the server environment. The key is not embedded in the JS bundle. Per-IP throttles are present, but production still needs shared gateway quotas, cost limits, monitoring and hardened deployment.

**What is tested and what isn't?**  
The automated tests mock provider responses and validate request contracts, error handling, rate limits and fact extraction. That is not live API quality testing. Before submission, I will run actual Prisma transcription with my registered key, capture the successful response in the screen recording, and test Timbre live only if I claim it.

**How do you handle a wrong transcript?**  
Show the text before it is saved or used. The user can edit it; extracted fields are suggestions and ambiguous values require confirmation. A transcript is not a verified transaction.

**What would you build next?**  
A source-versioned routing engine with explicit applicability conditions; more systematic speech evaluation across accents/code-mixing/noise; reply-aware follow-up; security review and, later, an authorised two-way integration with a willing merchant or support organisation.

## Personal contribution

Use a concise, honest breakdown in first person and be ready to discuss code you personally wrote. For teams, list the other member's work separately. Never claim someone else's implementation or rely on ununderstood generated code during an interview.
