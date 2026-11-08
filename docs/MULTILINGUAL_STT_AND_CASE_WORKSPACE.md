# BolKeResolve: multilingual speech and case workspace — implementation notes

Updated: 20 October 2026

For safely carrying forward existing local case data and evidence, see [`UPGRADE_GUIDE_2026-10-20.md`](UPGRADE_GUIDE_2026-10-20.md).

## What changed in this build

### Voice intake

- The default speech option is now **Auto-detect** and sends a comma-separated list of the ten configured Indian locales to Gnani REST STT, following the published Gnani Vachana SDK changelog note about REST language auto-detection.
- Users can still pin one language from the accessible native-script language chooser when they know what they are speaking.
- `itn_native_numerals=false` is omitted rather than explicitly sent. This matches the official SDK's pattern of including the field only when enabled and avoids a needless request field.
- Voice requests now carry a non-secret request ID for troubleshooting. Sanitized provider error details appear in the UI response (without exposing headers or keys) rather than a generic "HTTP 400" alone.
- Successful transcripts remain editable and case-field extraction remains a suggestion, not verified transaction data.
- The health endpoint deliberately reports provider auto-detection as **not yet live-verified**. Unit tests mock Gnani; they do not prove the user's API key supports auto mode.

### An important provider caveat

Gnani's public materials are not fully consistent at the time of this update. The changelog documents comma-separated language auto-detection for REST, while the current REST reference describes `language_code` as one of the listed BCP-47 locales and does not show auto mode in its request schema. The public SDK source also validates one locale before sending. The app calls REST directly so it can try the documented changelog behavior without the SDK's local validator, but the live result can depend on the endpoint/account's current feature rollout. If this request gets a language-related 400, the app should tell the user to pin the spoken language and ask Gnani to confirm/enable REST language auto-detection for that key. Do not tell judges or users that this feature is live until a recording has passed through the actual key.

Official references:

- REST STT request/parameters and supported locales: https://docs.gnani.ai/api/STT/speech-to-text
- SDK changelog mentioning REST auto-detection: https://github.com/Gnani-AI-Mintlify/Gnani-Vachana/blob/main/CHANGELOG.md
- SDK source/client behavior: https://github.com/Gnani-AI-Mintlify/Gnani-Vachana

### Case workflow / presentation

The case detail screen is now an action workspace, not a long stack of unrelated cards:

1. **Top snapshot** — issue, case ID, reported amount, merchant, date, evidence count and current stage.
2. **Next steps** — one recommended first action and an expandable, numbered plan with official sources tucked behind a disclosure.
3. **Evidence** — a dedicated view for uploaded receipts/screenshots, plus a clear empty state and privacy reminder.
4. **Message** — a dedicated view for the editable complaint/support message and language variants. Nothing sends automatically.
5. **Activity** — progress history and notes.

A sticky tab bar lets people switch context without traversing the entire document. On desktop, a compact right rail keeps the missing-info checklist and user-reported progress nearby; on small screens, this collapses to one column. Full story and editable facts are in progressive disclosures rather than dominating the initial view. Keyboard focus styles and reduced-motion handling have been added for the new workspace.

The reference pattern is the idea of a single contextual workspace seen in products such as Intercom Inbox, alongside Linear's issue-as-unit-of-work approach—not a copied visual or a claim that those products solve consumer disputes. Intercom describes keeping conversation context and actions together; Linear treats issues as tracked units with stable identifiers and status. References: https://www.intercom.com/help/en/articles/6258745-the-inbox-explained and https://linear.app/docs/creating-issues.

### Resolution behavior

- Saving an edited case re-runs the deterministic resolution classifier and rebuilds its source-backed plan.
- A **Refresh plan** action can reclassify older cases using the currently saved description. The example Zomato refund story should now route to **Refund not received** instead of remaining **Other payment issue**.
- Activity entries record when case facts or guidance were updated.
- Guidance remains explicit about uncertainty: case details are user-reported; no bank/merchant records are queried and no complaint is submitted.

## Speech recognition choices for the product roadmap

| Option | Strength | Cost/operations | Best use in BolKeResolve |
|---|---|---|---|
| Gnani Prisma REST | Existing integration; ten supported Indian-language locales; ITN helps normalize Indian currency/numbers; low integration change | Requires valid Gnani credentials and confirmation of auto-detection support for the user's account | Primary provider once live locale-detection and each pinned locale are verified |
| Gnani realtime WebSocket | Lower-latency streaming events and voice activity handling | Different PCM/WebSocket contract; more state and reconnect handling | Later upgrade when the one-shot voice-to-case path works reliably |
| OpenAI Whisper API | Multilingual recognition, language identification and translation documented by the provider | Metered API and an additional external-data processor/key; audio must not be sent there silently | Optional explicit user-consented fallback or benchmark provider, not an invisible backup |
| AI4Bharat IndicConformer | Open models covering 22 scheduled Indian languages; can be self-hosted and customized | Heavier deployment, inference infrastructure, model performance/latency tuning and additional ops | Future sovereignty/coverage experiment after building a representative benchmark |

References: 
- Gnani REST STT: https://docs.gnani.ai/api/STT/speech-to-text
- AI4Bharat model and code: https://github.com/AI4Bharat/IndicConformerASR and https://ai4bharat.iitm.ac.in/areas/model/ASR/IndicConformer/
- Whisper model and pricing: https://developers.openai.com/api/docs/models/whisper-1

Do not assume language identification makes arbitrary code-switching perfectly accurate. Evaluate separate utterance types: one language per sentence, Hindi-English Hinglish, Marathi-English, native script, Romanized Hindi, background noise, brand names (e.g. Zomato), Indian currency amounts, dates, corrections and short/long clips.

## Live validation matrix still required

Before claiming this is production-ready, test the actual Gnani key in a local environment and record the HTTP status + safe provider error text:

- Hindi audio, Auto-detect
- Hindi audio, pinned `hi-IN`
- English audio, Auto-detect
- Marathi audio, Auto-detect and pinned `mr-IN`
- Hindi-English Hinglish, Auto-detect
- a code-mixed utterance with a rupee amount and relative date
- a noisy/near-silent clip (expected graceful failure)
- unauthorized key / no-credit response (must never leak the key)

For all successful samples, manually verify transcript, extracted merchant, amount and date. Do not let a plausible but incorrect transcript silently populate case facts. Keep ambiguous amounts/dates flagged for user confirmation.

## Local verification performed

- `python -m unittest discover -s tests -v`: **55 tests passed** after the final UI asset assertion.
- `node --check frontend/app.js`: passed.
- `python -m compileall -q backend`: passed.
- Automated browser screenshot attempt was blocked by the execution environment's local-navigation policy, so this update does **not** claim a browser-rendered visual QA sign-off.


## UX reliability patch (2026-10-20)

- Voice UI language choice now uses user-facing language only; provider names, API-key eligibility, and server error types are not displayed. Errors remain generic and actionable.
- The transcript is run through the same extraction-preview endpoint as typed text before candidate facts are applied. Existing non-default user answers are preserved; suggestions stay reviewable.
- When the recognizer returns a strongly English-like sentence rendered in Devanagari, the app uses a conservative token map to make common words readable in Latin script before extraction. This is a presentation fallback, not translation; unknown words are preserved. The user can still edit the transcript.
- App HTML/JS/CSS are served with no-store headers to prevent an old cached interface from continuing to show previous provider-specific copy after an upgrade.
- Research: Gnani's public SDK documentation supports fixed language codes and documents comma-separated REST language lists for detection, but actual account behavior can vary. Do not expose that implementation detail to end users. AI4Bharat IndicConformer is a credible future benchmark/fallback candidate for 22 scheduled languages, but it has model/deployment requirements and is not added as a dependency in this lightweight Windows MVP.

## Research notes and design decisions

### Speech recognition

- **Gnani Vachana (official SDK and changelog):** the REST client accepts explicit BCP-47 language codes. The changelog/README also describes multi-language REST requests (comma-separated codes and `auto` in current SDK docs). This does not guarantee every account or API deployment has that capability enabled; BolKeResolve therefore keeps a user-selected-language fallback and does not expose provider configuration errors in its interface. Sources: https://github.com/Gnani-AI-Mintlify/Gnani-Vachana and https://github.com/Gnani-AI-Mintlify/gnani-vachana/blob/main/CHANGELOG.md
- **AI4Bharat IndicConformer:** open-source ASR models covering 22 scheduled Indian languages. It is a useful future benchmark or self-hosted fallback, but its model weights, inference stack, hardware and runtime requirements make it a separate deployment decision rather than a dependency bundled into this Windows MVP. Sources: https://github.com/AI4Bharat/IndicConformerASR and https://huggingface.co/ai4bharat/indic-conformer-600m-multilingual
- **OpenAI Whisper:** a widely used multilingual ASR baseline with explicit-language transcription options. It is a useful comparative benchmark, but does not by itself guarantee best performance on code-mixed Indian speech. Source: https://github.com/openai/whisper

### UX patterns applied

1. **Progressive disclosure:** do not show provider, endpoint, key permissions, raw error strings, or internal model names in the consumer interface. Offer one clear next action.
2. **Editable extraction:** treat each extracted value as a suggestion, preserve user-entered values, and show evidence/confirmation states rather than silently claiming correctness.
3. **One source of truth:** run both typed text and the final speech transcript through `/api/extraction/preview`; do not rely only on optional fields returned by a transcription vendor.
4. **Recover without re-recording:** keep the recorded blob temporarily in the page if language selection is needed, and retry the same clip after the user selects a language.
5. **Avoid stale UI:** serve the app shell and first-party JavaScript/CSS with `Cache-Control: no-store` so fixes aren't hidden by a cached older script.
6. **Conservative script repair:** if a transcript strongly resembles English phonetics rendered in Devanagari, convert a small known-token set to readable English before extracting facts. Unknown words are retained; this is not translation and the transcript remains editable.

### Acceptance scenarios

- English selected; provider returns common English phrases in Devanagari: transcript becomes readable English and the Zomato/₹850/refund facts are extracted.
- Auto mode is rejected: the user sees a simple language choice and can retry the same recording, without seeing provider names or account/endpoint details.
- User types the same story: the same extraction endpoint identifies issue, merchant, amount and refund status.
- A field the user already changed is not silently overwritten; conflicting or uncertain values remain reviewable.

### Remaining limitation

No live API key is included in the project, so account-specific language auto-detection and live recognition quality must still be validated with the user's own account. The deterministic script-repair dictionary is intentionally narrow; native-language, code-switched and unusual phonetic transcripts need a labelled evaluation set and human review before broadening it.
