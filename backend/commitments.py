"""Condition-aware commitment extraction and deterministic reconciliation.

This module deliberately extracts only conservative candidates from an explicitly
provided transcript/text. It never treats a transcript, user-confirmed event, or
uploaded document as independent proof that a company acted.
"""
from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from backend.security import scrub_sensitive_text

VERSION = "commitment-reconcile-v1"

_NUMBER_WORDS = {
    "one": 1, "a": 1, "an": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "fourteen": 14,
    "fifteen": 15, "twenty": 20, "thirty": 30,
}
_NUMBER_PATTERN = r"(?:\d{1,3}|one|a|an|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fourteen|fifteen|twenty|thirty)"
_DURATION_RE = re.compile(
    rf"(?P<lo>{_NUMBER_PATTERN})(?:\s*(?:-|–|to)\s*(?P<hi>{_NUMBER_PATTERN}))?\s*"
    r"(?P<daytype>business|working|calendar)?\s*(?P<unit>days?|weeks?|hours?)\b", re.I
)
_AMOUNT_RE = re.compile(r"(?:₹\s*|\b(?:inr|rs\.?|rupees?)\s*)(\d[\d,]*(?:\.\d{1,2})?)", re.I)
_CONDITION_PATTERNS = (
    re.compile(r"\b(?:after|once|when|upon|following)\s+(?:the\s+)?([^,.;]{3,180})", re.I),
    re.compile(r"\b(?:only if|provided that|conditional upon)\s+([^,.;]{3,180})", re.I),
    re.compile(r"\bif\s+([^,.;]{3,180})", re.I),
    re.compile(r"([^,.;]{3,120}?)\s+(?:ke baad|hone ke baad|milne par|hote hi)\b", re.I),
)
_PROMISE_RE = re.compile(
    r"\b(?:we will|we'll|we shall|shall|will|is committed to|are committed to|"
    r"we promise|we guarantee|we can confirm|kar denge|ho jayega|bhej denge|"
    r"process karenge|initiate karenge|refund kar diya jayega)\b", re.I
)
_QUALIFIER_RE = re.compile(r"\b(may|might|usually|typically|expect|expected|should|aim to|likely|approximately|around)\b", re.I)
_NEGATED_PROMISE_RE = re.compile(
    r"\b(?:will not|won't|shall not|cannot|can't|can not|will never|won't be able to|"
    r"not going to|are unable to|is unable to|nahi karenge|nahi kar sakte|"
    r"nahi kar pa(?:y|a)enge|refund nahi hoga|refund nahi milega)\b",
    re.I,
)
_EXCEPTION_CLAUSE_RE = re.compile(
    r"\b(?:unless|except\s+(?:when|if|where)|subject to)\b", re.I
)


def _primary_statement_sentence(text: str) -> str:
    """Choose the sentence most relevant to an actionable support statement.

    This helps prevent a hedge or negation in an unrelated sentence from
    changing the interpretation of the commitment sentence.
    """
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    action_terms = r"\b(refund|payment|return|deliver|replace|process|initiate|रिफंड)\b"
    for sentence in sentences:
        if _PROMISE_RE.search(sentence) and re.search(action_terms, sentence, re.I):
            return sentence
    for sentence in sentences:
        if _PROMISE_RE.search(sentence):
            return sentence
    return sentences[0] if sentences else text


def _number(token: str | None) -> int | None:
    if not token:
        return None
    token = token.strip().lower().replace(",", "")
    if token.isdigit():
        return int(token)
    return _NUMBER_WORDS.get(token)


def _clean_text(value: str, limit: int = 3000) -> str:
    return scrub_sensitive_text(str(value or "").strip()).text[:limit].strip()


def _extract_condition(text: str) -> str:
    # Do not treat a duration-only phrase such as "after 5 days" as a condition.
    for pattern in _CONDITION_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        condition = re.sub(r"\s+", " ", match.group(1)).strip(" ,:;.-")
        if re.fullmatch(r"\d+\s+(?:business|working|calendar)?\s*days?", condition, re.I):
            continue
        # If the text starts with a duration before the condition, condition extraction
        # should capture only the event predicate, not the entire remaining promise.
        condition = re.sub(r"\s+(?:and then|then)\s+.*$", "", condition, flags=re.I)
        if len(condition) >= 3:
            return condition[:180]
    return ""


def _action(text: str) -> tuple[str, str]:
    lower = text.lower()
    if "refund" in lower or "रिफंड" in lower:
        if re.search(r"\b(?:credit(?:ed)?|credited to your account|deposit(?:ed)?)\b", lower):
            return "credit_refund", "Credit the refund to the account"
        if re.search(r"\b(?:initi(?:ate|ated|ating)|start(?:ed|ing)?|raise|raised)\b", lower) or "initiate kar" in lower:
            return "initiate_refund", "Initiate the refund"
        if re.search(r"\b(?:process(?:ed|ing)?|process kar)\b", lower):
            return "process_refund", "Process the refund"
        return "refund_action", "Refund action (confirm the exact action)"
    if re.search(r"\b(?:review|verify|check)\b.{0,60}\b(?:document|invoice|receipt|proof|return)\b", lower):
        return "review_documents", "Review the requested documents"
    if re.search(r"\b(?:deliver|dispatch|ship|send)\b", lower):
        return "deliver_or_send", "Deliver or send the item (confirm exact action)"
    if re.search(r"\b(?:replace|replacement)\b", lower):
        return "replace_item", "Arrange a replacement"
    # Conservative fallback: capture the clause around a commitment marker for review.
    m = re.search(r"\b(?:we will|we'll|will|shall|kar denge|ho jayega)\b\s+([^.;]{3,160})", text, re.I)
    if m:
        return "other_action", re.sub(r"\s+", " ", m.group(1)).strip()[:160]
    return "unknown_action", ""


def extract_commitment_candidate(text: str, source_type: str = "support_call_transcript") -> dict[str, Any]:
    """Return a user-reviewable candidate. No state is saved by this function."""
    safe_text = _clean_text(text, 4000)
    if len(safe_text) < 8:
        return {"version": VERSION, "can_confirm": False, "notice": "Add a longer statement so it can be reviewed.", "candidate": None}

    condition = _extract_condition(safe_text)
    duration_match = _DURATION_RE.search(safe_text)
    duration = _number(duration_match.group("lo")) if duration_match else None
    duration_max = (_number(duration_match.group("hi")) if duration_match.group("hi") else duration) if duration_match else duration
    unit = duration_match.group("unit").lower().rstrip("s") if duration_match else ""
    unit = "hour" if unit == "hour" else ("week" if unit == "week" else ("day" if unit == "day" else ""))
    daytype_word = (duration_match.group("daytype") or "").lower() if duration_match else ""
    day_type = "business_day" if daytype_word in {"business", "working"} else ("calendar_day" if daytype_word == "calendar" else "unspecified")

    amount_minor = None
    currency = "INR"
    amount_match = _AMOUNT_RE.search(safe_text)
    if amount_match:
        try:
            amount = float(amount_match.group(1).replace(",", ""))
            amount_minor = round(amount * 100)
        except (ValueError, OverflowError):
            amount_minor = None

    action_code, action_text = _action(safe_text)
    primary_sentence = _primary_statement_sentence(safe_text)
    has_promise = bool(_PROMISE_RE.search(primary_sentence))
    # A negation must never silently become a positive promise. Preserve it as a
    # manually reviewable statement with no automatic clock calculation.
    is_negated_promise = bool(_NEGATED_PROMISE_RE.search(primary_sentence)) and bool(
        re.search(r"\b(refund|payment|return|deliver|replace|process|initiate|रिफंड)\b", primary_sentence, re.I)
    )
    is_exception_clause = bool(_EXCEPTION_CLAUSE_RE.search(primary_sentence)) and has_promise
    sentence_duration = _DURATION_RE.search(primary_sentence)
    qualifier_text = primary_sentence[:sentence_duration.start()] if sentence_duration else primary_sentence
    qualifier_match = _QUALIFIER_RE.search(qualifier_text)
    qualifier = qualifier_match.group(1).lower() if qualifier_match else "stated_by_speaker"
    # A qualifying hedge in the promise clause is not a guarantee, even when
    # the same full message contains "will". Ignore unrelated later sentences.
    if is_negated_promise:
        speech_act = "unclassified_statement"
        action_code = "negative_or_refusal"
        action_text = "Negative / refusal statement — review exact meaning"
    elif is_exception_clause:
        speech_act = "unclassified_statement"
        action_code = "user_reviewed_action"
        action_text = "Statement includes an exception — review exact meaning"
    elif qualifier in {"may", "might", "usually", "typically", "expect", "expected", "should", "aim to", "likely", "approximately", "around"}:
        speech_act = "estimated_timeline"
    elif condition and has_promise:
        speech_act = "conditional_process_commitment"
    elif has_promise:
        speech_act = "process_commitment"
    elif duration:
        speech_act = "estimated_timeline"
    elif action_code == "review_documents":
        speech_act = "request_or_process_step"
    else:
        speech_act = "unclassified_statement"

    trigger_type = "condition_met" if condition else "unspecified"
    if re.search(r"\b(from today|from now|from the date of this call|starting today)\b", safe_text, re.I):
        trigger_type = "statement_date"

    can_confirm = bool(action_text and speech_act in {"conditional_process_commitment", "process_commitment", "estimated_timeline", "request_or_process_step"}) or is_negated_promise or is_exception_clause
    warnings = []
    if not can_confirm:
        warnings.append("No clear actionable commitment was detected. Do not save a guessed interpretation; edit the transcript or record the statement manually as a note.")
    if is_negated_promise:
        warnings.append("This wording appears to contain a refusal or negated promise. It is saved only as a manual-review statement; no positive commitment or deadline will be inferred.")
    if is_exception_clause:
        warnings.append("This wording contains an exception (for example, 'unless'). Review the exact scope before deciding whether it creates a condition, a refusal, or no commitment. No deadline is inferred while it remains unclassified.")
    if condition:
        warnings.append("The start condition is only a candidate until you confirm it. The deadline clock will not start without a recorded trigger date.")
    if day_type == "business_day":
        warnings.append("Any estimated end date will exclude weekends only. Public holidays and the organisation's own calendar are not checked.")
    if action_code == "credit_refund":
        warnings.append("This is a statement about credit, not independent proof that money arrived in your account.")

    return {
        "version": VERSION,
        "can_confirm": can_confirm,
        "source_type": source_type,
        "candidate": {
            "statement_excerpt": safe_text[:1200],
            "speech_act": speech_act,
            "action_code": action_code,
            "action_text": action_text,
            "amount_minor_units": amount_minor,
            "currency": currency,
            "condition_text": condition,
            "condition_status": "unknown" if condition else "not_applicable_or_not_detected",
            "trigger_type": trigger_type,
            "duration_value": duration,
            "duration_max_value": duration_max,
            "duration_unit": unit,
            "day_type": day_type,
            "qualifier": qualifier,
            "statement_date": "",
            "review_state": "candidate",
            "confidence_note": "Rule-based candidate only. Review the source and correct every field before saving.",
        } if can_confirm else None,
        "warnings": warnings,
        "privacy": {"raw_recording_saved": False, "raw_transcript_saved": False, "redaction_applied": True},
        "notice": "This is an extraction suggestion, not a verified company promise. No case data changed.",
    }


def add_business_days(start: date, count: int) -> date:
    """Approximate business days by excluding weekends. India holidays are not included."""
    current = start
    added = 0
    while added < count:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


def evaluate_commitment(commitment: dict[str, Any], events: list[dict[str, Any]], today: date | None = None) -> dict[str, Any]:
    """Deterministically calculate the visible state without changing source history."""
    today = today or datetime.now(ZoneInfo("Asia/Kolkata")).date()
    condition = str(commitment.get("condition_text") or "").strip()
    confirmed_triggers = [e for e in events if e.get("relation") == "triggers" and e.get("event_date_confirmed")]
    contradictions = [e for e in events if e.get("relation") == "contradicts"]
    fulfilments = [e for e in events if e.get("relation") == "fulfils"]
    qualifications = [e for e in events if e.get("relation") in {"qualifies", "supersedes"}]

    result: dict[str, Any] = {
        "status": "condition_unknown" if condition else "clock_not_established",
        "status_label": "Condition not confirmed" if condition else "Start date not established",
        "clock_status": "not_established",
        "trigger_date": None,
        "estimated_due_date": None,
        "due_date_note": "No deadline is calculated until its start event and date are established.",
        "conflict_count": len(contradictions),
        "event_count": len(events),
        "next_action": "Confirm whether the condition occurred and record the date from a source you reviewed." if condition else "Confirm the date or event that starts this stated timeframe.",
        "honesty_note": "The statement and events are user-provided or user-reviewed. Sender identity and external status are not independently verified.",
    }
    if contradictions:
        result.update({
            "status": "conflict_needs_review", "status_label": "Conflicting information to review",
            "clock_status": "conflict", "next_action": "Keep both statements, inspect their sources, and confirm which facts are correct. Do not let a newer message silently erase the earlier commitment.",
        })
        return result
    if str(commitment.get("action_code") or "") == "negative_or_refusal" or str(commitment.get("speech_act") or "") == "unclassified_statement":
        result.update({
            "status": "statement_needs_manual_review", "status_label": "Statement needs manual review",
            "clock_status": "not_applicable_or_not_established",
            "next_action": "Review the exact wording. This record may be a refusal, estimate, exception or unclear statement; do not treat it as a positive promise or calculate a deadline automatically.",
            "due_date_note": "No deadline is calculated for a statement whose meaning has not been classified confidently.",
        })
        return result
    if fulfilments:
        result.update({
            "status": "reported_fulfilment_needs_check", "status_label": "Fulfilment reported — check it",
            "clock_status": "not_applicable_or_reported_complete",
            "next_action": "Check the relevant account or official record yourself. A message claiming completion is not proof that the money arrived.",
        })
        return result
    has_qualifications = bool(qualifications)
    if has_qualifications:
        result.update({
            "status": "commitment_qualified", "status_label": "Later statement qualifies the promise",
            "next_action": "Review the original and newer statement side by side. Confirm whether the condition, timeframe, or scope changed; do not automatically overwrite the original.",
        })
    if condition and not confirmed_triggers:
        return result
    if condition and confirmed_triggers:
        trigger = sorted(confirmed_triggers, key=lambda e: str(e.get("event_date_confirmed")))[0]
        trigger_date = date.fromisoformat(str(trigger["event_date_confirmed"]))
        result["trigger_date"] = trigger_date.isoformat()
        result["clock_status"] = "running"
    elif str(commitment.get("trigger_type") or "") == "statement_date" and commitment.get("statement_date"):
        trigger_date = date.fromisoformat(str(commitment["statement_date"]))
        result["trigger_date"] = trigger_date.isoformat()
        result["clock_status"] = "running"
    else:
        return result

    try:
        duration = int(commitment.get("duration_value")) if commitment.get("duration_value") is not None else None
        duration_max = int(commitment.get("duration_max_value")) if commitment.get("duration_max_value") is not None else duration
    except (TypeError, ValueError):
        duration = duration_max = None
    unit = str(commitment.get("duration_unit") or "")
    day_type = str(commitment.get("day_type") or "unspecified")
    if duration is None or duration < 0 or not unit:
        result.update({
            "status": "triggered_duration_unclear", "status_label": "Condition met; timeframe unclear",
            "next_action": "The start event is recorded, but no reliable duration was captured. Check the exact wording and ask the organisation to confirm its timeframe.",
            "due_date_note": "No end date is calculated because the stated duration is missing or unclear.",
        })
        return result

    def due_from(start: date, count: int) -> date:
        if unit == "hour":
            # The product stores date-level evidence only; no precise hourly deadline is asserted.
            raise ValueError("hour-level deadline needs a timestamp")
        if unit == "week":
            return start + timedelta(days=count * 7)
        if day_type == "business_day":
            return add_business_days(start, count)
        return start + timedelta(days=count)

    try:
        earliest = due_from(trigger_date, duration)
        latest = due_from(trigger_date, duration_max if duration_max is not None else duration)
    except ValueError:
        result.update({
            "status": "triggered_duration_unclear", "status_label": "Condition met; exact time needs review",
            "next_action": "The trigger date is recorded, but a date-only record cannot calculate an hours-level promise precisely. Review the original statement.",
            "due_date_note": "The exact time of day and timezone are not stored, so no hourly due date is shown.",
        })
        return result

    result["estimated_due_date"] = {"earliest": earliest.isoformat(), "latest": latest.isoformat()}
    result["due_date_note"] = "Estimated from the confirmed trigger date and the reported duration. Business-day estimates exclude weekends only; holidays and company-specific rules are not checked. This is not a legal deadline."
    if today > latest:
        result.update({
            "status": "stated_period_may_have_passed", "status_label": "The stated period may have passed",
            "clock_status": "period_may_have_passed",
            "next_action": "Check the original source and whether the promised action actually occurred. If it is still outstanding, follow up through the same official channel; this estimate is not a legal deadline.",
        })
    else:
        result.update({
            "status": "clock_running", "status_label": "Stated timeframe is running",
            "clock_status": "running",
            "next_action": "Keep the source and reference with the case. Check again after the estimated period; do not treat initiation as proof that the funds were credited.",
        })
    if has_qualifications:
        result.update({
            "status": "commitment_qualified", "status_label": "Later statement qualifies the promise",
            "next_action": "Review the original and newer statement side by side. Confirm whether the condition, timeframe, or scope changed, or whether the organisation claims to replace its earlier statement. Do not automatically overwrite the original. The displayed date is only an estimate.",
        })
    return result


def source_hash(text: str) -> str:
    """Integrity bookkeeping only; a hash does not establish source authenticity."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
