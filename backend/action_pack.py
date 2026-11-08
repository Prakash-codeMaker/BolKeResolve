"""Build a user-reviewable resolution pack from the saved case facts.

No external account is contacted and no fact is treated as independently verified.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any


CHECKLISTS: dict[str, list[dict[str, Any]]] = {
    "Refund not received": [
        {"key": "refund_order_record", "title": "Order receipt or invoice", "detail": "Keep the order ID, order date, merchant name and amount together.", "required": True},
        {"key": "refund_cancel_confirmation", "title": "Cancellation or refund promise", "detail": "Save the cancellation confirmation or the message that states when the refund was expected.", "required": True},
        {"key": "refund_payment_record", "title": "Original payment record", "detail": "Keep the payment entry and transaction reference. Hide unrelated account details.", "required": True},
        {"key": "refund_support_reference", "title": "Merchant support reference", "detail": "If you contacted support, record the ticket number and date of the conversation.", "required": False},
    ],
    "Failed UPI payment": [
        {"key": "upi_failed_transaction", "title": "Failed transaction record", "detail": "Save the failed status, amount, date/time and UPI transaction reference.", "required": True},
        {"key": "upi_debit_record", "title": "Debit entry from your bank or UPI app", "detail": "Check whether money actually left your account; do not include balances or unrelated entries.", "required": True},
        {"key": "upi_bank_acknowledgement", "title": "Bank or payment-app acknowledgement", "detail": "If you raised a complaint, keep its reference number and response.", "required": False},
    ],
    "UPI payment pending / recipient not credited": [
        {"key": "upi_pending_record", "title": "Pending transaction details", "detail": "Keep the current app status, transaction reference, date/time and amount.", "required": True},
        {"key": "upi_debit_record", "title": "Debit entry from your bank or UPI app", "detail": "Confirm whether your account was debited and retain the relevant entry.", "required": True},
        {"key": "upi_bank_acknowledgement", "title": "Bank or payment-app acknowledgement", "detail": "Save any complaint/reference number and the response you receive.", "required": False},
    ],
    "Duplicate charge": [
        {"key": "duplicate_charge_records", "title": "Both transaction entries", "detail": "Compare status, date/time, amount and transaction IDs for both entries.", "required": True},
        {"key": "duplicate_order_receipt", "title": "Receipt or order confirmation", "detail": "Use it to compare the amount that should have been charged with both entries.", "required": True},
        {"key": "duplicate_support_reference", "title": "Dispute reference", "detail": "Save any ticket number and the merchant/bank response.", "required": False},
    ],
    "Incorrect amount": [
        {"key": "amount_receipt", "title": "Receipt showing the expected amount", "detail": "Keep the itemised receipt or invoice for comparison.", "required": True},
        {"key": "amount_payment_record", "title": "Payment record showing the charged amount", "detail": "Record the disputed amount and transaction reference.", "required": True},
        {"key": "amount_support_reference", "title": "Merchant or bank response", "detail": "Keep a ticket number or written explanation if one is available.", "required": False},
    ],
    "Order paid but not received": [
        {"key": "order_confirmation", "title": "Order confirmation", "detail": "Keep the order ID, amount, merchant and promised delivery date.", "required": True},
        {"key": "order_payment_record", "title": "Payment record", "detail": "Save the related payment entry or transaction reference.", "required": True},
        {"key": "order_delivery_messages", "title": "Delivery or cancellation messages", "detail": "Keep status updates, cancellation confirmation or refund promises.", "required": False},
    ],
    "Suspected fraud or unauthorised transaction": [
        {"key": "fraud_transaction_record", "title": "Transaction details, if safe to access", "detail": "Note the date/time, amount and reference. Do not delay contacting your bank to collect files.", "required": False},
        {"key": "fraud_bank_reference", "title": "Bank report reference", "detail": "Record the bank's complaint/acknowledgement number after contacting its official channel.", "required": False},
        {"key": "fraud_cybercrime_reference", "title": "Cybercrime report acknowledgement", "detail": "If you report through 1930 or the official portal, keep the acknowledgement number.", "required": False},
    ],
}
DEFAULT_CHECKLIST = [
    {"key": "general_transaction_record", "title": "Relevant transaction or order record", "detail": "Keep the date, amount, merchant and reference needed to identify the issue.", "required": True},
    {"key": "general_support_correspondence", "title": "Relevant support correspondence", "detail": "Save messages, ticket numbers and replies if you have them.", "required": False},
]
PRIVACY_ITEM = {"key": "redact_sensitive_details", "title": "Check for sensitive details before sharing", "detail": "Remove OTPs, UPI PINs, passwords, full card numbers, full account numbers and unrelated personal information.", "required": True}
ALL_CHECKLIST_KEYS = {item["key"] for group in CHECKLISTS.values() for item in group} | {item["key"] for item in DEFAULT_CHECKLIST} | {PRIVACY_ITEM["key"]}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _due_status(due_date: str, completed: bool) -> tuple[str, int | None]:
    if completed:
        return "completed", None
    if not due_date:
        return "not_set", None
    try:
        delta = (date.fromisoformat(due_date) - date.today()).days
    except ValueError:
        return "not_set", None
    if delta < 0:
        return "overdue", delta
    if delta == 0:
        return "due_today", 0
    return "upcoming", delta


def build_action_pack(case: dict[str, Any], checklist_state: dict[str, bool] | None = None, follow_up: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a deterministic checklist, action snapshot and export-ready text."""
    checklist_state = checklist_state or {}
    follow_up = follow_up or {"due_date": "", "note": "", "completed": False}
    issue_type = _clean(case.get("issue_type")) or "Other payment issue"
    resolution = case.get("resolution") or {}
    classification = resolution.get("classification") or {}
    canonical = _clean(classification.get("issue_type")) or issue_type
    tasks = [dict(task) for task in CHECKLISTS.get(canonical, DEFAULT_CHECKLIST)]
    tasks.append(dict(PRIVACY_ITEM))
    for task in tasks:
        task["checked"] = bool(checklist_state.get(task["key"], False))
    required = [task for task in tasks if task["required"]]
    completed_required = sum(1 for task in required if task["checked"])
    evidence_files = case.get("evidence") or []
    due_date = _clean(follow_up.get("due_date"))
    completed = bool(follow_up.get("completed", False))
    due_status, days_until = _due_status(due_date, completed)
    amount = case.get("amount")
    amount_text = f"₹{float(amount):,.2f}" if amount is not None else "not provided"
    merchant = _clean(case.get("merchant")) or "not provided"
    payment_date = _clean(case.get("payment_date")) or "not provided"
    payment_status = _clean(case.get("payment_status")) or "unknown"
    stage = _clean(case.get("case_stage")) or "Needs next step"
    description = _clean(case.get("description"))
    next_steps = resolution.get("recommended_steps") or []
    first_step = next_steps[0] if next_steps else {}
    sources = resolution.get("official_sources") or []

    if canonical == "Suspected fraud or unauthorised transaction":
        action_summary = "Contact your bank/payment provider immediately through its official channel; report suspected online financial fraud using 1930 or the official cybercrime portal. Do not wait to finish this checklist."
    elif canonical in {"Refund not received", "Order paid but not received"}:
        action_summary = "Gather the order and payment references, then ask the merchant’s official support channel for a written status and acknowledgement. Use the consumer grievance route if the consumer issue remains unresolved."
    elif canonical in {"Failed UPI payment", "UPI payment pending / recipient not credited"}:
        action_summary = "Confirm the exact transaction status in your UPI app and contact your bank/payment provider with the transaction reference if it remains unresolved."
    else:
        action_summary = _clean(first_step.get("detail")) or "Confirm the relevant organisation and ask its official support channel for a written response."

    summary_lines = [
        f"Case: {case.get('case_id', '—')}",
        f"Issue: {canonical}",
        f"Merchant / organisation: {merchant}",
        f"Reported amount: {amount_text}",
        f"Payment date: {payment_date}",
        f"Status selected by user: {payment_status}",
        f"Case progress (self-reported): {stage}",
        f"Description supplied by user: {description or 'not provided'}",
    ]
    steps_lines = [f"{index}. {step.get('title', 'Next step')}\n   {step.get('detail', '')}" for index, step in enumerate(next_steps, 1)]
    checklist_lines = [f"[{'x' if task['checked'] else ' '}] {task['title']} — {task['detail']}" for task in tasks]
    route_lines = [f"- {source.get('organization', 'Official source')}: {source.get('title', '')}\n  {source.get('url', '')}" for source in sources]
    draft = _clean(case.get("support_draft")) or "No support message has been prepared yet. Prepare one in the Message tab and review it before sending."
    followup_line = f"Follow-up date: {due_date or 'not set'} ({due_status.replace('_', ' ')})"
    if _clean(follow_up.get("note")):
        followup_line += f"\nFollow-up note: {_clean(follow_up.get('note'))}"
    export_text = "\n".join([
        "BOLKERESOLVE — CASE ACTION PACK",
        "Generated from information saved by the user. No bank, merchant or government system has been queried by BolKeResolve.",
        "",
        "CASE SUMMARY",
        *summary_lines,
        "",
        "RECOMMENDED FIRST ACTION",
        action_summary,
        "",
        "GUIDED NEXT STEPS",
        *(steps_lines or ["No steps are available yet. Refresh the plan after reviewing the case details."]),
        "",
        "PREPARATION CHECKLIST",
        *checklist_lines,
        f"Required readiness: {completed_required}/{len(required)} complete",
        "",
        "OFFICIAL SOURCES TO REVIEW",
        *(route_lines or ["No official source is attached to this plan yet."]),
        "",
        "SUPPORT MESSAGE DRAFT",
        draft,
        "",
        "FOLLOW-UP",
        followup_line,
        "",
        "SAFETY REMINDER",
        "Never share OTPs, UPI PINs, passwords, full card numbers or remote-access codes. Review every detail and source before acting. Prepared drafts are not submitted automatically.",
    ])
    return {
        "version": 1,
        "title": "Your resolution pack",
        "issue_type": canonical,
        "first_action": action_summary,
        "first_step_title": _clean(first_step.get("title")) or "Review the next step",
        "evidence_checklist": tasks,
        "readiness": {
            "completed_required": completed_required,
            "required_total": len(required),
            "percent": round(completed_required / len(required) * 100) if required else 100,
        },
        "evidence_uploaded": len(evidence_files),
        "follow_up": {
            "due_date": due_date,
            "note": _clean(follow_up.get("note")),
            "completed": completed,
            "status": due_status,
            "days_until": days_until,
        },
        "official_sources": sources,
        "export_text": export_text,
        "disclaimer": "This pack is based on user-reported details and public guidance. It is not a filing, payment trace, legal determination or guarantee of resolution.",
    }
