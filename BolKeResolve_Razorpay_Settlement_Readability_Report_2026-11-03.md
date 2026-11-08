# BolKeResolve — Razorpay Settlement Classification & Readability Update

**Date:** 3 November 2026  
**Build:** `india-payments-2026.11.03.1` / Live Room shell `v40`

## What the screenshots revealed

The reported Razorpay issue describes money collected from several customers through a payment gateway, followed by an inability to withdraw/settle those collections into the user's business bank account. This is a **merchant settlement not credited** case, not a consumer ecommerce order refund. The old generic payment/refund route could therefore ask irrelevant order questions and direct the user into an incorrect consumer complaint path.

The evidence-review screenshot also showed a narrow transcript editor within a much wider review panel, while saved-case screens inherited many 8–11px text rules from the older design stylesheet. Those sizes made labels, evidence details and instructions difficult to read.

## What changed in the source

### 1. Top-level financial issue classification

- Added/strengthened description-first detection for a payment-gateway merchant settlement: customer collections → payment gateway → merchant's business bank account.
- The classifier now selects `Merchant settlement not credited` even when the first user phrase contains the word “refund”, if the described funds flow clearly points to settlement into the business account.
- A refund that a merchant has issued to its own customer remains a separate `Refund not received` path.
- The saved case type, resolution classification and case title now use the merchant-settlement category.

### 2. A settlement-specific first question and status routes

The first question asks the user to inspect the affected payment in Razorpay Dashboard:

> Open Transactions → Payments, select an affected captured Payment ID and open its `settlement_id` (or use the Settlements view). What status is shown?

The workflow then branches based on the status the user reports:

- **Processed:** find the UTR in settlement details/report, compare it with the bank statement, and ask the bank to trace that UTR. If it cannot be traced, continue with Razorpay support using the settlement ID.
- **Failed:** inspect the failed settlement and registered Razorpay email for the failure reason and requested action; use signed-in support if unclear.
- **On hold:** inspect the Dashboard notification and any Resolve action; do not send credentials or KYC documents through an unsolicited contact.
- **No settlement record:** check whether the underlying customer payments are marked Captured in Transactions → Payments.
- **Created / Initiated:** compare the Dashboard's scheduled date with the account's configured cycle and working-day calendar. If the user's reported promise has passed, prepare a traceable support follow-up.

### 3. Merchant-specific support and evidence

- Razorpay is the only automatic support destination for this business-settlement case; the consumer helpline is not automatically added.
- The editable support draft identifies this as a merchant settlement/payout issue, not a customer order refund.
- The draft asks for settlement ID(s), current status, scheduled date, UTR if generated, failure/hold reason and earlier ticket reference.
- Evidence prompts request the affected settlement detail, settlement/payment report, relevant customer-payment IDs where required, and a redacted bank-statement section where appropriate.
- The app does not log into Razorpay, query the merchant account or verify whether funds arrived.

### 4. Official source corrections

The Razorpay Dashboard instructions now point to the Payment Details flow: Transactions → Payments → select Payment ID → open `settlement_id` for its detailed breakdown. The case also links the official Razorpay settlement FAQ. Razorpay's FAQ says its standard domestic settlement cycle is T+2 **working days** from capture, but also says the actual cycle can vary based on bank approval, business vertical and risk factors; the UTR is available in settlement details/report. The T+2 statement is a standard cycle, not a guarantee for every merchant account.

### 5. Readability and alignment

- Introduced a consistent type scale in `design-v2.css`: 16px base body text, 15px primary case copy and approximately 12.5px metadata.
- Increased case-detail instructions, step descriptions, facts, field labels, evidence descriptions, timeline copy and support drafts from the old 8–11px microtype rules.
- Standardized body line-height and set a readable measure for long-form copy.
- Set case controls to a more comfortable minimum height and made mobile case layouts use a single column.
- Increased Live Room transcript turns and guidance copy to readable sizes; metadata now has a 12px minimum in key places.
- Kept the audio transcript editor full-width within its review panel, with a useful minimum height and matching typography.
- Updated the service-worker cache to `bolkeresolve-shell-v40` so clients do not keep loading the previous stylesheet.

## Verification actually performed

- `python -m pytest -q`: **334 passed, 129 subtests passed**.
- `python -m compileall -q backend`: passed.
- `node --check frontend/app.js`: passed.
- API integration: `POST /api/cases` returned HTTP 201 for a synthetic Razorpay merchant-settlement story; stored issue type was `Merchant settlement not credited`; first question asked for settlement status via Payment ID/settlement ID; only the Razorpay support route was included; official settlement Dashboard and FAQ sources were attached; the generated support draft used the merchant-settlement subject.
- Regression tests assert that the Razorpay gateway funds-flow case does not get the National Consumer Helpline route and that the dashboard path points to Transactions → Payments.

## What was not verified

- No authenticated Razorpay account was connected; no settlement status or bank credit was checked.
- No physical microphone/camera/screen-share session was run.
- A browser screenshot review at desktop/tablet/mobile viewports was not completed in this environment. CSS/asset regression checks passed, but that is not the same as a visual browser review.
- Contrast ratios have not yet been programmatically audited against WCAG.

## Local installation

1. Extract the ZIP into a new folder.
2. Copy the existing `.env` into the new folder; do not overwrite or share API keys.
3. Run `run_windows.bat`.
4. Open `http://127.0.0.1:8000` and press `Ctrl + F5`.
5. Create a new test case using a synthetic settlement story. Do not upload real customer records or unredacted bank details for the first test.
