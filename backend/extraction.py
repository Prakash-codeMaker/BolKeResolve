"""Conservative, reviewable extraction of case details from a user's story.

This is deliberately rules-based: it never claims that a payment was checked by a bank,
merchant, or payment network. Each extracted field includes evidence and a confidence label.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any

from backend.resolution import classify_issue

ISSUE_TYPES = {
    "Failed UPI payment",
    "UPI payment pending / recipient not credited",
    "Refund not received",
    "Merchant settlement not credited",
    "Duplicate charge",
    "Incorrect amount",
    "Order paid but not received",
    "Suspected fraud or unauthorised transaction",
    "Other payment issue",
}

# Known app/merchant names only. We don't try to infer an arbitrary business from a sentence.
# Canonical organisation names plus common Indic-script spellings produced by speech recognition.
# This is intentionally a bounded list, not free-form entity guessing.
MERCHANT_ALIASES = {
    "Google Pay": ("Google Pay", "GooglePay", "गूगल पे", "गूगलपे"),
    "PhonePe": ("PhonePe", "फोनपे", "फोन पे"),
    "Paytm": ("Paytm", "पेटीएम", "पेटियम", "पेटी एम"),
    "Amazon": ("Amazon", "अमेज़न", "अमेजन", "अमेजॉन"),
    "Flipkart": ("Flipkart", "फ्लिपकार्ट"),
    "Zomato": ("Zomato", "जोमैटो", "ज़ोमैटो", "जमैटो", "जोमाटो", "जॉमैटो"),
    "Swiggy": ("Swiggy", "स्विगी", "स्विग्गी"),
    "Uber": ("Uber", "उबर"),
    "Ola": ("Ola", "ओला"),
    "BigBasket": ("BigBasket", "बिग बास्केट", "बिगबास्केट"),
    "Myntra": ("Myntra", "मिंत्रा", "मिन्त्रा"),
    "Meesho": ("Meesho", "मीशो"),
    "IRCTC": ("IRCTC", "आईआरसीटीसी"),
    "Ajio": ("Ajio", "अजियो"),
    "Zepto": ("Zepto", "ज़ेप्टो", "जेप्टो"),
    "Blinkit": ("Blinkit", "ब्लिंकिट"),
    "JioMart": ("JioMart", "जियो मार्ट", "जियोमार्ट"),
    "MakeMyTrip": ("MakeMyTrip", "मेक माय ट्रिप"),
    "Cleartrip": ("Cleartrip", "क्लियरट्रिप"),
    "Rapido": ("Rapido", "रैपिडो"),
    "Airtel": ("Airtel", "एयरटेल"),
    "Jio": ("Jio", "जियो"),
    "CRED": ("CRED", "Cred"),
    "Razorpay": ("Razorpay", "रेज़रपे", "रेजरपे"),
    "Groww": ("Groww", "ग्रो"),
    "BookMyShow": ("BookMyShow", "बुकमायशो"),
    "Nykaa": ("Nykaa", "नायका"),
}
MERCHANTS = tuple(alias for aliases in MERCHANT_ALIASES.values() for alias in aliases)

MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9, "october": 10,
    "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
}


def _field(value: Any = None, confidence: str = "low", evidence: str = "", *, needs_confirmation: bool = False) -> dict[str, Any]:
    return {
        "value": value,
        "confidence": confidence,
        "evidence": evidence[:180],
        "needs_confirmation": needs_confirmation,
    }


def _normalise_digits(text: str) -> str:
    """Convert Unicode decimal digits (including Devanagari numerals) to ASCII."""
    return "".join(str(__import__("unicodedata").digit(ch)) if ch.isdecimal() else ch for ch in text)


def _amount_candidates(text: str) -> list[tuple[float, str]]:
    story = _normalise_digits(text)
    number = r"(\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)"
    patterns = [
        rf"(?:₹|\bINR\s*)\s*{number}",
        rf"\b{number}\s*(?:rupees?|rs\.?|inr|रुपये|रुपए|रुपया|रुपये|रु\.?)(?!\w)",
        rf"\b{number}\s+(?=(?:refund|रिफंड|रिफन्ड|debit(?:ed)?|कटे|कट गया|kat gaye|kat gaya)\b)",
    ]
    found: list[tuple[float, str]] = []
    for pattern in patterns:
        for match in re.finditer(pattern, story, flags=re.IGNORECASE):
            raw = match.group(1).replace(",", "")
            try:
                value = float(raw)
            except ValueError:
                continue
            if 0 < value <= 100_000_000:
                found.append((value, story[max(0, match.start() - 18):min(len(story), match.end() + 25)].strip()))

    # Spoken amounts are often transcribed without a currency marker, for example
    # “850 from Zomato, the refund has not arrived”. Only accept the number when
    # nearby wording explicitly ties it to a known merchant or payment/refund term.
    money_context = re.compile(
        r"(?:refund|रिफंड|रिफन्ड|रुपये|रुपए|रुपया|पैसे|रकम|amount|charged|charge|debited|debit|paid|payment|order|जोमैटो|ज़ोमैटो|जमैटो|जॉमैटो|zomato|स्विगी|swiggy|upi|कटे|कटा|कट गया|वापस|back)",
        re.IGNORECASE,
    )
    date_or_duration = re.compile(
        r"^\s*(?:days?|दिन|घंटे|hours?|minutes?|मिनट|years?|साल|महीने|months?)\b|"
        r"^\s*(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b",
        re.IGNORECASE,
    )
    already = {value for value, _ in found}
    for match in re.finditer(rf"(?<![\w/.-]){number}(?![\w/.-])", story, flags=re.IGNORECASE):
        raw = match.group(1).replace(",", "")
        try:
            value = float(raw)
        except ValueError:
            continue
        if not 0 < value <= 100_000_000 or value in already:
            continue
        after = story[match.end():match.end() + 30]
        before = story[max(0, match.start() - 30):match.start()]
        window = before + " " + after
        if date_or_duration.search(after):
            continue
        # Avoid treating the number of days waited or the year in a date as money.
        if re.search(r"(?:within|more than|over|last|past|for|since|from)\s*$", before, re.I) and re.search(r"\b(?:day|days|din|दिन|month|months|week|weeks|हफ्ते|सप्ताह)\b", after, re.I):
            continue
        if money_context.search(window):
            found.append((value, story[max(0, match.start() - 18):min(len(story), match.end() + 28)].strip()))
            already.add(value)

    # Preserve order and evidence for each distinct amount.
    distinct: dict[float, str] = {}
    for value, evidence in found:
        distinct.setdefault(value, evidence)
    return [(value, evidence) for value, evidence in distinct.items()]


def _extract_date(text: str, today: date) -> tuple[str, str, str, bool]:
    """Return ISO date, confidence, evidence and confirmation requirement."""
    # Explicit ISO, D/M/Y or D-M-Y dates.
    for match in re.finditer(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", text):
        try:
            parsed = date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            return parsed.isoformat(), "high", match.group(0), False
        except ValueError:
            continue
    for match in re.finditer(r"\b(\d{1,2})[/.\-](\d{1,2})[/.\-](20\d{2})\b", text):
        # India default: DD/MM/YYYY. The returned evidence makes this interpretable.
        try:
            parsed = date(int(match.group(3)), int(match.group(2)), int(match.group(1)))
            return parsed.isoformat(), "high", match.group(0) + " (interpreted DD/MM/YYYY)", False
        except ValueError:
            continue

    month_pattern = "|".join(sorted((re.escape(m) for m in MONTHS), key=len, reverse=True))
    patterns = [
        rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({month_pattern})(?:\s*,?\s+(20\d{{2}}))?\b",
        rf"\b({month_pattern})\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:\s*,?\s+(20\d{{2}}))?\b",
    ]
    for index, pattern in enumerate(patterns):
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        if index == 0:
            day, month_name, year_raw = match.group(1), match.group(2), match.group(3)
        else:
            month_name, day, year_raw = match.group(1), match.group(2), match.group(3)
        month = MONTHS[month_name.lower()]
        year = int(year_raw) if year_raw else today.year
        try:
            parsed = date(year, month, int(day))
        except ValueError:
            continue
        # Year omitted means a plausible year was assigned for form utility, not a verified date.
        return parsed.isoformat(), ("high" if year_raw else "medium"), match.group(0), not bool(year_raw)

    # Preserve relative wording as a hint, but do not turn it into a precise calendar date.
    relative = re.search(r"\b(today|yesterday|last\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|\d+\s+days?\s+ago|आज|कल|परसों)\b", text, re.IGNORECASE)
    if relative:
        return "", "low", relative.group(0), True
    return "", "low", "", False


def _merchant(text: str) -> tuple[str, str]:
    for canonical, aliases in sorted(MERCHANT_ALIASES.items(), key=lambda pair: max(map(len, pair[1])), reverse=True):
        for alias in sorted(aliases, key=len, reverse=True):
            # Word boundaries for Latin words; substring match for Indic script because
            # Unicode segmentation and speech-recognition spacing are inconsistent.
            pattern = rf"(?<![\w]){re.escape(alias)}(?![\w])" if alias.isascii() else re.escape(alias)
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return canonical, match.group(0)
    return "", ""


def extract_case_facts(text: str, *, today: date | None = None) -> dict[str, Any]:
    """Extract candidate fields without claiming unmentioned facts are true."""
    story = (text or "").strip()
    today = today or date.today()
    lower = story.lower()
    fields: dict[str, dict[str, Any]] = {
        "issue_type": _field("", "low"),
        "issue_family": _field("", "low"),
        "merchant": _field("", "low"),
        "amount": _field(None, "low"),
        "payment_date": _field("", "low"),
        "payment_status": _field("unknown", "low"),
        "contacted_support": _field(None, "low"),
    }
    conflicts: list[dict[str, Any]] = []
    questions: list[str] = []

    amount_candidates = _amount_candidates(story)
    if len(amount_candidates) == 1:
        amount, evidence = amount_candidates[0]
        fields["amount"] = _field(amount, "high", evidence)
    elif len(amount_candidates) > 1:
        conflicts.append({"field": "amount", "values": [amount for amount, _ in amount_candidates], "evidence": [ev for _, ev in amount_candidates], "message": "More than one amount appears in the story. Confirm which amount is disputed."})
        questions.append("You mentioned more than one amount. Which amount is the disputed payment or refund?")

    merchant, merchant_evidence = _merchant(story)
    if merchant:
        fields["merchant"] = _field(merchant, "high", merchant_evidence)

    issue, confidence, rationale = classify_issue("Other payment issue", story)
    # Catch natural conversational variants not covered by a canonical keyword phrase.
    refund_word = bool(re.search(r"refund|रिफंड|रिफन्ड|परतावा|টাকা ফেরত|પૈસા પાછા|பணம் திரும்ப|రిఫండ్|ಹಣ ಹಿಂತಿರುಗ|പണം തിരികെ|ਪੈਸੇ ਵਾਪਸ", lower))
    negative_refund_wording = bool(re.search(
        r"(?:not|no longer|never|haven't|have not|has not|did not|didn't|nahi|nahin|nhi|नॉट|नॉट गॉट|नॉट रीसिव्ड|नॉट कम|नो|नहीं|नही|नहि|नाही|नाय|आया नहीं|मिला नहीं|आया ही नहीं|मिले नहीं|नहीं आया|नहीं मिली|নেই|আসেনি|મળ્યું નથી|આવ્યા નથી|வரவில்லை|రాలేదు|ಬಂದಿಲ್ಲ|കിട്ടിയില്ല|ਨਹੀਂ ਆਇਆ|ਨਹੀਂ ਮਿਲਿਆ)",
        lower,
    ))
    refund_missing_language = (
        any(term in lower for term in (
            "have not got my refund", "haven't got my refund", "did not receive my refund",
            "didn't receive my refund", "refund back nahi mila", "refund nahi mila",
            "refund nahi aaya", "मेरा रिफंड नहीं मिला", "मेरा रिफंड नहीं आया",
            "रिफंड बैक नहीं आया", "रिफंड वापस नहीं आया", "रिफंड अभी तक नहीं आया",
            "अभी तक रिफंड नहीं मिला", "रिफंड नहीं मिला है", "पैसे वापस नहीं आए",
        ))
        or bool(re.search(r"\b(?:did not get|didn't get|have not received|haven't received|have not got|haven't got|do not get|don't get)\b.{0,70}\brefund\b", lower))
        or (refund_word and negative_refund_wording)
    )
    if refund_missing_language and issue == "Other payment issue":
        issue, confidence = "Refund not received", "medium"
    if issue in ISSUE_TYPES and issue != "Other payment issue" and confidence in {"high", "medium"}:
        # Keep the evidence field literal: show the user's words, not a generated explanation.
        fields["issue_type"] = _field(issue, confidence, story[:100])
        if issue == "Merchant settlement not credited":
            fields["issue_family"] = _field("merchant_settlement", "high", story[:100])

    status_rules = [
        ("unauthorized", ("unauthorised", "unauthorized", "not my transaction", "did not make this", "didn't make this", "मैंने नहीं किया", "அனுமதியில்லாத")),
        ("refund_pending", ("refund not received", "refund hasn't arrived", "refund has not arrived", "refund didn't come", "refund did not come", "did not get my refund", "didn't get my refund", "did not receive my refund", "refund pending", "रिफंड नॉट गॉट", "नॉट गॉट दी रिफंड", "नॉट गॉट रिफंड", "रिफंड बैक नॉट गॉट", "रिफंड नहीं आया", "रिफंड बैक नहीं आया", "रिफंड वापस नहीं आया", "रिफंड अभी तक नहीं आया", "अभी तक रिफंड नहीं मिला", "रिफंड नहीं मिला", "पैसे वापस नहीं आए", "परतावा आला नाही")),
        ("failed", ("payment failed", "transaction failed", "upi failed", "payment fail", "पेमेंट फेल", "भुगतान असफल")),
        ("pending", ("payment pending", "transaction pending", "upi pending", "recipient has not received", "not credited", "पेंडिंग", "लंबित")),
        ("successful", ("payment successful", "transaction successful", "payment went through", "paid successfully", "successful payment")),
    ]
    status_match = next(((status, term) for status, terms in status_rules for term in terms if term in lower), None)
    if not status_match and refund_word and negative_refund_wording:
        status_match = ("refund_pending", "wording indicates a refund was not received")
    if not status_match and re.search(r"\b(?:did not get|didn't get|have not received|haven't received|have not got|haven't got)\b.{0,70}\brefund\b", lower):
        status_match = ("refund_pending", "wording indicates a refund was not received")
    if status_match:
        fields["payment_status"] = _field(status_match[0], "high", status_match[1])

    support_yes = re.search(r"\b(already contacted|contacted support|contact support|called support|emailed support|raised a ticket|complained to support|support se baat|customer care ko call|tried to contact|try to contact)\b|कॉन्टैक्टेड? सपोर्ट|सपोर्ट से कॉन्टैक्ट|ट्राय टू कॉन्टैक्ट|सपोर्ट से बात|शिकायत दर्ज|कस्टमर केयर से बात|सपोर्ट को कॉल|सपोर्ट से संपर्क", lower)
    support_no = re.search(r"(?:\b(not contacted|has not been contacted|have not been contacted|haven't been contacted|haven't contacted|have not contacted|did not contact|didn't contact|not yet contacted|haven't raised a ticket|abhi tak.*(?:call|contact))\b|अभी तक.*(?:बात|शिकायत|कॉल|संपर्क).*(?:नहीं|नही)|(?:सपोर्ट|कस्टमर केयर).*(?:नहीं किया|नहीं किया है|बात नहीं|संपर्क नहीं))", lower)
    if support_no:
        fields["contacted_support"] = _field(False, "high", support_no.group(0))
    elif support_yes:
        fields["contacted_support"] = _field(True, "high", support_yes.group(0))

    iso_date, date_confidence, date_evidence, needs_date_confirmation = _extract_date(story, today)
    if iso_date:
        fields["payment_date"] = _field(iso_date, date_confidence, date_evidence, needs_confirmation=needs_date_confirmation)
    elif date_evidence:
        fields["payment_date"] = _field("", "low", date_evidence, needs_confirmation=True)
        questions.append(f"You said “{date_evidence}”. What calendar date was the payment or refund?")

    if fields["amount"]["value"] is None and not any(c["field"] == "amount" for c in conflicts):
        # No extra question if amount genuinely wasn't mentioned; the product can proceed without it.
        pass
    if fields["issue_type"]["value"] == "" and not any(q.startswith("What happened") for q in questions):
        questions.append("What went wrong: was the payment failed, the refund missing, or something else?")

    filled = [key for key, item in fields.items() if item["value"] not in (None, "", "unknown")]
    return {
        "fields": fields,
        "conflicts": conflicts,
        "clarifying_questions": questions[:2],
        "field_count": len(filled),
        "source": "rule_based_candidate_extraction",
        "notice": "These are candidates extracted from your words, not verified transaction facts. Check them before saving.",
    }
