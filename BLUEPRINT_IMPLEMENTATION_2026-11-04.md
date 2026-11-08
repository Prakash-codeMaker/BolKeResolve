# BolKeResolve — Product Blueprint Implementation Report
**Implementation date:** 4 November 2026  
**Source release:** `BolKeResolve_Product_Foundation_Upgrade_2026-11-03.zip`  
**Design basis:** `BolKeResolve_Product_Research_Blueprint_2026-11-04.md`  
**Implementation status:** Code changes made; regression-tested; not yet production-certified.

**Follow-up note (4 November 2026):** a second UI/account increment after this initial blueprint pass fixed the consent-checkbox CSS cascade, added discoverable sign-in/sign-up, made local account routes available and owner-scoped, refined the homepage/Live Resolution presentation, and added a pausable photo sequence. The combined final package and verification record are in [`FOLLOWUP_UI_ACCOUNT_IMPLEMENTATION_2026-11-04.md`](FOLLOWUP_UI_ACCOUNT_IMPLEMENTATION_2026-11-04.md); the final combined suite is **354 passed, 129 subtests passed**. Counts later in this initial report reflect the first 350-test tranche.

## Executive result

The existing BolKeResolve resolution engine has been retained. This implementation increment connects the previous product-foundation work to a clearer Live Resolution experience, a more structured evidence record, richer case export, and a more complete account-security lifecycle.

The release is intentionally additive. Existing SQLite cases, Resolution Passport routes and legacy ZIP entry paths are retained. New case record tables and export functionality are introduced without replacing the rule-based guidance and case workflow.

## 1. Blueprint-to-code status

| Blueprint area | Implemented in this release | Remaining or conditional work |
|---|---|---|
| Start screen and consent | Unavailable AI options now show clear status rows; available features use real selectable controls; AI interpretation and translation are distinct; browser capture permissions remain separate. | Live provider configuration and production consent/privacy review. |
| Live Resolution layout | Case-aware header, back-to-case/My Cases actions, more compact next-action panel, expandable long explanation, case preview visual, evidence filters and improved evidence cards. | Browser/assistive-technology visual QA on real target devices. |
| My Cases | Search/status filters and next-action, follow-up and evidence summaries. | Usability testing with representative users and larger case volumes. |
| Evidence organisation | Original evidence stays separate from versioned extracted/derived records; capture metadata, scan state, previews and claim relations are exposed; derivative records are case-scoped. | Real malware scanning/quarantine, cloud object storage, richer media annotation and multi-user evidence sharing. |
| Conversation history | Structured user turns, transcript confidence/source metadata, append-only corrections, supersession links and chronological transcript reconstruction with assistant guidance. | Full browser-level review of transcription quality, audio playback and long-session restore. |
| Timeline | Case audit events and timeline events are retained; file preview/download and account-sensitive actions are recorded. | Centralised immutable/externally retained security audit sink for production operations. |
| Case export | Complete PDF + ZIP and selective share-ready ZIP; manifest, CSV indexes, facts, transcript, timeline, derivative data, originals and SHA-256 checksums. | Advanced configurable redaction, redaction preview for scanned documents/images, and legal/records policy review. |
| Authentication | Existing account registration/login/sessions retained; SMTP verification, password reset, password change, session revoke/list and persistent auth throttling added. | Live SMTP test, MFA/passkeys, managed identity decision and account recovery support runbook. |
| Authorization | Per-case ownership checks remain in the backend; account profile exposes verification state. | Multi-user collaboration roles and formal external authorization review. |
| Production security | Safer password work factor, single-use token lifecycle, email enumeration protection, audit events and more accurate preflight checks. | Malware scanning, private object storage, backup restore proof, infrastructure quotas, monitoring, penetration and legal review. |

## 2. User-interface changes

### Start Live Resolution

The previous interface made disabled capabilities appear like normal empty checkboxes. The new behavior is capability-aware:
- When AI case understanding is not configured, the user sees a non-interactive status explanation and can still start.
- When translation is unavailable, its status is explained separately.
- When services are available, optional choices have actual selected states and labels.
- AI interpretation, translation, microphone access, camera access and image review are treated as separate permissions.

The start experience now includes an original product preview illustrating the three steps of the workflow. It uses synthetic demo information rather than displaying a real customer case.

### Live Resolution workspace

The Live Resolution view has a persistent case header and direct return paths. The main action is easier to identify, while secondary explanation is collapsible. Evidence is shown in its own section with filters and clear distinctions between the uploaded original and its derivatives.

The current product still uses the established case-detail tool groups (plan/details, prepare/contact and progress) rather than replacing every legacy case panel with a brand-new five-route page shell. The principal blueprint areas remain reachable through the case workspace and Live Resolution experience; a further navigation consolidation can be considered after browser usability testing.

### Evidence cards

Evidence entries distinguish:
- Original user-supplied/captured file.
- File metadata, capture source, upload/capture date and session references.
- Processing/scan status and whether the information is user-confirmed.
- Reviewed document-fact extraction and visual-AI observations (where configured); live conversation transcript turns are stored separately.
- Claim relationship (supports, contradicts or contextualises).

The original file is not overwritten by extraction, AI review or transcript correction. A preview/download creates an audit/timeline record but does not change the original bytes.

## 3. Data and evidence model changes

New/extended persistent records include:
- `conversation_turns`: speaker, text, language, input source, confidence, linked audio/evidence, session, confirmation, timestamp and supersession relationship.
- `evidence_derivatives`: reviewed document-fact/visual-AI output type, stored JSON, hash, processor/version, processing/review status and supersession relationship.
- `auth_rate_limit_attempts`: persistent rate-limit observations keyed by action and hashed IP value.
- `auth_action_tokens`: hashed verification/reset token, owner, purpose, expiry and one-time consumed state.
- `audit_events`: account/case security and export event history.
- `case_exports`: export mode, selected evidence, manifest/package hash and export timestamp.

Existing case fact history, evidence-claim links and settlement reconciliation are preserved.

Transcript correction is append-only. The old text remains in history with a link to the replacement; the current correction informs later rule-based case guidance. On case resume, the interface rebuilds the visible conversation chronologically and keeps earlier assistant guidance instead of accidentally hiding it after a correction.

## 4. Complete case export format

The complete export includes a structured archive with these areas:

```text
BolKeResolve-Case-BR-XXXX/
  00-Readme/
    Case-Summary.pdf
    Export-Manifest.json
    Evidence-Index.csv
    Case-Facts.json
    File-Hashes-SHA256.txt
  01-Case-History/
    Timeline.pdf
    Case-Events.csv
    Confirmed-Facts.csv
    Superseded-or-Disputed-Facts.csv
    Support-Message-DRAFT-ONLY.txt   (when a draft exists)
  02-Conversation/
    Conversation-Transcript.pdf
    Conversation-Transcript.txt
  03-Original-Evidence/
    Photos/
    Documents/
    Audio/
    Video/
  04-Derivatives/
    OCR / transcript / reviewed extraction JSON records
  case/Resolution-Passport.json      (legacy compatibility path)
```

The transcript merges structured user turns with assistant guidance and user-confirmed organisation replies stored in the timeline. The timeline and CSV remain the event-level source for all case activity. A support draft is explicitly labelled draft-only; no export implies that the product actually sent a message.

A share-ready export lets the user select evidence IDs. Optional text redaction applies only to text-based output and is best-effort pattern matching. It does not alter original media or guarantee removal of every sensitive item. Users should review the archive before sharing.

PDFs are readable companions; `Conversation-Transcript.txt` is the lossless UTF-8 transcript. Indic-language glyph shaping still needs verification with representative Hindi/Marathi/etc. text on the target deployment environment.

The PDF and manifest clearly state that this is a user-assembled case record, not a certified legal document. SHA-256 checksums can identify byte changes but do not prove who created a file, when it was created or whether its contents are true.

## 5. Authentication and authorization

The codebase already had local account sign-up/login, server-side sessions and case ownership checks. This release improves rather than replaces that system.

Added behavior:
1. Email verification for production registration through a configured TLS-protected SMTP relay.
2. Single-use verification and password-reset tokens: only token hashes are stored, links expire after 30 minutes, and consumed tokens cannot be replayed.
3. Generic password-reset request response to avoid disclosing whether an email address has an account.
4. Password change and active session listing/revoke-other-sessions.
5. Persistent SQLite auth rate-limit tracking.
6. PBKDF2-HMAC-SHA256 with 600,000 iterations; older PBKDF2 hashes are upgraded on successful login.
7. A session profile response that includes `email_verified`.

Production behavior requires a configured HTTPS public origin and SMTP host/from-address with SSL or STARTTLS. The release preflight checks configuration presence but cannot confirm real-world delivery, deliverability, TLS termination or link routing.

The database is still SQLite. It does not have PostgreSQL Row Level Security, and Supabase Auth has not been connected. The application API enforces owner access for private case and evidence operations. Do not expose SQLite files or the local evidence directory as public static files.

MFA, passkeys, a managed identity provider, collaborator roles and support-agent access delegation remain future work. Before using customer evidence at public scale, commission an independent auth/authorization review.

## 6. Configuration for account email

Set these server-side variables in `.env` or the deployment secret manager; do not commit credentials:

```ini
BOLKE_ENV=production
BOLKE_AUTH_REQUIRED=true
BOLKE_PUBLIC_ORIGIN=https://your-real-domain.example
BOLKE_EMAIL_VERIFICATION_REQUIRED=true
BOLKE_SMTP_HOST=smtp-provider.example
BOLKE_SMTP_PORT=587
BOLKE_SMTP_USERNAME=your-smtp-user
BOLKE_SMTP_PASSWORD=your-smtp-password
BOLKE_SMTP_FROM=no-reply@your-real-domain.example
BOLKE_SMTP_USE_STARTTLS=true
BOLKE_SMTP_USE_SSL=false
```

Use the exact public origin that serves the application. Confirm sender-domain authentication, SPF/DKIM/DMARC and that verification/reset links resolve correctly before inviting users. Port 465 commonly uses implicit SSL; use the setting appropriate to your relay. The application does not include a mail provider or SMTP credential.

## 7. Verification performed

| Check | Result |
|---|---|
| Baseline suite before changes | 340 passed, 129 subtests passed |
| Final suite after implementation | **350 passed, 129 subtests passed** |
| `python -m py_compile backend/main.py scripts/check_release_readiness.py` | Passed |
| `node --check frontend/app.js` | Passed |
| `node --check frontend/sw.js` | Passed |
| `python scripts/check_release_readiness.py` in local development configuration | Ran; reports expected operator setup warnings |
| Fresh ZIP extraction and test suite | **350 passed, 129 subtests passed** |
| Playwright browser visual smoke test | Not run successfully; Chromium navigation blocked by runtime policy (`ERR_BLOCKED_BY_ADMINISTRATOR`) |

The release ZIP contains 170 files (about 1.51 MB), excludes `.env` and runtime data, and was extracted into a clean verification directory before the test run. A companion SHA-256 file is distributed beside the ZIP and records the final archive fingerprint. The tests cover the existing case workflow, ownership isolation, auth lifecycle, email verification/reset token behavior, export structure/original-byte preservation, transcript correction and case list summary fields. The browser could not be used to claim a successful visual review.

## 8. Explicit production blockers / decisions

These are not simulated as complete:
- Real malware scanner and quarantine integration.
- Private durable object storage and tested restore/backup procedures.
- Public HTTPS deployment, reverse proxy, DNS and SMTP delivery.
- MFA/passkeys or a deliberate migration to Supabase/Clerk/Auth0 after selecting the persistent data architecture.
- Shared infrastructure rate limits, AI usage quotas, monitoring and incident response.
- Published privacy notice, monitored support channel, data retention/deletion policy, DPDP and other applicable legal review.
- External penetration test and WCAG 2.2 AA browser/screen-reader/device QA.
- Final Indic-language PDF visual validation.

## 9. Recommended next deployment order

1. Run the project locally and complete desktop/mobile browser QA with synthetic cases.
2. Select the persistent hosting/data/storage architecture; do not move customer evidence into a public static directory.
3. Publish privacy/support information and configure HTTPS plus SMTP; test registration, verification, password reset and account deletion end-to-end.
4. Add malware scanning/quarantine and persistent private object storage; test backup/restore.
5. Run ownership/authorization, upload, export, accessibility and security penetration tests.
6. Pilot with a small group using synthetic or redacted records before collecting sensitive customer evidence.

**Conclusion:** the requested local implementation increment is in place and the automated suite passes. The product is improved and more coherent, but it is not yet safe to describe as production-ready until the external infrastructure, browser QA, privacy and security gates above are completed.
