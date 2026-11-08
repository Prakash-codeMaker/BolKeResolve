# Meesho refund workflow and duration parsing fix — 2026-11-02

## Problem reproduced
The Live Resolution flow could keep asking what happened to the order after the user had explained that products were unavailable, the merchant promised a refund within two days, and more than six days had passed. It also confused time durations with amounts and could confuse an elapsed period with the merchant's promised deadline.

## Changes
- Added/retained spoken and text aliases for Meesho, including “MeeShop”.
- Recognise unavailable-product / merchant-unable-to-fulfil order outcomes.
- Detect that a merchant statement promising a refund makes the refund pending, without claiming the refund was initiated.
- Parse the promised refund deadline only inside the promise clause and stop at contrast markers such as “but” and “however”.
- Parse elapsed time independently from the promised deadline.
- Prevent spoken durations such as “two days” from being extracted as amounts when currency context occurs earlier in the sentence.
- Preserve “ordered three weeks ago” as order-age context without automatically treating it as refund waiting time.
- When the user-reported elapsed period exceeds the stated promise, generate a case-specific overdue-refund action and Meesho's order-specific Help Center route, instead of asking the order-outcome question again.
- The action asks the merchant to confirm approval, refund initiation date/payment method, refund reference/ARN if generated, and exact expected credit date. It asks for cancellation/unavailability proof, the promise evidence, and original payment proof. It tells the user to continue an existing support conversation rather than create a duplicate ticket.

## Case-specific example verified
User turn 1: “I have not got the refund back of 6,000 rupees from Meesho.”
User turn 2: “Some of the products were not available, so they were not able to deliver it. They told me to give the refund back in two days, but it has been more than six days and I have not got the refund back.”

Expected extracted facts:
- Merchant: Meesho
- Amount: ₹6,000
- Order outcome: merchant unable to fulfil
- Refund status: pending
- Promised deadline: 2 days
- Elapsed time: more than 6 days

Expected workflow: `action / overdue_refund_promise`, with no repeated `order_outcome` question.

## Validation
- Full Python test suite: 321 tests passed.
- Dedicated persisted Live Room API regression for the two-turn Meesho example: passed.
- JavaScript syntax check: passed.
- Python compilation: passed.
- Fresh ZIP extraction and test run: 321 tests passed (verified in the extracted archive).

## Limitations
The automated regression verifies server-side persistence, extraction, decisioning and response data. It does not establish that an authenticated merchant account was checked, that a refund exists in merchant systems, or that a physical microphone/camera was tested. User-reported facts remain labelled as such.
