# Challenge technology notes and sources

Reviewed on 22 October 2026. Recheck before final submission.

- Challenge overview, models, awards, eligibility, public demo and deadline: https://www.gnani.ai/internship
- Participation terms and required submission materials: https://www.gnani.ai/great-indian-ai-internship-registration-form
- Gnani speech API introduction and authentication header: https://docs.gnani.ai/api/introduction/introduction
- Prisma STT REST documentation: https://docs.gnani.ai/api/STT/speech-to-text
- Timbre TTS inference documentation: https://docs.gnani.ai/api/TTS/tts-inference

## Notes for the challenge reviewer

- Prisma v2.5 endpoint configured in `backend/main.py`: `https://api.vachana.ai/stt/v3`.
- Timbre v2.5 endpoint configured in `backend/main.py`: `https://api.vachana.ai/api/v1/tts/inference`.
- Auth header: `X-API-Key-ID`; the key comes from the server environment variable `GNANI_API_KEY`.
- The app uses the returned transcript to propose case facts but does not claim that speech recognition validates bank activity.
- Existing automated API tests use fakes/mocks. A true challenge demo must use a participant-owned valid key and show a real successful call. Document which model actually appears in the recording.
