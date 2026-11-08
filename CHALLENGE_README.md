# BolKeResolve — Great Indian AI Internship Challenge (Gnani AI), 2026

Project name for submission: **BolKeResolve: Hinglish Voice-to-Resolution Passport**.

Start with [`START_HERE_GNANI_AI_CHALLENGE_2026.md`](START_HERE_GNANI_AI_CHALLENGE_2026.md), then read `docs/challenge/GNANI_AI_CHALLENGE_PLAYBOOK_2026.md`.

This project is a voice-first workflow for common Indian payment disputes. It integrates adapters for Gnani AI Prisma v2.5 speech-to-text and Timbre v2.5 text-to-speech. The API credential stays on the server. The included automated tests mock provider responses; **before recording the public challenge demo, run and capture a successful live Prisma call with the participant's own registered API key**. Demonstrate Timbre only if a live TTS call is tested.

The app does not verify payment records or guarantee refunds. The resolution playbooks link to official information; users retain control of the transcript, case facts, support message and handoff.

## Challenge links and deadline

- Official page: https://www.gnani.ai/internship
- Official registration/submission terms: https://www.gnani.ai/great-indian-ai-internship-registration-form
- Current deadline on official page as checked 22 October 2026: **10 November 2026, 11:59 PM IST**. Recheck before submission.

The rules require an eligible participant (currently enrolled at an Indian college/university and 18+), solo or team of two; a working app using at least one Gnani AI model/API; a public demo video posted to LinkedIn and/or X before final submission; official account tag plus `#GnaniAI` and `#GreatIndianAIInternshipChallenge`; and nomination of the post URL in the submission. Bought engagement, bots, paid promotion, engagement swaps, plagiarism and misleading demos are prohibited.

No personal API key, `.env`, runtime cases or real consumer information is included in this package. See `.env.example` for configuration names.
