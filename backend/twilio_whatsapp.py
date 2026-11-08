"""Twilio WhatsApp Sandbox adapter (development/testing only by default).

This module translates Twilio's form-encoded payloads and REST API into the
provider-neutral contracts in backend.messaging. Credentials are always read
from the server environment and are never included in status responses/logs.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Mapping
from urllib.parse import urlsplit

import httpx
from fastapi import Request

from backend.messaging import InboundMessage
from backend.whatsapp import normalise_phone

logger = logging.getLogger("bolkeresolve.twilio_whatsapp")
_ACCOUNT_SID_RE = re.compile(r"^AC[0-9a-fA-F]{32}$")


def config_status() -> dict[str, Any]:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    sender = os.getenv("TWILIO_WHATSAPP_FROM", "").strip()
    webhook_url = os.getenv("TWILIO_WEBHOOK_PUBLIC_URL", "").strip()
    status_url = os.getenv("TWILIO_STATUS_CALLBACK_URL", "").strip()
    if not status_url and webhook_url:
        status_url = webhook_url.rstrip("/") + "/status"

    parsed_webhook = urlsplit(webhook_url) if webhook_url else None
    parsed_status = urlsplit(status_url) if status_url else None
    webhook_url_valid = bool(
        parsed_webhook
        and parsed_webhook.scheme == "https"
        and parsed_webhook.hostname
        and not parsed_webhook.username
        and not parsed_webhook.password
        and parsed_webhook.path == "/api/webhooks/twilio/whatsapp"
        and parsed_webhook.query == ""
        and parsed_webhook.fragment == ""
    )
    status_url_valid = bool(
        parsed_status
        and parsed_status.scheme == "https"
        and parsed_status.hostname
        and not parsed_status.username
        and not parsed_status.password
        and parsed_status.path == "/api/webhooks/twilio/whatsapp/status"
        and parsed_status.query == ""
        and parsed_status.fragment == ""
    )
    sender_valid = bool(sender.startswith("whatsapp:+") and normalise_phone(sender[len("whatsapp:+"):]))
    credentials_present = bool(_ACCOUNT_SID_RE.fullmatch(account_sid) and auth_token)
    return {
        "credentials_present": credentials_present,
        "sender_configured": sender_valid,
        "webhook_url_configured": webhook_url_valid,
        "status_callback_configured": status_url_valid,
        "send_ready": credentials_present and sender_valid,
        "webhook_ready": credentials_present and webhook_url_valid,
        "ready_for_sandbox_testing": credentials_present and sender_valid and webhook_url_valid and status_url_valid,
        "status_callback_url": status_url if status_url_valid else "",
    }


def webhook_url_for_request(request: Request, *, status_callback: bool = False) -> str:
    """Return the exact externally configured URL Twilio signs.

    Explicit configured URLs are preferred to request.url because reverse proxies
    may cause scheme/host mismatches. Query strings (if present) are preserved.
    """
    config = config_status()
    if status_callback:
        base = config.get("status_callback_url", "")
    else:
        base = os.getenv("TWILIO_WEBHOOK_PUBLIC_URL", "").strip()
    if not base:
        # Useful in local tests; production preflight requires an explicit HTTPS URL.
        base = str(request.url).split("?", 1)[0]
    query = request.url.query
    if query:
        return base + ("&" if "?" in base else "?") + query
    return base


def verify_webhook_signature(url: str, params: Mapping[str, Any], signature: str, auth_token: str | None = None) -> bool:
    """Validate `X-Twilio-Signature` with Twilio's official Python SDK.

    Twilio recommends using its SDK's RequestValidator rather than maintaining a
    local signature implementation. Fail closed if the SDK or secret is missing.
    """
    token = (auth_token if auth_token is not None else os.getenv("TWILIO_AUTH_TOKEN", "")).strip()
    if not url or not signature or not token:
        return False
    try:
        from twilio.request_validator import RequestValidator  # type: ignore[import-not-found]
    except ImportError:
        logger.error("Twilio SDK is missing; webhook signature validation fails closed")
        return False
    try:
        return bool(RequestValidator(token).validate(url, dict(params), signature.strip()))
    except Exception as exc:  # malformed provider input must not fail open
        logger.warning("Twilio webhook signature validation errored (%s)", type(exc).__name__)
        return False


def parse_inbound_form(form: Mapping[str, Any]) -> InboundMessage | None:
    """Normalize a Twilio inbound WhatsApp form payload; media is not downloaded in Phase 1."""
    sender_raw = str(form.get("From", "") or "").strip()
    to_raw = str(form.get("To", "") or "").strip()
    sid = str(form.get("MessageSid", form.get("SmsMessageSid", "")) or "").strip()
    body = str(form.get("Body", "") or "")[:4096]
    num_media_raw = str(form.get("NumMedia", "0") or "0")
    if not sender_raw.startswith("whatsapp:+") or not to_raw.startswith("whatsapp:+") or not sid:
        return None
    sender = normalise_phone(sender_raw[len("whatsapp:+"):])
    if not sender:
        return None
    try:
        num_media = max(0, min(int(num_media_raw), 10))
    except ValueError:
        num_media = 0
    if body.strip():
        message_type = "text"
        text = body
    elif num_media > 0:
        message_type = "unsupported_media"
        text = ""
    else:
        message_type = "text"
        text = ""
    return InboundMessage(
        message_id=sid,
        sender=sender,
        message_type=message_type,
        text=text,
        provider="twilio",
        media_id="",
        mime_type=str(form.get("MediaContentType0", "") or "")[:100],
    )


async def send_text_message(to_phone: str, body: str) -> dict[str, Any]:
    """Send one free-form reply through Twilio; API acceptance is not delivery."""
    config = config_status()
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    sender = os.getenv("TWILIO_WHATSAPP_FROM", "").strip()
    to = normalise_phone(to_phone)
    text = str(body or "").strip()
    if not config["send_ready"] or not to:
        raise RuntimeError("Twilio WhatsApp Sandbox is not configured.")
    if not text:
        raise ValueError("WhatsApp message text cannot be empty.")
    # WhatsApp provider body limits are bounded and avoid empty outbound requests.
    text = text[:1600]
    data: dict[str, str] = {
        "From": sender,
        "To": "whatsapp:+" + to,
        "Body": text,
    }
    status_callback = config.get("status_callback_url", "")
    if status_callback:
        data["StatusCallback"] = status_callback
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
        response = await client.post(url, auth=(account_sid, auth_token), data=data)
    if not 200 <= response.status_code < 300:
        logger.warning("Twilio WhatsApp send failed with HTTP %s", response.status_code)
        raise RuntimeError(f"Twilio WhatsApp message send failed (HTTP {response.status_code}).")
    try:
        response_json = response.json()
    except (json.JSONDecodeError, ValueError):
        response_json = {}
    message_sid = str(response_json.get("sid", ""))[:180]
    if not message_sid:
        raise RuntimeError("Twilio accepted no usable message ID for the WhatsApp reply.")
    return {
        "accepted": True,
        "message_id": message_sid,
        "provider": "twilio",
        "status": str(response_json.get("status", "accepted"))[:40],
    }


def parse_status_form(form: Mapping[str, Any]) -> dict[str, str]:
    return {
        "message_id": str(form.get("MessageSid", form.get("SmsMessageSid", "")) or "").strip()[:180],
        "status": str(form.get("MessageStatus", form.get("SmsStatus", "")) or "").strip().lower()[:40],
        "error_code": str(form.get("ErrorCode", "") or "").strip()[:40],
        "error_message": str(form.get("ChannelStatusMessage", "") or "").strip()[:300],
    }
