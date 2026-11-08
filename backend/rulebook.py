"""Versioned, conservative metadata for BolKeResolve's deterministic playbooks.

This is a transparency layer over resolution.py; it does not independently verify a
transaction, compute a live RBI deadline, or replace legal review.
"""
from __future__ import annotations

from typing import Any

RULEBOOK_VERSION = "india-payments-2026.11.03.1"
RULEBOOK_REVIEWED_ON = "2026-11-03"

SOURCE_URLS = {
    "npci_upi_faq": "https://www.npci.org.in/what-we-do/upi/faqs",
    "rbi_failed_transaction_framework": "https://www.rbi.org.in/commonman/Upload/English/Notification/PDFs/CIRCULAR677EC931A7A65E4D99AA957D8E85BC0A2A.PDF",
    "nch": "https://consumerhelpline.gov.in/public/convergencepartners",
    "razorpay_settlement": "https://razorpay.com/docs/payments/payments/dashboard/?preferred-country=IN",
    "razorpay_settlement_faq": "https://tfs.np.razorpay.in/docs/payments/settlements/faqs",
    "cybercrime": "https://cybercrime.gov.in/",
    "rbi_ombudsman_2026": "https://old.rbi.org.in/commonman/english/scripts/faqs.aspx?id=3407",
}

_RULES: dict[str, dict[str, Any]] = {
    "urgent_unauthorised_payment": {
        "title": "Possible unauthorised payment — act promptly",
        "scope": "Use when the user reports an unrecognised debit, suspected fraud or unauthorised transaction.",
        "next_action": "Contact the bank/payment provider through its official channel immediately and use the official cyber-fraud reporting route when appropriate. Do not delay to complete other BolKeResolve steps.",
        "source_ids": ["cybercrime"],
        "type": "safety_guidance",
    },
    "failed_upi_debit_npci_faq": {
        "title": "Failed UPI transaction with a debit reported",
        "scope": "Only applies when the transaction is actually shown as failed and the account was debited; confirm the payment type and current provider status.",
        "next_action": "Check the transaction's current status and reference in the official app. NPCI's FAQ advises contacting bank customer support if a failed debit has not returned within one hour; verify the precise scenario and current official instructions before relying on that guidance.",
        "source_ids": ["npci_upi_faq", "rbi_failed_transaction_framework"],
        "type": "provider_guidance_not_universal_deadline",
    },
    "upi_pending_recipient_not_credited": {
        "title": "UPI pending / recipient not credited",
        "scope": "Only use for a pending funds transfer where the beneficiary may not yet have been credited. Do not use this timing for a merchant refund.",
        "next_action": "Confirm the live status in the payment app and retain the transaction reference. NPCI's FAQ describes up to 48 hours for some pending debit/not-credited cases; this is not universal and the current transaction type and provider guidance must be checked.",
        "source_ids": ["npci_upi_faq", "rbi_failed_transaction_framework"],
        "type": "provider_guidance_not_universal_deadline",
    },
    "merchant_gateway_settlement": {
        "title": "Payment gateway settlement not credited to the business bank account",
        "scope": "Use when a business accepts customer payments through a payment gateway and the gateway settlement/payout has not reached the business bank account. Do not treat it as a consumer ecommerce order refund.",
        "next_action": "Sign in to the provider's Dashboard. Open Transactions → Payments, select an affected captured payment and open its settlement_id for the breakdown (or use the Settlements view). Inspect the settlement status, settlement ID, scheduled date and UTR if available. Follow the status-specific path: trace a processed settlement using its UTR, investigate the failure/hold reason for a failed or held settlement, or compare a created/initiated settlement with the account's configured settlement schedule. Raise or continue a traceable support ticket with the settlement ID and relevant report.",
        "source_ids": ["razorpay_settlement", "razorpay_settlement_faq"],
        "type": "merchant_funds_flow_and_settlement_trace",
    },
    "merchant_refund_policy_first": {
        "title": "Delayed merchant refund",
        "scope": "Use for an order/service refund promised by a merchant. UPI failed-transaction turnaround times do not automatically apply.",
        "next_action": "Check the cancellation/refund confirmation and the merchant's policy that applied to the order. Ask the merchant for a refund reference and expected credit date, then choose an escalation route based on the merchant's response and the applicable process.",
        "source_ids": ["nch"],
        "type": "merchant_policy_and_case_specific_timing",
    },
    "rbi_ombudsman_eligibility": {
        "title": "RBI Ombudsman route — eligibility required",
        "scope": "Only for grievances involving a covered RBI-regulated entity when the prior-contact and other scheme conditions are satisfied.",
        "next_action": "Check the current scheme's eligibility, prior-contact and timing requirements before escalating. A general merchant refund dispute is not automatically an RBI Ombudsman case.",
        "source_ids": ["rbi_ombudsman_2026"],
        "type": "conditional_escalation",
    },
    "general_consumer_grievance": {
        "title": "Consumer grievance route",
        "scope": "For a consumer-service grievance where the merchant's own support has not resolved the matter and NCH's current scope is relevant.",
        "next_action": "Review the official National Consumer Helpline instructions and submit your grievance yourself if appropriate. BolKeResolve does not register a complaint for you.",
        "source_ids": ["nch"],
        "type": "official_route_guidance",
    },
    "general_user_reported_case": {
        "title": "General first-pass guidance",
        "scope": "Use when the issue cannot confidently be classified into a narrower supported path.",
        "next_action": "Confirm the issue type and key facts, then review the official support route before taking action.",
        "source_ids": [],
        "type": "general_guidance",
    },
}


def rulebook_metadata(issue_type: str, payment_status: str = "unknown", description: str = "") -> dict[str, Any]:
    """Return reproducible metadata and a small number of matched applicable rules."""
    issue = str(issue_type or "").strip().casefold()
    status = str(payment_status or "unknown").strip().casefold()
    text = str(description or "").casefold()
    if any(token in text for token in ("unauthorised", "unauthorized", "unrecognised", "unrecognized", "fraud", "scam", "i did not make", "i didn't make", "not my transaction", "मैंने नहीं किया", "धोखाधड़ी")) or status == "unauthorized":
        ids = ["urgent_unauthorised_payment"]
    elif "merchant settlement" in issue or "gateway settlement" in issue or "merchant_settlement" in text:
        ids = ["merchant_gateway_settlement"]
    elif "pending" in issue or status == "pending":
        ids = ["upi_pending_recipient_not_credited"]
    elif "failed upi" in issue or "upi payment failed" in text or (status == "failed" and ("upi" in text or "upi" in issue)):
        ids = ["failed_upi_debit_npci_faq"]
    elif "refund" in issue or "refund" in text:
        ids = ["merchant_refund_policy_first"]
    else:
        ids = ["general_consumer_grievance"] if any(token in text for token in ("merchant", "order", "service", "consumer", "delivery", "ऑर्डर", "रिफंड")) else ["general_user_reported_case"]
    return {
        "version": RULEBOOK_VERSION,
        "reviewed_on": RULEBOOK_REVIEWED_ON,
        "engine": "deterministic_playbook_metadata",
        "matched_rules": [
            {
                "id": rid,
                "title": _RULES[rid]["title"],
                "scope": _RULES[rid]["scope"],
                "next_action": _RULES[rid]["next_action"],
                "type": _RULES[rid]["type"],
                "sources": [{"id": sid, "url": SOURCE_URLS[sid]} for sid in _RULES[rid]["source_ids"]],
            }
            for rid in ids
        ],
        "notice": "This is versioned guidance based on user-reported facts, not a live transaction check or legal determination. Source pages can change; review them before acting.",
    }
