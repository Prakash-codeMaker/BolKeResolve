"""State-aware next-step guidance for the Resolution Completion Loop.

This is deterministic product logic, not a claim that an external organisation
has taken an action. All status signals originate from user-reported case data.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Any

VERSION = "completion-loop-v2-reply-aware"

# A reply is only used to steer the next action after the user has reviewed and
# confirmed its interpretation. The categories are conservative first-pass text
# patterns; they are never evidence that a sender is authentic or that a refund
# was actually made.
_REPLY_GUIDANCE: dict[str, dict[str, Any]] = {
    "credential_or_remote_access_request": {
        "state": "safety_check", "state_label": "Potentially unsafe request",
        "title": "Do not share credentials or pay a release fee",
        "detail": "This reply may be asking for an OTP, UPI PIN, password, remote-access app or fee. Do not comply. Verify the sender using the organisation's official app or website. If you already shared a secret or suspect fraud, contact your bank immediately and use the official cyber-fraud reporting route.",
        "button": "Review safety steps", "target": "progress",
        "milestone": "Secure the account and verify the official support route",
        "why": "The text pattern may be unsafe. The sender and its claims have not been independently verified.",
    },
    "more_information_requested": {
        "state": "information_requested", "state_label": "Information requested",
        "title": "Send only the evidence they actually requested",
        "detail": "Check the original reply for the exact document, transaction reference or detail requested. Add or review relevant evidence here, redact unrelated personal information, and share it only through the organisation's verified official channel. Never send an OTP or UPI PIN.",
        "button": "Review requested evidence", "target": "evidence",
        "milestone": "Provide the requested information through the official channel",
        "why": "The reviewed reply appears to request more information; a generic follow-up may not answer that request.",
    },
    "refund_claimed_initiated": {
        "state": "awaiting_credit", "state_label": "Refund initiation reported",
        "title": "Get the refund reference and check for credit",
        "detail": "Ask for the refund reference (such as an ARN/RRN where applicable) and the expected credit date if either is missing. Check your own transaction history after that date. 'Initiated' or 'processed' does not mean the money has reached your account.",
        "button": "Update progress", "target": "progress",
        "milestone": "Record the stated refund reference/date and check the account",
        "why": "This is a user-confirmed interpretation of a reply, not independent proof of a refund or credit.",
    },
    "refund_claimed_credited": {
        "state": "verify_credit", "state_label": "Credit claimed — verify it",
        "title": "Check whether the money actually arrived",
        "detail": "Open your bank or payment-app transaction history and check the amount yourself. Do not mark this case resolved only because a message says 'credited'. If the credit is missing or partial, keep the case open and ask for the refund reference and expected credit date.",
        "button": "Review outcome", "target": "progress",
        "milestone": "Confirm the credit in your own account or record what is still missing",
        "why": "A support message claiming credit is not a bank verification.",
    },
    "under_review": {
        "state": "waiting_for_decision", "state_label": "Under review",
        "title": "Keep the existing case moving",
        "detail": "Save the support reference and the response date. If the reply gives an expected update date, record a follow-up after it; if no date is given, ask when you should expect one. Do not open a duplicate complaint without checking the existing process.",
        "button": "Update progress", "target": "progress",
        "milestone": "Record the next promised update or follow-up date",
        "why": "The reply appears to describe an investigation or escalation, not a completed resolution.",
    },
    "waiting_period_stated": {
        "state": "waiting_for_credit", "state_label": "Waiting period stated",
        "title": "Track the date they gave you",
        "detail": "Record the exact period or expected date stated in the original reply and save a follow-up after it. Treat this as the organisation's estimate, not a universal legal or regulatory deadline. If that date has passed, prepare a follow-up using the same reference.",
        "button": "Set follow-up", "target": "progress",
        "milestone": "Check again after the stated period",
        "why": "The reply appears to provide a waiting estimate; applicability of any official deadline must be checked separately.",
    },
    "acknowledgement_only": {
        "state": "awaiting_timeline", "state_label": "Acknowledged — timeline unclear",
        "title": "Keep the reference and ask when to expect an update",
        "detail": "Save the ticket/reference number. An acknowledgement alone does not mean the issue is being resolved. If no response date is stated, ask the organisation for one and record a follow-up in this case.",
        "button": "Update progress", "target": "progress",
        "milestone": "Record the expected response date or next reply",
        "why": "The reply appears to acknowledge receipt but does not describe a resolution.",
    },
    "rejected_or_closed": {
        "state": "review_rejection", "state_label": "Rejection needs review",
        "title": "Check the reason before choosing an escalation route",
        "detail": "Read the full original reply and preserve its reason and reference. Compare the reason with your confirmed facts and evidence, then check the current official eligibility and timing rules. Not every merchant refund belongs with the RBI Ombudsman.",
        "button": "Review next steps", "target": "progress",
        "milestone": "Identify the stated reason and the appropriate review route",
        "why": "This is a text classification, not a legal determination that the rejection is valid or invalid.",
    },
    "mixed_or_conflicting_reply": {
        "state": "reply_conflict", "state_label": "Reply has mixed signals",
        "title": "Pause and clarify the current status",
        "detail": "The message may contain contradictory statements or quoted older text. Read the full original and identify the latest statement. If the current status is unclear, ask the organisation to confirm it in writing before choosing another route.",
        "button": "Review reply", "target": "progress",
        "milestone": "Confirm the latest status without assuming resolution",
        "why": "Conflicting text should not trigger an automatic escalation or a resolved state.",
    },
    "needs_manual_review": {
        "state": "manual_reply_review", "state_label": "Reply needs your review",
        "title": "Review the original before deciding what to do",
        "detail": "The reply did not clearly match a supported pattern. Identify what the organisation actually says it did and what it asks you to do next. If unclear, ask for clarification through the official channel; BolKeResolve will not guess.",
        "button": "Review reply", "target": "progress",
        "milestone": "Record your own short interpretation and any reference",
        "why": "The reply was ambiguous to the deterministic classifier; manual review is safer than a guess.",
    },
}


def stage_for_reply_category(category: str) -> str:
    """Map a user-confirmed reply interpretation to an existing case stage."""
    if category in {"refund_claimed_initiated", "under_review", "waiting_period_stated", "acknowledgement_only"}:
        return "Awaiting response"
    if category in {"more_information_requested", "credential_or_remote_access_request", "mixed_or_conflicting_reply", "needs_manual_review"}:
        return "Needs next step"
    # A claimed credit or rejection still needs a user-controlled check/review.
    return "Follow-up needed"


def _latest_confirmed_reply(timeline: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not timeline:
        return None
    # case_bundle returns timeline newest-first. Respect that order for equal-second
    # events so a later explicit user action supersedes an older reply interpretation.
    latest = timeline[0]
    metadata = latest.get("metadata") or {}
    category = str(metadata.get("reply_review_category") or "")
    if (
        latest.get("event_type") == "response_received"
        and metadata.get("reply_interpretation_confirmed") is True
        and category in _REPLY_GUIDANCE
    ):
        return {
            "category": category,
            "label": str(metadata.get("reply_review_label") or category.replace("_", " ")),
            "channel": str(latest.get("channel") or "web"),
            "raw_reply_retained": False,
        }
    return None


def build_completion_loop(case: dict[str, Any], action_pack: dict[str, Any] | None = None) -> dict[str, Any]:
    stage = str(case.get("case_stage") or "Needs next step")
    outcome = case.get("outcome") or {}
    follow = case.get("follow_up") or {}
    timeline = case.get("timeline") or []
    pack = action_pack or {}
    readiness = pack.get("readiness") or {}
    pct = int(readiness.get("percent") or 0)
    follow_status = str((pack.get("follow_up") or {}).get("status") or "not_set")
    outcome_code = str(outcome.get("outcome_code") or "")
    reply_context = _latest_confirmed_reply(timeline)

    if reply_context:
        guidance = _REPLY_GUIDANCE[reply_context["category"]]
        action = {"key": reply_context["category"], **{key: guidance[key] for key in ("title", "detail", "button", "target", "why")}}
        state = guidance["state"]
        milestone = guidance["milestone"]
        if reply_context["category"] == "waiting_period_stated" and follow_status in {"overdue", "due_today"}:
            action = {
                "key": "reply-wait-follow-up-due",
                "title": "The stated waiting period may have passed",
                "detail": "Check the date in the original reply. If it has passed and the credit or resolution is still missing, follow up through the same official support thread and include its reference. This is not a universal regulatory deadline.",
                "button": "Prepare follow-up", "target": "draft",
                "why": "Your saved follow-up date is due or overdue; verify the actual date the organisation stated.",
            }
            state = "follow_up_due"
            milestone = "Record the result of this follow-up"
        elif reply_context["category"] == "under_review" and follow_status in {"overdue", "due_today"}:
            action = {
                "key": "reply-review-follow-up-due",
                "title": "Ask for an update on the existing review",
                "detail": "Use the same ticket/reference and ask for the current status and expected resolution date. Avoid opening duplicate complaints unless the official process requires it.",
                "button": "Prepare follow-up", "target": "draft",
                "why": "The saved follow-up date is due or overdue and the reviewed reply said the case was under review.",
            }
            state = "follow_up_due"
            milestone = "Record the result of this follow-up"
    elif outcome_code == "resolved" or stage == "Resolved (user-reported)":
        action = {"key":"confirm-outcome", "title":"Check that the money has actually arrived", "detail":"Check your bank or payment app yourself. If the credit is missing or partial, reopen this case and record what is still unresolved.", "button":"Review outcome", "target":"progress", "why":"A resolution was reported by you; BolKeResolve has not verified the credit."}
        state = "reported_resolved"
        milestone = "Confirm the credit in your own account"
    elif outcome_code == "no_response" or stage == "Follow-up needed":
        action = {"key":"follow-up", "title":"Continue the existing support thread", "detail":"Use your saved reference, mention the previous contact date, and ask for a specific status or expected resolution date. Avoid opening duplicate complaints unless the official process requires it.", "button":"Prepare follow-up", "target":"draft", "why":"Your case indicates that a response or resolution is still outstanding."}
        state = "needs_follow_up"
        milestone = "Record the next response or follow-up date"
    elif stage in {"Contacted support", "Awaiting response"} or outcome_code == "still_pending":
        if follow_status in {"overdue", "due_today"}:
            action = {"key":"follow-up-now", "title":"Your follow-up is due", "detail":"Check the original support channel and follow up using the same reference. If the organisation gave a specific timeline, compare against that promise before escalating.", "button":"Prepare follow-up", "target":"draft", "why":"Your saved follow-up date is due or overdue; this is a reminder, not a legal deadline."}
            state = "follow_up_due"
            milestone = "Record the result of this follow-up"
        else:
            action = {"key":"track-response", "title":"Keep the existing case moving", "detail":"Keep the support reference and any reply with this case. If you were given an expected response date, save it as a follow-up; if it passes, use the follow-up message rather than restarting from scratch.", "button":"Update progress", "target":"progress", "why":"You have reported contacting support or waiting for a response."}
            state = "waiting_for_response"
            milestone = "Record the reply or the next follow-up date"
    elif pct < 100:
        action = {"key":"complete-first-contact", "title":"Make the first contact more complete", "detail":"Check the short evidence list, fill any essential missing details, then review the message before sharing it with the organisation.", "button":"Finish preparation", "target":"prep", "why":"Your saved preparation checklist is not complete yet."}
        state = "prepare_first_contact"
        milestone = "Prepare and send the first support request yourself"
    else:
        action = {"key":"contact-support", "title":"Send the reviewed support request", "detail":"Copy the message into the organisation’s official support channel. Keep the acknowledgement or ticket reference, then record the result here.", "button":"Review support message", "target":"draft", "why":"Your preparation checklist is complete; sending still requires your action."}
        state = "ready_to_contact"
        milestone = "Record the support acknowledgement or reference"

    # Timestamps are ISO seconds in the existing schema; the timeline query uses
    # row insertion order as a secondary key so later actions win within a second.
    latest = max(timeline, key=lambda item: (str(item.get("created_at") or ""), item.get("event_type") != "created")) if timeline else None
    last_event = None
    if latest:
        last_event = {"type": str(latest.get("event_type") or "update"), "at": latest.get("created_at"), "label": str(latest.get("message") or "")[:180]}
    state_labels = {
        "reported_resolved": "Resolution reported",
        "needs_follow_up": "Follow-up needed",
        "follow_up_due": "Follow-up due",
        "waiting_for_response": "Waiting for response",
        "prepare_first_contact": "Prepare first contact",
        "ready_to_contact": "Ready to contact",
    }
    state_labels.update({item["state"]: item["state_label"] for item in _REPLY_GUIDANCE.values()})
    return {
        "version": VERSION,
        "state": state,
        "state_label": state_labels.get(state, "Next step"),
        "action": action,
        "next_milestone": milestone,
        "last_recorded_update": last_event,
        "follow_up_status": follow_status,
        "preparation_percent": pct,
        "reply_context": reply_context,
        "honesty_note": "This plan uses information you reported. BolKeResolve does not receive live bank or merchant status unless an explicitly authorised integration is connected.",
    }
