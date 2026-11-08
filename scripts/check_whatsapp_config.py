"""Safe WhatsApp Cloud API preflight. Prints presence/readiness only, never secret values."""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT))
from backend.whatsapp import config_status  # noqa: E402
from backend.twilio_whatsapp import config_status as twilio_config_status  # noqa: E402
from backend.messaging import selected_provider  # noqa: E402

REQUIRED = {
    "WHATSAPP_BUSINESS_NUMBER": "official WhatsApp business number",
    "WHATSAPP_ACCESS_TOKEN": "server-side Cloud API access token",
    "WHATSAPP_PHONE_NUMBER_ID": "Meta Phone Number ID (not the public phone number)",
    "WHATSAPP_APP_SECRET": "Meta app secret for webhook signature verification",
    "WHATSAPP_VERIFY_TOKEN": "random webhook verification token",
    "WHATSAPP_PHONE_ENCRYPTION_KEY": "Fernet encryption key for stored phone numbers",
}


def main() -> int:
    provider = selected_provider()
    print("BolKeResolve messaging configuration preflight")
    print("No outbound messages are sent by this script. Secret values are never printed.\n")
    whatsapp = config_status()
    if provider == "twilio":
        required = {
            "TWILIO_ACCOUNT_SID": "Twilio Account SID",
            "TWILIO_AUTH_TOKEN": "server-side Twilio Auth Token",
            "TWILIO_WHATSAPP_FROM": "Twilio WhatsApp Sandbox sender address",
            "TWILIO_WEBHOOK_PUBLIC_URL": "exact public HTTPS inbound webhook URL",
        }
        missing = []
        for name, description in required.items():
            configured = bool(os.getenv(name, "").strip())
            print(f"{'PASS' if configured else 'MISSING'}  {name}: {description}")
            if not configured:
                missing.append(name)
        for key, label in (
            ("persistent_identity_ready", "valid encrypted phone storage key"),
            ("privacy_policy_configured", "public HTTPS privacy notice"),
            ("support_escalation_configured", "real monitored support escalation path"),
        ):
            okay = bool(whatsapp.get(key))
            print(f"{'PASS' if okay else 'NOT READY'}  {label}")
        twilio = twilio_config_status()
        sdk_installed = importlib.util.find_spec("twilio") is not None
        print(f"{'PASS' if sdk_installed else 'MISSING'}  Twilio Python SDK: required for official signature validation")
        for key, label in (
            ("sender_configured", "valid Twilio WhatsApp sender address"),
            ("webhook_url_configured", "valid public HTTPS inbound webhook URL"),
            ("status_callback_configured", "valid HTTPS status callback URL"),
            ("ready_for_sandbox_testing", "Twilio Sandbox adapter configuration"),
        ):
            okay = bool(twilio.get(key))
            print(f"{'PASS' if okay else 'NOT READY'}  {label}")
        print("\nTwilio Sandbox is for development/testing only, not production.")
        return 0 if not missing and sdk_installed and twilio["ready_for_sandbox_testing"] and whatsapp["persistent_identity_ready"] and whatsapp["privacy_policy_configured"] and whatsapp["support_escalation_configured"] else 1

    missing = []
    print("Active preference: Meta WhatsApp Cloud API\n")
    for name, description in REQUIRED.items():
        configured = bool(os.getenv(name, "").strip())
        print(f"{'PASS' if configured else 'MISSING'}  {name}: {description}")
        if not configured:
            missing.append(name)
    for key, label in (
        ("privacy_policy_configured", "public HTTPS privacy notice"),
        ("support_escalation_configured", "real monitored support escalation path"),
        ("persistent_identity_ready", "valid phone-encryption key"),
        ("cloud_api_ready", "all Meta integration readiness gates"),
    ):
        okay = bool(whatsapp.get(key))
        print(f"{'PASS' if okay else 'NOT READY'}  {label}")
    print(f"Info  Graph API version selected: {whatsapp['graph_api_version']}")
    print("\nTwilio sandbox is available independently if you set BOLKE_WHATSAPP_PROVIDER=twilio.")
    return 0 if not missing and whatsapp["cloud_api_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
