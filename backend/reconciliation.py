"""Safe, review-first CSV reconciliation import.

The parser intentionally extracts only transaction/settlement fields useful for a case.
It does not execute formulas, import arbitrary columns, or claim the CSV is provider-verified.
"""
from __future__ import annotations

import csv
import io
import re
from collections import Counter
from typing import Any

MAX_CSV_BYTES = 8 * 1024 * 1024
MAX_CSV_ROWS = 5000

FIELD_ALIASES: dict[str, set[str]] = {
    "payment_id": {"payment id", "payment_id", "paymentid", "payment reference", "payment ref"},
    "order_id": {"order id", "order_id", "orderid", "merchant order id"},
    "settlement_id": {"settlement id", "settlement_id", "settlementid", "payout id", "payout_id"},
    "utr": {"utr", "bank utr", "utr number", "bank reference", "bank reference number"},
    "status": {"status", "payment status", "settlement status", "payout status", "transaction status"},
    "amount": {"amount", "payment amount", "gross amount", "transaction amount", "debit amount"},
    "net_amount": {"net amount", "settled amount", "settlement amount", "net settled amount", "net payout"},
    "currency": {"currency", "currency code"},
    "settlement_date": {"settlement date", "settled at", "settlement timestamp", "payout date"},
    "fees": {"fee", "fees", "gateway fee", "processing fee", "mdr"},
    "tax": {"tax", "gst", "gst on fee", "tax on fees"},
    "refund_offset": {"refund", "refund amount", "refund offset", "refunds"},
    "chargeback": {"chargeback", "chargeback amount", "dispute amount"},
}


def _header_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").strip().casefold()).strip()


def _clean_cell(value: Any, limit: int = 120) -> str:
    text = str(value or "").replace("\x00", "").strip()
    # Spreadsheet formula strings are data, not executable commands. Do not let them
    # become part of a preview/export as formulas; preserve a visible apostrophe.
    if text.startswith(("=", "+", "-", "@")):
        text = "'" + text
    return text[:limit]


def parse_reconciliation_csv(content: bytes, *, provider_hint: str = "") -> dict[str, Any]:
    if not content:
        raise ValueError("The CSV file is empty.")
    if len(content) > MAX_CSV_BYTES:
        raise ValueError("The CSV file exceeds the 8 MB import limit.")
    if b"\x00" in content[:4096]:
        raise ValueError("The file does not look like a text CSV.")
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Please export the report as UTF-8 CSV and try again.") from exc
    sample = decoded[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(decoded), dialect=dialect)
    headers = [str(h or "").strip() for h in (reader.fieldnames or [])]
    if not headers:
        raise ValueError("The CSV needs a header row.")
    normalized_headers = {_header_key(h): h for h in headers if h}
    mapping: dict[str, str] = {}
    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            if _header_key(alias) in normalized_headers:
                mapping[field] = normalized_headers[_header_key(alias)]
                break
    identifier_fields = {"payment_id", "order_id", "settlement_id", "utr"}
    if not (set(mapping) & identifier_fields) or not (set(mapping) & {"status", "amount", "net_amount"}):
        raise ValueError(
            "I could not recognise this as a payment or settlement report. Include a transaction/payment/settlement reference and a status or amount column."
        )
    rows: list[dict[str, str]] = []
    for index, raw in enumerate(reader):
        if index >= MAX_CSV_ROWS:
            raise ValueError(f"The report has more than {MAX_CSV_ROWS} rows. Export a smaller date range.")
        item = {field: _clean_cell(raw.get(source, "")) for field, source in mapping.items()}
        if not any(item.values()):
            continue
        # Ignore rows that only contain an amount without a transaction or settlement reference.
        if not any(item.get(field) for field in identifier_fields):
            continue
        item["source_row"] = str(index + 2)
        rows.append(item)
    if not rows:
        raise ValueError("No usable payment or settlement rows were found in this report.")
    statuses = Counter((r.get("status") or "not provided").casefold() for r in rows)
    detected = "Razorpay" if "razorpay" in (provider_hint + " " + " ".join(headers)).casefold() else (provider_hint or "Unspecified provider")
    return {
        "provider": detected[:60],
        "status": "preview_requires_user_review",
        "row_count": len(rows),
        "headers_recognised": mapping,
        "status_counts": dict(statuses),
        "rows": rows,
        "notice": "These are values read from a user-uploaded CSV. They are not verified against the provider or bank. Review the original report before confirming any row.",
    }
