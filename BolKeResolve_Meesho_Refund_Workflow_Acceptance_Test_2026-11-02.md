# BolKeResolve — Meesho workflow acceptance test

## Test 1: exact two-turn refund scenario
1. Start a new Live Resolution case with AI assistance disabled, to verify deterministic behavior.
2. Speak or type: “I have not got the refund back of 6,000 rupees from MeeShop.”
3. Finish explaining. Confirm the first missing route-changing detail is asked, not a generic resolution.
4. Reply: “Some of the products were not available, so they were not able to deliver it. They told me to give the refund back in two days, but it has been more than six days and I have not got the refund back.”
5. Confirm that the case moves to an overdue-refund action instead of asking again what happened to the order.

Expected facts:
- Merchant: Meesho
- Amount: ₹6,000 (not ₹2)
- Outcome: merchant unable to fulfil due to unavailable products
- Refund status: pending / promised (not independently verified)
- Promised deadline: two days
- Elapsed time: more than six days

Expected action:
- Open the Meesho order-specific Help Center route.
- Continue the existing support thread/ticket if one exists.
- Request approval status, refund initiation date/payment method, refund reference/ARN if generated, and exact expected credit date.
- Attach order cancellation/unavailable-product proof, the two-day promise, and original payment proof.
- Do not ask “What happened to the order?” again.

## Test 2: promise/elapsed separation
Input: “Support said the refund would arrive in two days, but it has been more than six days.”
Expected: promised_days=2; elapsed_days=6; do not invert the values.

## Test 3: spoken duration must not overwrite the amount
Input turn 1: “My six thousand rupees refund from Meesho is missing.”
Input turn 2: “They told me the refund would come in two days, but it has been more than six days.”
Expected: amount stays ₹6,000; promised_days=2; elapsed_days=6.

## Test 4: order age is not refund elapsed time
Input: “I ordered three weeks ago.”
Expected: order-age phrase may be retained as context, but it must not independently prove that a refund has been pending for three weeks.

## Test 5: spoken duration is not money
Input: “They told me to refund it in two days.”
Expected: amount is not overwritten with ₹2.

## Test 6: verify persistence
After the action is generated, reload the saved case and reopen guidance. Expected: `overdue_refund_promise` remains current; the old order-outcome question does not return.

## Safety
Use redacted screenshots. Never upload OTPs, UPI PINs, CVV, passwords, full card numbers or unrelated account data.
