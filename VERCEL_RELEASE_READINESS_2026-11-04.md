# BolKeResolve — Vercel release-readiness result

**Review date:** 4 November 2026  
**Result:** technical Preview candidate prepared; public production launch remains gated.

## What is ready in the repository

- Static frontend output configured as `frontend/` in `vercel.json`.
- Same-origin `/api/*` rewrite configured to the Render service hostname declared by `render.yaml` (verify the actual Render hostname after Blueprint creation).
- Production Render Blueprint retains the persistent 1 GB disk at `/var/data`, where SQLite and original evidence files are stored.
- Secure browser headers and service-worker/app-shell revalidation configured for Vercel static responses.
- Exact optional Preview-origin allowlist supported through `BOLKE_ALLOWED_ORIGINS`; wildcard origins are rejected. `BOLKE_PUBLIC_ORIGIN` remains the canonical origin for verification/reset links.
- Deployment steps and acceptance tests documented in `VERCEL_DEPLOYMENT_GUIDE.md`.

## Local verification

- `python -m compileall -q backend` — passed.
- `node --check frontend/app.js` — passed.
- `node --check frontend/sw.js` — passed.
- `python -m pytest -q` — **360 passed, 129 additional subtests passed**.
- `vercel.json` JSON parse — passed.
- `render.yaml` YAML parse — passed.

## Production preflight result

The production preflight was exercised using sample (non-secret) configuration values and a temporary writable directory. It passed the HTTPS origin, auth-required, support route, data-directory and SMTP-shape checks, but **failed the bundled privacy-notice content check**. `frontend/privacy.html` still contains operator placeholders for the responsible legal person/entity, monitored privacy/support contact, actual retention periods, and age/children's-data handling. These must be completed with real operator information and reviewed before collecting real-user data.

A successful configuration-shape check is not proof that SMTP, hosting persistence, provider credentials, TLS, backups or compliance work in production.

## Must pass on deployed Preview before production

1. Render `/api/health` is healthy and the service disk is mounted at `/var/data`.
2. Vercel `/api/health` reaches the Render backend through the external rewrite.
3. Register, verify email, sign in, refresh, password reset and sign out work with production cookie settings.
4. Distinct accounts cannot see one another's cases or evidence.
5. Evidence uploads, previews, downloads and PDF/ZIP export work through the proxy.
6. Guided Chat voice transcription works with the configured Gnani key.
7. Live Resolution `/api/live-room/voice` WebSocket upgrade succeeds through the Vercel external rewrite; audio and transcript events stream correctly.
8. Synthetic case/account deletion works and Render persistence survives restart/redeploy; backup restoration has been tested.
9. Desktop/mobile visual QA, keyboard and screen-reader checks, privacy/legal review, upload malware-scanning plan and dependency/security review are completed.

**Do not publish this as a real-user production service until the privacy notice and deployed Preview checks above are completed.**
