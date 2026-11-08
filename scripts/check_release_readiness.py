#!/usr/bin/env python3
"""Check minimum BolKeResolve configuration without printing secret values.

This helper cannot verify external DNS, TLS, persistent storage, provider credentials,
backup restorability, privacy/legal compliance or a real-user workflow. It reports
those as operator checks rather than claiming the project is production-certified.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit


def https_url(value: str) -> bool:
    try:
        parsed = urlsplit(value.strip())
        return parsed.scheme == "https" and bool(parsed.netloc) and not parsed.username and not parsed.password
    except ValueError:
        return False


def https_origin(value: str) -> bool:
    """True only for a bare HTTPS origin, not a path, query, or credential URL."""
    try:
        parsed = urlsplit(value.strip())
        return (
            parsed.scheme == "https" and bool(parsed.netloc)
            and not parsed.username and not parsed.password
            and parsed.path in {"", "/"} and not parsed.query and not parsed.fragment
        )
    except ValueError:
        return False


def privacy_notice_status(path: Path) -> tuple[bool, str]:
    """Refuse production readiness while the shipped privacy page is still a template."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return False, "The bundled privacy notice cannot be read."
    markers = (
        "DRAFT FOR THE OPERATOR",
        "[REPLACE WITH",
        "[OPERATOR:",
    )
    found = [marker for marker in markers if marker.casefold() in content.casefold()]
    if found:
        return False, "The bundled privacy notice still contains operator placeholders or a draft banner."
    if not re.search(r"<h1[^>]*>\s*Privacy Notice\s*</h1>", content, flags=re.IGNORECASE):
        return False, "The bundled page does not contain the expected Privacy Notice heading."
    return True, "The bundled notice has no known draft markers; legal/operator review is still required."




def email_delivery_status(environ: dict[str, str], *, production: bool) -> tuple[bool, str]:
    """Check that SMTP-based account verification/recovery is configured, without secrets."""
    host = environ.get("BOLKE_SMTP_HOST", "").strip()
    sender = environ.get("BOLKE_SMTP_FROM", "").strip()
    origin = environ.get("BOLKE_PUBLIC_ORIGIN", "").strip().rstrip("/")
    username = environ.get("BOLKE_SMTP_USERNAME", "")
    password = environ.get("BOLKE_SMTP_PASSWORD", "")
    try:
        port = int(environ.get("BOLKE_SMTP_PORT", "587"))
    except ValueError:
        port = 0
    use_ssl = environ.get("BOLKE_SMTP_USE_SSL", "false").strip().lower() in {"1", "true", "yes", "on"}
    use_starttls = environ.get("BOLKE_SMTP_USE_STARTTLS", "true").strip().lower() in {"1", "true", "yes", "on"}
    sender_ok = bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", sender))
    origin_ok = https_origin(origin) if production else bool(re.fullmatch(r"https?://[^/]+", origin))
    auth_ok = not (username or password) or bool(username and password)
    if not (host and sender_ok and 1 <= port <= 65535 and (use_ssl or use_starttls) and origin_ok and auth_ok):
        return False, "Configure SMTP host/sender, a valid public origin, encrypted SMTP transport and a complete optional credential pair; no secret values are printed."
    return True, "SMTP settings appear complete. Actual message delivery, sender-domain reputation and link operation still require a live test."

def check(label: str, passed: bool, detail: str, *, required: bool = True) -> bool:
    marker = "PASS" if passed else ("FAIL" if required else "WARN")
    print(f"[{marker}] {label}: {detail}")
    return passed or not required


def main() -> int:
    env = os.getenv("BOLKE_ENV", "development").strip().lower()
    production = env == "production"
    errors = 0
    print("BolKeResolve release-readiness preflight")
    print("No secret values are displayed. This is a config check, not a security certification.\n")

    public_origin = os.getenv("BOLKE_PUBLIC_ORIGIN", "").strip().rstrip("/")
    privacy_url = os.getenv("BOLKE_PRIVACY_POLICY_URL", "").strip()
    support_email = os.getenv("BOLKE_SUPPORT_EMAIL", "").strip()
    support_url = os.getenv("BOLKE_SUPPORT_URL", "").strip()
    auth_required = env == "production" or os.getenv("BOLKE_AUTH_REQUIRED", "false").strip().lower() in {"1", "true", "yes", "on"}

    def run(*args, **kwargs):
        nonlocal errors
        ok = check(*args, **kwargs)
        if not ok:
            errors += 1

    run("Environment", env in {"development", "test", "staging", "production"},
        f"BOLKE_ENV is {env or '(empty)'}.", required=production)
    origin_ok = https_origin(public_origin)
    run("HTTPS public origin", origin_ok,
        "BOLKE_PUBLIC_ORIGIN must be a bare HTTPS origin (for example https://your-domain.example), without a path, query, or fragment." if not origin_ok else "Bare HTTPS origin is set.", required=production)
    run("Authentication", auth_required,
        "Sign-in required for private case APIs." if auth_required else "Local-style mode allows cases without user authentication; do not expose this instance publicly.", required=production)
    privacy_url_ok = https_url(privacy_url)
    run("Published privacy notice URL", privacy_url_ok,
        "Configure a real public HTTPS privacy notice." if not privacy_url_ok else "HTTPS privacy URL is configured.", required=production)
    privacy_ready, privacy_detail = privacy_notice_status(Path(__file__).resolve().parents[1] / "frontend" / "privacy.html")
    run("Bundled privacy notice content", privacy_ready, privacy_detail, required=production)
    support_ok = bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", support_email)) or https_url(support_url)
    run("Monitored support route", support_ok,
        "Configure a monitored support email or a real HTTPS support page." if not support_ok else "Support route is configured.", required=production)

    data_dir = Path(os.getenv("BOLKE_DATA_DIR", "./runtime")).expanduser()
    if data_dir.exists():
        data_dir_ok = data_dir.is_dir() and os.access(data_dir, os.W_OK)
        data_dir_detail = "Configured data directory exists and is writable." if data_dir_ok else "Configured data path is not a writable directory."
    else:
        parent = data_dir.parent if str(data_dir.parent) else Path(".")
        parent_ok = parent.exists() and parent.is_dir() and os.access(parent, os.W_OK)
        data_dir_ok = parent_ok and not production
        data_dir_detail = (
            "Directory does not exist yet, but its parent is writable; the app creates it on startup."
            if parent_ok and not production else
            "Production data directory must already exist as a writable mount; parent writability is not enough."
            if parent_ok else "Directory is missing and its parent is not writable."
        )
    run("Data directory", data_dir_ok, data_dir_detail, required=production)

    print("\nMessaging provider status")
    print("[INFO] Core case intake, source-backed guidance, outcome capture and passport exports do not require WhatsApp, Meta or Twilio credentials.")
    provider = os.getenv("BOLKE_WHATSAPP_PROVIDER", "meta").strip().lower()
    if provider == "twilio":
        twilio_ok = all(os.getenv(name, "").strip() for name in (
            "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_WHATSAPP_FROM", "TWILIO_WEBHOOK_PUBLIC_URL"
        ))
        check("Twilio Sandbox configuration", twilio_ok,
              "Required configuration values are present." if twilio_ok else "Optional: set the Twilio values only if actively testing the Sandbox.", required=False)
    elif provider == "meta":
        meta_ok = all(os.getenv(name, "").strip() for name in (
            "WHATSAPP_ACCESS_TOKEN", "WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_APP_SECRET", "WHATSAPP_VERIFY_TOKEN", "WHATSAPP_PHONE_ENCRYPTION_KEY", "WHATSAPP_BUSINESS_NUMBER"
        ))
        check("Meta Cloud API configuration", meta_ok,
              "Required values are present (credentials not verified)." if meta_ok else "Optional: WhatsApp isn't needed to use the core web product; Meta variables are incomplete.", required=False)
    else:
        check("Messaging provider", False, "Unrecognized BOLKE_WHATSAPP_PROVIDER; use 'meta' or 'twilio'.", required=False)

    email_configured, email_detail = email_delivery_status(os.environ, production=production)
    verification_required = production or os.getenv("BOLKE_EMAIL_VERIFICATION_REQUIRED", "false").strip().lower() in {"1", "true", "yes", "on"}
    check("Email verification and password recovery", email_configured, email_detail,
          required=verification_required)

    print("\nOptional Case Inbox Bridge")
    bridge_values = {
        "domain": os.getenv("BOLKE_INBOUND_EMAIL_DOMAIN", "").strip().lower().rstrip("."),
        "encryption_key": os.getenv("BOLKE_INBOUND_EMAIL_ENCRYPTION_KEY", "").strip(),
        "bearer_token": os.getenv("BOLKE_INBOUND_WEBHOOK_TOKEN", "").strip(),
        "basic_user": os.getenv("BOLKE_INBOUND_WEBHOOK_USERNAME", "").strip(),
        "basic_password": os.getenv("BOLKE_INBOUND_WEBHOOK_PASSWORD", "").strip(),
    }
    bridge_requested = any(bridge_values.values())
    domain_valid = bool(re.fullmatch(r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", bridge_values["domain"]))
    try:
        from cryptography.fernet import Fernet
        Fernet(bridge_values["encryption_key"].encode("ascii"))
        bridge_key_valid = True
    except (ValueError, UnicodeEncodeError, ImportError):
        bridge_key_valid = False
    bridge_bearer_valid = len(bridge_values["bearer_token"]) >= 32
    bridge_basic_valid = len(bridge_values["basic_user"]) >= 8 and len(bridge_values["basic_password"]) >= 24
    bridge_auth_valid = bridge_bearer_valid or bridge_basic_valid
    bridge_ready = domain_valid and bridge_key_valid and bridge_auth_valid
    if not bridge_requested:
        bridge_detail = "Automatic forwarding is not configured and stays disabled; the case panel still supports manual paste-and-review without a provider."
    elif bridge_ready:
        bridge_detail = "Required environment values look complete. DNS/MX, HTTPS, provider payload/auth and live test delivery still need operator verification."
    else:
        bridge_detail = "Some automatic-forwarding variables are present, but the domain, valid Fernet key or strong webhook authentication is incomplete; automatic forwarding stays disabled. Manual paste-and-review remains available."
    check("Inbound email configuration", not bridge_requested or bridge_ready, bridge_detail, required=False)

    print("\nOperator verification still required")
    for item in (
        "Confirm the configured data directory is backed by persistent storage; filesystem presence alone cannot prove persistence.",
        "Verify TLS, reverse-proxy forwarding, DNS, logs, backups and a successful restore on the deployment host.",
        "Complete mobile/accessibility QA, upload malware-scanning strategy, security review and privacy/legal review.",
        "Run a synthetic end-to-end case: story → fact review → case save → outcome → export → delete case and account.",
        "Confirm backups and third-party providers have documented retention periods; self-service deletion cannot recall exported copies or external provider data.",
    ):
        print(f"[CHECK] {item}")

    if errors:
        print(f"\nPreflight completed with {errors} required check(s) to fix.")
        return 1
    print("\nPreflight passed its configured required checks. This does not mean the service is ready for production without the operator checks above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
