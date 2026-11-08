# BolKeResolve — Vercel launch guide

## Recommended deployment shape

Deploy the **static frontend to Vercel** and keep the **FastAPI backend on Render with its persistent disk**. Do not deploy the current SQLite/local-evidence backend as a Vercel Function: Vercel Function filesystems are read-only except for temporary `/tmp` storage, which is not durable case storage.

The root `vercel.json` is configured to:

- Serve `frontend/` as the static site (`outputDirectory`).
- Forward same-origin `/api/*` requests—including the live-room WebSocket path—to `https://bolkeresolve.onrender.com/api/*` through a Vercel external rewrite.
- Add browser security headers and prevent stale caching of the service worker and app shell.

Vercel documents WebSocket support for Functions as generally available, but this project uses an **external rewrite to Render**, not a Vercel WebSocket Function. The Vercel documentation describes external HTTP rewrites but does not make an explicit guarantee for this exact FastAPI WebSocket-proxy arrangement. Therefore, successful Live Resolution WebSocket upgrade is a mandatory Preview acceptance test, not something to assume from a successful `/api/health` response. If the upgrade is rejected, do not publish with Live Resolution voice advertised as working; use a supported dedicated WebSocket route/proxy or a custom same-site backend domain and test the session-ticket/auth design before launch.

The backend URL above is based on the `name: bolkeresolve` in `render.yaml`. After creating the Render Blueprint, open the Render service and verify its exact public URL. If Render assigned a different hostname, update the rewrite destination in `vercel.json` and redeploy Vercel.

## 1. Deploy the backend first

1. Push this project to a private GitHub repository (recommended while the project is pre-launch).
2. In Render, choose **New → Blueprint**, select the repository and apply `render.yaml`.
3. Confirm the web service is using the Dockerfile and the persistent disk is mounted at `/var/data` (the Blueprint requests a 1 GB disk on the Starter plan).
4. Wait for the first deployment. Open `https://YOUR-RENDER-SERVICE.onrender.com/api/health` and confirm it returns a healthy JSON response.
5. Copy the exact Render service URL. Update the API rewrite in `vercel.json` if it differs from `https://bolkeresolve.onrender.com`.

Do not use an ephemeral/free filesystem for real user cases. The SQLite database and original evidence files must remain on the persistent disk.

## 2. Configure Render environment variables

Set the following in **Render → Service → Environment**. Use the exact Vercel production origin, with no path or trailing slash.

| Variable | Value / action |
|---|---|
| `BOLKE_ENV` | `production` |
| `BOLKE_ACCOUNTS_ENABLED` | `true` |
| `BOLKE_AUTH_REQUIRED` | `true` |
| `BOLKE_EMAIL_VERIFICATION_REQUIRED` | `true` |
| `BOLKE_COOKIE_SECURE` | `true` |
| `BOLKE_DATA_DIR` | `/var/data` |
| `BOLKE_PUBLIC_ORIGIN` | `https://YOUR-PROJECT.vercel.app` (exact production domain; canonical URL for verification/reset emails) |
| `BOLKE_ALLOWED_ORIGINS` | Optional comma-separated exact origins for a stable Preview/staging domain; never use `*` or broad wildcards |
| `BOLKE_PRIVACY_POLICY_URL` | `https://YOUR-PROJECT.vercel.app/privacy.html` after reviewing/publishing the privacy notice |
| `BOLKE_SUPPORT_EMAIL` | A real, monitored support email address |
| `BOLKE_SUPPORT_URL` | Optional public HTTPS support page |
| `GNANI_API_KEY` | Server-side Gnani key; never put it in Vercel frontend variables |
| `BOLKE_SMTP_HOST` | SMTP host for verification and password recovery |
| `BOLKE_SMTP_PORT` | Usually `587` for STARTTLS; follow your provider's instructions |
| `BOLKE_SMTP_USERNAME` | SMTP username, if required |
| `BOLKE_SMTP_PASSWORD` | SMTP password/app password, if required |
| `BOLKE_SMTP_FROM` | Verified sender address |
| `BOLKE_SMTP_USE_STARTTLS` | `true` for port 587, unless provider instructs otherwise |
| `BOLKE_SMTP_USE_SSL` | `false` for STARTTLS; use `true` only for implicit TLS configuration |
| `OPENAI_API_KEY` | Optional; required for the separately consented AI case interpretation/translation/visual assistance features |
| `BOLKE_PUBLIC_VOICE_ENABLED` | Keep `false` unless you intentionally want unauthenticated visitors to consume paid voice transcription |
| `BOLKE_SHARE_INTAKE_ENCRYPTION_KEY` | Stable Fernet key if Share-to-Case intake is enabled; back it up securely and never rotate casually |

WhatsApp and automatic inbound-email variables are optional. Do not configure them unless those channels are fully set up and tested.

**Important:** production registration requires email verification. Do not launch account creation until SMTP delivery works end-to-end. Environment variable changes on Render require a redeploy/restart.

## 3. Deploy the frontend to Vercel

1. In Vercel, choose **Add New → Project** and import the same repository.
2. Set **Framework Preset** to `Other`.
3. Set **Root Directory** to the repository root (`./`).
4. Leave the **Build Command** blank (the static HTML/CSS/JS app has no compile step).
5. Set **Output Directory** to `frontend` (also declared in `vercel.json`).
6. Do not add backend API secrets to Vercel. Vercel only serves the static client and proxies `/api/*` to Render.
7. Deploy a Preview first. Confirm that `/api/health` on the Preview URL is proxied successfully. For authenticated mutation testing on a stable Preview/staging domain, add that exact origin to `BOLKE_ALLOWED_ORIGINS` on Render. The application uses an exact allowlist; do not add wildcards or permit arbitrary `vercel.app` origins.
8. Once staging passes, set `BOLKE_PUBLIC_ORIGIN` on Render to the exact production Vercel domain (this remains the canonical host for verification/reset links), retain only the exact stable Preview origin(s) required in `BOLKE_ALLOWED_ORIGINS`, and redeploy the backend. Then redeploy Vercel.

Vercel's external rewrite keeps the browser URL on the Vercel origin, so the app's same-origin `/api/*` fetches and HttpOnly session cookie continue to use one site. Keep external rewrite caching disabled for `/api/*`; private case/account responses must never be CDN-cached.

## 4. Final acceptance tests before announcing launch

- [ ] `https://YOUR-RENDER-SERVICE.onrender.com/api/health` returns healthy JSON.
- [ ] `https://YOUR-PROJECT.vercel.app/` loads the homepage and local image fallbacks.
- [ ] `/api/health` on the Vercel domain returns the Render backend health response.
- [ ] Register a new account; email verification arrives and its link returns to the Vercel domain.
- [ ] Sign in, refresh, and confirm the session persists.
- [ ] Create a synthetic test case, upload a small image/PDF, preview and download it.
- [ ] Sign out; confirm private cases are not accessible.
- [ ] Register a second test user; confirm the first user's case is not visible.
- [ ] Test password reset email and one-time reset link.
- [ ] Test Guided Chat voice transcription with a short synthetic recording and the production Gnani key.
- [ ] Start Live Resolution voice and confirm the `/api/live-room/voice` WebSocket upgrades, streams audio, returns transcript events and closes cleanly. Test from the Vercel Preview domain, not only localhost.
- [ ] Test case export (PDF/ZIP) and verify it contains the selected original evidence.
- [ ] Delete the synthetic test case and test accounts.
- [ ] Confirm the Render persistent disk is mounted and a backup/restore procedure has been tested.
- [ ] Check Vercel and Render logs for errors; verify no secrets or sensitive case text appear in logs.

## 5. Platform limits and operational notes

- Vercel external rewrites are reverse proxies; they are not Vercel Functions. Vercel documents a 120-second proxied-request timeout. The application still has its own upload limits (8 MB evidence, 12 MB audio) and backend processing constraints.
- The frontend includes a persistent, bidirectional Live Resolution WebSocket. Treat the WebSocket handshake/stream test as a launch blocker until verified through the actual Vercel Preview deployment.
- Do not add `/api/*` rewrite caching. The backend intentionally marks API responses as `no-store`.
- The Render SQLite/evidence storage path must be `/var/data`. Do not set it to `/tmp`, the repository, or an unmounted directory.
- Browser visual QA must be done against the deployed Preview URL on desktop and mobile; automated unit tests do not validate the live proxy, SMTP, microphone permissions, browser media APIs, or persistence across restarts.
- Review the privacy notice and terms with a qualified reviewer before accepting real financial/identity documents. This application records user-provided statements and evidence; it does not independently verify bank transactions or guarantee legal admissibility.

## References

- Vercel static build settings: https://vercel.com/docs/builds/configure-a-build
- Vercel external rewrites: https://vercel.com/docs/routing/rewrites
- Vercel Function filesystem/runtime: https://vercel.com/docs/functions/runtimes
- Vercel environments and variables: https://vercel.com/docs/deployments/environments
- Render Blueprint: https://render.com/docs/blueprint-spec
