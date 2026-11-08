# Changelog — Live Resolution UI, homepage and accounts
**Date:** 4 November 2026

- Fixed hidden AI-consent labels being overridden by a legacy `display:grid !important` rule; unavailable capabilities now show status messages without orphan checkbox squares.
- Improved Live Resolution heading, trust panel, action tiles, consent card, spacing, typography, buttons and responsive layout.
- Added a visible account header entry and refreshed split-panel sign-in/sign-up screen; connected it to the existing FastAPI account/session routes. Added modal semantics, focus management and a keyboard focus loop.
- Enabled account routes in local development independently of whether authentication is mandatory. Private API requests resolve sessions and scope cases by `owner_id`.
- Set fresh `.env.example` setup to require authentication and clarified that optional guest-mode cases share the local anonymous workspace.
- Added slow Pexels hero photo sequence with captions, local image fallbacks, explicit pause/play control and reduced-motion support (static first image; no pause control when motion is reduced).
- Added regression coverage for control visibility, account discovery/local mode, case isolation and animated homepage assets.
- Bumped public service-worker cache to `bolkeresolve-shell-v47` and precached the new stylesheet.
- Updated README, asset credits and implementation documentation.

Verification: 355 tests passed; Python compile and JavaScript syntax checks passed. Browser visual QA remains unverified because Chromium navigation is blocked in this execution environment.


## Follow-up corrective pass — Guided Chat voice, Live Resolution consent and homepage

- Corrected `/api/config` so authenticated production users are considered eligible for Guided Chat voice when the speech service is configured. The public-voice opt-in now applies only to anonymous production sessions, matching the authorization branch in `/api/voice/transcribe`.
- Removed provider names and environment-variable instructions from Guided Chat voice-status copy. The visitor sees whether voice is ready or can type instead.
- Fixed the checkbox cascade by explicitly hiding unavailable consent labels with a final, high-specificity rule and inline hidden-state handling. Available controls remain native, label-clickable and keyboard-operable.
- Kept capability boundaries accurate: speech transcription uses `GNANI_API_KEY`; optional case interpretation and translation use `OPENAI_API_KEY`. The latter controls remain unavailable until that feature is configured.
- Simplified the disclosure below Start Live Resolution and strengthened the homepage's photo-led hero and dark-green issue selector.
- Bumped the service-worker shell to `bolkeresolve-shell-v47`.

Verification: the regression suite passed at the implementation checkpoint (355 tests). Python compilation and JavaScript syntax checks passed. The local HTTP health/config/static-asset smoke checks passed. Real Chromium interaction remains unverified because this execution environment blocks local browser navigation (`ERR_BLOCKED_BY_ADMINISTRATOR`).
