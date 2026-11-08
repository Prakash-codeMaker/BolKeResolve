"""Provider-neutral contracts shared by supported WhatsApp adapters.

Provider-specific authentication, payloads and APIs belong in provider modules.
Case workflow, consent, phone identity and persistence remain in backend.main.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class InboundMessage:
    """Normalized inbound WhatsApp event, independent of provider wire format."""

    message_id: str
    sender: str
    message_type: str
    text: str
    phone_number_id: str = ""
    media_id: str = ""
    mime_type: str = ""
    provider: str = "meta"


@dataclass(frozen=True)
class SendResult:
    """Provider send acceptance. `accepted` is not a delivery confirmation."""

    accepted: bool
    message_id: str = ""
    provider: str = ""
    raw_status: str = "accepted"

    def as_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "message_id": self.message_id,
            "provider": self.provider,
            "status": self.raw_status,
        }


class MessagingAdapter(Protocol):
    """Small contract for provider-specific WhatsApp transport adapters."""

    provider_name: str

    async def send_reply(self, to_phone: str, body: str) -> dict[str, Any]: ...


class MetaCloudApiAdapter:
    """Adapter around the existing Meta implementation; behavior is preserved."""

    provider_name = "meta"

    async def send_reply(self, to_phone: str, body: str) -> dict[str, Any]:
        from backend import whatsapp

        return await whatsapp.send_guided_reply(to_phone, body)


class TwilioSandboxAdapter:
    """Text-only Phase 1 adapter around the Twilio Sandbox transport."""

    provider_name = "twilio"

    async def send_reply(self, to_phone: str, body: str) -> dict[str, Any]:
        from backend import twilio_whatsapp

        return await twilio_whatsapp.send_text_message(to_phone, body)


def get_adapter(provider: str) -> MessagingAdapter:
    """Resolve an adapter without coupling the case engine to its wire format."""
    normalized = str(provider or "meta").strip().lower()
    if normalized == "twilio":
        return TwilioSandboxAdapter()
    return MetaCloudApiAdapter()


async def send_reply(provider: str, to_phone: str, body: str) -> dict[str, Any]:
    """Provider-neutral reply dispatch; each inbound reply uses its own adapter."""
    return await get_adapter(provider).send_reply(to_phone, body)


def storage_message_id(provider: str, provider_message_id: str) -> str:
    """Return a stable DB key while preserving legacy Meta IDs for existing rows."""
    value = str(provider_message_id or "").strip()
    if not value:
        return ""
    normalized_provider = str(provider or "meta").strip().lower()
    if normalized_provider in {"meta", "meta_whatsapp_cloud_api", "whatsapp_cloud_api"}:
        return value
    prefix = normalized_provider + ":"
    return value if value.startswith(prefix) else prefix + value


def selected_provider() -> str:
    """Configured provider preference used for display and operator diagnostics."""
    import os

    value = os.getenv("BOLKE_WHATSAPP_PROVIDER", "meta").strip().lower()
    return value if value in {"meta", "twilio"} else "meta"
