"""Evidence-first resolution playbooks for BolKeResolve.

This module intentionally uses deterministic rules and cited official sources for the
first competition-ready workflow. It is not a payment-status verifier or legal adviser.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any

from backend.rulebook import rulebook_metadata

REVIEWED_ON = "2026-11-03"

SOURCES: dict[str, dict[str, str]] = {
    "razorpay_settlement": {
        "id": "razorpay_settlement",
        "title": "Razorpay settlements — Dashboard and support guidance",
        "organization": "Razorpay",
        "url": "https://razorpay.com/docs/payments/payments/dashboard/?preferred-country=IN",
        "summary": "In the signed-in Dashboard, open Transactions → Payments, select an affected Payment ID, inspect its settlement details and open the settlement_id for the breakdown. The official settlement FAQ explains that each settlement has a unique settlement ID and UTR. Standard domestic T+2 working days is not a guarantee for every account: bank approval, business vertical, risk factors and bank holidays affect the schedule. This guidance does not verify the merchant account.",
        "reviewed_on": REVIEWED_ON,
    },
    "razorpay_settlement_faq": {
        "id": "razorpay_settlement_faq",
        "title": "Razorpay payment settlements — official FAQs",
        "organization": "Razorpay",
        "url": "https://tfs.np.razorpay.in/docs/payments/settlements/faqs",
        "summary": "Explains settlement flow, the account-specific settlement cycle, the standard domestic T+2 working-day cycle, UTR lookup and what to do when a settlement fails. Check the merchant Dashboard and account-specific schedule; do not assume this standard cycle applies to every account.",
        "reviewed_on": REVIEWED_ON,
    },
    "npci_upi_faq": {
        "id": "npci_upi_faq",
        "title": "UPI — Frequently Asked Questions",
        "organization": "National Payments Corporation of India (NPCI)",
        "url": "https://www.npci.org.in/what-we-do/upi/faqs",
        "summary": "NPCI guidance says that for a failed transaction where the account was debited, the refund should return to the account; if it has not arrived within one hour, contact bank customer support. Its FAQ separately notes that a pending debit not credited to the beneficiary can take up to 48 hours to reach them.",
        "reviewed_on": REVIEWED_ON,
    },
    "rbi_ombudsman_2026": {
        "id": "rbi_ombudsman_2026",
        "title": "Reserve Bank — Integrated Ombudsman Scheme, 2026 FAQ",
        "organization": "Reserve Bank of India (RBI)",
        "url": "https://old.rbi.org.in/commonman/english/scripts/faqs.aspx?id=3407",
        "summary": "For complaints about eligible RBI-regulated entities, the customer generally must first approach the entity. RBI's FAQ describes when an Ombudsman complaint may be made if there is no response within the applicable period or the response is unsatisfactory. Eligibility and time limits depend on the Scheme and applicable instructions.",
        "reviewed_on": REVIEWED_ON,
    },
    "national_consumer_helpline": {
        "id": "national_consumer_helpline",
        "title": "National Consumer Helpline — official portal and contact details",
        "organization": "Department of Consumer Affairs, Government of India",
        "url": "https://consumerhelpline.gov.in/public/index.php/contact",
        "summary": "Consumer grievances can be registered through the official portal; the published contact page lists 1915 and WhatsApp +91 88000 1915. This is a pre-litigation consumer grievance mechanism and does not guarantee a particular outcome.",
        "reviewed_on": REVIEWED_ON,
    },
    "cybercrime_1930": {
        "id": "cybercrime_1930",
        "title": "National Cyber Crime Reporting Portal",
        "organization": "Indian Cyber Crime Coordination Centre / Ministry of Home Affairs",
        "url": "https://cybercrime.gov.in/",
        "summary": "The official portal instructs people to report online financial fraud through helpline 1930 or the portal. For suspected unauthorised or fraudulent transactions, contact your bank/payment provider immediately as well.",
        "reviewed_on": REVIEWED_ON,
    },
    "e_jagriti": {
        "id": "e_jagriti",
        "title": "e-Jagriti — Consumer Commission case filing and help documents",
        "organization": "Department of Consumer Affairs / National Informatics Centre",
        "url": "https://e-jagriti.gov.in/help-docs",
        "summary": "The official portal provides help documents and filing workflows for consumer-commission matters. Filing type, eligibility, documents and any required steps depend on the particular case; BolKeResolve does not file a case for the user.",
        "reviewed_on": REVIEWED_ON,
    },
}

ISSUE_ALIASES = {
    "Failed UPI payment": {
        "failed upi", "upi failure", "transaction failed", "payment failed", "upi fail",
        "यूपीआई असफल", "भुगतान असफल", "पेमेंट फेल", "लेन-देन असफल", "पेमेंट अयशस्वी", "व्यवहार अयशस्वी",
        "পেমেন্ট ব্যর্থ", "লেনদেন ব্যর্থ", "પેમેન્ટ નિષ્ફળ", "વ્યવહાર નિષ્ફળ",
        "பரிவர்த்தனை தோல்வி", "చెల్లింపు విఫలమైంది", "లావాదేవీ విఫలమైంది",
        "ಪಾವತಿ ವಿಫಲ", "ವಹಿವಾಟು ವಿಫಲ", "പേയ്മെന്റ് പരാജയപ്പെട്ടു", "ഇടപാട് പരാജയപ്പെട്ടു",
        "ਭੁਗਤਾਨ ਅਸਫਲ", "ਲੈਣ-ਦੇਣ ਅਸਫਲ",
    },
    "Refund not received": {
        "refund", "money back", "paise wapas", "paisa wapas", "refund pending",
        "रिफंड", "पैसे वापस", "पैसा वापस", "वापस नहीं आया", "रिफंड नहीं आया", "रिफंड लंबित", "परतावा आला नाही", "पैसे परत आले नाहीत",
        "রিফান্ড আসেনি", "টাকা ফেরত আসেনি", "રિફંડ મળ્યું નથી", "પૈસા પાછા આવ્યા નથી",
        "ரீஃபண்ட் வரவில்லை", "பணம் திரும்ப வரவில்லை", "రిఫండ్ రాలేదు", "డబ్బు తిరిగి రాలేదు",
        "ರಿಫಂಡ್ ಬಂದಿಲ್ಲ", "ಹಣ ಹಿಂತಿರುಗಿಲ್ಲ", "റീഫണ്ട് കിട്ടിയില്ല", "പണം തിരികെ വന്നില്ല",
        "ਰਿਫੰਡ ਨਹੀਂ ਆਇਆ", "ਪੈਸੇ ਵਾਪਸ ਨਹੀਂ ਆਏ",
    },
    "Duplicate charge": {
        "duplicate", "charged twice", "double charge", "do baar", "twice",
        "दो बार पैसे", "दो बार चार्ज", "डबल चार्ज", "दुबारा कट", "दोनदा पैसे", "दोन वेळा पैसे",
        "দুইবার টাকা", "দুবার টাকা", "બે વાર પૈસા", "இரண்டு முறை பணம்", "రెండు సార్లు డబ్బు",
        "ಎರಡು ಬಾರಿ ಹಣ", "രണ്ടു തവണ പണം", "ਦੋ ਵਾਰ ਪੈਸੇ",
    },
    "Incorrect amount": {
        "incorrect amount", "wrong amount", "extra charge", "charged extra", "zyada paise",
        "less than expected", "short refund", "underpaid refund", "refund amount is short",
        "गलत राशि", "गलत अमाउंट", "ज्यादा पैसे", "अधिक राशि", "कम राशि", "कम रकम वापस", "चुकीची रक्कम",
        "ভুল পরিমাণ", "বেশি টাকা", "ખોટી રકમ", "அதிக தொகை", "தவறான தொகை", "తప్పు మొత్తం",
        "ತಪ್ಪು ಮೊತ್ತ", "തെറ്റായ തുക", "ਗਲਤ ਰਕਮ",
    },
    "Order paid but not received": {
        "order not received", "not delivered", "paid but", "delivery", "order cancel",
        "ऑर्डर नहीं मिला", "डिलीवरी नहीं हुई", "सामान नहीं आया", "पार्सल नहीं आया", "ऑर्डर मिळाली नाही", "वस्तू मिळाली नाही",
        "অর্ডার পাইনি", "ডেলিভারি হয়নি", "ઓર્ડર મળ્યો નથી", "ஆர்டர் வரவில்லை", "பொருள் வரவில்லை",
        "ఆర్డర్ రాలేదు", "వస్తువు రాలేదు", "ಆರ್ಡರ್ ಬಂದಿಲ್ಲ", "ವಸ್ತು ಬಂದಿಲ್ಲ", "ഓർഡർ ലഭിച്ചില്ല",
        "ഓർഡർ വന്നില്ല", "ਆਰਡਰ ਨਹੀਂ ਮਿਲਿਆ",
    },
}


def _contains(text: str, *terms: str) -> bool:
    return any(t in text for t in terms)


def classify_issue(issue_type: str, description: str, payment_status: str = "unknown") -> tuple[str, str, str]:
    # The description is the evidence to classify. The selected issue is used as a
    # fallback, not mixed into the description, so a stale/default dropdown cannot
    # override what the person actually wrote.
    text = re.sub(r"\s+", " ", (description or "").lower()).strip()
    selected = (issue_type or "Other payment issue").strip()
    fraud_terms = (
        "fraud", "scam", "unauthori", "not mine", "didn't make", "did not make",
        "unknown transaction", "chori", "dhokha", "फ्रॉड", "धोखाधड़ी", "फसवणूक",
        "अनजान ट्रांजैक्शन", "अनधिकृत", "मैंने नहीं किया", "मेरे द्वारा नहीं", "फर्जी लेनदेन", "मी हा व्यवहार केला नाही",
        "প্রতারণা", "জালিয়াতি", "আমি করিনি", "অজানা লেনদেন", "છેતરપિંડી", "મેં નથી કર્યું", "અજાણ્યો વ્યવહાર",
        "மோசடி", "நான் செய்யவில்லை", "தெரியாத பரிவர்த்தனை", "మోసం", "నేను చేయలేదు", "తెలియని లావాదేవీ",
        "ವಂಚನೆ", "ನಾನು ಮಾಡಿಲ್ಲ", "ತಿಳಿಯದ ವಹಿವಾಟು", "തട്ടിപ്പ്", "ഞാൻ ചെയ്തിട്ടില്ല", "അറിയാത്ത ഇടപാട്",
        "ਧੋਖਾਧੜੀ", "ਮੈਂ ਨਹੀਂ ਕੀਤਾ", "ਅਣਜਾਣ ਲੈਣ-ਦੇਣ",
    )
    # Safety route always takes precedence over ordinary complaint categories.
    if payment_status == "unauthorized" or selected == "Suspected fraud or unauthorised transaction" or _contains(text, *fraud_terms):
        return "Suspected fraud or unauthorised transaction", "high", "The description contains wording that may indicate an unauthorised or fraudulent payment. This is a safety route, not a verified fraud finding."

    # A payment-gateway merchant settlement is not a consumer order refund.
    # Detect the funds flow (customer collections -> gateway -> business bank)
    # before any broad occurrence of the words "refund" or "money back".
    gateway_provider = bool(re.search(r"\brazor\s*pay\b|\brazorpay\b|रेज़रपे|रेजरपे", text))
    gateway_money_flow = bool(re.search(
        r"(?:extract|withdraw|transfer|settle|payout|settlement|release).{0,100}(?:from|through|via)\s+razor\s*pay|"
        r"razor\s*pay.{0,120}(?:to|into)\s+(?:my|our|business|company)\s+(?:bank\s+)?account|"
        r"(?:customer|customers|client|clients).{0,100}(?:payment|payments|paid).{0,100}(?:my|our|business)\s+(?:bank\s+)?account",
        text,
    ))
    explicit_merchant_settlement = bool(re.search(
        r"\b(?:merchant\s+settlement|settlement\s+(?:not\s+credited|delay|delayed|failed|on\s+hold)|payout\s+(?:not\s+received|failed|delayed)|gateway\s+balance)\b",
        text,
    ))
    customer_refund_to_buyer = bool(re.search(
        r"(?:refund|money\s+back).{0,50}(?:to\s+my\s+customer|to\s+customers|buyer|end\s+user)|"
        r"(?:customer|buyer).{0,50}(?:has\s+not\s+received|did\s+not\s+receive).{0,40}refund",
        text,
    ))
    if not customer_refund_to_buyer and (explicit_merchant_settlement or (gateway_provider and gateway_money_flow)):
        return (
            "Merchant settlement not credited",
            "high",
            "The described funds flow is a payment-gateway merchant settlement to a business bank account, not a consumer ecommerce refund. Check the gateway settlement record and its status.",
        )

    refund_missing_terms = (
        "refund pending", "refund is pending", "refund has not arrived", "refund hasn't arrived",
        "refund not received", "refund is delayed", "refund still pending", "refund not credited", "refund didn't arrive", "refund did not arrive",
        "not received a refund", "haven't received the refund", "has not been refunded",
        "refund didn't come", "refund hasn't come", "money back not received",
        "did not get my refund back", "do not get my refund back", "didn't get my refund back",
        "have not got the refund back", "we have not got the refund back", "not got the refund back",
        "refund back not received", "refund not come back", "refund has not come back",
        "haven't got my refund", "have not got my refund", "i haven't received my refund",
        "i have not received my refund", "i did not receive my refund", "i didn't receive my refund",
        "refund not come yet", "refund still not received", "refund has not been credited",
        "refund hasn't been credited", "money has not come back", "money hasn't come back",
        "रिफंड लंबित", "रिफंड नहीं आया", "रिफंड नहीं मिला", "पैसे वापस नहीं", "परतावा प्रलंबित", "परतावा आला नाही",
        "রিফান্ড আসেনি", "টাকা ফেরত আসেনি", "રિફંડ મળ્યું નથી", "પૈસા પાછા આવ્યા નથી",
        "ரீஃபண்ட் வரவில்லை", "பணம் திரும்ப வரவில்லை", "రిఫండ్ రాలేదు", "డబ్బు తిరిగి రాలేదు",
        "ರಿಫಂಡ್ ಬಂದಿಲ್ಲ", "ಹಣ ಹಿಂತಿರುಗಿಲ್ಲ", "റീഫണ്ട് കിട്ടിയില്ല", "പണം തിരികെ വന്നില്ല",
        "ਰਿਫੰਡ ਨਹੀਂ ਆਇਆ", "ਪੈਸੇ ਵਾਪਸ ਨਹੀਂ ਆਏ",
        "पैसा वापस नहीं", "वापस नहीं आया", "मेरा रिफंड नहीं आया",
        "रिफंड बैक नहीं आया", "रिफंड वापस नहीं आया", "रिफंड अभी तक नहीं आया",
        "अभी तक रिफंड नहीं मिला", "रिफंड बैक नॉट गॉट", "रिफंड नॉट गॉट",
        "नॉट गॉट दी रिफंड", "नॉट गॉट रिफंड",
    )
    transliterated_refund_missing = (
        _contains(text, "रिफंड", "रिफन्ड")
        and _contains(text, "नॉट", "नहीं", "नही", "नहि", "नाही", "नाय", "नॉट गॉट", "नहीं आया", "नहीं मिला", "नहीं मिली", "नहीं आए")
    )
    customer_refund_uncredited = bool(
        customer_refund_to_buyer and re.search(
            r"(?:customer|buyer|end user).{0,70}(?:has not received|hasn't received|did not receive|didn't receive|not received)|"
            r"(?:refund|money back).{0,70}(?:customer|buyer|end user).{0,70}(?:not received|has not received|hasn't received)",
            text,
        )
    )
    if customer_refund_uncredited:
        return (
            "Refund not received", "medium",
            "The merchant reports issuing a refund to a customer through a payment provider, but the customer has not received it. Trace the provider refund ID/status and the original payment reference; do not use a merchant-settlement or ecommerce-order workflow.",
        )

    refund_context = payment_status == "refund_pending" or _contains(text, *refund_missing_terms) or transliterated_refund_missing
    explicit_failed = _contains(
        text, "failed upi", "upi failure", "transaction failed", "payment failed", "upi fail",
        "declined", "यूपीआई असफल", "भुगतान असफल", "पेमेंट फेल", "लेन-देन असफल",
    )
    explicit_pending_status = _contains(
        text, "pending", "processing", "beneficiary not credited", "recipient not credited",
        "recipient has not received", "پینڈنگ", "पेंडिंग", "लंबित", "প্রলম্বিত", "লেনদেন পেন্ডিং",
        "બાકી", "நிலுவையில்", "పెండింగ్", "ಬಾಕಿ", "കാത്തിരിക്കുന്നു", "ਬਕਾਇਆ",
    )
    transaction_hint = _contains(text, "upi", "transaction", "payment", "debited", "deduct", "पैसे कट", "पैसा कट", "यूपीआई", "लेन-देन", "भुगतान")
    # A confirmed status choice should influence routing, while contradictions must not
    # be silently normalised into a confident category.
    if payment_status == "pending" and transaction_hint and not refund_context:
        return "UPI payment pending / recipient not credited", "medium", "The user selected pending in the payment app. Confirm whether the recipient was credited and follow the pending-transaction guidance, not the failed-payment path."
    if payment_status == "failed" and not refund_context and (selected == "Failed UPI payment" or _contains(text, "upi", "यूपीआई")):
        return "Failed UPI payment", "medium", "The user selected failed as the payment-app status. Follow the failed-payment playbook and confirm the debit/reversal details before escalating."
    if payment_status == "successful" and (explicit_failed or explicit_pending_status):
        stated_status = "failed" if explicit_failed else "pending"
        return "Other payment issue", "low", f"The story describes the payment as {stated_status}, but the selected status says successful. Resolve this mismatch before following a specific playbook."
    # If the user describes a failed UPI transaction whose money was debited, NPCI's
    # failed-transaction flow is a better fit than a generic merchant-refund flow.
    if explicit_failed and payment_status in {"unknown", "failed"}:
        return "Failed UPI payment", "medium", "The description says the transaction failed. Confirm the payment status and whether money was debited before following the relevant NPCI steps."
    if refund_context:
        return "Refund not received", "medium", "The description or selected status indicates a refund may still be due. Confirm the original transaction and the merchant/provider's refund status."

    pending_wording = _contains(
        text, "pending", "processing", "beneficiary not credited", "recipient ko nahi mila",
        "saamne wale ko nahi mila", "recipient has not received", "not credited", "not received yet",
        "पेंडिंग", "लंबित", "प्राप्त नहीं हुआ", "नहीं मिला", "नहीं मिले", "नहीं पहुंचे", "नहीं पहुँचे", "प्रलंबित",
        "পেন্ডিং", "বাকি", "બાકી", "நிலுவையில்", "పెండింగ్", "ಬಾಕಿ", "കാത്തിരിക്കുന്നു", "ਬਕਾਇਆ",
    )
    transaction_wording = _contains(
        text, "upi", "transaction", "beneficiary", "recipient", "debited", "deduct",
        "kat gaye", "kat gaya", "यूपीआई", "लेन-देन", "भुगतान", "पैसे कट", "पैसा कट",
        "खाते से कट", "लाभार्थी", "ব্যবহার", "লেনদেন", "ટ્રાન્ઝેક્શન", "વ્યવહાર", "பரிவர்த்தனை",
        "లావాదేవీ", "చెల్లింపు", "ವಹಿವಾಟು", "പണമിടപാട്", "ഇടപാട്", "ਲੈਣ-ਦੇਣ",
    )
    order_words = _contains(text, "order", "delivery", "package", "parcel", "item", "ऑर्डर", "डिलीवरी", "सामान", "প্যাকেজ", "অর্ডার", "ડિલિવરી", "ઓર્ડર", "ஆர்டர்", "பொருள்", "ఆర్డర్", "వస్తువు", "ಆರ್ಡರ್", "ವಸ್ತು", "ഓർഡർ", "ਆਰਡਰ")
    order_missing_terms = _contains(text, "not received", "not delivered", "hasn't arrived", "has not arrived", "didn't arrive", "did not arrive", "nahi mila", "nahi aaya", "नहीं मिला", "नहीं आया", "सामान नहीं आया", "ऑर्डर नहीं मिला", "ডেলিভারি হয়নি", "অর্ডার পাইনি", "ઓર્ડર મળ્યો નથી", "வரவில்லை", "ఆర్డర్ రాలేదు", "ಆರ್ಡರ್ ಬಂದಿಲ್ಲ", "ഓർഡർ ലഭിച്ചില്ല", "ਆਰਡਰ ਨਹੀਂ ਮਿਲਿਆ")
    order_missing_context = order_words and order_missing_terms
    pending_context = (payment_status == "pending" and not refund_context) or (pending_wording and transaction_wording and not refund_context and not order_missing_context)
    if order_missing_context and payment_status != "pending" and not ("recipient" in text or "beneficiary" in text or "ലാഭാർത്ഥി" in text):
        return "Order paid but not received", "medium", "The description sounds like an order or delivery issue rather than a payment transaction still pending. Check both the order status and payment receipt."
    if pending_context or (selected == "UPI payment pending / recipient not credited" and payment_status != "refund_pending"):
        return "UPI payment pending / recipient not credited", "medium", "The description or selected status suggests the transaction may still be pending or the recipient may not have been credited. Confirm the status shown in the payment app."

    # Description-first routing avoids a stale selected category overriding clear evidence.
    for canonical in ("Duplicate charge", "Incorrect amount", "Order paid but not received", "Failed UPI payment"):
        aliases = ISSUE_ALIASES[canonical]
        if _contains(text, *aliases):
            return canonical, "medium" if selected == canonical else "low", "The issue type is inferred from the wording supplied by the user. Confirm it if it does not fit."

    known_categories = set(ISSUE_ALIASES) | {"UPI payment pending / recipient not credited", "Suspected fraud or unauthorised transaction"}
    if selected in known_categories:
        return selected, "medium", "The issue type comes from the user's selection. Confirm the category if it does not fit the description."
    if payment_status == "failed":
        return "Failed UPI payment", "medium", "The selected payment status is failed; confirm the status shown by your payment app or bank."
    return (selected or "Other payment issue"), "low", "This issue is not confidently classified. The suggested steps are general; choose the closest issue type or add more detail."


def extract_facts(description: str, amount: float | None, payment_date: str, merchant: str, payment_status: str) -> dict[str, Any]:
    # Amount detection is only a prompt for user confirmation; it does not replace the amount field.
    amount_patterns = re.findall(r"(?:₹|\brs\.?\s*|\binr\s*)([\d,]+(?:\.\d{1,2})?)", description, re.I)
    mentioned_amounts: list[float] = []
    for raw in amount_patterns[:5]:
        try:
            mentioned_amounts.append(float(raw.replace(",", "")))
        except ValueError:
            pass
    return {
        "amount_entered": amount,
        "amounts_mentioned_in_story": mentioned_amounts,
        "amount_needs_confirmation": bool(
            mentioned_amounts
            and (
                amount is None
                or len({round(value, 2) for value in mentioned_amounts}) > 1
                or all(abs(value - amount) > 0.009 for value in mentioned_amounts)
            )
        ),
        "payment_date_entered": payment_date or None,
        "merchant_entered": merchant or None,
        "payment_status_selected": payment_status or "unknown",
        "statement": "Facts are based on user input only; no bank or payment network has been queried.",
    }


def build_resolution(
    issue_type: str,
    description: str,
    merchant: str = "",
    amount: float | None = None,
    payment_date: str = "",
    payment_status: str = "unknown",
    contacted_support: bool | None = None,
) -> dict[str, Any]:
    canonical, confidence, rationale = classify_issue(issue_type, description, payment_status)
    text = f"{issue_type} {description}".lower()
    sources_used: set[str] = set()
    steps: list[dict[str, Any]] = []
    urgent = canonical == "Suspected fraud or unauthorised transaction"
    safety_message = "Never share an OTP, UPI PIN, password, full card number or remote-access code with anyone, including someone claiming to help recover your money."

    def step(title: str, detail: str, why: str = "", source_ids: list[str] | None = None, priority: str = "normal") -> None:
        ids = source_ids or []
        sources_used.update(ids)
        steps.append({"title": title, "detail": detail, "why": why, "source_ids": ids, "priority": priority})

    facts = extract_facts(description, amount, payment_date, merchant, payment_status)
    missing: list[str] = []
    if amount is None:
        distinct_story_amounts = {round(value, 2) for value in facts["amounts_mentioned_in_story"]}
        if len(distinct_story_amounts) > 1:
            missing.append("Confirm which amount in your story is the disputed amount")
        elif facts["amounts_mentioned_in_story"]:
            missing.append("Confirm the amount mentioned in your story")
        else:
            missing.append("Exact amount, if known")
    elif facts["amount_needs_confirmation"]:
        missing.append("Confirm which amount in your story is the disputed amount")
    if not payment_date:
        missing.append("Date/time of transaction, if known")
    if not merchant:
        missing.append("Payment app, bank or merchant involved")
    if payment_status == "unknown" and canonical in {"Failed UPI payment", "UPI payment pending / recipient not credited"}:
        missing.append("Exact transaction status shown in the payment app (failed, pending or successful)")
    if contacted_support is None:
        missing.append("Whether you have already contacted support")

    if urgent:
        step("Contact your bank or payment provider now", "Use the official number or in-app support channel printed on the bank/provider's own website or app. Ask them to block or secure the affected payment instrument if appropriate, register the dispute, and give you an acknowledgement/reference number.", "Fast reporting may be important for online financial fraud; do not wait for the app to finish processing this case.", ["cybercrime_1930"], "urgent")
        step("Report suspected online financial fraud", "Call 1930 as soon as possible and/or submit a report at the National Cyber Crime Reporting Portal. Keep the acknowledgement/reference number. This app does not submit the report for you.", "This is the official cybercrime reporting route; it does not guarantee recovery.", ["cybercrime_1930"], "urgent")
    elif canonical == "Merchant settlement not credited":
        # Business gateway settlements follow the gateway's settlement ledger,
        # not an ecommerce order/return/refund process.
        step(
            "Open the gateway settlement ledger",
            "Sign in to the Razorpay Dashboard yourself. Open Transactions → Payments, select an affected customer Payment ID, inspect its settlement details and open the settlement_id for the breakdown. You can also use the Dashboard Settlements view if available. Record the status shown, settlement ID, scheduled date and amount. If no settlement is visible, check whether the relevant customer payments are marked Captured.",
            "The settlement ledger identifies whether funds are still processing, have been processed, failed, or are on hold. This is different from a customer refund.",
            ["razorpay_settlement", "razorpay_settlement_faq"],
        )
        step(
            "Use the status to choose the next trace",
            "If Processed, locate the UTR in the settlement details/report and ask your bank to trace that reference. If Failed, check Razorpay's registered email for the failure reason and requested action. If On hold, review the Dashboard notification and Resolve action. If Created or Initiated, compare the displayed scheduled date with your account's configured settlement cycle and bank working days.",
            "The status and UTR determine whether the next party to contact is your bank or Razorpay. Do not assume that every account has the same settlement timing.",
            ["razorpay_settlement", "razorpay_settlement_faq"],
        )
        step(
            "Raise or continue a traceable Razorpay support ticket",
            "Use the signed-in Dashboard or Razorpay's official support page. Include settlement ID(s), affected amount, scheduled date, current status, UTR if present and any earlier ticket reference. Ask for the precise reason the funds have not reached the registered bank account and the next expected update.",
            "A traceable settlement reference is more useful than describing the amount as a missing order refund.",
            ["razorpay_settlement"],
        )
    elif canonical == "UPI payment pending / recipient not credited":
        if contacted_support is True:
            step("Follow up through your existing complaint", "Use the existing acknowledgement/reference number in the official UPI app or bank channel. Ask for the current transaction trace/status and a written update; avoid opening a duplicate ticket unless the provider directs you to.", "You have already contacted support, so continuing the traceable thread is usually more useful than starting over.", ["npci_upi_faq"])
            step("Re-check the transaction status in your UPI app", "Open the specific transaction and compare its current status, date/time, amount and reference ID with the provider's reply. Do not treat a support acknowledgement as proof of credit.", "NPCI distinguishes a failed debit from a pending transaction where the beneficiary has not yet been credited.", ["npci_upi_faq"])
        else:
            step("Check the transaction status in your UPI app", "Open the specific transaction and save its current status, UPI transaction/reference ID, date/time and amount. Do not rely only on an SMS or a screenshot forwarded by someone else.", "NPCI distinguishes a failed debit from a pending transaction where the beneficiary has not yet been credited.", ["npci_upi_faq"])
            step("If it remains unresolved, raise it through the UPI app or your bank", "Contact the app/bank's official support channel with the transaction reference and ask them to trace the payment. Save the complaint acknowledgement.", "NPCI's FAQ describes a possible delay of up to 48 hours for some pending debit/not-credited cases; check the current transaction status and applicable provider guidance before assuming that period applies to your case.", ["npci_upi_faq"])
    elif canonical == "Failed UPI payment":
        if contacted_support is True:
            step("Continue the existing bank/provider complaint", "Use the current complaint reference and ask for a transaction trace, reversal status and expected next update. If the provider has not given a reference, request an acknowledgement and retain it with this case.", "You have already contacted support, so focus on the existing trace instead of restarting the conversation.", ["npci_upi_faq"])
            step("Compare the reply with your transaction history", "Check the specific transaction in your UPI app or bank history. A message that a reversal was initiated is not proof that the amount has arrived.", "Only mark the issue resolved after you can confirm the credit yourself.", ["npci_upi_faq"])
        else:
            step("Confirm that the transaction is marked failed", "Open the transaction in your UPI app and check the status, amount, timestamp and transaction ID. If the status is pending, use the pending-payment guidance instead.", "The correct next step depends on the actual transaction status shown by your app or bank.", ["npci_upi_faq"])
            step("If the amount was debited and the refund has not arrived within one hour, contact your bank", "Use the bank's official customer-support channel and give the UPI transaction ID/reference. Ask for a complaint/reference number and keep it with this case.", "This timing is stated in NPCI's UPI FAQ for failed transactions where the account was debited; confirm current instructions for your transaction.", ["npci_upi_faq"])
    elif canonical == "Refund not received":
        if contacted_support is True:
            step("Continue the existing refund complaint", "Reply in the same official support thread with the order/cancellation ID and original transaction reference. Ask for the refund reference and a specific status or expected credit date; avoid opening a duplicate complaint unless the organisation asks you to.", "Because you have already contacted support, the next useful step is to make the existing request traceable and specific.")
            step("Check the original refund promise and payment history", "Compare the merchant's written promise or refund reference with your own account history. Keep the promise date labelled as merchant-stated or user-reported, as appropriate.", "A merchant saying 'initiated' does not itself establish that the refund was credited.")
        else:
            step("Collect the refund and order references", "Find the cancellation/order ID, refund reference (if shown), original transaction ID, promised refund date and any merchant message. Mark any date as reported by you unless the merchant confirms it.", "These identifiers help the merchant or payment provider trace the specific payment.")
            step("Ask the merchant or payment provider to trace the refund", "Contact the official support channel, quote the order and transaction references, and request the refund status and written acknowledgement. Do not share OTPs or payment PINs.", "Start with the organisation that handled the order/payment; the right party depends on whether the issue concerns the merchant, bank or payment app.")
        step("Consider the National Consumer Helpline if the merchant issue remains unresolved", "Review the official NCH portal or contact 1915 / WhatsApp +91 88000 1915. BolKeResolve prepares information; it does not file an NCH grievance for you.", "NCH is a Government of India pre-litigation consumer grievance mechanism. It does not guarantee a particular outcome.", ["national_consumer_helpline"])
        step("If the dispute remains unresolved, review the formal consumer-commission route", "Read the official e-Jagriti help documents to understand filing types, required documents and the process before deciding whether to proceed.", "Formal filing is a separate process with case-specific requirements. This app does not decide eligibility or file the case for you.", ["e_jagriti"])
    elif canonical == "Duplicate charge":
        step("Compare the transaction records", "Check whether there are two completed transactions or one transaction plus a pending/failed entry. Record both reference IDs, dates and amounts; redact unrelated account details from evidence.", "A duplicate-looking entry may have a different status, so verify before describing it as a confirmed duplicate.")
        step("Raise a trace/dispute with the provider and merchant", "Use the payment app or bank's official support channel and the merchant's official channel, as relevant. Explain that you see two charges and ask for a written status and acknowledgement.", "This creates a traceable record without assuming either transaction was incorrectly processed.")
        step("Use a consumer grievance route if a merchant dispute remains unresolved", "Review whether the National Consumer Helpline is appropriate and use the official portal/contact details if you choose to lodge a grievance.", "NCH handles consumer grievances, but applicability depends on the actual dispute.", ["national_consumer_helpline"])
        step("If earlier steps do not resolve the dispute, review formal consumer-commission filing", "Check e-Jagriti's official filing help documents and confirm the appropriate case type and documents before proceeding.", "Formal filing requirements depend on the case. This app does not determine eligibility or submit the case.", ["e_jagriti"])
    elif canonical == "Incorrect amount":
        step("Confirm the amount shown in the original record", "Compare the merchant receipt with the transaction entry. Note the expected amount, charged amount, date/time and transaction reference; do not upload unredacted bank credentials.", "This helps distinguish an incorrect merchant bill from a payment-processing discrepancy.")
        step("Ask the relevant merchant or payment provider to review it", "Contact the official support channel, explain the difference, and request a written response/reference number.", "The responsible party depends on whether the wrong amount appears on the bill or on the payment transaction.")
        step("Consider consumer grievance support if the merchant issue remains unresolved", "Review the National Consumer Helpline's official options and conditions before filing.", "The helpline is a pre-litigation consumer grievance mechanism and cannot guarantee a result.", ["national_consumer_helpline"])
        step("Review formal consumer-commission filing if earlier steps do not resolve the issue", "Check e-Jagriti's official filing help documents and confirm the appropriate case type and documents before proceeding.", "Formal filing requirements depend on the case. This app does not determine eligibility or submit the case.", ["e_jagriti"])
    elif canonical == "Order paid but not received":
        step("Collect order and payment details", "Keep the order ID, promised delivery date, receipt, transaction reference and any messages from the merchant together. Do not include a UPI PIN or OTP.", "The order record and transaction record serve different purposes; both may help explain the issue.")
        step("Contact the merchant through its official channel", "Request a delivery update or cancellation/refund status and save the response or complaint acknowledgement.", "The merchant is usually the first point of contact for a missing order; payment support may be needed if the transaction itself is disputed.")
        step("Consider the National Consumer Helpline if the consumer grievance remains unresolved", "Review the official NCH portal or contact 1915 / WhatsApp +91 88000 1915.", "NCH is an official pre-litigation route and does not guarantee the requested remedy.", ["national_consumer_helpline"])
        step("If still unresolved, review the formal consumer-commission route", "Use e-Jagriti's official help documents to review case-filing steps and documents before deciding whether to proceed.", "Formal filing has separate requirements; BolKeResolve does not determine eligibility or file a case for you.", ["e_jagriti"])
    else:
        step("Confirm the issue and relevant organisation", "Check the transaction receipt and identify whether the problem is with a bank/payment app, merchant order or unauthorised payment. Select a more specific issue type if one applies.", "More precise classification helps avoid directing you to the wrong process.")
        step("Contact the organisation through its official support channel", "Describe what happened, provide the relevant reference number and ask for a complaint acknowledgement. Keep copies of your correspondence.", "This is a general record-keeping step, not a finding about who is responsible.")
        step("Consider the relevant official consumer grievance route", "For a consumer/merchant service issue, review the National Consumer Helpline. For a complaint against an eligible RBI-regulated entity, review RBI's current Integrated Ombudsman Scheme after first approaching that entity.", "Different routes have different eligibility and waiting-period requirements; the app cannot determine eligibility without complete details.", ["national_consumer_helpline", "rbi_ombudsman_2026", "e_jagriti"])

    if canonical not in {"Suspected fraud or unauthorised transaction"} and contacted_support is False:
        # The first official escalation may be the provider directly; no automatic RBI escalation.
        pass
    if canonical in {"Failed UPI payment", "UPI payment pending / recipient not credited"}:
        missing.append("UPI transaction/reference ID (store it privately; do not publish it in a demo)")
    if not steps:
        steps.append({"title": "Add details", "detail": "Share a little more about what happened so the next steps can be tailored.", "why": "The current information is not enough to choose a specific playbook.", "source_ids": [], "priority": "normal"})

    # Fastest Safe Path asks at most one decision-changing question at a time.
    # Structured options are intentionally restricted to explicit user confirmations;
    # the app does not infer the answer or claim to verify a payment externally.
    question = ""
    next_question: dict[str, Any] | None = None
    if urgent:
        # Urgent safety guidance must not be delayed by intake questions. The user can
        # update support-contact details later in the saved case if helpful.
        question = ""
        next_question = None
    elif canonical == "Merchant settlement not credited":
        question = "In your Razorpay Dashboard, open Transactions → Payments, select an affected captured Payment ID and open its settlement_id (or use the Settlements view). What status is shown for the affected amount?"
        next_question = {
            "id": "confirm_merchant_settlement_status", "field": "settlement_status", "prompt": question,
            "why_it_matters": "A merchant settlement is not an ecommerce refund. The Dashboard status (Created, Initiated, Processed, Failed or On hold) determines whether to check the schedule, trace a UTR, or resolve a failed/held settlement.",
            "step": 1, "options": [
                {"value": "created", "label": "Created"},
                {"value": "initiated", "label": "Initiated / Processing"},
                {"value": "processed", "label": "Processed"},
                {"value": "failed", "label": "Failed"},
                {"value": "on_hold", "label": "On hold"},
                {"value": "no_record", "label": "No settlement entry"},
            ], "priority": "route_changing",
        }
    elif payment_status == "successful" and (
        _contains(text, "failed upi", "upi failure", "transaction failed", "payment failed", "upi fail", "declined", "यूपीआई असफल", "भुगतान असफल", "पेमेंट फेल", "लेन-देन असफल")
        or _contains(text, "pending", "processing", "beneficiary not credited", "recipient not credited", "recipient has not received", "पेंडिंग", "लंबित", "প্রলম্বিত", "நிலுவையில்", "పెండింగ్", "ಬಾಕಿ", "ਬਕਾਇਆ")
    ):
        story_status = "failed" if _contains(text, "failed upi", "upi failure", "transaction failed", "payment failed", "upi fail", "declined", "यूपीआई असफल", "भुगतान असफल", "पेमेंट फेल", "लेन-देन असफल") else "pending"
        question = f"Your story describes the payment as {story_status}, but you selected Successful. What does the payment app actually show?"
        next_question = {
            "id": "resolve_status_conflict", "field": "payment_status", "prompt": question,
            "why_it_matters": "We should not select a failed/pending-payment process while the reported status conflicts. Choose only the current status shown in the app; if the story has a transcription mistake, use “Edit my story” below.",
            "step": 2, "options": [
                {"value": "failed", "label": "It shows Failed"},
                {"value": "pending", "label": "It shows Pending"},
            ], "priority": "route_changing",
        }
    elif payment_status == "unknown" and canonical in {"Failed UPI payment", "UPI payment pending / recipient not credited"}:
        question = "What exact status does the payment app show: failed, pending, or successful?"
        next_question = {
            "id": "confirm_payment_status", "field": "payment_status", "prompt": question,
            "why_it_matters": "A failed transfer, a pending transfer and a successful payment can follow different processes. Choose only what the app actually shows.",
            "step": 2, "options": [
                {"value": "failed", "label": "Failed"},
                {"value": "pending", "label": "Pending"},
                {"value": "successful", "label": "Successful"},
            ], "priority": "route_changing",
        }
    elif contacted_support is None:
        question = "Have you already contacted the merchant, payment app or bank about this?"
        next_question = {
            "id": "confirm_support_contact", "field": "contacted_support", "prompt": question,
            "why_it_matters": "If you have already contacted them, we can focus on following up on that record instead of starting from scratch.",
            "step": 2, "options": [
                {"value": "no", "label": "Not yet"},
                {"value": "yes", "label": "Yes, I have a reference or reply"},
            ], "priority": "route_changing",
        }


    if urgent:
        fastest_path = {
            "mode": "urgent", "label": "SAFETY FIRST · ACT NOW",
            "title": "Contact your bank/provider and report suspected fraud now",
            "reason": "Do not wait for more questions or for this app to finish preparing a case.",
        }
    elif next_question and next_question.get("id") == "confirm_merchant_settlement_status":
        fastest_path = {
            "mode": "clarify", "label": "MERCHANT SETTLEMENT · CHECK THE LEDGER",
            "title": "Check the Razorpay settlement status",
            "reason": "We have identified a gateway-to-business payout issue. One Dashboard status will determine the correct trace; you do not need to answer order or return questions.",
        }
    elif next_question and next_question.get("id") in {"confirm_payment_status", "resolve_status_conflict"}:
        fastest_path = {
            "mode": "clarify", "label": "FASTEST SAFE PATH · ONE ANSWER",
            "title": "Confirm the status before choosing the route",
            "reason": next_question["why_it_matters"],
        }
    elif contacted_support is True:
        fastest_path = {
            "mode": "follow_up", "label": "FASTEST SAFE PATH · CONTINUE THE THREAD",
            "title": steps[0]["title"], "reason": steps[0].get("why", rationale),
        }
    elif next_question and next_question.get("id") == "confirm_support_contact":
        fastest_path = {
            "mode": "clarify", "label": "FASTEST SAFE PATH · ONE ANSWER",
            "title": "Continue from where you are",
            "reason": "We only need to know whether a support conversation is already open. The rest of the case details can be added later.",
        }
    elif next_question:
        fastest_path = {
            "mode": "clarify", "label": "FASTEST SAFE PATH · ONE ANSWER",
            "title": "Answer one useful question to sharpen the next step",
            "reason": next_question["why_it_matters"],
        }
    else:
        fastest_path = {
            "mode": "act", "label": "FASTEST SAFE PATH · YOUR NEXT ACTION",
            "title": steps[0]["title"], "reason": steps[0].get("why", rationale),
        }

    sources = [SOURCES[sid] for sid in sorted(sources_used)]
    return {
        "engine": "bolkeresolve_rules_v1",
        "rulebook": rulebook_metadata(canonical, payment_status, description),
        "generated_at": date.today().isoformat(),
        "classification": {"issue_type": canonical, "confidence": confidence, "rationale": rationale},
        "urgency": {"level": "urgent" if urgent else "standard", "label": "Act now" if urgent else "Next steps", "message": "If this may be an unauthorised/fraudulent transaction, contact your bank/payment provider and report it immediately. Do not wait for this assistant." if urgent else "These are guided next steps based on what you told us, not a verification of your transaction."},
        "summary": f"You reported: {description.strip()[:800]}",
        "facts": facts,
        "missing_information": list(dict.fromkeys(missing)),
        "clarifying_question": question,
        "next_question": next_question,
        "fastest_path": fastest_path,
        "recommended_steps": steps,
        "official_sources": sources,
        "safety_message": safety_message,
        "limits": ["BolKeResolve has not checked your bank, UPI app or merchant records.", "These steps are guidance, not a guarantee of refund or resolution.", "Official procedures and time limits can change; open the source before acting.", "Do not paste OTPs, UPI PINs, passwords, full card numbers or other authentication secrets."],
    }


_REPLY_PATTERNS = {
    "credential_or_remote_access_request": {
        "label": "Potentially unsafe request",
        "meaning": "The message may be asking you to share an authentication secret, install remote-access software, or pay a fee to release a refund.",
        "next_step": "Do not share OTPs, UPI PINs, passwords or card security codes; do not install remote-access apps or pay an unsolicited release fee. Verify the sender through the organisation's official app or website. If you shared a secret or suspect fraud, contact your bank immediately and use the official cyber-fraud reporting route.",
        "priority": "urgent",
    },
    "refund_claimed_credited": {
        "label": "Refund credit is claimed",
        "meaning": "The reply appears to say the refund was credited. This message alone does not prove the money reached your account.",
        "next_step": "Check your own bank/payment-app transaction history. Only mark the case resolved if you can confirm the credit yourself. If it is missing, ask the organisation for the refund reference and expected credit timeline.",
        "priority": "normal",
    },
    "refund_claimed_initiated": {
        "label": "Refund initiation is claimed",
        "meaning": "The reply appears to say that a refund was initiated or processed, but it does not independently confirm that the amount reached your account.",
        "next_step": "Ask for the refund reference (such as the reference/ARN/RRN if applicable) and expected credit date if those are missing. Compare that information with your own account history before changing the case to resolved.",
        "priority": "normal",
    },
    "more_information_requested": {
        "label": "More information requested",
        "meaning": "The reply appears to ask for additional details or documents.",
        "next_step": "Identify exactly which document or reference is requested. Share only relevant information through the organisation's verified official channel and redact unrelated personal data. Never send an OTP or UPI PIN.",
        "priority": "normal",
    },
    "rejected_or_closed": {
        "label": "Rejected or marked closed",
        "meaning": "The reply appears to reject the request or say that the case is closed. The classification may miss context, so check the original wording.",
        "next_step": "Read the stated reason, preserve the reply and reference number, and identify any missing evidence or review route. Check current eligibility and deadlines on the relevant official source before escalating.",
        "priority": "normal",
    },
    "under_review": {
        "label": "Under review / escalated",
        "meaning": "The reply appears to say that the issue is being investigated, reviewed or escalated.",
        "next_step": "Save the ticket/reference number and any stated response date. If no date is given, ask for one and set a follow-up you control. Do not interpret 'under review' as approval or a confirmed refund.",
        "priority": "normal",
    },
    "waiting_period_stated": {
        "label": "A waiting period is stated",
        "meaning": "The reply appears to ask you to wait for a stated period. This may be a support estimate, not a universal regulatory deadline.",
        "next_step": "Record the date/period the organisation stated and set a follow-up after it. Check the official rules applicable to your specific transaction before relying on the estimate.",
        "priority": "normal",
    },
    "acknowledgement_only": {
        "label": "Acknowledgement only",
        "meaning": "The reply appears to acknowledge receipt or provide a ticket/reference number without describing a resolution.",
        "next_step": "Keep the reference number with this case. If no response timeline is stated, ask when you should expect an update and set a follow-up.",
        "priority": "normal",
    },
    "mixed_or_conflicting_reply": {
        "label": "Mixed signals — check the original",
        "meaning": "The text appears to combine statements that may conflict, such as a refund being processed while the request is also described as rejected. Quoted older messages can also cause this result.",
        "next_step": "Read the full original message and identify the latest statement and any quoted history. Do not assume the issue is resolved or rejected from this classification alone. If unclear, ask the organisation to state the current status in writing.",
        "priority": "normal",
    },
    "needs_manual_review": {
        "label": "Needs your review",
        "meaning": "The wording did not clearly match a supported reply pattern. BolKeResolve will not guess what the organisation decided.",
        "next_step": "Read the original reply, identify what the organisation says it did and what it asks you to do next, then save your own short summary and reference. If unclear, ask the organisation to clarify through its official channel.",
        "priority": "normal",
    },
}


def review_support_reply(reply_text: str) -> dict[str, Any]:
    """Conservatively classify user-pasted support text without asserting external truth.

    The caller must redact sensitive patterns before invoking this function. This function
    returns only a category and next-step guidance; it must never persist or echo the reply.
    """
    text = re.sub(r"\s+", " ", str(reply_text or "")).strip().lower()
    if not text:
        key = "needs_manual_review"
    else:
        # Do not flag safety notices that warn the customer *not* to share credentials.
        negated_warning = bool(re.search(
            r"\b(?:never|do not|don't|dont|should not|shouldn't|will not|won't)\b.{0,48}\b(?:share|send|provide|tell|enter|install|pay)\b.{0,48}\b(?:otp|one[- ]time password|upi[ -]?pin|pin|password|cvv|anydesk|teamviewer|remote access|fee)\b|\b(?:otp|one[- ]time password|upi[ -]?pin|pin|password|anydesk|teamviewer)\b.{0,35}\b(?:mat|nahi|na karein|na kare|kabhi nahi)\b|\b(?:kabhi|bilkul)?\s*(?:mat|nahi|na)\b.{0,35}\b(?:share|bhej|bata|install|pay)\w*\b.{0,35}\b(?:otp|upi pin|pin|password|anydesk|fee)\b",
            text,
        ))
        asks_secret = bool(re.search(
            r"\b(?:send|share|provide|tell us|enter|confirm|verify)\s+(?:us\s+|to us\s+)?(?:your\s+)?(?:otp|one[- ]time password|upi[ -]?pin|pin|password|cvv|security code)\b|\b(?:install|download)\s+(?:the\s+)?(?:anydesk|teamviewer|air[d ]roid|remote access|screen.?sharing)\b|\bpay\s+(?:a\s+)?(?:refund|release|processing|verification|unlocking)\s+fee\b|\b(?:otp|one[- ]time password|upi pin|pin|password)\s+(?:bhejo|bhejein|batao|batayein|share karo|share karein|send karo)\b|\b(?:apna|apni|aapka|aapki)\s+(?:otp|upi pin|pin|password)\b.{0,25}\b(?:bhejo|bhejein|batao|batayein|share karo|share karein)\b|\b(?:anydesk|teamviewer)\b.{0,25}\b(?:install karo|download karo|install karein|download karein)\b|\b(?:refund|paisa)\b.{0,45}\b(?:processing fee|release fee|verification fee)\b",
            text,
        ))
        credit_claim = bool(re.search(r"\b(refund|reversal|amount)\b.{0,50}\b(credited|received in your account|deposited|reflected in your account)\b|\b(credited|deposited)\b.{0,50}\b(refund|reversal|amount|account)\b|\brefund\b.{0,45}\b(account mein|account me|paise|paisa)\b.{0,25}\b(aa gaya|aa gaye|credit ho gaya|credit ho gaye|jama ho gaya)\b", text))
        initiation_claim = bool(re.search(r"\b(refund|reversal)\b.{0,55}\b(initiated|processed|issued|sent|triggered|approved)\b|\b(initiated|processed|issued|triggered)\b.{0,45}\b(refund|reversal)\b|\brefund\b.{0,40}\b(initiate|process|bhej|issue)\w*\b.{0,22}\b(kar diya|ho gaya|ho gayi|kar diya hai|kar diya gaya)\b", text))
        rejection_claim = bool(re.search(r"\b(rejected|declined|denied|cannot approve|can't approve|not eligible|case closed|complaint closed|request closed|not admissible)\b", text))
        under_review_claim = bool(re.search(r"\b(under review|being reviewed|investigat(?:e|ing|ion)|escalated|forwarded to the concerned|sent to the concerned team|working on your case)\b", text))
        if asks_secret and not negated_warning:
            key = "credential_or_remote_access_request"
        elif rejection_claim and (credit_claim or initiation_claim or under_review_claim):
            key = "mixed_or_conflicting_reply"
        elif credit_claim and initiation_claim:
            key = "mixed_or_conflicting_reply"
        elif credit_claim:
            key = "refund_claimed_credited"
        elif initiation_claim:
            key = "refund_claimed_initiated"
        elif re.search(r"\b(please provide|please upload|submit|send us|share|attach|need.{0,12}(?:document|details|information|invoice|receipt|statement)|additional (?:documents|information|details)|supporting documents|documents upload karein|invoice bhejein|details bhejein|details submit karein|proof bhejein)\b", text):
            key = "more_information_requested"
        elif rejection_claim:
            key = "rejected_or_closed"
        elif under_review_claim:
            key = "under_review"
        elif re.search(r"\b(wait|wait for|allow|within|business days|working days|hours|days to reflect|processing time|please be patient|intezar karein|intazaar karein|wait karein|wait kijiye|din mein|din me|ghante mein|ghante me|din lagenge)\b", text):
            key = "waiting_period_stated"
        elif re.search(r"\b(received your complaint|complaint received|ticket (?:number|id)|reference number|case id|service request|acknowledg(?:e)?ment|registered successfully|we have received|complaint register ho gayi|shikayat darj|ticket number hai)\b", text):
            key = "acknowledgement_only"
        else:
            key = "needs_manual_review"
    selected = _REPLY_PATTERNS[key]
    return {
        "engine": "reply_review_rules_v1",
        "category": key,
        "label": selected["label"],
        "interpretation": selected["meaning"],
        "next_step": selected["next_step"],
        "priority": selected["priority"],
        "is_automatic_decision": False,
        "user_confirmation_required": True,
        "limitations": [
            "This is a first-pass text interpretation, not proof that the organisation did what it says.",
            "Review the original sender and full message before acting.",
            "The original reply text is not returned for storage by this function; keep an original copy only if you choose to store it as evidence.",
        ],
    }
