# BolKeResolve — Follow-up UI and Account Implementation
**Date:** 4 November 2026  
**Scope:** Live Resolution consent controls, layout refinement, homepage photography, and discoverable local account access.  
**Implementation:** additive; existing resolution and case engines retained.

## What was wrong in the supplied screenshots

The optional AI rows were implemented as real checkbox labels, but the provider-unavailable logic hid the label while an older `display:grid !important` rule in `live-room.css` overrode the browser's hidden state. The empty square therefore remained on screen, next to the unavailability notice. This was a CSS cascade defect, not a missing click handler.

The account form was already present in the HTML and its API existed, but there was no visible header entry to open it. Additionally, authentication APIs were gated by `AUTH_REQUIRED`, which is false in a default local development process. That made the account experience hard to discover and test locally.

## Changes shipped

### 1. Live Resolution start screen

- Added `experience-refresh.css` after the legacy component sheets so the new states take precedence.
- Added an explicit hidden-state rule with matching selector specificity for `.live-room-ai-consent[hidden]`; unavailable providers now show a readable capability status without a dead checkbox square.
- When a provider is configured, the real checkbox is enabled and the entire labelled row remains a clickable target with visible focus styling.
- Unavailable options are disabled, unchecked, and removed from the accessibility tree. AI case interpretation, translation, and browser microphone/camera permissions remain distinct concepts.
- Improved the start page's two-column layout, text widths, spacing, trust panel, three workflow tiles, consent panel, CTAs and responsive single-column mobile layout.
- The feature is not falsely presented as available when the AI provider or translation provider has not been configured. A status explanation is shown; users can still continue with deterministic/rule-based guidance and typing.

### 2. Homepage

- Replaced the single static hero visual with three context-matched, real Pexels photographs: describing the problem, reviewing evidence, and taking the next step.
- Added a slow 24-second cross-fade sequence and captions, with distinct local fallbacks if a third-party image host is blocked.
- Added a visible pause/play control for people who do not want motion; the control is hidden when the operating system requests reduced motion, and the first image remains static.
- Refined issue cards, section alignment, card spacing, image proportions, and responsive behaviour while keeping the existing cream, deep-green and mint identity.
- Reused photographs whose source pages and license notes already exist in `ASSET_CREDITS.md`. The pictured people are not represented as customers or endorsers.

### 3. Sign-in and sign-up

- Added an always-visible `Sign in / Sign up` header entry when accounts are enabled.
- The entry opens the existing account form in a split visual panel. Users can switch between sign-in and create-account modes, request password recovery, and close to continue as a guest only when authentication is optional. The dialog has a labelled modal role, initial focus, a keyboard focus loop and Escape-to-close only in optional-auth mode.
- After successful authentication the header shows the account email, Account/Security and Sign out controls.
- Existing backend routes for registration, login, verification, password recovery, session management, password change and account deletion remain the source of truth; no new client-only authentication was introduced.

### 4. Local identity and case isolation

- `BOLKE_ACCOUNTS_ENABLED` controls whether account APIs and the header entry are available. It defaults to enabled in local development.
- `BOLKE_AUTH_REQUIRED` decides whether users must sign in before accessing/saving cases. The supplied `.env.example` now sets it to `true` so a fresh local setup uses private account workspaces.
- Even when sign-in is optional, the backend resolves an available session on every private API request and scopes signed-in users' cases to their `owner_id`. Guest users only see guest-owned (`owner_id IS NULL`) cases; they cannot view a signed-in account's cases.
- Important: when `BOLKE_AUTH_REQUIRED=false`, multiple anonymous visitors on that same local database share the guest workspace. Use this mode only for a single trusted local demo with synthetic data. Existing `.env` files are not automatically overwritten; set `BOLKE_AUTH_REQUIRED=true` manually and restart to require private accounts.
- Production still forces authentication and requires HTTPS, secure cookies, a trusted public origin and configured TLS-protected SMTP for email verification/reset.

## Research and design references used

- GOV.UK Design System: checkbox semantics, labels and task clarity — https://design-system.service.gov.uk/components/checkboxes/
- U.S. Web Design System: checkbox/form structure and accessible form guidance — https://designsystem.digital.gov/components/checkbox/
- W3C WCAG 2.2: minimum pointer target size (2.5.8) — https://www.w3.org/TR/WCAG22/#target-size-minimum
- W3C WCAG: pause, stop, hide for moving/auto-updating content (2.2.2) — https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html
- MDN: `prefers-reduced-motion` — https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion
- Pexels license and image source records — https://www.pexels.com/legal-pages/license/ and `ASSET_CREDITS.md`

The design keeps the existing lightweight HTML/CSS/JavaScript frontend and custom FastAPI account routes rather than introducing a new framework or a separate hosted identity system that would require migration and additional account/data separation work.

## Verification

- `python -m compileall -q backend tests` — passed.
- `node --check frontend/app.js` — passed.
- `python -m unittest discover -s tests -v` — **354 tests passed**.
- Regression tests added for the hidden checkbox state, account header entry, local account enablement, account isolation between two users and guest workspace, hero photo sequence, pause control and reduced-motion styling.
- Local HTTP health/API check returned HTTP 200.
- A Playwright Chromium attempt against `http://127.0.0.1` was blocked by the execution environment (`ERR_BLOCKED_BY_ADMINISTRATOR`). Consequently, visual rendering, real-browser interaction and viewport screenshots are **not marked as passed**. Run the manual browser checks below on the target machine.

## Manual acceptance checklist on local Chrome/Edge

1. Start the app with `.env` containing `BOLKE_ACCOUNTS_ENABLED=true` and `BOLKE_AUTH_REQUIRED=true`.
2. Confirm the header visibly offers **Sign in / Sign up** while signed out.
3. Open the form, switch to Create account, register with a unique email and a 12+ character password, and confirm the account header state appears after success.
4. Sign out, sign back in, and verify cases are restored to that account. Create a second account and confirm it cannot list/open the first account's cases.
5. With AI case understanding and translation providers unconfigured, confirm the start screen shows their explanatory status rows and no empty checkbox squares.
6. In a configuration where the corresponding providers are enabled, confirm each actual checkbox can be selected by mouse and keyboard, and that consent remains separate for each capability.
7. Confirm the Live Resolution start card, trust strip, consent panel and action buttons fit at desktop and mobile widths with no clipped content or horizontal scrolling.
8. Confirm the homepage photo captions transition slowly, the Pause button stops the sequence, Play resumes it, and OS reduced-motion preference keeps the first image static.
9. Confirm the photo images fall back to local assets with the network disconnected.
10. Confirm existing guided chat, Live Room capture, evidence previews, case history and exports continue to work.

## Remaining production gates

This implementation does not create a hosted cloud database or private object-storage service. The current application remains SQLite-backed with owner checks at the API layer, not PostgreSQL RLS. Real SMTP delivery, public HTTPS, malware scanning, durable cloud storage, tested backups/restores, MFA/passkeys, external security testing, privacy/legal review and normal-device browser accessibility QA remain operator/deployment requirements. Do not represent these as completed by the local UI changes.
