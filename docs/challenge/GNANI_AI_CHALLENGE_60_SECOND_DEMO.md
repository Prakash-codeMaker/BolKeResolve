# Public submission demo: 2–3 minute walkthrough + 60-second cutdown

The Microsoft submission form asks for a **2–3 minute demo of the build**. The challenge also lists a 60-second Demo Day award category. Record the 2–3 minute walkthrough for the form; make a separate 60-second edit for the award. Do not try to squeeze the whole case workflow into one minute.

## The story

**BolKeResolve — Voice-to-Proof Consumer Resolution Workspace**

A message saying “refund initiated” is not proof that money was credited. BolKeResolve helps a user preserve the issue, supporting material, original support promise and later updates as one traceable case.

## Recommended 2:40 submission storyboard

| Time | Screen and action | Narration |
|---|---|---|
| 0:00–0:15 | Show the live application and title. State the problem. | “A failed payment or delayed refund leaves screenshots, reference numbers and support replies scattered. A refund promise is not proof of credit.” |
| 0:15–0:48 | Open a synthetic case and use the microphone. Say: “Mere ₹850 UPI se kat gaye, app failed dikha raha hai, aur saamne wale ko paise nahi mile.” Show the actual returned transcript. | “I can explain the issue in Hinglish. Gnani Prisma converts speech into text; the user still reviews the words and details.” |
| 0:48–1:10 | Review the transcript and key details. Show missing information clearly. | “The transcript is not bank verification. I can correct it, and unknown fields are not invented.” |
| 1:10–1:35 | Show issue-specific guidance, evidence checklist and official source link. | “The case now has a next step and a place for supporting records. The application does not query my bank or contact a merchant.” |
| 1:35–2:05 | In the synthetic refund case, open **Commitments & Conditions**. Load the fictional ₹850 refund example. Review source wording, amount and five-business-day timeframe, then save. | “Here is the promise as stated. BolKeResolve preserves the wording, amount and timeframe rather than treating it as a successful refund.” |
| 2:05–2:25 | Load the fictional 10 November follow-up note. Review it, keep the relation as “I’m not sure yet”, record it, and show history. | “The later update is separate and labelled user-reported. It does not erase the original promise or claim independent verification.” |
| 2:25–2:40 | Open Resolution Passport/export view and show the title/end card with app and repository. | “The user keeps a portable case record: what was said, what evidence exists and what still needs checking.” |

## Exact model attribution

The current repository `.env.example` configures:
- **Prisma v3.0** for speech-to-text.
- **Timbre v2.5** for text-to-speech.

Only say a model was used in the recorded flow when its successful live API response is shown or otherwise verified for that recording. The application's case guidance, Promise-to-Proof reconciliation and export logic are application features; do not attribute them to Evon. Keep model IDs consistent in the video, README, pitch and public post.

## Recording checklist

- Record the real deployed application, not a slide deck or prototype substitute.
- Use a real microphone interaction and keep the actual transcript response in the recording. Do not paste a transcript while implying it came from the microphone.
- Use synthetic case details only: the ₹850 example and later follow-up are fictional.
- Never show an API key, `.env` file, personal bank/UPI identifier, phone number, Aadhaar/PAN, private support message or another person's data.
- Keep transcript and UI text readable; add accurate captions.
- Do not edit a failed request to look successful or show a fake “refund credited” state.
- Clearly distinguish user-reported updates from independently verified facts.
- If spoken TTS is not played live in the recording, do not claim that the video proves a live Timbre call.
- Test the finished public video link in a fresh browser profile before submitting it.

## 60-second cutdown for Demo Day Drop

- **0–5s:** “A refund promise is not proof of credit.”
- **5–22s:** One natural Hinglish voice input and the actual returned transcript.
- **22–35s:** Show the promise ledger preserving amount and timeframe.
- **35–48s:** Show the later update as user-reported, separate from the original promise.
- **48–60s:** Show Resolution Passport and the line: “BolKeResolve — Speak the issue. Keep the proof. Know the next step.”

Do not turn the cutdown into a fast montage that hides the real interaction. It should still show actual application behaviour.

## Optional deeper evaluator walkthrough

After the submission video, be ready to demonstrate:
1. A conditional commitment whose clock must not start until its stated trigger is reviewed.
2. A missing amount or date that remains blank and triggers a clarification.
3. Contradictory support statements that are both preserved and flagged for review.
4. A user marking a case resolved without the app claiming independent bank verification.
5. The exported Resolution Passport, including provenance labels and evidence index.

## Evaluator access check

1. Open the live link in a fresh incognito/private browser and on a phone.
2. Confirm a new evaluator can reach the demo without access to your personal account or local machine.
3. If sign-in is required, do not share your personal password. Use an explicitly approved synthetic evaluator account or ask the organisers which access route they prefer.
4. Confirm demo data is synthetic and no private case is visible to another account.

The live app is an MVP. Do not claim production readiness, bank verification, automatic grievance filing or full offline case access unless those capabilities have been independently implemented and tested.