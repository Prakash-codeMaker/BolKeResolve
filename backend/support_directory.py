"""Curated official support destinations for BolKeResolve action plans.

Only public, first-party or government URLs belong here. Links are guidance, not a claim
that BolKeResolve contacted the organisation or filed a complaint. Review this directory
periodically because providers can change their processes.
"""
from __future__ import annotations

from typing import Any
import re

REVIEWED_ON = "2026-11-03"

# Use official entry points and explain when the user must act inside their signed-in app.
PLATFORMS: list[dict[str, Any]] = [
    {
        "id": "google_pay", "name": "Google Pay", "aliases": ["google pay", "gpay", "googlepay"],
        "url": "https://support.google.com/pay/india/answer/7562363?hl=en",
        "label": "Open Google Pay support", "action": "Open the Google Pay app → profile photo → Get help → Contact Support. Choose the issue shown in your transaction.",
        "note": "Google Pay says chat support is available 8 AM–12 AM IST. Follow authentication steps only inside the official app; never share UPI PINs or ordinary OTPs with someone claiming to be support.",
    },
    {
        "id": "paytm", "name": "Paytm", "aliases": ["paytm"],
        "url": "https://paytm.com/company/grievance",
        "label": "Open Paytm grievance guidance", "action": "Start with Help & Support in the Paytm app and keep the ticket number. Use the official grievance policy if the first route does not resolve the issue within its stated process.",
        "note": "The published policy may require an earlier support ticket before escalation. Check the current policy for the specific Paytm product.",
    },
    {
        "id": "phonepe", "name": "PhonePe", "aliases": ["phonepe", "phone pe"],
        "url": "https://support.phonepe.com/",
        "label": "Open PhonePe support", "action": "Open the PhonePe app → History → select the transaction → Contact PhonePe Support. Use the grievance policy only when its escalation conditions fit your case.",
        "note": "For UPI transactions, the account-holding bank/payment route may be needed depending on the issue. PhonePe's policy recommends first contacting the merchant for purchase disputes, then the bank or NPCI where appropriate.",
    },
    {
        "id": "flipkart", "name": "Flipkart", "aliases": ["flipkart"],
        "url": "https://www.flipkart.com/helpcentre",
        "label": "Open Flipkart Help Centre", "action": "In the Flipkart app, sign in → Account → Orders → select the order → Help (top right) → Chat with us. On the website, sign in → 24x7 Customer Care → select the order/issue → Chat with us.",
        "note": "Order-specific support may require signing into the account that placed the order. Do not use phone numbers found in unrelated search results.",
    },
    {
        "id": "amazon_india", "name": "Amazon India", "aliases": ["amazon", "amazon.in"],
        "url": "https://www.aboutamazon.in/news/operations/contact-amazon-india-customer-service",
        "label": "Open Amazon India support instructions", "action": "Use Amazon.in Customer Service, sign in, choose the relevant order or payment issue, and select the available chat or callback option.",
        "note": "Use a link reached from Amazon's official site or app; support options can depend on the order and account.",
    },
    {
        "id": "meesho", "name": "Meesho", "aliases": ["meesho", "मीशो"],
        "url": "https://www.meesho.com/adult-support/pl/9o6",
        "label": "Open Meesho Help Center guidance", "action": "In the Meesho app, open Account → Help Center → choose the relevant order. Use the order-specific support options shown there (for example, chat or callback where available).",
        "note": "Meesho says the official customer-care contact option is available inside the app for the chosen order. Do not use phone numbers found in unrelated search results.",
    },
    {
        "id": "blinkit", "name": "Blinkit", "aliases": ["blinkit", "ब्लिंकिट"],
        "url": "https://blinkit.com/terms",
        "label": "Open Blinkit's official terms and support route", "action": "Open Customer Support in the Blinkit app or website and select the affected order. For permitted returns/cancellations, check the order-specific policy and upload the requested photo/video proof.",
        "note": "Blinkit states that order issues should first go through in-app chat support and that it has no official customer-care phone line. Its terms describe different return windows by item category; check the current order and item policy rather than assuming one universal window.",
    },
    {
        "id": "zepto", "name": "Zepto", "aliases": ["zepto", "ज़ेप्टो", "जेप्टो"],
        "url": "https://www.zepto.com/s/terms-of-service",
        "label": "Open Zepto's official terms and support route", "action": "Start with chat support on the Zepto app for the affected order. If the issue remains unresolved, use the grievance route published in Zepto's current terms and quote the earlier complaint details.",
        "note": "Zepto's terms publish support@zepto.com and a Grievance cum Nodal Officer route. Confirm the current officer details on the official terms page before sending a formal escalation.",
    },
    {
        "id": "zomato", "name": "Zomato", "aliases": ["zomato", "zomato.com", "जोमैटो", "ज़ोमैटो"],
        "url": "https://www.zomato.com/policies/terms-of-service/",
        "label": "Open Zomato's official support and grievance policy", "action": "Start with chat support on the Zomato app for the exact order. If needed, write to order@zomato.com and retain the ticket number; the current terms describe a further grievance escalation using that ticket reference.",
        "note": "The grievance policy and timings can change. Recheck the current official terms before using a phone number or formal escalation.",
    },
    {
        "id": "swiggy", "name": "Swiggy", "aliases": ["swiggy", "instamart"],
        "url": "https://www.swiggy.com/swiggy_customer_care",
        "label": "Open Swiggy's official support guidance", "action": "Use support inside the Swiggy app for the relevant order. Keep the order ID and any refund/status response.",
        "note": "Swiggy explicitly warns that it does not have an official customer-care phone line; use in-app support and beware of fake numbers.",
    },
    {
        "id": "uber", "name": "Uber", "aliases": ["uber", "uber eats"],
        "url": "https://help.uber.com/riders/article/about-india-customer-support?nodeId=42a24d9b-ef73-40a5-9bdf-b6e48790569e",
        "label": "Open Uber support", "action": "Choose the trip in the Uber app, open Help, and select the payment or fare issue that matches your case.",
        "note": "Trip-specific assistance may require the account used for the trip. If access is unavailable, use the official web help page.",
    },
    {
        "id": "makemytrip", "name": "MakeMyTrip", "aliases": ["makemytrip", "make my trip", "mmt"],
        "url": "https://www.makemytrip.com/support/contact-us.php?q1=html",
        "label": "Open MakeMyTrip support", "action": "Use My Trips for e-ticket, cancellation and refund-status questions; choose the relevant booking before raising a request.",
        "note": "Refund handling depends on the booking and the supplier. This link does not indicate that a refund has been initiated.",
    },
    {
        "id": "razorpay", "name": "Razorpay", "aliases": ["razorpay", "razor pay", "razor-pay", "रेज़रपे", "रेजरपे"],
        "url": "https://razorpay.com/support/",
        "label": "Open Razorpay merchant support",
        "action": "Sign in to the Razorpay Dashboard. Open Transactions → Payments, select an affected Payment ID, inspect its settlement details and open the settlement_id for the breakdown. Record the status, scheduled date and UTR if present. For a failed or held settlement, check the registered email and Dashboard notification. If unresolved, raise a support ticket through the signed-in Dashboard or Razorpay official support page.",
        "note": "Razorpay distinguishes Created, Initiated, Processed and Failed settlement states. A processed settlement has a bank UTR; a failed settlement may involve inactive/frozen bank details or bank rejection; an on-hold settlement may require a Dashboard Resolve action. The user's account-specific settlement cycle and bank working days must be checked—do not assume one universal deadline.",
    },
    {
        "id": "irctc", "name": "IRCTC", "aliases": ["irctc", "indian railway catering"],
        "url": "https://equery.irctc.co.in/irctc_equery/",
        "label": "Open IRCTC eQuery", "action": "Use IRCTC's official eQuery/support route and include the ticket/transaction references requested by that service.",
        "note": "Do not include passwords or OTPs in a complaint draft.",
    },
]

NCH = {
    "id": "national_consumer_helpline", "name": "National Consumer Helpline", "url": "https://consumerhelpline.gov.in/public/index.php/contact",
    "label": "Open National Consumer Helpline", "action": "Consider NCH for a consumer-service complaint after reviewing its current scope and instructions. The portal/WhatsApp process asks for grievance details and may issue a docket number when registration is completed.",
    "note": "BolKeResolve does not submit an NCH grievance. You will complete the official process yourself and keep the acknowledgement/docket number.",
}
NPCI = {
    "id": "npci_upi", "name": "NPCI UPI", "url": "https://www.npci.org.in/register-a-complaint",
    "label": "Open NPCI UPI complaint route", "action": "For a supported UPI complaint, check the product and transaction type first and have the official reference details requested by NPCI available.",
    "note": "NPCI states that fraudulent, unidentified or unauthorised transactions should be raised with the customer's bank. The relevant member bank/institution is responsible for redressal; check eligibility and fields before proceeding.",
}
CYBERCRIME = {
    "id": "cybercrime_india", "name": "National Cyber Crime Reporting Portal", "url": "https://cybercrime.gov.in/",
    "label": "Open National Cyber Crime Reporting Portal", "action": "If you suspect an unauthorised transaction or financial cyber fraud, contact your bank/payment provider immediately and use the official cybercrime reporting route. In India, the cyber-financial-fraud helpline is 1930.",
    "note": "Urgent safety guidance takes priority. Do not wait to finish a BolKeResolve case, and never share an OTP, UPI PIN, password or remote-access code.",
}
RBI = {
    "id": "rbi_ombudsman", "name": "RBI Complaint Management System", "url": "https://cms.rbi.org.in/",
    "label": "Open RBI Complaint Management System", "action": "Consider the RBI complaint route only for covered regulated entities and when the applicable prior-contact, waiting-period and eligibility requirements are satisfied.",
    "note": "RBI's 2026 scheme FAQ says the contact centre guides people on the process but does not itself file a complaint. Check current eligibility before using this route.",
}




NCH_CONVERGENCE_DIRECTORY_URL = "https://consumerhelpline.gov.in/public/convergencepartners"
NCH_CONVERGENCE_REVIEWED_ON = "2026-10-23"

# Reviewed snapshot of selected entries visible in the official NCH convergence
# directory on the date above. This is deliberately not exhaustive or live.
NCH_CONVERGENCE_SNAPSHOT: dict[str, dict[str, str]] = {
    "zomato": {"brand": "Zomato", "legal_name": "ETERNAL LIMITED"},
    "phonepe": {"brand": "PhonePe", "legal_name": "Phonepe Private limited"},
    "amazon": {"brand": "Amazon.in", "legal_name": "Amazon Seller Services Private Limited"},
    "flipkart": {"brand": "Flipkart.com", "legal_name": "Flipkart Internet Private Limited"},
    "swiggy": {"brand": "Swiggy", "legal_name": "BUNDL Technologies Private Limited"},
    "paytm": {"brand": "Paytm.com", "legal_name": "One97 Communications Pvt. Limited"},
    "uber": {"brand": "Uber", "legal_name": "Uber India Systems Private Limited"},
    "makemytrip": {"brand": "MakeMyTrip.com", "legal_name": "MakeMyTrip India Pvt Ltd"},
    "irctc": {"brand": "IRCTC- Air Ticketing", "legal_name": "Indian Railway Catering & Tourism Corporation Limited"},
}

_NCH_MERCHANT_ALIASES = {
    "zomato": "zomato", "zomatocom": "zomato", "wwwzomatocom": "zomato", "eternallimited": "zomato",
    "phonepe": "phonepe", "phonepecom": "phonepe", "phonepeprivatelimited": "phonepe",
    "amazon": "amazon", "amazonin": "amazon", "amazonincom": "amazon", "amazonsellerservicesprivatelimited": "amazon",
    "flipkart": "flipkart", "flipkartcom": "flipkart", "wwwflipkartcom": "flipkart", "flipkartinternetprivatelimited": "flipkart",
    "swiggy": "swiggy", "swiggycom": "swiggy", "wwwswiggycom": "swiggy", "bundltechnologiesprivatelimited": "swiggy",
    "paytm": "paytm", "paytmcom": "paytm", "one97communicationspvtlimited": "paytm",
    "uber": "uber", "ubercom": "uber", "uberindiasystemsprivatelimited": "uber",
    "makemytrip": "makemytrip", "makemytripcom": "makemytrip", "makemytripindiapvtltd": "makemytrip",
    "irctc": "irctc", "irctcairticketing": "irctc", "indianrailwayscateringtourismcorporationlimited": "irctc",
}

def find_nch_convergence_match(merchant: str = "") -> dict[str, str]:
    """Compare a merchant name against a dated, selected snapshot of the official NCH directory."""
    raw = str(merchant or "").strip()
    normalized = re.sub(r"[^a-z0-9]+", "", raw.casefold())
    key = _NCH_MERCHANT_ALIASES.get(normalized)
    base = {
        "source_url": NCH_CONVERGENCE_DIRECTORY_URL,
        "reviewed_on": NCH_CONVERGENCE_REVIEWED_ON,
        "merchant_input": raw,
    }
    if key and key in NCH_CONVERGENCE_SNAPSHOT:
        item = NCH_CONVERGENCE_SNAPSHOT[key]
        return {
            **base,
            "status": "listed_in_reviewed_snapshot",
            "matched_brand": item["brand"],
            "legal_name": item["legal_name"],
            "message": (
                f"{item['brand']} appears in BolKeResolve's reviewed snapshot of the public NCH "
                f"convergence directory as {item['legal_name']}. This does not mean your individual "
                "grievance was registered, guarantee a response, or make BolKeResolve an NCH partner."
            ),
        }
    return {
        **base,
        "status": "not_matched_in_reviewed_snapshot",
        "matched_brand": "",
        "legal_name": "",
        "message": (
            "No exact match was found in BolKeResolve's small reviewed snapshot. This does not mean "
            "the organisation is absent from the full, live NCH directory; check the official directory before deciding."
        ),
    }


def find_support_destinations(merchant: str = "", description: str = "", issue_type: str = "") -> list[dict[str, str]]:
    """Return a maximum of two official routes, specific-first, based on user-reported context."""
    text = f"{merchant or ''} {description or ''} {issue_type or ''}".casefold()
    result: list[dict[str, str]] = []
    matched = None
    # Avoid broad substring matches such as 'mmt' inside another token.
    for item in PLATFORMS:
        aliases = item["aliases"]
        if any((f" {alias} " in f" {text} ") if " " in alias else re.search(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", text) for alias in aliases):
            matched = item
            break
    def copy_item(item: dict[str, Any]) -> dict[str, str]:
        return {key: str(item[key]) for key in ("id", "name", "url", "label", "action", "note")}
    t = text
    urgent = any(token in t for token in ("unauthorised", "unauthorized", "unrecognised", "unrecognized", "fraud", "scam", "मैंने नहीं", "अनधिकृत", "धोखाधड़ी", "फ्रॉड"))
    is_upi = any(token in t for token in ("upi", "npci", "recipient not credited", "payment pending", "failed upi", "यूपीआई", "पैसे कट"))
    issue_key = (issue_type or "").casefold()
    funds_to_business_account = bool(re.search(
        r"(?:extract|withdraw|transfer|settle|payout|settlement).{0,100}(?:from|through|via)\s+razor\s*pay|"
        r"razor\s*pay.{0,120}(?:to|into)\s+(?:my|our|business|company)\s+(?:bank\s+)?account|"
        r"customer payments?.{0,100}(?:business|company)\s+(?:bank\s+)?account",
        text,
    ))
    business_settlement_issue = (
        "merchant settlement not credited" in issue_key
        or "merchant_settlement" in issue_key
        or any(token in t for token in ("merchant settlement", "settlement", "payout", "gateway balance", "customer collections"))
        or funds_to_business_account
    )
    consumer_issue = (not business_settlement_issue) and any(token in t for token in ("refund", "order", "merchant", "delivery", "service", "consumer", "रिफंड", "ऑर्डर", "डिलीवरी"))
    # Safety-first routes must lead; a brand-specific support route must not push urgent
    # unauthorised-payment guidance below the fold.
    if urgent:
        result.append(copy_item(CYBERCRIME))
        if matched and matched["id"] != CYBERCRIME["id"]:
            result.append(copy_item(matched))
        return result[:2]
    if matched:
        result.append(copy_item(matched))
    if is_upi and len(result) < 2:
        result.append(copy_item(NPCI))
    elif consumer_issue and len(result) < 2:
        result.append(copy_item(NCH))
    # The RBI route is deliberately not auto-added: eligibility depends on entity and prior steps.
    return result[:2]


def build_quick_support_draft(merchant: str, issue_type: str, description: str, amount: float | None = None) -> dict[str, str]:
    """Create an editable, non-submitted support draft from user-confirmed/scrubbed context."""
    organisation = (merchant or "the support team").strip() or "the support team"
    issue = (issue_type or "payment or consumer issue").strip()
    story = " ".join((description or "").split())[:1200]
    amount_line = f"\nAmount involved: ₹{amount:g} (as reported by me)." if amount is not None else ""
    no_response_reported = any(phrase in story.casefold() for phrase in ("no response", "no reply", "haven't heard back", "have not heard back"))
    if issue == "Merchant settlement not credited":
        amount_text = f"₹{amount:,.2f}".rstrip("0").rstrip(".") if amount is not None else "[Amount]"
        message = (
            "Hello Razorpay Support,\n\n"
            f"I am a merchant using Razorpay and customer collections totalling {amount_text} have not reached my registered business bank account. "
            "This is a merchant settlement/payout query, not a customer order refund.\n\n"
            "Please confirm the settlement status, settlement ID, scheduled date and expected credit date. "
            "If the settlement is marked Processed, please share/confirm the UTR so my bank can trace it. "
            "If it is Failed or On hold, please explain the exact reason and the action/documents required. "
            "Please link this request to any earlier support ticket.\n\n"
            "Merchant ID: [Merchant ID]\nSettlement ID: [Settlement ID, if shown]\nPayment IDs: [Relevant Payment IDs]\nEarlier ticket: [Reference, if any]\n\n"
            "I can provide redacted settlement and payment reports through the signed-in Dashboard/support channel.\n\nThank you."
        )
    elif issue == "Refund not received" and no_response_reported:
        amount_text = f" of ₹{amount:,.2f}".rstrip("0").rstrip(".") if amount is not None else ""
        message = (
            f"Hello {organisation} Support,\n\n"
            f"I am following up on the refund{amount_text} for my order [Order ID]. "
            "The refund has not reached the original payment method. I previously contacted support, "
            "but I have not received a response yet.\n\n"
            "Please confirm: (1) whether the refund has been processed, (2) the processing date, "
            "(3) the refund reference / ARN / UTR / RRN if one has been generated, "
            "(4) the expected credit date, and (5) the support ticket or acknowledgement number.\n\n"
            "I can share the order, cancellation and original payment references through this official support channel. "
            "Please keep this follow-up linked to my earlier complaint.\n\nThank you."
        )
    else:
        message = (
            f"Hello {organisation} Support,\n\n"
            f"I need help with the following issue: {issue}.\n"
            f"What happened: {story}{amount_line}\n\n"
            "Please confirm the current status, tell me whether any information is still needed, "
            "and share a support/reference number and the expected next update. I can provide "
            "order or transaction references through your official secure channel.\n\n"
            "Thank you."
        )
    return {
        "subject": f"Support request: {issue}",
        "message": message,
        "notice": "Draft only. Review and edit it before sending. BolKeResolve has not contacted the organisation.",
    }
