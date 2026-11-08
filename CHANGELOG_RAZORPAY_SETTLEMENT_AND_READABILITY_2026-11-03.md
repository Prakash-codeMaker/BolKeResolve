# Razorpay merchant settlement and readability correction — 3 November 2026

- Added/strengthened description-first classification for payment-gateway customer collections that have not reached the merchant's business bank account.
- Kept merchant settlement cases out of consumer National Consumer Helpline auto-routing.
- Added a Razorpay-specific editable support draft using settlement ID, status, scheduled date, UTR, Payment IDs and previous ticket.
- Updated the first question and status branches to the official Dashboard flow: Transactions → Payments → affected Payment ID → `settlement_id` (or Settlements view).
- Added the official Razorpay settlement FAQ as a second source; the product explains T+2 working days as a standard domestic cycle that is subject to account/bank/business conditions, not a universal guarantee.
- Hardened the recording-transcript textarea to full width with readable 16px text, a useful minimum height and responsive sizing.
- Normalised case-detail typography: 16px body, 15px primary copy and ~12.5px metadata; increased step copy, labels, fields, timeline and evidence descriptions.
- Increased Live Room metadata, conversation turns and guidance text for readability.
- Bumped the public shell cache to v40. Private API and case data remain excluded from the service-worker cache.
- Added tests for the settlement source, support-route exclusivity, current Dashboard path and readable case typography.
