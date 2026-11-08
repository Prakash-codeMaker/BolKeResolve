# BolKeResolve — Meesho refund workflow fix

Date: 2 November 2026

## What was broken
A user gave two turns: first, that a ₹6,000 refund had not arrived from Meesho; second, that products were unavailable, delivery could not be fulfilled, a two-day refund had been promised, and more than six days had passed. The app could continue asking “What happened to the order?” instead of using the newly supplied facts to move to a specific action.

## Root cause
The natural-language fact extractor and workflow engine did not reliably separate three different values:
1. the amount involved (₹6,000),
2. the merchant's promised refund deadline (two days), and
3. the time that had actually elapsed (more than six days).

The spoken-number amount parser could scan beyond the number into a duration phrase and interpret “two” as a money amount. The promise parser could also see “support said … seven days” anywhere in a clause and capture a later elapsed period as the promised deadline. These parsing errors meant the workflow's overdue-refund condition was not satisfied, and the old intake question remained active.

## What changed
- Promise parsing now stays inside the same clause as the promise and splits on contrast words such as “but”, “however” and “although”.
- Elapsed-time parsing is separate from promise parsing.
- A duration word immediately following a spoken number prevents that number from being interpreted as currency.
- “X weeks ago” is retained as order-age context but is not automatically treated as time since refund initiation.
- Unavailable-product fulfilment failures and natural-language promise statements feed the refund facts.
- When elapsed time exceeds the reported promise, the workflow moves to an overdue-refund action using the official Meesho Help Center path already present in the reviewed support directory.

## Exact verified outcome
| Field | Result |
|---|---|
| Merchant | Meesho |
| Amount | ₹6,000 |
| Order outcome | Merchant could not fulfil because products were unavailable |
| Refund status | Pending (reported promise; not independently verified) |
| Promised deadline | 2 days |
| Elapsed time | More than 6 days |
| Workflow | `overdue_refund_promise` action |
| Next question | None; the engine presents the action instead |

The action tells the user to continue the existing order support thread, request refund approval/initialisation date/reference/expected credit date, and attach the order cancellation/unavailability screen, the two-day promise, and payment proof. It warns users not to share OTPs, PINs, CVV or full account/card details. It does not claim to have contacted Meesho or verified its internal records.

## Cross-checks
- Full test suite: 321 passed, 0 failed.
- Dedicated persistent Live Room API test for the exact two-turn Meesho scenario: passed, including a fresh guidance reload to ensure the action persists.
- Existing regression for Flipkart whole-order answer and deadline progression: passed.
- Existing regression for spoken amount parsing: passed.
- JavaScript syntax: passed.
- Python compilation: passed.
- ZIP integrity and fresh extraction test: performed before delivery.

## Design and layout
The Live Room layout now uses a more balanced desktop column split, a bounded conversation history area (max 520px / 56vh on desktop and 440px / 52vh on mobile), automatic scroll-to-latest message, a compact camera-off placeholder, and a single-column workspace below the tablet breakpoint. This prevents long histories from making the entire left column grow indefinitely while keeping the composer outside the transcript scroller. The CSS is covered by frontend asset tests and service-worker cache v35 forces the browser to fetch the updated shell. A real device/browser visual review was not completed in this environment, so visual polish should still be checked on the target Windows Chrome setup.

Research principles used: GOV.UK Design System recommends asking only information needed, making the reason for each question clear, accepting “I don't know”, and not asking for the same information twice; W3C WCAG 2.2 Reflow expects content to adapt down to 320 CSS px without two-dimensional scrolling for ordinary content. Sources: https://design-system.service.gov.uk/patterns/question-pages/ and https://www.w3.org/WAI/WCAG22/Understanding/reflow.html.

## Installation
1. Extract the ZIP into a new folder.
2. Copy the existing `.env` into the new folder; do not put secrets in the archive.
3. Run `run_windows.bat`.
4. Open `http://127.0.0.1:8000` and press Ctrl+F5.
5. Run the manual acceptance test with a fresh Meesho refund case.

## Not verified
No authenticated Meesho lookup, actual refund state, physical mic/camera session, or production deployment security audit was performed. “Pending” and the dates are user-reported facts, not merchant-verified facts.
