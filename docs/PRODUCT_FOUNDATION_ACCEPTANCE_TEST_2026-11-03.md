# BolKeResolve Product Foundation — Acceptance Test

## Local installation
1. Extract the ZIP to a new folder.
2. Copy the existing local `.env` into the project root; do not share or commit it.
3. Start with `run_windows.bat` or the documented local command.
4. Open the local site and hard-refresh once so service-worker cache `v41` is active.

## Fact ledger
1. Create a new Live Room case.
2. Say/type: `My Meesho refund of 3000 rupees is pending.`
3. Confirm the case shows the Meesho and amount facts with source/provenance.
4. Correct the amount: `Actually the amount is 3500 rupees.`
5. Reopen the case dossier / Passport JSON. Confirm both values are in history, the previous one is marked superseded and 3500 is current.

## Evidence-to-claim mapping
1. Upload an order, cancellation, support or payment screenshot.
2. On its evidence card, choose a claim such as `Refund promise` or `Settlement`.
3. Select `Supports`, `Contradicts` or `Context`; save the relationship.
4. Confirm the claim chip appears and the Passport JSON/print export includes it.
5. Remove the link and confirm the original file remains in evidence.

## Razorpay CSV reconciliation
1. Open a case classified as a merchant settlement/gateway issue.
2. Choose `Import settlement CSV` and select a Razorpay report.
3. Inspect recognised columns and rows. No case financial facts should change yet.
4. Select only the rows needed for the case and confirm.
5. Reopen the case. Confirm the original CSV is still evidence and the import is marked confirmed.
6. Confirm amount/payment status are not silently overwritten by CSV confirmation.
7. Export the Passport and verify only user-confirmed rows appear in its reconciliation section.

Use a synthetic CSV for testing; do not upload live customer data to a development instance.

## Quality metrics
1. Keep `BOLKE_QUALITY_METRICS_TOKEN` unset; `/api/internal/quality/summary` should be unavailable.
2. Configure a long random token in server environment and restart.
3. Request the endpoint without the header (401), then with `X-Bolke-Metrics-Token` (200).
4. Confirm output has aggregate event counts and contains no story text, filenames, payment IDs, UTRs or uploaded content.
5. Never put the token in `frontend/` or commit it.

## Passport
1. Export JSON and print/PDF from a case containing a fact correction, linked evidence and confirmed CSV rows.
2. Confirm Passport format is 1.5.
3. Confirm fact history includes current/superseded values and evidence links show their relation.
4. Confirm scan status is clearly `not_scanned` unless a real scanner has been deployed.
5. Confirm reconciliation rows are explicitly marked user-confirmed and not independently verified.

## Browser/device QA still required
- Chrome and Edge on Windows: 100%, 125% and 150% zoom.
- Mobile viewport around 320px, 375px and 430px wide.
- Keyboard-only navigation and visible focus.
- Screen reader labels for CSV row selection and claim controls.
- Upload large/invalid CSVs and malformed rows.
- Verify microphone/camera permission and authenticated provider flows separately.
