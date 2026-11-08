"""Progressive, evidence-led case intake and resolution workflow.

The engine is intentionally conservative. It asks one route-changing question at a time,
keeps user-reported facts distinct from verified facts, and never implies that BolKeResolve
has checked a merchant/bank system or submitted a complaint.
"""
from __future__ import annotations

import re
from typing import Any

from backend.support_directory import find_support_destinations, NCH, NPCI, CYBERCRIME

ENGINE_VERSION = "adaptive-intake-2026-11-03.1"

MERCHANTS = {
    "Meesho": ("meesho", "mee shop", "meeshop", "मीशो"),
    "Flipkart": ("flipkart", "फ्लिपकार्ट"),
    "Amazon": ("amazon", "amazon.in", "अमेज़न", "अमेजन"),
    "Zomato": ("zomato", "जोमैटो", "ज़ोमैटो"),
    "Swiggy": ("swiggy", "स्विगी"),
    "Blinkit": ("blinkit", "ब्लिंकिट"),
    "Zepto": ("zepto", "ज़ेप्टो", "जेप्टो"),
    "BigBasket": ("bigbasket", "big basket"),
    "Myntra": ("myntra", "मिंत्रा"),
    "JioMart": ("jiomart", "jio mart", "जियो मार्ट"),
    "Razorpay": ("razorpay", "razor pay", "razor-pay", "रेज़रपे", "रेजरपे"),
}
PAYMENT_APPS = {
    "Google Pay": ("google pay", "googlepay", "gpay", "गूगल पे"),
    "PhonePe": ("phonepe", "phone pe", "फोनपे"),
    "Paytm": ("paytm", "पेटीएम"),
    "BHIM": ("bhim", "भीम"),
}

_NUM = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}
_SCALE = {"hundred": 100, "thousand": 1_000, "lakh": 100_000, "lac": 100_000, "million": 1_000_000}


def _word_number(words: list[str]) -> int | None:
    total = current = 0
    seen = False
    for word in words:
        if word in _NUM:
            current += _NUM[word]; seen = True
        elif word == "and":
            continue
        elif word in _SCALE:
            seen = True
            scale = _SCALE[word]
            if scale == 100:
                current = max(1, current) * scale
            else:
                total += max(1, current) * scale
                current = 0
        else:
            break
    value = total + current
    return value if seen and 0 < value <= 100_000_000 else None


def _extract_amount(text: str) -> float | None:
    numeric = re.search(r"(?:₹|\bINR\s*)\s*([\d,]+(?:\.\d{1,2})?)|\b([\d,]+(?:\.\d{1,2})?)\s*(?:rupees?|rs\.?|रुपये|रुपए|रुपया|रु\.?)(?!\w)", text, re.I)
    if numeric:
        raw = (numeric.group(1) or numeric.group(2)).replace(",", "")
        try:
            amount = float(raw)
            if 0 < amount <= 100_000_000: return amount
        except ValueError:
            pass
    # Speech transcripts often spell out amounts. Only accept a word-number phrase
    # when the nearby sentence also mentions money/payment/refund/order context.
    tokens = re.findall(r"[a-z]+", text.casefold())
    context = re.search(r"\b(refund|rupees?|rs|amount|paid|payment|charged|debit|order|money|रिफंड|पैसे|रुपये)\b", text, re.I)
    if not context: return None
    duration_words = {"day", "days", "week", "weeks", "month", "months", "hour", "hours", "year", "years"}
    money_words = {"rupee", "rupees", "rs", "refund", "payment", "paid", "order", "money", "charged", "debit", "meesho", "flipkart", "zomato", "swiggy", "blinkit", "zepto"}
    for start in range(len(tokens)):
        for end in range(min(len(tokens), start + 7), start, -1):
            value = _word_number(tokens[start:end])
            if value is None:
                continue
            following = tokens[end] if end < len(tokens) else ""
            nearby = tokens[max(0, start - 3):min(len(tokens), end + 4)]
            # Do not interpret duration words as spoken money. The immediate
            # token after a spoken number is decisive: “two days” is a timeline,
            # not a ₹2 amount, even if “refund” appears earlier in the sentence.
            if following in duration_words or (start + 1 < len(tokens) and tokens[start + 1] in duration_words):
                continue
            if any(word in money_words for word in nearby):
                return float(value)
    return None


def _first_match(text: str, mapping: dict[str, tuple[str, ...]]) -> str:
    lowered = text.casefold()
    for canonical, aliases in mapping.items():
        for alias in sorted(aliases, key=len, reverse=True):
            if re.search(r"(?<![\w])" + re.escape(alias.casefold()) + r"(?![\w])", lowered):
                return canonical
    return ""


def extract_workflow_facts(text: str, previous: dict[str, Any] | None = None, expected_field: str = "") -> dict[str, Any]:
    """Extract conservative, user-reported facts from all conversation turns."""
    text = str(text or "")
    # Realtime speech is often committed in several chunks. Join whitespace-only
    # chunk boundaries before extracting phrases so “in like\nFour days” remains
    # one semantic phrase, while punctuation still separates clauses.
    lower = re.sub(r"\s+", " ", text.casefold()).strip()
    prior = previous if isinstance(previous, dict) else {}
    merchant = _first_match(text, MERCHANTS) or prior.get("merchant", "")
    if prior.get("merchant") == "Other / unlisted platform" and not _first_match(text, MERCHANTS):
        custom_matches = list(re.finditer(r"(?:the order is from|this order is from|the app is|the store is|the merchant is|it is from|it's from)\s+([A-Za-z][A-Za-z0-9&._-]*(?:\s+[A-Za-z][A-Za-z0-9&._-]*){0,2})", text, re.I))
        for custom_match in reversed(custom_matches):
            candidate = custom_match.group(1).strip()
            if candidate.casefold() not in {"another app", "another store", "another app or", "another app or store", "an app", "a store"}:
                merchant = candidate
                break
        if merchant == "Other / unlisted platform":
            last_line = text.strip().splitlines()[-1].strip(" .,!\t") if text.strip() else ""
            generic = {"other", "another app", "another app or store", "i don't know", "not sure"}
            if last_line.casefold() not in generic and re.fullmatch(r"[A-Z][A-Za-z0-9&._-]{1,39}", last_line):
                merchant = last_line
    if not merchant and re.search(r"another app or store|another app/store|unlisted platform", lower):
        merchant = "Other / unlisted platform"
    payment_app = _first_match(text, PAYMENT_APPS) or prior.get("payment_app", "")
    amount = _extract_amount(text)
    if amount is None: amount = prior.get("amount")

    # Distinguish a merchant's gateway settlement (customer collections paid out
    # to the business bank account) from a consumer refund (money returned to a buyer).
    gateway_provider = _first_match(text, {"Razorpay": ("razorpay", "razor pay", "razor-pay", "रेज़रपे", "रेजरपे")}) or str(prior.get("gateway_provider") or "")
    has_customer_collections = bool(re.search(
        r"customers?\s+(?:have\s+)?paid\s+(?:me|us)|payments?\s+(?:that\s+)?customers?\s+(?:have\s+)?paid|customer\s+payments?", lower
    ))
    money_to_business_account = bool(re.search(
        r"(?:to|into)\s+(?:my|our|the business)\s+(?:bank\s+)?account|"
        r"(?:to|into)\s+(?:my|our)\s+bank|"
        r"(?:receive|get|credit|transfer|withdraw|extract|settle).*?(?:my|our)\s+(?:bank\s+)?account", lower
    ))
    explicit_settlement = bool(re.search(r"\bsettlements?\b|\bmerchant payout\b|\bsettlement payout\b|\bsettle(?:d|ment)?\s+(?:the\s+)?funds?\b", lower))
    gateway_withdrawal = bool(gateway_provider and re.search(
        r"(?:withdraw|extract|transfer|receive|get|credit|settle).*?(?:from|through|via)\s+razor\s*pay|"
        r"razor\s*pay.*?(?:to|into).*?(?:my|our|business)\s+(?:bank\s+)?account|"
        r"payment\s+gateway.*?(?:customer|payments?)", lower
    ))
    customer_refund_to_buyer = bool(re.search(r"refunds?\s+to\s+(?:the\s+)?customers?|refund(?:ed|ing)?\s+(?:a\s+)?customer|customer\s+(?:refund|reimbursement)", lower))
    gateway_settlement = bool(
        not customer_refund_to_buyer and (
            explicit_settlement or
            (gateway_provider and has_customer_collections and money_to_business_account) or
            (gateway_provider and gateway_withdrawal and money_to_business_account)
        )
    )

    unauthorized = bool(re.search(r"\b(fraud|scam|unauthori[sz]ed|not mine|i did not make|i didn't make|unknown transaction|not me)\b|धोखाधड़ी|फ्रॉड|अनधिकृत", lower))
    refund = bool(re.search(r"\b(refund|money back|cashback not received)\b|रिफंड|पैसे वापस", lower))
    order_not_received = bool(re.search(r"\b(not delivered|never delivered|order not received|did not receive.*order|didn't receive.*order|missing order)\b|ऑर्डर नहीं मिला|डिलीवरी नहीं हुई", lower))
    order_issue = bool(re.search(r"\b(wrong item|incorrect item|damaged|defective|missing item|incomplete order|missing product|expired item|something was wrong)\b", lower))
    issue_family = "merchant_settlement" if gateway_settlement else str(prior.get("issue_family") or "")
    issue_type = "Suspected fraud or unauthorised transaction" if unauthorized else (
        "Merchant settlement not credited" if gateway_settlement else (
            "Refund not received" if refund else (
                "Order paid but not received" if order_not_received else (
                    "Order missing, incomplete or incorrect" if order_issue else prior.get("issue_type", "")
                )
            )
        )
    )

    order_outcome = str(prior.get("order_outcome") or "")
    unavailable_to_fulfil = bool(re.search(
        r"(?:products?|items?|stock|goods?)\s+(?:were\s+)?(?:not available|unavailable|out of stock)|"
        r"(?:not available|unavailable|out of stock).*?(?:could not|couldn't|unable to|not able to)\s+(?:deliver|fulfil|fulfill|ship)|"
        r"(?:could not|couldn't|unable to|not able to)\s+(?:deliver|fulfil|fulfill|ship).*?(?:products?|items?|stock)|"
        r"merchant (?:could not|couldn't|was unable to) fulfil|order could not be fulfilled", lower))
    if re.search(r"return (?:was )?picked up|item (?:was )?collected|pickup (?:was )?completed", lower): order_outcome = "return_picked_up"
    elif unavailable_to_fulfil: order_outcome = "merchant_unable_to_fulfil"
    elif re.search(r"cancelled|canceled|order cancel", lower): order_outcome = "cancelled"
    elif order_not_received: order_outcome = "not_delivered"
    elif re.search(r"delivered|received the product|got the product", lower): order_outcome = "delivered"
    elif re.search(r"wrong item|incorrect item|damaged|defective|missing item|incomplete order|missing product|expired|something was wrong", lower): order_outcome = "delivered_with_issue"

    settlement_status = str(prior.get("settlement_status") or "")
    if gateway_settlement or prior.get("issue_family") == "merchant_settlement":
        if re.search(r"\bon[ -]?hold\b|\bheld\b|settlement is paused|settlements? (?:are|is) blocked", lower): settlement_status = "on_hold"
        elif re.search(r"\bfailed\b|\bfailure\b|rejected by (?:the )?bank", lower): settlement_status = "failed"
        elif re.search(r"\bprocessed\b|successfully credited|credited to (?:my|our) bank", lower): settlement_status = "processed"
        elif re.search(r"\binitiated\b|\bin process\b|\bprocessing\b", lower): settlement_status = "initiated"
        elif re.search(r"\bcreated\b|settlement created", lower): settlement_status = "created"
        elif re.search(r"no settlement (?:entry|record|shown)|settlement (?:is )?not listed|cannot see (?:a )?settlement", lower): settlement_status = "no_record"

    refund_status = str(prior.get("refund_status") or "")
    # A merchant's promise to issue a refund is evidence that the refund is pending,
    # even when the transcript does not use the word "processing".
    promised_refund_statement = bool(re.search(
        r"(?:told|said|promised|assured).*?(?:refund|money back|amount back|pay back)|"
        r"(?:refund|money back|amount back).*?(?:will be|would be|to be)\s+(?:given|sent|credited|refunded|processed)|"
        r"(?:give|send|credit|refund) (?:the )?(?:refund|money|amount) back", lower))
    if re.search(r"\bnot initiated\b|\bnot started\b|not processed", lower): refund_status = "not_initiated"
    elif re.search(r"\brefund initiated\b|\brefund processed\b", lower): refund_status = "initiated"
    elif re.search(r"\brefund pending\b|\bprocessing refund\b", lower): refund_status = "pending"
    if re.search(r"refund (?:was )?not initiated|refund has not been initiated|refund has not initiated|refund hasn't been initiated|not started|refund hasn't started|refund has not started|not processed|अभी तक.*रिफंड.*शुरू नहीं", lower): refund_status = "not_initiated"
    elif re.search(r"refund (?:has been )?(?:initiated|processed|completed)|refund reference|arn\b|refund id", lower): refund_status = "initiated"
    elif promised_refund_statement or re.search(r"refund (?:is )?(?:still )?(?:pending|processing|in process|in progress|under process)|processing (?:the )?refund|process(?:ing)? the refund|refund (?:is )?being processed|procedure to (?:give|process) (?:the )?refund|refund.*(?:in process|in progress|under process)|रिफंड.*(?:प्रोसेस|प्रक्रिया में)", lower): refund_status = "pending"
    # A user's report that money has not arrived does not tell us whether the
    # merchant initiated a refund; leave the status unknown so we ask explicitly.

    support_contacted = prior.get("support_contacted")
    if re.search(r"\b(no|not|never)\s+(?:contacted|raised|reached out)|haven't contacted|have not contacted|did not contact|not yet contacted|अभी तक संपर्क नहीं", lower): support_contacted = False
    elif re.search(r"\b(already contacted|contacted (?:them|support|their support|the support|merchant support|the merchant|the company)|reached out to (?:them|support|the merchant|the company|(?:their |the )?support(?: team)?)|messaged (?:them|support|the merchant)|emailed (?:them|support|the merchant)|spoke to (?:them|support|the merchant)|talked to (?:them|support|the merchant)|chatted with (?:them|support)|raised a complaint|raised a ticket|spoke to (?:their |the )?support|emailed support|chatted with support|complained earlier|support (?:told|said|replied)|support.*no response|no response from support)\b|सपोर्ट से बात", lower): support_contacted = True

    refund_scope = str(prior.get("refund_scope") or "")
    # Users commonly answer this question colloquially, including code-mixed
    # speech transcripts such as “whole order ma'am” or “poora order”. Treat
    # these as equivalent to the option label “entire order” so the workflow
    # cannot trap the user on the same question.
    full_scope_patterns = (
        r"\b(full order|whole order|entire order|all items|all products|complete order|whole thing|all of it)\b",
        r"\b(poora order|pura order|saara order|saare products|sabhi products)\b",
        r"पूरे ऑर्डर|पूरा ऑर्डर|सारा ऑर्डर|सभी सामान",
    )
    partial_scope_patterns = (
        r"\b(some items|selected items|selected products|partial refund|one item|only one product|part of the order|few items)\b",
        r"कुछ सामान|कुछ आइटम|चुने हुए प्रोडक्ट",
    )
    if any(re.search(pattern, lower, re.I) for pattern in full_scope_patterns): refund_scope = "full_order"
    elif any(re.search(pattern, lower, re.I) for pattern in partial_scope_patterns): refund_scope = "some_items"
    elif expected_field == "refund_scope":
        # Short spoken answers often omit the noun (“all of it”, “full”, etc.).
        if re.fullmatch(r"\s*(full|whole|entire|all|all of it|the whole thing|poora|pura|saara|sab)\s*(order|refund|it|thing|ma'?am|sir)?[.! ]*", lower):
            refund_scope = "full_order"
        elif re.fullmatch(r"\s*(some|partial|selected|few|only some)\s*(items|products|item|product)?[.! ]*", lower):
            refund_scope = "some_items"
    elif re.search(r"\bnot sure\b|don't know", lower) and "refund" in lower: refund_scope = refund_scope or "unknown"
    item_count = prior.get("item_count")
    item_match = re.search(r"\b(\d{1,2})\s+(?:items?|products?|pieces?)\b", lower)
    item_word_match = re.search(r"\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:items?|products?|pieces?)\b", lower)
    if item_match: item_count = int(item_match.group(1))
    elif item_word_match: item_count = _word_number([item_word_match.group(1)])
    elif expected_field == "item_count":
        last_line = text.strip().splitlines()[-1].strip() if text.strip() else ""
        if re.fullmatch(r"\d{1,2}", last_line): item_count = int(last_line)
        elif last_line.casefold() in {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"}: item_count = _NUM[last_line.casefold()]
    refund_reason = str(prior.get("refund_reason") or "")
    if re.search(r"return (?:was )?rejected|refund rejected|not eligible|seller rejected", lower): refund_reason = "rejected_or_not_eligible"
    elif re.search(r"pickup pending|inspection pending|return pickup.*pending", lower): refund_reason = "pickup_or_inspection_pending"
    elif re.search(r"no reason (?:was )?shown|app (?:gave|shows) no reason", lower): refund_reason = "no_reason_shown"
    elif expected_field == "refund_reason":
        last_line = text.strip().splitlines()[-1].strip() if text.strip() else ""
        if len(last_line) >= 3: refund_reason = "user_described_reason: " + last_line[:180]

    support_reference = prior.get("support_reference", "")
    if re.search(r"\b(no|not|without)\s+(?:ticket|case|complaint|reference)\s*(?:number|id|no\.?|#)?\b", lower):
        support_reference = ""
    else:
        ref = re.search(r"\b(?:ticket|case|complaint|reference|ref)\s*(?:number|id|no\.?|#)?\s*[:#-]?\s*([A-Z0-9-]{4,})\b", text, re.I)
        if ref: support_reference = ref.group(1)
        elif prior.get("support_reference") == "reference_claimed":
            last_line = text.strip().splitlines()[-1].strip() if text.strip() else ""
            standalone = re.fullmatch(r"[A-Z0-9][A-Z0-9-]{3,}", last_line, re.I)
            if standalone: support_reference = standalone.group(0)
        elif re.search(r"i have a support ticket|i have a ticket|i have a support reference", lower): support_reference = "reference_claimed"
        elif re.search(r"received a reply but no ticket|reply but no reference", lower): support_reference = "reply_no_ref"

    settlement_reference = str(prior.get("settlement_reference") or "")
    settlement_ref_match = re.search(r"\b(?:settlement\s*(?:id|reference|ref)?|\bUTR)\s*[:#-]?\s*([A-Z0-9_-]{5,})\b", text, re.I)
    if settlement_ref_match:
        settlement_reference = settlement_ref_match.group(1)

    payment_method = str(prior.get("payment_method") or "")
    for method, pattern in (("UPI", r"\bupi\b|यूपीआई"), ("card", r"\b(?:credit|debit) card\b|कार्ड"), ("netbanking", r"net banking|internet banking"), ("wallet", r"wallet|वॉलेट"), ("cash_on_delivery", r"cash on delivery|\bcod\b")):
        if re.search(pattern, lower): payment_method = method; break
    transaction_status = str(prior.get("transaction_status") or "")
    transaction_context = bool(payment_app or re.search(r"\b(upi|transaction|payment transfer|bank transfer|debited|deducted|recipient|beneficiary)\b|यूपीआई|लेन-देन", lower))
    if transaction_context:
        if re.search(r"\b(successful|success|completed|paid successfully)\b", lower): transaction_status = "success"
        elif re.search(r"\b(pending|processing)\b", lower): transaction_status = "pending"
        elif re.search(r"\b(failed|failure|declined)\b", lower): transaction_status = "failed"
        elif re.search(r"debited.*not credited|money deducted.*not received|recipient not credited", lower): transaction_status = "debit_no_credit"

    elapsed = str(prior.get("elapsed") or "")
    elapsed_days = prior.get("elapsed_days")
    promised = str(prior.get("promised_timeline") or "")
    promised_days = prior.get("promised_days")

    # Identify elapsed time only when the wording says the period has already
    # passed. This prevents "they promised it in two days" becoming elapsed=2.
    elapsed_patterns = (
        r"(?:more than|over|past|above)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(working\s+)?(days?|weeks?|months?)",
        r"(?:it has been|it's been|its been|has been|have been|for)\s+(?:more than\s+)?(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(working\s+)?(days?|weeks?|months?)",
        r"(?:already|now)\s+(?:over|more than)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(working\s+)?(days?|weeks?|months?)",
    )
    elapsed_match = next((re.search(pattern, lower) for pattern in elapsed_patterns if re.search(pattern, lower)), None)
    def _duration_value(raw: str, unit: str) -> int | None:
        number = int(raw) if raw.isdigit() else _word_number([raw])
        if number is None:
            return None
        multiplier = 7 if unit.startswith("week") else (30 if unit.startswith("month") else 1)
        return number * multiplier
    if elapsed_match:
        raw, working, unit = elapsed_match.groups()
        elapsed_days = _duration_value(raw, unit)
        display_unit = unit if raw == "1" or raw == "one" else (unit if unit.endswith("s") else unit + "s")
        elapsed = f"more than {raw} {('working ' if working else '')}{display_unit}" if re.search(r"more than|over|past|above", elapsed_match.group(0)) else f"{raw} {('working ' if working else '')}{display_unit}"
    else:
        # Preserve order age phrases for case context, but do not treat them as
        # elapsed refund-credit time. “I ordered three weeks ago” does not prove
        # the refund has been pending for three weeks.
        ago_match = re.search(
            r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(days?|weeks?|months?)\s+ago\b",
            lower,
        )
        if ago_match:
            raw, unit = ago_match.groups()
            display_unit = unit if raw == "1" or raw == "one" else (unit if unit.endswith("s") else unit + "s")
            elapsed = f"{raw} {display_unit}"
            elapsed_days = None
        elif re.search(r"\byesterday\b", lower):
            elapsed, elapsed_days = "1 day", 1
        elif re.search(r"\btoday\b", lower):
            elapsed = "today"

    # Parse the promised deadline only inside the same clause as the promise.
    # Split on sentence boundaries and contrast markers so “they promised two
    # days, but it has been six days” cannot turn the elapsed six days into the
    # promised deadline.
    number_word = r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty)"
    promise_match = None
    promise_clause_pattern = re.compile(
        rf"(?:told|said|promised|assured|showed|informed).*?(?:refund|money|amount).*?\b(?:within|in|after)(?:\s+like)?\s+{number_word}\s*(working\s+)?(days?|weeks?)\b",
        re.I,
    )
    for clause in re.split(r"[.!?;\n]+|\bbut\b|\bhowever\b|\balthough\b", lower):
        found = promise_clause_pattern.search(clause)
        if found:
            promise_match = found
            break
    # Also accept the common order “refund in two days, support told me”.
    if not promise_match:
        for clause in re.split(r"[.!?;\n]+|\bbut\b|\bhowever\b|\balthough\b", lower):
            found = re.search(rf"(?:refund|money|amount).*?\b(?:within|in|after)(?:\s+like)?\s+{number_word}\s*(working\s+)?(days?|weeks?)\b", clause, re.I)
            if found and re.search(r"\b(told|said|promised|assured|support|app|merchant|refund)\b", clause):
                promise_match = found
                break
            # A short follow-up answer such as “the app said seven working days”
            # is valid timeline evidence even when it omits the word refund.
            found = re.search(rf"\b(?:app|support|they|merchant)\b.*?\b(?:said|told|promised|showed|assured|informed)\b.*?{number_word}\s*(working\s+)?(days?|weeks?)\b", clause, re.I)
            if found:
                promise_match = found
                break
    if promise_match:
        raw = promise_match.group(1)
        working = promise_match.group(2)
        unit = promise_match.group(3)
        promised_days = _duration_value(raw, unit)
        display_unit = unit if raw == "1" or raw == "one" else (unit if unit.endswith("s") else unit + "s")
        promised = f"{raw} {('working ' if working else '')}{display_unit}"
    elif prior.get("promised_timeline") == "given_details_needed":
        exact_timeline = re.search(r"\b(\d{1,3})\s*(working\s+)?(days?|weeks?)\b", lower)
        exact_date = re.search(r"\b(\d{1,2}[-/ ](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*[-/ ]\d{2,4}|\d{4}-\d{2}-\d{2})\b", text, re.I)
        if exact_timeline:
            raw, working, unit = exact_timeline.groups()
            display_unit = unit if raw == "1" else (unit if unit.endswith("s") else unit + "s")
            promised = f"{raw} {('working ' if working else '')}{display_unit}"
            promised_days = _duration_value(raw, unit)
        elif exact_date:
            promised = exact_date.group(1)
    if re.search(r"\bnot given\b|no date|no timeline", lower):
        promised, promised_days = "not_given", None
    elif re.search(r"\bnot sure\b|don't know|do not know", lower):
        promised, promised_days = "not_sure", None
    elif re.search(r"\b(given|shown)\b", lower) and not promised:
        promised = "given_details_needed"

    if re.search(r"\b(no reply|no response|no reference yet|not (?:got|get|received) (?:a |any )?(?:reply|response)|haven't (?:heard|got|received) (?:anything )?back|hasn't replied|not heard back|no one (?:replied|responded))\b", lower):
        support_reference = "no_response_or_reference"

    return {
        "merchant": merchant, "gateway_provider": gateway_provider, "payment_app": payment_app, "amount": amount,
        "issue_family": issue_family, "gateway_settlement": gateway_settlement, "settlement_status": settlement_status,
        "settlement_reference": settlement_reference, "issue_type": issue_type, "unauthorized": unauthorized,
        "order_outcome": order_outcome, "refund_status": refund_status,
        "support_contacted": support_contacted, "support_reference": support_reference,
        "payment_method": payment_method, "transaction_status": transaction_status, "elapsed": elapsed,
        "promised_timeline": promised, "promised_days": promised_days, "elapsed_days": elapsed_days,
        "refund_scope": refund_scope, "item_count": item_count, "refund_reason": refund_reason,
    }


def _question(field: str, prompt: str, options: list[tuple[str, str]], why: str) -> dict[str, Any]:
    return {"field": field, "prompt": prompt, "options": [{"value": v, "label": label} for v, label in options], "why_it_matters": why}


def build_adaptive_workflow(story: str, *, previous: dict[str, Any] | None = None,
                            intake_complete: bool = False, evidence_count: int = 0,
                            semantic_facts: dict[str, Any] | None = None,
                            semantic_analysis: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a single-next-question workflow from the current case narrative."""
    prior = previous if isinstance(previous, dict) else {}
    previous_facts = dict(prior.get("facts", {})) if isinstance(prior.get("facts"), dict) else {}
    expected_field = str((prior.get("next_question") or {}).get("field", "")) if isinstance(prior.get("next_question"), dict) else ""
    facts = extract_workflow_facts(story, previous_facts, expected_field)
    if isinstance(semantic_facts, dict):
        # The caller has already validated each AI candidate against an exact quote
        # in the latest user turn. Semantic facts complement, rather than replace,
        # deterministic extraction and retained prior facts.
        facts.update(semantic_facts)
        # Deterministic merchant-settlement evidence has precedence over a broad
        # semantic label triggered by the word "refund" in a disfluent transcript.
        if facts.get("gateway_settlement"):
            facts["issue_family"] = "merchant_settlement"
            facts["issue_type"] = "Merchant settlement not credited"
    analysis = semantic_analysis if isinstance(semantic_analysis, dict) else {}
    base = {
        "engine_version": ENGINE_VERSION,
        "intake_complete": bool(intake_complete or prior.get("intake_complete")),
        "collecting_update": bool(prior.get("collecting_update")),
        "facts": facts,
        "evidence_count": int(evidence_count or 0),
        "support_destinations": [],
        "evidence_request": None,
        "next_question": None,
        "current_step": None,
        "support_draft": None,
        "status": "collecting_story",
        "semantic_interpretation": {
            "enabled": bool(analysis),
            "intent": str(analysis.get("intent") or "")[:40],
            "summary": str(analysis.get("summary") or "")[:500],
            "applied_fact_count": int(len((analysis.get("applied_fact_updates") or []))),
            "different_issue": bool(analysis.get("different_issue")),
        } if analysis else {"enabled": False, "intent": "", "summary": "", "applied_fact_count": 0, "different_issue": False},
    }

    if not base["intake_complete"] or base["collecting_update"]:
        is_update = bool(base["collecting_update"])
        base.update({
            "title": "Add an update to your case" if is_update else "Tell us what happened",
            "reason": "Your new information is saved alongside the existing case. Explain the whole update before asking for a revised action." if is_update else "Your story is saved. Continue speaking or typing until you have explained the issue. No resolution plan is generated before you finish.",
            "message": "I've saved this update. Tell me what the merchant or bank replied, what changed, or what happened next. When you are finished, choose ‘Finish update’ and I'll recalculate the next action from the full case history." if is_update else "I've saved that. Keep telling me what happened, in your own words. When you're finished, choose ‘Finish explaining’ and I'll work out the next step from the full story.",
            "stage": "update" if is_update else "story",
            "status": "collecting_update" if is_update else "collecting_story",
        })
        return base

    issue = facts["issue_type"]
    merchant = facts["merchant"]
    payment_app = facts["payment_app"]

    # Immediate safety path must never be delayed by ordinary intake.
    if facts["unauthorized"]:
        base.update({
            "status": "action", "stage": "urgent_safety", "title": "Secure the account and report the unauthorised transaction",
            "reason": "You reported a transaction you did not authorise. Do not wait for the merchant's ordinary refund process.",
            "current_step": {"title": "Contact your bank/payment provider immediately", "detail": "Use the number or in-app route printed on the bank/payment provider's official website or app. Ask them to block further unauthorised activity, raise a dispute and record the complaint reference.", "why": "Your bank/payment provider can take account-protection steps that BolKeResolve cannot take."},
            "support_destinations": [CYBERCRIME],
            "evidence_request": {"title": "Save the transaction record", "detail": "Keep the bank/app transaction entry and complaint acknowledgement. Do not upload or share OTPs, PINs, passwords, CVV or full account/card numbers."},
            "message": "Because you reported a payment you did not authorise, contact your bank/payment provider immediately. Do not share an OTP, UPI PIN, password or remote-access code with anyone. In India, report suspected financial cyber fraud through 1930 / the official cybercrime portal as well.",
        })
        return base

    semantic_family = str(facts.get("issue_family") or "")
    # A newly interpreted issue family overrides stale keywords in older turns.
    # Without this precedence, an old word like "refund" could trap a later UPI or
    # subscription issue in the refund playbook forever.
    is_refund = semantic_family == "refund" or (not semantic_family and (issue == "Refund not received" or "refund" in story.casefold()))
    is_upi = semantic_family == "payment_transaction" or (bool(payment_app or facts["payment_method"] == "UPI" or re.search(r"\bupi\b|यूपीआई", story, re.I)) and not is_refund)
    is_gateway_settlement = semantic_family == "merchant_settlement" or facts.get("issue_family") == "merchant_settlement" or bool(facts.get("gateway_settlement"))

    if is_gateway_settlement:
        provider = facts.get("gateway_provider") or merchant or "the payment gateway"
        amount_text = f"₹{facts['amount']:,.2f}".rstrip("0").rstrip(".") if facts.get("amount") is not None else "the unsettled amount"
        promised_text = facts.get("promised_timeline") or (f"{facts.get('promised_days')} days" if facts.get("promised_days") else "the timeline you were given")
        elapsed_text = facts.get("elapsed") or (f"{facts.get('elapsed_days')} days" if facts.get("elapsed_days") else "the time you reported")
        route_list = find_support_destinations(provider, story, "merchant settlement")
        settlement_status = facts.get("settlement_status") or ""
        if not settlement_status:
            q = _question(
                "settlement_status",
                f"In your {provider} Dashboard, open Transactions → Payments, select an affected Payment ID and open its settlement_id (or use the Settlements view). What status is shown?",
                [("created", "Created"), ("initiated", "Initiated / Processing"), ("processed", "Processed"), ("failed", "Failed"), ("on_hold", "On hold / Blocked"), ("no_record", "No settlement entry visible")],
                "The Dashboard status separates a settlement still being processed from one that failed, was placed on hold, or was marked processed. The settlement ID and UTR are the references needed to trace it."
            )
            base.update({"status": "question", "stage": "gateway_settlement_intake", "title": f"Let's trace your {provider} settlement", "reason": f"This sounds like customer payments collected through {provider} that have not reached your business bank account. That is a merchant settlement issue, not a customer refund or ecommerce order. You reported {amount_text} and that the promised time was {promised_text}, with {elapsed_text} passed.", "next_question": q, "support_destinations": route_list[:1], "evidence_request": {"title": "Keep the settlement proof ready", "detail": "You can add the relevant settlement details screen or settlement report. Hide full bank-account numbers, credentials, API keys, OTPs and unrelated customer data."}, "message": q["prompt"]})
            return base
        if settlement_status == "processed":
            base.update({"status": "action", "stage": "gateway_settlement_processed_trace", "title": f"Trace the {provider} settlement marked processed", "reason": f"You reported that {provider} marks this settlement as processed. That status is not the same as BolKeResolve independently confirming a bank credit. The next useful identifier is the bank UTR.", "current_step": {"title": "Find the UTR for this settlement and trace it with your bank", "detail": "In the Dashboard, open Transactions → Payments, select an affected Payment ID and open its settlement_id (or open that entry from Settlements). If the UTR is available, compare it with your bank statement and ask your bank to trace that UTR. If the UTR is missing or the bank cannot trace it, raise a Razorpay support ticket and include the settlement ID and dates. Do not share full bank details or credentials in this case.", "why": "Razorpay's settlement documentation says the UTR is the bank-traceable reference for a settlement."}, "support_destinations": route_list[:1], "evidence_request": {"title": "Add these settlement records", "detail": "1. Settlement detail showing status and settlement ID. 2. UTR, if displayed. 3. A redacted bank statement section for the relevant date showing whether the credit arrived. Mask account number and unrelated transactions."}, "support_draft": {"subject": f"Settlement marked processed but not credited — {amount_text}", "message": f"Hello {provider} Support,\n\nMy merchant settlement of {amount_text} is marked as processed in the Dashboard, but I cannot identify the corresponding credit in my bank account. Please confirm the UTR, settlement date, destination bank account (masked), and whether the settlement was returned or rejected by the bank.\n\nSettlement ID: [Settlement ID]\nUTR: [UTR, if shown]\nRelevant date: [Date]\n\nThank you.", "notice": "Draft only. Review and submit through the official Razorpay support route. BolKeResolve has not contacted Razorpay."}, "message": "The dashboard says this settlement was processed. Find its UTR in the settlement details/report, compare it with your bank statement, and ask your bank to trace that UTR. If the reference is missing or cannot be traced, raise a Razorpay support ticket with the settlement ID."})
            return base
        if settlement_status == "failed":
            base.update({"status": "action", "stage": "gateway_settlement_failed", "title": f"Resolve the failed {provider} settlement", "reason": "You reported that the settlement is marked failed. The failure reason—not the original customer payment—is now the key detail.", "current_step": {"title": "Open the failed settlement and check the registered email", "detail": "Open the failed settlement details in your Dashboard. Check the registered email for Razorpay's failure notice and requested information. Razorpay documentation lists inactive/frozen bank accounts, incorrect bank details and bank rejection among possible causes. Do not change bank details based on an unsolicited message; use the signed-in Dashboard and official support route.", "why": "The failure reason determines whether the bank account, bank rejection or a provider-side review needs attention."}, "support_destinations": route_list[:1], "evidence_request": {"title": "Attach the failed-settlement proof", "detail": "Add the settlement detail showing Failed and the Razorpay email/notice explaining the reason. Redact full bank-account numbers, IFSC where unnecessary, customer information and all credentials."}, "message": "Open the failed settlement in your Razorpay Dashboard and read the failure reason. Check the registered email for a Razorpay notice. If the reason is unclear or no email arrived, raise a support ticket using the official support route and include the settlement ID."})
            return base
        if settlement_status == "on_hold":
            base.update({"status": "action", "stage": "gateway_settlement_on_hold", "title": f"Resolve the {provider} settlement hold", "reason": "You reported that settlements are on hold. This needs the Dashboard's hold notification or requested action, not an order-refund workflow.", "current_step": {"title": "Open the Dashboard hold notification and review the requested action", "detail": "On the Dashboard Home page, look for the settlement-on-hold notification and its Resolve action. Review the reason and any requested documents. Use the signed-in Dashboard or official support route; do not send KYC documents, passwords, API secrets or bank credentials through an unsolicited contact.", "why": "Razorpay's documentation says held settlements can require a Resolve action from the Dashboard and contact with support."}, "support_destinations": route_list[:1], "evidence_request": {"title": "Save the hold notification", "detail": "Add the redacted Dashboard notification showing the hold reason and any document request. Do not upload API keys, passwords, OTPs or full account details."}, "message": "Open the Razorpay Dashboard Home page and inspect the settlement hold notification. Use its Resolve action if shown, then follow the requested steps through the signed-in Dashboard. Keep the notification and ticket reference in this case."})
            return base
        if settlement_status == "no_record":
            q = _question("settlement_payments_captured", "In Transactions → Payments, are the customer payments marked Captured?", [("yes", "Yes, Captured"), ("no", "No / failed / authorised only"), ("unsure", "I am not sure")], "Razorpay settlement is based on captured payments; this distinguishes a settlement delay from payments that have not entered the settlement flow.")
            base.update({"status": "question", "stage": "gateway_settlement_no_record", "title": "Check whether the customer payments entered settlement", "reason": "No settlement entry is visible, so we should first confirm whether those payments were captured.", "next_question": q, "support_destinations": route_list[:1], "evidence_request": {"title": "Add a transaction details screen", "detail": "Choose one representative payment, show its Payment ID and status, and redact customer names, phone numbers and sensitive information."}, "message": q["prompt"]})
            return base
        # Created / Initiated / pending: compare the reported account promise to elapsed time.
        if facts.get("promised_days") is not None and facts.get("elapsed_days") is not None and facts["elapsed_days"] > facts["promised_days"]:
            base.update({"status": "action", "stage": "gateway_settlement_overdue", "title": f"Follow up on your overdue {provider} settlement", "reason": f"You reported {amount_text} awaiting settlement. The stated promise was {promised_text}; you report {elapsed_text} has passed. This is based on your account and has not been checked against Razorpay's live systems. Bank holidays and your account's configured cycle can affect working-day timing.", "current_step": {"title": "Trace the settlement ID and expected bank-credit date", "detail": "In your Dashboard, open Settlements and select the relevant settlement. Check the status, settlement ID, scheduled date and expected credit date. Compare the promise with business days and your account's configured settlement cycle. If it is past the displayed date, raise a ticket through Razorpay Support and include the settlement ID, affected amount, last captured payment date and any prior ticket reference.", "why": "Razorpay's dashboard exposes the settlement status and schedule; the exact account's configured cycle and any risk/bank review matter more than a generic timeline."}, "support_destinations": route_list[:1], "evidence_request": {"title": "Attach the settlement details", "detail": "1. Settlement screen with status, settlement ID and scheduled date. 2. Payment/settlement report for the affected amount. 3. The Razorpay message promising a four-day timeline, if available. Redact full account details, customer personal data, passwords, API keys and OTPs."}, "support_draft": {"subject": f"Overdue merchant settlement — {amount_text}", "message": f"Hello Razorpay Support,\n\nI am following up on merchant settlements totalling {amount_text} that have not reached my registered bank account. I was informed that the amount would be settled within {promised_text}; I report that {elapsed_text} has passed.\n\nPlease confirm the settlement ID(s), current processing status, scheduled/processed date, UTR if generated, and any hold, bank rejection or document requirement. Please link this request to my earlier support contact if one exists.\n\nI can provide the relevant redacted settlement and payment reports through the official Dashboard/support channel.\n\nThank you.", "notice": "Draft only. Review and submit it yourself through Razorpay's official support route."}, "message": f"This is a merchant-settlement follow-up, not a customer refund. Your reported {amount_text} is beyond the {promised_text} promise ({elapsed_text} elapsed). Open the same settlement in the Razorpay Dashboard, confirm its scheduled date and settlement ID, then raise a support ticket with the settlement report and prior ticket reference."})
            return base
        q = _question("settlement_expected_date", "What expected settlement date or business-day schedule does the Dashboard show?", [("shown_date", "A date is shown"), ("no_date", "No date is shown"), ("unsure", "I cannot find it")], "Your account's configured settlement cycle and bank working days determine whether the current status is actually overdue.")
        base.update({"status": "question", "stage": "gateway_settlement_timeline", "title": "Check the settlement schedule", "reason": "The settlement is reported as created or initiated. Compare the exact dashboard date with business days and the cycle configured for your account.", "next_question": q, "support_destinations": route_list[:1], "evidence_request": {"title": "Add the settlement schedule", "detail": "A screenshot of the settlement detail showing status and scheduled date is enough. Mask your full bank account and all customer details."}, "message": q["prompt"]})
        return base

    if is_refund:
        # Ask only the first unanswered fact that changes the refund route.
        if not facts["merchant"]:
            q = _question("merchant", "Which app or store is this order from?", [("Meesho", "Meesho"), ("Flipkart", "Flipkart"), ("Zomato", "Zomato"), ("Other", "Another app / store")], "The support route and refund rules depend on the organisation that accepted the order.")
        elif merchant == "Other / unlisted platform":
            q = _question("merchant_name", "Please type the exact name of the app or store so I can use the correct support route.", [("type_name", "I'll type the app name below")], "I won't invent a support link or contact detail for an organisation I cannot identify.")
        elif facts.get("support_contacted") and facts.get("support_reference") in {"no_response_or_reference", "reply_no_ref"}:
            route_list = find_support_destinations(merchant)
            route = route_list[0] if route_list else None
            amount_text = f"₹{facts['amount']:,.0f}" if facts.get("amount") is not None else "the refund amount"
            base.update({
                "status": "action", "stage": "existing_support_no_response",
                "title": f"Follow up on your existing {merchant} support request",
                "reason": f"You told us that you already contacted {merchant}, but have not received a useful reply. Do not start a duplicate complaint yet. Continue from the same order and earlier support conversation so the merchant can trace the request.",
                "current_step": {
                    "title": "Continue the existing order-specific support conversation",
                    "detail": (route.get("action") if route else f"Open {merchant}'s official app, select this order and use its Help/Support option.") + " Continue the same existing support conversation and refer to the earlier contact. Ask them to confirm the complaint/ticket reference, whether the refund has been initiated, the initiation date, any refund reference and the exact expected credit date. If the earlier chat is no longer visible, ask support to locate it using the order ID and contact details already on the account.",
                    "why": "A traceable complaint reference and written status let you follow up without opening duplicate tickets."
                },
                "support_destinations": route_list[:1],
                "evidence_request": {"title": "Add proof of the earlier contact", "detail": "Upload one screenshot of the previous support chat, email or call acknowledgement. If you cannot find it, add the order cancellation/refund status screenshot instead. Hide OTPs, PINs, passwords and unrelated personal information."},
                "support_draft": {
                    "subject": f"Follow-up on earlier refund request — {merchant} order [Order ID]",
                    "message": f"Hello {merchant} Support,\n\nI am following up on my earlier contact about order [Order ID] and the refund of {amount_text}. I have already contacted support but have not received a reply/update yet.\n\nPlease locate my earlier request and share the complaint/ticket reference. Also confirm whether the refund has been approved and initiated, the initiation date, the refund reference/ARN if generated, and the expected credit date. Please keep this linked to the earlier conversation rather than creating a duplicate ticket.\n\nThank you.",
                    "notice": f"Draft only. Review and send it yourself through {merchant}'s official support route. BolKeResolve has not contacted the merchant."
                },
                "message": f"You have already contacted {merchant}, but you have not received a reply. Continue the same order-specific support conversation; do not open a duplicate ticket yet. Ask for the complaint reference and written refund status. Add a screenshot of the earlier chat or email so this case keeps a record."
            })
            return base
        elif (facts.get("refund_status") in {"pending", "initiated"}
              and facts.get("promised_days") is not None
              and facts.get("elapsed_days") is not None
              and facts["elapsed_days"] > facts["promised_days"]):
            # A clearly overdue merchant promise is actionable. Do not force the
            # user through order-scope questions before explaining the follow-up.
            route_list = find_support_destinations(merchant)
            route = route_list[0] if route_list else None
            amount_text = f"₹{facts['amount']:,.0f}" if facts.get("amount") is not None else "the refund amount"
            promise_text = facts.get("promised_timeline") or f"{facts['promised_days']} days"
            elapsed_text = facts.get("elapsed") or f"more than {facts['elapsed_days']} days"
            order_context = "The merchant could not fulfil the order because products were unavailable. " if facts.get("order_outcome") == "merchant_unable_to_fulfil" else ""
            action_detail = (route.get("action") if route else "Open the order in the official merchant app or website and use its order-specific Help/Support option.")
            base.update({
                "status": "action", "stage": "overdue_refund_promise", "title": f"Your {merchant} refund promise is overdue",
                "reason": f"{order_context}You reported a {amount_text} refund promise of {promise_text}, and {elapsed_text} have passed. The reported waiting period is longer than the promise, so a written follow-up is reasonable now. This is based on your account; BolKeResolve has not checked the merchant's systems.",
                "current_step": {"title": "Follow up on the existing refund promise", "detail": action_detail + " Open the exact order and continue in the same support conversation/ticket if one exists. Ask them to confirm (1) whether the cancellation/refund is approved, (2) the date and payment method to which it was initiated, (3) the refund reference/ARN if generated, and (4) the exact expected credit date. Do not create duplicate tickets if the existing one is active.", "why": "The promise has passed according to the dates you reported. The merchant needs to confirm whether the refund was actually initiated and provide a traceable reference."},
                "support_destinations": route_list[:1],
                "evidence_request": {"title": "Attach these three proofs", "detail": "1. The order page showing cancellation or unavailable products. 2. The message/screen where the two-day refund promise was shown. 3. The original payment entry for the reported amount. Hide full card/account numbers, CVV, UPI PIN, OTPs and unrelated personal data."},
                "support_draft": {"subject": f"Overdue refund follow-up — {merchant} order [Order ID]", "message": f"Hello {merchant} Support,\n\nMy order [Order ID] could not be fulfilled because products were unavailable. I was informed that the refund of {amount_text} would be issued within {promise_text}. More than {facts['elapsed_days']} days have now passed, but the refund has not reached my original payment method.\n\nPlease confirm whether the order cancellation and refund are approved, the date the refund was initiated, the refund reference/ARN (if generated), and the exact expected credit date. Please keep this request linked to my existing support conversation, if applicable.\n\nI can provide the order, refund-promise and payment screenshots through this official support channel.\n\nThank you.", "notice": f"Draft only. Review and send it yourself through {merchant}'s official support route. BolKeResolve has not contacted the merchant."},
                "message": f"Your refund promise appears overdue: {merchant} reportedly promised {promise_text}, and you report that {elapsed_text} have passed. You do not need to restart the complaint. Open the same order in {merchant}'s official Help Center, continue the existing support thread if you have one, and request the refund initiation date, refund reference and exact credit date. Attach the order cancellation, two-day promise and payment proof."
            })
            return base
        elif not facts["order_outcome"]:
            q = _question("order_outcome", "What happened to the order before you expected the refund?", [("cancelled", "I cancelled the order"), ("return_picked_up", "The return was picked up"), ("not_delivered", "It was never delivered"), ("delivered_with_issue", "It arrived, but something was wrong"), ("delivered", "It was delivered normally")], "A cancellation, returned parcel, failed delivery and delivered-item complaint can have different refund triggers and evidence.")
        elif not facts.get("refund_scope"):
            q = _question("refund_scope", "Is the refund for the whole order or only some products?", [("full_order", "The entire order"), ("some_items", "Only selected products / items"), ("unknown", "I am not sure")], "A partial refund may need the affected item names and quantities, not just the order total.")
        elif facts.get("refund_scope") == "some_items" and not facts.get("item_count"):
            q = _question("item_count", "How many products or items are included in this refund? Type the number in the message box.", [("type_count", "I'll enter the number")], "This helps identify whether the refund is for one item or multiple items in the order.")
        elif not facts["refund_status"]:
            q = _question("refund_status", "When you open this order in the app, what does the refund section say?", [("not_initiated", "Refund not initiated / no refund shown"), ("pending", "Refund pending / processing"), ("initiated", "Refund initiated / processed"), ("unknown_not_credited", "I cannot find a refund status")], "We need to separate a merchant that has not initiated a refund from a refund already sent to the payment provider.")
        elif facts["refund_status"] == "not_initiated" and not facts.get("refund_reason"):
            q = _question("refund_reason", "What reason or status did the app show for not starting the refund?", [("rejected", "Return / refund rejected or not eligible"), ("pickup_pending", "Pickup or inspection is still pending"), ("no_reason", "No reason was shown"), ("other", "Something else — I'll type it")], "The reason shown by the app determines whether to clarify the return decision, fix a pickup issue or challenge a rejection.")
        elif facts["refund_status"] in {"initiated", "pending", "unknown_not_credited"} and facts["promised_timeline"] == "given_details_needed":
            q = _question("promised_timeline_details", "What exact date or number of working days did the app show? You can type it in the message box.", [("type_date", "I'll type the date or number of days")], "The exact deadline helps distinguish a refund still within the stated window from one that needs a follow-up.")
        elif facts["refund_status"] in {"initiated", "pending", "unknown_not_credited"} and not facts["promised_timeline"]:
            q = _question("promised_timeline", "Did the app or support team give you a refund date or number of working days?", [("given", "Yes, a date/timeline was shown"), ("not_given", "No date or timeline was given"), ("not_sure", "I am not sure")], "If a refund is already in process, its stated deadline tells us whether to wait or follow up now.")
        elif facts["support_contacted"] is None:
            q = _question("support_contacted", f"Have you already contacted {merchant} about this order?", [("yes", "Yes, I contacted support"), ("no", "No, not yet")], "If you already have a complaint, we should follow up on that record instead of starting again.")
        elif facts["support_contacted"] and facts["support_reference"] == "reference_claimed":
            q = _question("support_reference_details", "Please type the ticket or complaint reference exactly as shown (do not include passwords or OTPs).", [("type_reference", "I'll type the reference below")], "The exact reference keeps the follow-up linked to the correct existing complaint.")
        elif facts["support_contacted"] and not facts["support_reference"]:
            q = _question("support_reference", "Did support give you a ticket number or send a written reply?", [("reference", "I have a ticket / reference"), ("reply_no_ref", "I received a reply, but no reference"), ("no_response", "No reply or reference yet")], "A ticket or written response helps keep the follow-up tied to the earlier complaint.")
        else:
            # Resolve only a curated official merchant route. An unknown merchant must
            # never accidentally receive NCH as if it were the order's support desk.
            route_list = find_support_destinations(merchant)
            # Use a merchant route first; add the National Consumer Helpline only as a
            # later pre-litigation option, not as the first answer to a new refund issue.
            base.update({
                "status": "action", "stage": "merchant_action", "title": f"Follow up on the {merchant} refund" if merchant else "Follow up on the order refund",
                "reason": f"You reported {merchant or 'the merchant'} and a refund that has not reached you. This next step is based on the details saved in this case, not on a live check of the merchant's systems.",
                "current_step": {"title": "Open the order-specific support route", "detail": (route_list[0].get("action") if route_list else "Open the order in the official app or website and use its Help/Support option. Ask for the refund initiation status, processing date, reference and expected credit date."), "why": "The merchant can confirm whether the refund was approved and whether a reference was generated."},
                "support_destinations": route_list[:1],
                "evidence_request": ({"title": "Add your earlier support record", "detail": "Upload the support ticket, chat reply or email acknowledgement. This helps keep the follow-up linked to the complaint you already raised. Hide unrelated personal details."} if facts.get("support_contacted") else {"title": "Add the most useful proof", "detail": ("Start with the order page showing the affected products and quantities, then add the return/refund status for those items." if facts.get("refund_scope") == "some_items" else "Start with one screenshot showing the order ID and cancellation/return/delivery status. If the app says refund initiated, add that status/reference screen.") + " Hide unrelated personal details."}),
                "support_draft": {
                    "subject": f"Refund follow-up — {merchant or 'my order'}",
                    "message": f"Hello {merchant or 'Support'} Support,\n\nI am following up on my order [Order ID]. The amount involved is ₹{facts['amount']:,.0f} (as I reported) and the refund has not reached my original payment method.\n\nPlease confirm whether the refund has been approved and initiated, the processing date, the refund reference / ARN / UTR / RRN if generated, and the expected credit date. Please keep this linked to my earlier complaint if one exists.\n\nI can share the order and payment proof through this official support channel.\n\nThank you." if facts.get("amount") is not None else f"Hello {merchant or 'Support'} Support,\n\nPlease confirm the order's cancellation/return status, whether the refund has been approved and initiated, the processing date, any refund reference / ARN / UTR / RRN, and the expected credit date. Please keep this linked to my earlier complaint if one exists.\n\nThank you.",
                    "notice": "Draft only. Review and send it yourself through the official support channel. BolKeResolve has not contacted the merchant.",
                },
                "message": "Your case has enough detail for the next action: contact the order-specific support route shown here. Ask whether the refund was approved and initiated, the processing date, the reference (if generated), and the expected credit date. Add the relevant order/refund screenshot so the history is preserved.",
            })
            if facts.get("support_contacted") and facts.get("support_reference"):
                base["support_destinations"].append(NCH)
                base["message"] += " If the merchant does not resolve the complaint, you can consider the National Consumer Helpline as a pre-litigation grievance route; keep your merchant ticket and evidence ready."
            return base
        base.update({
            "status": "question", "stage": "refund_intake", "title": "Let's narrow down the refund issue",
            "reason": "I have used what you already told me. This is the one remaining detail that changes the next step.",
            "next_question": q,
            "evidence_request": {"title": "A screenshot can help", "detail": "You can add the order page or return/cancellation status now, or answer the question first. The original file will stay attached to this case."},
            "support_destinations": find_support_destinations(merchant)[:1],
            "message": q["prompt"],
        })
        return base

    if issue in {"Order paid but not received", "Order missing, incomplete or incorrect"}:
        if not merchant:
            q = _question("merchant", "Which app or store handled this order?", [("Meesho", "Meesho"), ("Flipkart", "Flipkart"), ("Zomato", "Zomato"), ("Other", "Another app / store")], "The order support route belongs to the platform that accepted the order.")
        elif merchant == "Other / unlisted platform":
            q = _question("merchant_name", "Type the exact app or store name so the case can use the correct route.", [("type_name", "I'll type the name below")], "I won't invent a support contact for an unidentified platform.")
        elif not facts["order_outcome"]:
            q = _question("order_outcome", "What is wrong with the order?", [("not_delivered", "It was never delivered"), ("delivered_with_issue", "It arrived but was missing, wrong or damaged"), ("cancelled", "It was cancelled")], "This determines which order proof and remedy to request.")
        elif facts["support_contacted"] is None:
            q = _question("support_contacted", f"Have you reported this order issue to {merchant} yet?", [("yes", "Yes, I contacted support"), ("no", "No, not yet")], "We should follow up on an existing support case if one already exists.")
        else:
            routes = find_support_destinations(merchant)
            base.update({"status": "action", "stage": "order_action", "title": f"Resolve the order issue with {merchant}", "reason": f"Your report identifies {merchant} and the order outcome. This action is based on your account, not an independent check of the order.", "current_step": {"title": "Open support for the affected order", "detail": routes[0]["action"] if routes else "Open the affected order in the official app and choose Help or Support. Select the closest issue category and ask for the order status, available remedy and a complaint reference.", "why": "The platform holding the order record can confirm delivery/return evidence and available remedy."}, "support_destinations": routes[:1], "evidence_request": {"title": "Add the order proof that matches the issue", "detail": "For non-delivery, add the order status and delivery updates. For missing/wrong/damaged items, add the order details and clear photos/video of the item and packaging if available. Cover addresses, phone numbers and unrelated details."}, "message": f"Open {merchant}'s support for this exact order. Add the order status and the relevant photo/video or delivery proof. Ask for the case reference and the specific remedy available for this issue."})
            return base
        base.update({"status": "question", "stage": "order_intake", "title": "Let's identify the order problem", "reason": "This answer changes which evidence and remedy to request.", "next_question": q, "support_destinations": find_support_destinations(merchant)[:1], "evidence_request": {"title": "Order proof", "detail": "You can add the order page or delivery status screenshot now. Add item photos/video only when the issue is missing, wrong or damaged goods."}, "message": q["prompt"]})
        return base

    if is_upi:
        if not payment_app:
            q = _question("payment_app", "Which payment app did you use for this UPI transaction?", [("Google Pay", "Google Pay"), ("PhonePe", "PhonePe"), ("Paytm", "Paytm"), ("Other", "Another UPI app")], "The app-specific dispute path depends on where the transaction was initiated.")
        elif not facts["transaction_status"]:
            q = _question("transaction_status", "What status does the UPI transaction show in the app?", [("success", "Successful"), ("pending", "Pending"), ("failed", "Failed"), ("debit_no_credit", "Money debited, recipient not credited")], "A successful merchant payment is normally disputed with the merchant; a failed or pending UPI transfer follows a payment-dispute route.")
        elif not facts["elapsed"]:
            q = _question("transaction_time", "When did this transaction happen?", [("today", "Today"), ("yesterday", "Yesterday"), ("2_to_5_days", "2–5 days ago"), ("older", "More than 5 days ago")], "Transaction age can change the provider's dispute and reversal process.")
        else:
            routes = find_support_destinations(payment_app, story, "UPI transaction")
            base.update({
                "status": "action", "stage": "upi_dispute", "title": "Open the exact UPI transaction and raise the matching issue",
                "reason": f"You reported using {payment_app}. The right path depends on the exact status shown in its transaction history.",
                "current_step": {"title": "Open transaction history and select this payment", "detail": "Check the status and note the UPI reference ID / UTR. If successful and a merchant received it, request resolution from the merchant. If failed/pending/debited-not-credited, raise the transaction issue in the UPI app and contact your bank when the app directs you.", "why": "The payment provider and bank need the specific transaction reference; a generic refund request could go to the wrong organisation."},
                "support_destinations": routes[:1] + [NPCI],
                "evidence_request": {"title": "Add the transaction receipt", "detail": "Upload the selected transaction details screen showing date, amount, status and UPI reference. Hide account balances and unrelated transactions."},
                "message": "Open this transaction in your payment app and use its ‘Having issues?’ or dispute option. Keep the UPI reference. If the payment succeeded and the merchant received it, contact the merchant for the order/refund issue instead.",
            })
            return base
        base.update({"status": "question", "stage": "upi_intake", "title": "Let's identify the payment route", "reason": "This answer determines whether the issue belongs with the merchant or the payment provider.", "next_question": q, "support_destinations": routes if 'routes' in locals() else find_support_destinations(payment_app, story, "UPI transaction")[:1], "evidence_request": {"title": "Keep the transaction proof", "detail": "A transaction details screenshot with the UPI reference can help. Do not share your UPI PIN or OTP."}, "message": q["prompt"]})
        return base

    if issue in {"Subscription or recurring billing complaint", "Account access complaint", "Service quality complaint", "Other consumer complaint"}:
        if not merchant:
            q = _question("merchant", "Which company, app or service is this about?", [("type_name", "I'll type the organisation name")], "The responsible provider determines the correct official support route.")
        elif facts.get("support_contacted") is None:
            q = _question("support_contacted", f"Have you already contacted {merchant} about this specific issue?", [("yes", "Yes"), ("no", "Not yet")], "If you already have a complaint, the next step should follow that record rather than start over.")
        else:
            routes = find_support_destinations(merchant)
            issue_label = issue.casefold()
            if issue == "Subscription or recurring billing complaint":
                evidence_detail = "Add the subscription plan or invoice, the billing entry, renewal/cancellation status and any cancellation confirmation. Mask unrelated account details."
                action_title = "Check the subscription and billing record"
            elif issue == "Account access complaint":
                evidence_detail = "Add the account error screenshot and any support case reference. Never upload passwords, OTPs, recovery codes or full identity numbers."
                action_title = "Use the provider's official account-recovery route"
            elif issue == "Service quality complaint":
                evidence_detail = "Add the booking/order/service reference, date, what was promised, what happened and any support response."
                action_title = "Raise a complaint against the specific service"
            else:
                evidence_detail = "Add only the document or message that shows what was promised, what happened and the provider's response."
                action_title = "Open a case with the responsible organisation"
            base.update({"status": "action", "stage": "consumer_service_action", "title": f"Resolve the {issue_label}", "reason": "The issue has been classified from the details you provided. The route below is a first-party support route when available; BolKeResolve has not accessed the provider's internal records.", "current_step": {"title": action_title, "detail": routes[0].get("action") if routes else f"Open {merchant}'s official app or website, locate the relevant account/order/subscription record, and use its Help or Support option. Ask for a written case reference and the specific resolution available.", "why": "The provider holding the account or billing record can confirm the underlying event and available remedy."}, "support_destinations": routes[:1], "evidence_request": {"title": "Add the proof relevant to this issue", "detail": evidence_detail}, "message": f"I understand this is a {issue_label} involving {merchant}. Start with the specific account or billing record, then use the organisation's official support route. Keep the case reference and response here so we can decide the next step from what they tell you."})
            return base
        base.update({"status": "question", "stage": "consumer_service_intake", "title": "Let's identify the responsible provider", "reason": "I will use the specific issue and provider rather than assume this is a payment refund.", "next_question": q, "support_destinations": find_support_destinations(merchant)[:1] if merchant else [], "message": q["prompt"]})
        return base

    # Unknown/ambiguous issue: ask for the route-changing category instead of defaulting
    # to an arbitrary payment issue playbook.
    q = _question("problem_type", "Which of these best describes what went wrong?", [("refund", "Refund not received"), ("order", "Order missing / incomplete / wrong"), ("payment", "Payment failed or money debited"), ("account", "Unknown or unauthorised transaction"), ("other", "Something else")], "I don't have enough information to choose a safe, specific route yet.")
    base.update({"status": "question", "stage": "classify_issue", "title": "I need one detail before recommending an action", "reason": "I won't guess the merchant or assume this is a refund when the story doesn't establish that yet.", "next_question": q, "message": q["prompt"]})
    return base
