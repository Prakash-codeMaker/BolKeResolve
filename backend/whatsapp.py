"""Minimal, privacy-conscious WhatsApp Cloud API integration helpers.

The module deliberately contains no hard-coded credentials. Configuration is read
from environment variables at call time so local tests can patch it safely.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
from typing import Any
from urllib.parse import urlsplit

import httpx
from cryptography.fernet import Fernet, InvalidToken

from backend.messaging import InboundMessage as WhatsAppMessage

logger = logging.getLogger("bolkeresolve.whatsapp")
DEFAULT_GRAPH_API_VERSION = "v26.0"
PHONE_RE = re.compile(r"^\+?[0-9]{8,15}$")
GRAPH_VERSION_RE = re.compile(r"^v[0-9]{1,2}\.0$")


def normalise_phone(value: str) -> str:
    """Return an E.164-like digits-only WhatsApp ID, or empty if invalid."""
    digits = re.sub(r"\D", "", str(value or ""))
    if not 8 <= len(digits) <= 15:
        return ""
    return digits


def graph_api_version() -> str:
    value = os.getenv("WHATSAPP_GRAPH_API_VERSION", DEFAULT_GRAPH_API_VERSION).strip()
    return value if GRAPH_VERSION_RE.fullmatch(value) else DEFAULT_GRAPH_API_VERSION


def config_status() -> dict[str, Any]:
    business_number = normalise_phone(os.getenv("WHATSAPP_BUSINESS_NUMBER", ""))
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    app_secret = os.getenv("WHATSAPP_APP_SECRET", "").strip()
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "").strip()
    encryption_key = os.getenv("WHATSAPP_PHONE_ENCRYPTION_KEY", "").strip()
    privacy_url = os.getenv("BOLKE_PRIVACY_POLICY_URL", "").strip()
    if not privacy_url:
        public_origin = os.getenv("BOLKE_PUBLIC_ORIGIN", "").strip().rstrip("/")
        if public_origin.startswith("https://"):
            privacy_url = f"{public_origin}/privacy.html"
    privacy_parts = urlsplit(privacy_url) if privacy_url else None
    privacy_policy_configured = bool(
        privacy_parts and privacy_parts.scheme == "https" and privacy_parts.netloc
        and not privacy_parts.username and not privacy_parts.password
    )
    support_url = os.getenv("BOLKE_SUPPORT_URL", "").strip()
    support_email = os.getenv("BOLKE_SUPPORT_EMAIL", "").strip()
    support_parts = urlsplit(support_url) if support_url else None
    support_url_valid = bool(
        support_parts and support_parts.scheme == "https" and support_parts.netloc
        and not support_parts.username and not support_parts.password
    )
    support_email_valid = bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", support_email))
    support_escalation_configured = support_url_valid or support_email_valid
    fernet_key_valid = False
    if encryption_key:
        try:
            Fernet(encryption_key.encode("ascii"))
            fernet_key_valid = True
        except (ValueError, UnicodeEncodeError):
            fernet_key_valid = False
    send_ready = bool(access_token and phone_number_id)
    webhook_ready = bool(app_secret and verify_token)
    persistent_identity_ready = fernet_key_valid
    return {
        "business_number": business_number,
        "graph_api_version": graph_api_version(),
        "send_ready": send_ready,
        "webhook_ready": webhook_ready,
        "persistent_identity_ready": persistent_identity_ready,
        "privacy_policy_configured": privacy_policy_configured,
        "support_escalation_configured": support_escalation_configured,
        "cloud_api_ready": send_ready and webhook_ready and persistent_identity_ready and bool(business_number) and privacy_policy_configured and support_escalation_configured,
    }


def verify_webhook_signature(raw_body: bytes, signature_header: str, app_secret: str) -> bool:
    """Verify Meta's X-Hub-Signature-256 HMAC over the exact request body."""
    if not raw_body or not signature_header or not app_secret:
        return False
    expected = "sha256=" + hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header.strip())


def _extract_message_text(message: dict[str, Any]) -> tuple[str, str]:
    message_type = str(message.get("type", "unknown"))[:30]
    if message_type == "text":
        body = message.get("text", {}).get("body", "")
        return message_type, str(body or "")[:4096]
    if message_type == "button":
        button = message.get("button", {})
        return message_type, str(button.get("text") or button.get("payload") or "")[:4096]
    if message_type == "interactive":
        interactive = message.get("interactive", {})
        reply = interactive.get("button_reply") or interactive.get("list_reply") or {}
        return message_type, str(reply.get("id") or reply.get("title") or "")[:4096]
    return message_type, ""


def parse_inbound_messages(payload: dict[str, Any]) -> list[WhatsAppMessage]:
    """Flatten the normal Meta Cloud API webhook shape, ignoring status-only events."""
    results: list[WhatsAppMessage] = []
    for entry in payload.get("entry", []) if isinstance(payload.get("entry", []), list) else []:
        for change in entry.get("changes", []) if isinstance(entry.get("changes", []), list) else []:
            value = change.get("value", {}) if isinstance(change, dict) else {}
            if not isinstance(value, dict) or change.get("field") not in (None, "messages"):
                continue
            metadata = value.get("metadata", {}) or {}
            phone_number_id = str(metadata.get("phone_number_id", ""))[:100]
            messages = value.get("messages", []) or []
            for message in messages if isinstance(messages, list) else []:
                if not isinstance(message, dict):
                    continue
                sender = normalise_phone(str(message.get("from", "")))
                message_id = str(message.get("id", ""))[:180]
                if not sender or not message_id:
                    continue
                message_type, text = _extract_message_text(message)
                media_id = ""
                mime_type = ""
                if message_type == "audio":
                    audio = message.get("audio", {}) if isinstance(message.get("audio", {}), dict) else {}
                    media_id = str(audio.get("id", ""))[:180]
                    mime_type = str(audio.get("mime_type", "audio/ogg"))[:100]
                results.append(WhatsAppMessage(message_id, sender, message_type, text, phone_number_id, media_id, mime_type))
    return results



def parse_status_updates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract outbound message delivery receipts from Meta webhook payloads.

    Only stable provider message IDs, status, timestamps, and bounded error codes
    are retained; recipient phone numbers and raw payloads are not returned.
    """
    results: list[dict[str, Any]] = []
    allowed = {"sent", "delivered", "read", "failed"}
    for entry in payload.get("entry", []) if isinstance(payload.get("entry", []), list) else []:
        for change in entry.get("changes", []) if isinstance(entry.get("changes", []), list) else []:
            if not isinstance(change, dict) or change.get("field") not in (None, "messages"):
                continue
            value = change.get("value", {})
            if not isinstance(value, dict):
                continue
            for item in value.get("statuses", []) if isinstance(value.get("statuses", []), list) else []:
                if not isinstance(item, dict):
                    continue
                message_id = str(item.get("id", ""))[:180]
                status = str(item.get("status", "")).lower()
                if not message_id or status not in allowed:
                    continue
                timestamp = str(item.get("timestamp", ""))[:20]
                errors = item.get("errors", [])
                first_error = errors[0] if isinstance(errors, list) and errors and isinstance(errors[0], dict) else {}
                error_code = str(first_error.get("code", ""))[:40]
                results.append({"message_id": message_id, "status": status, "timestamp": timestamp, "error_code": error_code})
    return results

def _fernet() -> Fernet:
    key = os.getenv("WHATSAPP_PHONE_ENCRYPTION_KEY", "").strip()
    if not key:
        raise RuntimeError("WhatsApp phone encryption is not configured.")
    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise RuntimeError("WhatsApp phone encryption key is invalid.") from exc


def encrypt_phone(phone: str) -> str:
    normalised = normalise_phone(phone)
    if not normalised:
        raise ValueError("Invalid phone number.")
    return _fernet().encrypt(normalised.encode("ascii")).decode("ascii")


def decrypt_phone(ciphertext: str) -> str:
    try:
        value = _fernet().decrypt(str(ciphertext).encode("ascii"), ttl=None).decode("ascii")
    except (InvalidToken, ValueError, UnicodeEncodeError, RuntimeError) as exc:
        raise RuntimeError("Stored WhatsApp contact cannot be decrypted with the configured key.") from exc
    normalised = normalise_phone(value)
    if not normalised:
        raise RuntimeError("Stored WhatsApp contact is invalid.")
    return normalised


def phone_fingerprint(phone: str) -> str:
    normalised = normalise_phone(phone)
    if not normalised:
        raise ValueError("Invalid phone number.")
    # A keyed digest prevents the low-entropy phone number from being trivially dictionary-tested.
    key = hashlib.sha256(os.getenv("WHATSAPP_PHONE_ENCRYPTION_KEY", "").encode("utf-8")).digest()
    if not os.getenv("WHATSAPP_PHONE_ENCRYPTION_KEY", "").strip():
        raise RuntimeError("WhatsApp phone encryption is not configured.")
    return hmac.new(key, normalised.encode("ascii"), hashlib.sha256).hexdigest()


async def download_audio_media(media_id: str, *, max_bytes: int = 12 * 1024 * 1024) -> tuple[bytes, str]:
    """Fetch a WhatsApp audio media object through Meta, enforcing host and size limits."""
    config = config_status()
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    media_id = str(media_id or "").strip()
    if not config["send_ready"] or not media_id or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,180}", media_id):
        raise RuntimeError("WhatsApp media access is not configured.")
    headers = {"Authorization": f"Bearer {token}"}
    meta_url = f"https://graph.facebook.com/{config['graph_api_version']}/{media_id}"
    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=5.0), follow_redirects=False) as client:
        meta_response = await client.get(meta_url, headers=headers)
        if meta_response.status_code < 200 or meta_response.status_code >= 300:
            raise RuntimeError("WhatsApp media metadata could not be retrieved.")
        try:
            metadata = meta_response.json()
        except ValueError as exc:
            raise RuntimeError("WhatsApp media metadata was invalid.") from exc
        media_url = str(metadata.get("url", ""))
        parsed = urlsplit(media_url)
        allowed_hosts = ("lookaside.fbsbx.com", "scontent.whatsapp.net", "pps.whatsapp.net", "graph.facebook.com")
        if parsed.scheme != "https" or not parsed.hostname or not any(parsed.hostname == host or parsed.hostname.endswith("." + host) for host in allowed_hosts):
            raise RuntimeError("WhatsApp returned an unexpected media host.")
        mime_type = str(metadata.get("mime_type", "audio/ogg"))[:100].split(";", 1)[0].strip().lower()
        if not mime_type.startswith("audio/"):
            raise RuntimeError("The received WhatsApp attachment is not audio.")
        chunks: list[bytes] = []
        size = 0
        async with client.stream("GET", media_url, headers=headers) as response:
            if response.status_code < 200 or response.status_code >= 300:
                raise RuntimeError("WhatsApp audio could not be downloaded.")
            async for chunk in response.aiter_bytes():
                size += len(chunk)
                if size > max_bytes:
                    raise ValueError("WhatsApp voice notes must be 12 MB or smaller.")
                chunks.append(chunk)
    if not chunks:
        raise ValueError("The WhatsApp voice note was empty.")
    return b"".join(chunks), mime_type


async def send_text_message(to_phone: str, body: str) -> dict[str, Any]:
    config = config_status()
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    to = normalise_phone(to_phone)
    if not config["send_ready"] or not to:
        raise RuntimeError("WhatsApp messaging is not configured.")
    text = str(body or "").strip()
    if not text:
        raise ValueError("WhatsApp message text cannot be empty.")
    # Cloud API text body limits are bounded here before making a paid/external request.
    text = text[:4096]
    url = f"https://graph.facebook.com/{config['graph_api_version']}/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
        response = await client.post(url, headers=headers, json=payload)
    if response.status_code < 200 or response.status_code >= 300:
        logger.warning("WhatsApp Cloud API send failed with HTTP %s", response.status_code)
        raise RuntimeError(f"WhatsApp message send failed (HTTP {response.status_code}).")
    try:
        body_json = response.json()
    except json.JSONDecodeError:
        body_json = {}
    return {"accepted": True, "message_id": ((body_json.get("messages") or [{}])[0]).get("id", "")}


async def send_interactive_buttons(to_phone: str, body: str, buttons: list[dict[str, str]]) -> dict[str, Any]:
    """Send up to three native WhatsApp reply buttons inside an open service window."""
    config = config_status()
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    to = normalise_phone(to_phone)
    text = str(body or "").strip()[:1024]
    if not config["send_ready"] or not to or not text:
        raise RuntimeError("WhatsApp interactive messaging is not configured.")
    if not 1 <= len(buttons) <= 3:
        raise ValueError("WhatsApp reply buttons must contain between one and three choices.")
    cleaned = []
    for button in buttons:
        button_id = str(button.get("id", "")).strip()
        title = str(button.get("title", "")).strip()
        if not button_id or len(button_id) > 256 or not title or len(title) > 20:
            raise ValueError("WhatsApp reply button IDs and titles are invalid.")
        cleaned.append({"type": "reply", "reply": {"id": button_id, "title": title}})
    url = f"https://graph.facebook.com/{config['graph_api_version']}/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {"type": "button", "body": {"text": text}, "action": {"buttons": cleaned}},
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
        response = await client.post(url, headers=headers, json=payload)
    if response.status_code < 200 or response.status_code >= 300:
        logger.warning("WhatsApp interactive send failed with HTTP %s", response.status_code)
        raise RuntimeError(f"WhatsApp interactive message send failed (HTTP {response.status_code}).")
    try:
        body_json = response.json()
    except json.JSONDecodeError:
        body_json = {}
    return {"accepted": True, "message_id": ((body_json.get("messages") or [{}])[0]).get("id", "")}


async def send_guided_reply(to_phone: str, body: str) -> dict[str, Any]:
    """Use native reply buttons for key decisions; fall back to text for every other reply."""
    text = str(body or "")
    if "Thanks for opting in." in text:
        buttons = [
            {"id": "START_CASE", "title": "Start a case"},
            {"id": "CHECK_STATUS", "title": "Check status"},
            {"id": "GET_HELP", "title": "Get help"},
        ]
        return await send_interactive_buttons(to_phone, text, buttons)
    if "Reply SAVE to create the case" in text:
        buttons = [
            {"id": "SAVE_CASE", "title": "Save case"},
            {"id": "EDIT_STORY", "title": "Edit story"},
            {"id": "CANCEL_CASE", "title": "Cancel"},
        ]
        return await send_interactive_buttons(to_phone, text, buttons)
    if text.startswith("Your case BR-"):
        buttons = [
            {"id": "CHECK_STATUS", "title": "Check status"},
            {"id": "CONTACTED_SUPPORT", "title": "Contacted support"},
            {"id": "STILL_WAITING", "title": "Still waiting"},
        ]
        return await send_interactive_buttons(to_phone, text, buttons)
    return await send_text_message(to_phone, text)


async def send_template_message(to_phone: str, template_name: str, language_code: str, parameters: list[str]) -> dict[str, Any]:
    """Send an approved utility template, intended for opted-in reminders outside the 24h window."""
    config = config_status()
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    to = normalise_phone(to_phone)
    name = str(template_name or "").strip()
    language = str(language_code or "en_US").strip()
    if not config["send_ready"] or not to or not re.fullmatch(r"[a-z0-9_]{1,512}", name) or not re.fullmatch(r"[a-z]{2}_[A-Z]{2}", language):
        raise RuntimeError("WhatsApp reminder template or messaging settings are invalid.")
    url = f"https://graph.facebook.com/{config['graph_api_version']}/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    body_parameters = [{"type": "text", "text": str(value)[:200]} for value in parameters]
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "template",
        "template": {
            "name": name,
            "language": {"code": language},
            "components": [{"type": "body", "parameters": body_parameters}],
        },
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
        response = await client.post(url, headers=headers, json=payload)
    if response.status_code < 200 or response.status_code >= 300:
        logger.warning("WhatsApp Cloud API template send failed with HTTP %s", response.status_code)
        raise RuntimeError(f"WhatsApp reminder send failed (HTTP {response.status_code}).")
    try:
        body_json = response.json()
    except json.JSONDecodeError:
        body_json = {}
    return {"accepted": True, "message_id": ((body_json.get("messages") or [{}])[0]).get("id", "")}
