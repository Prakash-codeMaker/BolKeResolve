"""Product-foundation tests: fact provenance, claim links, reconciliation CSV and privacy-safe metrics."""
from __future__ import annotations

import io
import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from backend import main


class ProductFoundationTests(unittest.TestCase):
    def setUp(self):
        self.auth_required = main.AUTH_REQUIRED
        main.AUTH_REQUIRED = False
        self.client = TestClient(main.app)
        created = self.client.post("/api/live-room/cases", json={"language_code": "en-IN", "session_id": "foundation-tests"})
        self.assertEqual(created.status_code, 201, created.text)
        self.case_id = created.json()["case_id"]

    def tearDown(self):
        self.client.close()
        main.AUTH_REQUIRED = self.auth_required


    def test_my_cases_list_includes_next_action_and_followup_date(self):
        initial = self.client.get("/api/cases")
        self.assertEqual(initial.status_code, 200, initial.text)
        item = next(row for row in initial.json() if row["case_id"] == self.case_id)
        self.assertTrue(item["next_action"])
        self.assertIn("follow_up_due", item)
        saved = self.client.put(f"/api/cases/{self.case_id}/follow-up", json={"due_date": "2026-11-06", "note": "Check the support reply", "completed": False})
        self.assertEqual(saved.status_code, 200, saved.text)
        refreshed = self.client.get("/api/cases")
        item = next(row for row in refreshed.json() if row["case_id"] == self.case_id)
        self.assertEqual(item["follow_up_due"], "2026-11-06")

    def test_live_turn_appends_fact_history_with_provenance(self):
        first = self.client.post(f"/api/cases/{self.case_id}/live-room/turn", json={
            "text": "My Meesho refund of 3000 rupees is pending.",
            "language_code": "en-IN", "session_id": "foundation-tests", "input_source": "typed",
        })
        self.assertEqual(first.status_code, 200, first.text)
        ledger = first.json().get("fact_ledger", [])
        self.assertTrue(ledger)
        merchant = next(item for item in ledger if item["fact_key"] == "merchant" and item["is_current"])
        self.assertEqual(merchant["value"], "Meesho")
        self.assertEqual(merchant["source_type"], "typed")
        self.assertIn("Meesho", merchant["source_excerpt_redacted"])

        second = self.client.post(f"/api/cases/{self.case_id}/live-room/turn", json={
            "text": "Actually the amount is 3500 rupees.",
            "language_code": "en-IN", "session_id": "foundation-tests", "input_source": "typed",
        })
        self.assertEqual(second.status_code, 200, second.text)
        amounts = [item for item in second.json().get("fact_ledger", []) if item["fact_key"] == "amount"]
        self.assertTrue(any(not item["is_current"] for item in amounts))
        self.assertTrue(any(item["is_current"] and float(item["value"]) == 3500 for item in amounts))

    def test_evidence_can_be_linked_to_a_case_claim_and_unlinked(self):
        from PIL import Image
        image = io.BytesIO()
        Image.new("RGB", (20, 20), "white").save(image, format="PNG")
        upload = self.client.post(f"/api/cases/{self.case_id}/evidence", files={"file": ("proof.png", image.getvalue(), "image/png")})
        self.assertEqual(upload.status_code, 201, upload.text)
        evidence_id = upload.json()["uploaded_evidence_id"]
        linked = self.client.post(f"/api/cases/{self.case_id}/evidence/{evidence_id}/claims", json={
            "claim_key": "refund_promise", "claim_label": "Merchant promised refund within two working days",
            "relation": "supports", "note": "Screenshot of support chat, reviewed by the user.",
        })
        self.assertEqual(linked.status_code, 201, linked.text)
        file = next(item for item in linked.json()["case"]["evidence"] if item["evidence_id"] == evidence_id)
        self.assertEqual(file["claim_links"][0]["claim_key"], "refund_promise")
        self.assertEqual(file["claim_links"][0]["relation"], "supports")
        link_id = file["claim_links"][0]["link_id"]
        removed = self.client.delete(f"/api/cases/{self.case_id}/evidence-claim-links/{link_id}")
        self.assertEqual(removed.status_code, 200, removed.text)
        file_after = next(item for item in removed.json()["case"]["evidence"] if item["evidence_id"] == evidence_id)
        self.assertEqual(file_after["claim_links"], [])

    def test_reconciliation_csv_is_saved_as_original_and_requires_explicit_row_confirmation(self):
        csv_text = (
            "Payment ID,Order ID,Settlement ID,UTR,Status,Amount,Net Amount,Currency\n"
            "pay_123,order_123,setl_123,UTR123456,processed,35000,34500,INR\n"
            "pay_456,order_456,setl_456,UTR654321,on_hold,20000,19800,INR\n"
        )
        preview = self.client.post(
            f"/api/cases/{self.case_id}/reconciliation/preview",
            files={"file": ("razorpay-settlement-report.csv", csv_text.encode(), "text/csv")},
        )
        self.assertEqual(preview.status_code, 201, preview.text)
        data = preview.json()
        self.assertEqual(data["preview"]["provider"], "Razorpay")
        self.assertEqual(data["preview"]["row_count"], 2)
        self.assertIn("utr", data["preview"]["headers_recognised"])
        self.assertEqual(data["preview"]["status"], "preview_requires_user_review")
        self.assertTrue(any(item["mime_type"] == "text/csv" for item in data["case"]["evidence"]))
        import_id = data["import_id"]
        rejected = self.client.post(f"/api/cases/{self.case_id}/reconciliation/{import_id}/confirm", json={
            "confirmed": False, "selected_rows": [0],
        })
        self.assertEqual(rejected.status_code, 400)
        confirmed = self.client.post(f"/api/cases/{self.case_id}/reconciliation/{import_id}/confirm", json={
            "confirmed": True, "selected_rows": [0],
        })
        self.assertEqual(confirmed.status_code, 201, confirmed.text)
        self.assertEqual(confirmed.json()["confirmed_rows"], 1)
        stored = confirmed.json()["case"]["reconciliation_imports"][0]
        self.assertEqual(stored["status"], "confirmed")
        self.assertEqual(len(stored["preview"]["confirmed_rows"]), 1)
        # Confirming a report does not silently mutate a payment status or amount.
        self.assertIsNone(confirmed.json()["case"]["amount"])

    def test_csv_parser_rejects_unrecognised_headers_and_formula_rows_are_not_executable(self):
        from backend.reconciliation import parse_reconciliation_csv
        with self.assertRaises(ValueError):
            parse_reconciliation_csv(b"Name,Email,Phone\nA,a@example.test,9999999999\n")
        parsed = parse_reconciliation_csv(
            b"Payment ID,Status,Amount\npay_1,=HYPERLINK(\"http://bad\"),-350\n",
            provider_hint="Razorpay",
        )
        self.assertEqual(parsed["rows"][0]["status"], "'=HYPERLINK(\"http://bad\")")
        self.assertEqual(parsed["rows"][0]["amount"], "'-350")

    def test_passport_exports_fact_history_claim_links_and_user_confirmed_reconciliation(self):
        from PIL import Image
        image = io.BytesIO()
        Image.new("RGB", (16, 16), "white").save(image, format="PNG")
        upload = self.client.post(
            f"/api/cases/{self.case_id}/evidence",
            files={"file": ("order-proof.png", image.getvalue(), "image/png")},
        )
        self.assertEqual(upload.status_code, 201, upload.text)
        evidence_id = upload.json()["uploaded_evidence_id"]
        link = self.client.post(f"/api/cases/{self.case_id}/evidence/{evidence_id}/claims", json={
            "claim_key": "settlement", "claim_label": "Settlement shown in provider dashboard",
            "relation": "supports", "note": "User reviewed this exhibit.",
        })
        self.assertEqual(link.status_code, 201, link.text)
        csv_text = "Payment ID,Settlement ID,UTR,Status,Amount\npay_1,setl_1,UTR123,processed,35000\n"
        preview = self.client.post(
            f"/api/cases/{self.case_id}/reconciliation/preview",
            files={"file": ("settlements.csv", csv_text.encode(), "text/csv")},
        )
        self.assertEqual(preview.status_code, 201, preview.text)
        import_id = preview.json()["import_id"]
        confirmed = self.client.post(f"/api/cases/{self.case_id}/reconciliation/{import_id}/confirm", json={
            "confirmed": True, "selected_rows": [0],
        })
        self.assertEqual(confirmed.status_code, 201, confirmed.text)
        turn = self.client.post(f"/api/cases/{self.case_id}/live-room/turn", json={
            "text": "The payment amount is 35000 rupees.", "language_code": "en-IN",
            "session_id": "foundation-passport", "input_source": "typed",
        })
        self.assertEqual(turn.status_code, 200, turn.text)
        passport = self.client.get(f"/api/cases/{self.case_id}/passport.json")
        self.assertEqual(passport.status_code, 200, passport.text)
        case = passport.json()["case"]
        self.assertEqual(passport.json()["format_version"], "1.5")
        self.assertTrue(case["fact_history"])
        claim_links = case["evidence_inventory"][0]["claim_links"]
        self.assertEqual(claim_links[0]["claim_key"], "settlement")
        self.assertEqual(case["evidence_inventory"][0]["scan_status"], "not_scanned")
        self.assertEqual(case["reconciliation_imports"][0]["status"], "confirmed")
        self.assertEqual(case["reconciliation_imports"][0]["confirmed_rows"][0]["utr"], "UTR123")
        printed = self.client.get(f"/api/cases/{self.case_id}/passport/print")
        self.assertEqual(printed.status_code, 200, printed.text)
        self.assertIn("Fact history &amp; corrections", printed.text)
        self.assertIn("Settlement / reconciliation imports", printed.text)
        self.assertIn("Malware scan: not_scanned", printed.text)

    def test_quality_summary_is_operator_token_gated_and_contains_no_user_text(self):
        previous = os.environ.get("BOLKE_QUALITY_METRICS_TOKEN")
        os.environ["BOLKE_QUALITY_METRICS_TOKEN"] = "test-quality-token-with-enough-entropy-12345"
        try:
            turn = self.client.post(f"/api/cases/{self.case_id}/live-room/turn", json={
                "text": "My Zepto refund is pending.", "language_code": "en-IN", "input_source": "typed",
            })
            self.assertEqual(turn.status_code, 200, turn.text)
            no_token = self.client.get("/api/internal/quality/summary")
            self.assertEqual(no_token.status_code, 401)
            summary = self.client.get("/api/internal/quality/summary", headers={
                "X-Bolke-Metrics-Token": os.environ["BOLKE_QUALITY_METRICS_TOKEN"]
            })
            self.assertEqual(summary.status_code, 200, summary.text)
            payload = summary.json()
            self.assertGreaterEqual(payload["events"].get("user_turn_saved", 0), 1)
            self.assertNotIn("My Zepto refund", summary.text)
            self.assertIn("User message text", payload["privacy"])
        finally:
            if previous is None:
                os.environ.pop("BOLKE_QUALITY_METRICS_TOKEN", None)
            else:
                os.environ["BOLKE_QUALITY_METRICS_TOKEN"] = previous


if __name__ == "__main__":
    unittest.main()
