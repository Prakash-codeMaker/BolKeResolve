# BolKeResolve — Guided Chat, consent controls and homepage corrective pass
**Date:** 4 November 2026  
**Scope:** Fix the misleading Guided Chat voice warning, correct the Live Resolution optional-consent controls, remove provider-specific visitor copy, and make the homepage redesign visibly distinct.

## 1. Guided Chat voice warning — exact cause and fix

The red warning was caused by a mismatch between the public configuration endpoint and the transcription endpoint. `/api/config` previously treated `BOLKE_PUBLIC_VOICE_ENABLED` as a requirement for every production visitor. The actual `/api/voice/transcribe` handler only requires that setting for anonymous production requests; a signed-in account can use transcription when the speech provider is configured.

The config endpoint now follows that same rule:

- No speech provider key: voice is unavailable.
- Authentication is not mandatory: the configured speech service is available.
- Authentication is mandatory and the user is signed in: the configured speech service is available.
- Authentication is mandatory and the visitor is anonymous: public voice must be explicitly enabled.

This fixes the authenticated Guided Chat button being disabled and showing the anonymous-user warning even though the signed-in Live Resolution flow could use the same speech service. No API key is exposed to the browser.

Visitor-facing status is now plain language: “Voice is ready. Your transcript will appear for review before you send it.” or “Voice input is not available in this session. You can type your story instead.” Provider names and environment variable names are not shown.

## 2. The two Live Resolution consent options

The controls looked like empty checkboxes because `live-room.css` contained a legacy `display:grid !important` rule. That rule overrode the browser's hidden state on the labels, even though JavaScript had disabled the inputs. The resulting square looked interactive but could not be selected.

The corrective code explicitly hides the label when the capability is unavailable and presents a short status explanation. When the service is configured, the native checkbox returns, with the full labelled row acting as the click target and visible keyboard focus.

The two checkboxes are different from voice transcription:

- **Voice transcription:** uses `GNANI_API_KEY`.
- **AI case understanding and translation:** use the optional AI assistance service configured with `OPENAI_API_KEY`.

Therefore, configuring the Gnani speech key alone does not activate those two optional AI settings. In the current supplied `.env.example`, `OPENAI_API_KEY` is blank. The interface will not pretend that an unavailable AI feature can be enabled; it shows an honest status instead. Add a valid OpenAI key to the local `.env` to make the relevant consent controls appear and become selectable. Do not put either provider key in frontend files.

## 3. Live Resolution privacy note

The technical vendor/deployment explanation below the start button has been replaced with user-facing language. It says that microphone use is optional, speech is transcribed for review, and camera/screen sharing remain off until the user chooses them. It does not mention an API vendor or deployment variable.

## 4. Homepage presentation

The final homepage stylesheet is loaded after the existing design styles and is included in the service-worker shell. It makes the redesign visible in the first-screen experience and the issue-selection section:

- A wider editorial hero with a slow three-photo sequence, readable captions and a pause control.
- A deep-evergreen issue-selection panel with contrasting cards, larger tap targets, clearer title hierarchy and hover/focus states.
- More generous image-led “how it works” cards, with mobile stacking and reduced-motion support.
- Existing image credits and local fallback assets are retained.

The public shell cache is now `bolkeresolve-shell-v47`; this removes the old cached shell after the new service worker activates.

## 5. Tests and verification

- Regression test covers signed-in production voice with public voice disabled, anonymous production voice disabled, anonymous voice with explicit opt-in, and the no-provider case.
- Frontend tests assert provider/deployment instructions are absent from Guided Chat copy, consent controls have an authoritative hidden state, and the final homepage stylesheet is included and contains the evergreen issue-picker treatment.
- The full automated suite passed at the implementation checkpoint: **355 tests**. Python compilation and JavaScript syntax checks passed.
- Local HTTP health and static stylesheet smoke checks passed.
- Real Chromium browser navigation was blocked by the execution environment with `ERR_BLOCKED_BY_ADMINISTRATOR`; visual interaction on a normal Windows Chrome/Edge installation remains a manual acceptance test. No live Gnani request was made with a real key in this environment.

## 6. Remaining configuration

To enable the two optional AI consent options locally, configure `OPENAI_API_KEY` in the server-side `.env`. Keep `GNANI_API_KEY` server-side for speech transcription. Restart the backend after configuration changes. The public voice flag should remain disabled unless anonymous voice use is specifically intended.
