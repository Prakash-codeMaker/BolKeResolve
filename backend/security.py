"""Small defensive text scrubber for obvious authentication secrets and identifiers.

This is a best-effort safety net, not a DLP product. It does not inspect image/PDF evidence.
"""
from __future__ import annotations

import re
from typing import NamedTuple


class ScrubResult(NamedTuple):
    text: str
    redacted_types: list[str]


def _luhn_valid(value: str) -> bool:
    digits = [int(ch) for ch in value if ch.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    parity = len(digits) % 2
    for idx, digit in enumerate(digits):
        if idx % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def scrub_sensitive_text(value: str) -> ScrubResult:
    text = value or ""
    redacted: list[str] = []

    # Keep the secret label while removing the value so the surrounding sentence remains useful.
    secret_patterns = [
        ("OTP/PIN", re.compile(r"(?i)\b(otp|one[- ]time password|upi[ -]?pin|pin|cvv|cvc|security code)\b(\s*(?:is|was|:|=|number)?\s*)[0-9]{3,8}\b")),
        ("password", re.compile(r"(?i)\b(password|passcode)\b(\s*(?:is|was|:|=)\s*)[^\s,;.!]{4,80}")),
        ("Aadhaar", re.compile(r"(?i)\b(aadhaar|aadhar|uid)\b([^\d]{0,18})(\d{4}[ -]?\d{4}[ -]?\d{4})\b")),
        ("PAN", re.compile(r"(?i)\b[A-Z]{5}\d{4}[A-Z]\b")),
        ("account number", re.compile(r"(?i)\b(account|a/c|account number)\b([^\d]{0,12})(\d{8,20})\b")),
        ("phone number", re.compile(r"(?i)\b(phone|mobile|mob(?:ile)? number|contact number)\b([^\d]{0,12})([6-9]\d{9})\b")),
    ]
    for kind, pattern in secret_patterns:
        if kind in {"OTP/PIN", "password", "Aadhaar", "account number", "phone number"}:
            if kind in {"OTP/PIN", "password"}:
                text, n = pattern.subn(lambda m: f"{m.group(1)}{m.group(2)}[REDACTED]", text)
            elif kind in {"Aadhaar", "account number", "phone number"}:
                text, n = pattern.subn(lambda m: f"{m.group(1)}{m.group(2)}[REDACTED]", text)
            else:
                text, n = pattern.subn("[REDACTED]", text)
        else:
            text, n = pattern.subn("[REDACTED PAN]", text)
        if n and kind not in redacted:
            redacted.append(kind)

    # Detect and redact Luhn-valid payment card numbers, including groups separated by spaces/hyphens.
    card_pattern = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
    def redact_card(match: re.Match[str]) -> str:
        digits = re.sub(r"\D", "", match.group(0))
        if _luhn_valid(digits):
            if "payment card" not in redacted:
                redacted.append("payment card")
            return "[REDACTED CARD]"
        return match.group(0)
    text = card_pattern.sub(redact_card, text)

    return ScrubResult(text=text, redacted_types=redacted)
