# Vercel launch preparation — 4 November 2026

## Deployment architecture

- Added `vercel.json` to deploy `frontend/` as a static site.
- Added same-origin `/api/*` external rewrite to the Render service named by `render.yaml` (`https://bolkeresolve.onrender.com`). Update that destination if Render assigns another hostname.
- Added security headers, `no-referrer` protection for one-time auth links, strict transport security, and no-cache rules for the service worker/app shell.
- Added `.vercelignore` to keep runtime data, local secrets, backend sources and test/doc directories out of the static frontend deployment upload.
- Kept persistent SQLite/evidence storage on Render at `/var/data`; do not deploy the current local-filesystem database/storage layer as a Vercel Function.

## Render production environment

- Made account/auth/email-verification settings explicit in `render.yaml`.
- Added `BOLKE_ALLOWED_ORIGINS` for exact, optional Preview/staging origin allowlisting while retaining `BOLKE_PUBLIC_ORIGIN` as the canonical email-link origin; the HTTP mutation and WebSocket origin checks share the same helper and reject wildcard origins.
- Added SMTP variable placeholders for production verification and password recovery.
- Added optional OpenAI, Share-to-Case encryption and anonymous voice configuration entries.
- Retained the 1 GB persistent disk mount and `/var/data` data directory.

## Verification

- `vercel.json` parses as valid JSON.
- Python compilation passed.
- `node --check frontend/app.js` passed.
- `node --check frontend/sw.js` passed.
- Full test suite: 360 passed, 129 additional subtests passed.
- Added tests for Vercel static output, API rewrite coverage, private API no-cache policy and Render persistent-disk/auth/email environment configuration.

## Remaining production blockers / operator checks

- `scripts/check_release_readiness.py` still fails the production privacy-content check because `frontend/privacy.html` contains legal/operator placeholders for the responsible entity, contact, retention periods and age/children's-data policy. These cannot be invented in code; the operator must supply and obtain review of the real details.
- Render service must be created and its actual hostname copied into `vercel.json` if different from the default.
- SMTP, Gnani and optional OpenAI credentials must be configured in Render, not exposed in frontend/Vercel client variables.
- Verify account creation/email verification/password reset, case isolation, file upload/download, exports and deletion on the deployed Preview.
- Verify the Live Resolution WebSocket upgrade through the Vercel external rewrite. Vercel's own Function WebSocket support is generally available, but the current Vercel external rewrite docs do not explicitly guarantee this particular FastAPI-upstream WebSocket proxy path. Treat the Preview socket test as a release gate.
- Verify Render disk persistence across redeploy/restart and perform a backup restore test.
- Complete privacy/legal/security, malware-scanning, mobile/accessibility and real-provider checks before real customer data is accepted.
