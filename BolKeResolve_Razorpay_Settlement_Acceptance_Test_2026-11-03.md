# Acceptance Tests — Razorpay Merchant Settlement & Readability (3 Nov 2026)

## A. New case classification

Use synthetic data only:

> We have not received ₹350 from Razorpay. We made several customer payments. When I try to withdraw the customer collections from Razorpay to our business bank account, it does not happen. Support said it would be settled in four days, but more than twelve days have passed.

Expected:
- Case type: `Merchant settlement not credited`.
- Not classified as a consumer order refund.
- First question points to Razorpay Dashboard → Transactions → Payments → affected captured Payment ID → `settlement_id` (or Settlements view) and asks for the status.
- Only Razorpay merchant support is auto-listed; no National Consumer Helpline route.
- Official Razorpay Dashboard documentation and settlement FAQ are linked.
- Support draft subject is about merchant settlement, not a missing order.

## B. Status-specific branches

Create or update the same synthetic case with each status:

| User-reported status | Expected next route |
|---|---|
| Processed | Locate UTR; compare it to bank statement; request bank trace if the credit is not visible |
| Failed | Inspect failure reason and registered Razorpay email; use official support if unclear |
| On hold | Inspect Dashboard notification/Resolve action; share documents only via signed-in official channel |
| No record | Check whether relevant customer payments are marked Captured |
| Created / Initiated | Compare Dashboard schedule and configured working-day cycle; if overdue, prepare a ticket with settlement ID/report |

BolKeResolve must label these as user-reported statuses until confirmed through a future authorised integration.

## C. Keep flows distinct

- A gateway refund that a merchant issued to its customer must stay in the customer-refund flow.
- A customer collection not transferred to the business bank must use merchant settlement.
- RazorpayX payouts should be a separately modelled workflow before the product claims support for all Razorpay transfers.
- A UPI transfer, card settlement, bank transfer and ecommerce order are not interchangeable.

## D. Readability / layout checks

- Body text displays at approximately 16px; primary case copy approximately 15px; metadata approximately 12.5px.
- Long case instructions wrap within a readable measure.
- Case details collapse to one column on small screens.
- Audio transcript editor uses the full review-panel width.
- Live Room turns, guidance, evidence labels and controls use readable sizes.
- Tab order, focus visibility, 200% text zoom and 320 CSS-pixel reflow must be manually checked in a browser.
- Contrast ratios must be measured; CSS source tests are not an accessibility audit.

## E. Commands run for this build

```bash
python -m pytest -q
python -m compileall -q backend
node --check frontend/app.js
```

Most recent automated run: **334 passed, 129 subtests passed**. A separate local FastAPI TestClient run returned HTTP 201 with `Merchant settlement not credited`, the dashboard settlement-status question, Razorpay-only support destination and both official settlement sources.

## F. Manual tests still required on the user's machine

1. Extract into a new folder and copy the existing `.env` securely.
2. Run `run_windows.bat` and hard-refresh with `Ctrl + F5`.
3. Create the synthetic Razorpay case above.
4. Inspect the new case title, first question, source links and support draft.
5. Test each settlement status from the status table.
6. Verify the physical microphone, transcript pause/commit, camera, screen share, clip recorder, stop/cancel and evidence persistence.
7. Open the case on desktop, tablet and a 320 CSS-pixel viewport; test 200% zoom and keyboard-only operation.

A real bank/gateway account was not queried and a full browser screenshot audit was not performed for this build.
