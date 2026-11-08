# BolKeResolve — Blueprint implementation changelog
**Date:** 4 November 2026  
**Scope:** Implementation of the 4 November Product Research & Implementation Blueprint against the supplied November 3 project archive.

## Front-end and Live Resolution
- Replaced selectable-looking unavailable AI/translation options with explicit non-interactive status explanations when the server does not have the capability configured.
- Kept AI case interpretation and translated guidance as separate optional permissions. Microphone, camera and visual-evidence approvals remain separate browser/user actions.
- Added accessible selected/focus/disabled states and larger clickable option rows when the capabilities are available.
- Reworked the Live Resolution start area around a three-part product preview: tell your story, show evidence, take the next step.
- Added case-aware workspace header, case ID/status and direct navigation back to the same case or My Cases.
- Reduced visible guidance text by keeping the immediate next action prominent and putting extended explanation behind disclosure controls.
- Added compact evidence type filters and redesigned evidence entries around original file, readable metadata, processing and verification labels, preview/download, and claim relationships.
- Kept the original evidence distinct from extracted text, OCR/transcription and AI-derived observations. Derivatives are stored as separate, versioned records.
- Added case search and status filtering to My Cases. Case list summaries include next action, evidence count and follow-up date.
- Added account recovery and security UI for verification, password reset, password change, session listing and revocation.
- Bumped the service-worker shell cache to `bolkeresolve-shell-v43` so clients do not keep the previous frontend shell.

## Case records and evidence architecture
- Added structured `conversation_turns` records with speaker, source, language, confidence, capture/session/evidence references, confirmation state and supersession link.
- Transcript corrections append a new turn and preserve the original wording; the corrected current turn is used for subsequent case guidance.
- Added `evidence_derivatives` records for reviewed document-fact extraction and visual-AI review outputs, tied back to immutable original evidence. Live transcripts are stored separately in structured conversation-turn records; file previews render from the preserved original.
- Added case-scoped audit event records and export history.
- Case resume merges current structured user turns with assistant guidance timeline events in chronological order; old assistant guidance is not lost when a user corrects a previous transcript turn.
- Evidence preview and download actions are recorded without modifying original file bytes.

## Complete case export
- Added a structured PDF + ZIP case dossier with case summary, timeline PDF, conversation transcript PDF and UTF-8 text, event CSV, evidence index CSV, confirmed-fact CSV, disputed/superseded-fact CSV, fact JSON, reviewed derivative records, export manifest, SHA-256 checksums and original evidence files.
- The transcript includes structured user turns, assistant guidance events and user-confirmed organisation replies where recorded in the case timeline.
- Added a share-ready mode that can include only selected original evidence and request best-effort redaction in text-based outputs.
- Original evidence files are never changed by export redaction.
- Retained older Resolution Passport and evidence manifest ZIP paths for compatibility.
- Export wording explicitly says the package is a user-assembled record, not a certified legal record; file hashes do not establish source authenticity or truth.

## Authentication and authorization
- Added SMTP-backed, one-time email verification and password-reset links. Tokens are random, stored as hashes, expire after 30 minutes and can be consumed once.
- Production registration requires configured encrypted SMTP delivery and a trusted HTTPS public origin; the application refuses registration rather than silently creating unverified production accounts.
- Password reset uses the same public response for unknown and known email addresses to reduce account enumeration.
- Added account session listing, revoke-other-sessions and authenticated password-change routes/UI.
- Added persistent SQLite-backed account rate-limit attempts, rather than relying only on process memory.
- Password hashing uses PBKDF2-HMAC-SHA256 with 600,000 iterations; older PBKDF2 hashes are transparently upgraded after successful login.
- `/api/auth/me` now returns the boolean email-verification state for the active account.
- Release preflight checks whether SMTP host/sender, public origin and encrypted transport settings appear configured without printing any secret values.

## Compatibility and verification
- Preserved the existing SQLite case database and current resolution engine. Additive schema migrations are used for new tables/columns.
- No Supabase or third-party identity provider was connected. Existing API authorization continues to enforce case ownership on protected requests.
- Regression suite: **350 passed, 129 subtests passed**.
- `python -m py_compile backend/main.py scripts/check_release_readiness.py`, `node --check frontend/app.js` and `node --check frontend/sw.js` pass.
- A Playwright visual smoke test could not run: the installed browser runtime blocked local navigation with `ERR_BLOCKED_BY_ADMINISTRATOR`. Visual/browser verification must be run on a normal local development machine before launch.

## Still required before public production
- Configure and live-test a real SMTP relay and public HTTPS domain.
- Complete MFA/passkeys or choose and integrate a managed identity provider after the database decision.
- Add a real malware scanner/quarantine flow; current file signature and MIME checks do not scan for malware.
- Deploy private durable object storage and test encrypted backups/restoration. The current release stores files locally under the configured data directory and uses SQLite.
- Configure a persistent production data mount, HTTPS/reverse proxy, monitoring, shared infrastructure rate limits and usage quotas.
- Replace the privacy page draft placeholders and publish a reviewed privacy notice, monitored support route and retention/deletion policy.
- Complete WCAG 2.2 AA keyboard/screen-reader/reflow testing, real-device visual QA, penetration testing and India-specific privacy/legal review.
- PDF text rendering for Indic scripts requires a real-font/shaping visual check. The UTF-8 transcript text file remains the lossless transcript companion.
- Share-export redaction is best-effort pattern-based text redaction, not DLP; original images, PDFs, audio and video are not redacted.

