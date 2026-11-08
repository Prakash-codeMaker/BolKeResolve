"""Integration tests for the portable Resolution Passport and user-reported outcome."""
from __future__ import annotations

import os
import tempfile
import unittest

_TEST_DATA = tempfile.TemporaryDirectory(prefix="bolke-resolution-passport-test-")
os.environ["BOLKE_DATA_DIR"] = _TEST_DATA.name

from fastapi.testclient import TestClient  # noqa: E402
from backend import main  # noqa: E402


class ResolutionPassportApiTests(unittest.TestCase):
    def setUp(self):
        self.auth_state = main.AUTH_REQUIRED
        main.AUTH_REQUIRED = False
        self.client = TestClient(main.app)
        response = self.client.post("/api/cases", json={
            "issue_type": "Refund not received",
            "merchant": "Zomato",
            "amount": 50,
            "payment_date": "2026-10-11",
            "language_code": "en-IN",
            "payment_status": "refund_pending",
            "contacted_support": True,
            "description": "My ₹50 refund from Zomato has not arrived after the promised two to three days.",
        })
        self.assertEqual(response.status_code, 201, response.text)
        self.case_id = response.json()["case_id"]

    def tearDown(self):
        self.client.close()
        main.AUTH_REQUIRED = self.auth_state

    def test_passport_json_is_portable_and_includes_clear_provenance(self):
        outcome = self.client.put(f"/api/cases/{self.case_id}/outcome", json={
            "outcome_code": "still_pending",
            "details": "Merchant has not replied yet.",
            "reference": "SUP-1234",
        })
        self.assertEqual(outcome.status_code, 200, outcome.text)

        response = self.client.get(f"/api/cases/{self.case_id}/passport.json")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("attachment; filename=", response.headers.get("content-disposition", ""))
        passport = response.json()
        self.assertEqual(passport["passport_format"], "bolkeresolve-resolution-passport")
        self.assertEqual(passport["format_version"], "1.5")
        self.assertIn("not independently verified", passport["notice"])
        case = passport["case"]
        self.assertEqual(case["merchant"], "Zomato")
        self.assertIn("fact_provenance", case)
        amount_fact = next(item for item in case["fact_provenance"] if item["field"] == "amount")
        self.assertIn("not independently verified", amount_fact["status"])
        self.assertEqual(case["outcome"]["outcome_code"], "still_pending")
        self.assertEqual(case["outcome"]["provenance"], "user_reported")
        self.assertGreaterEqual(len(case["resolution_plan"]["official_sources"]), 1)
        self.assertTrue(all(item.get("url", "").startswith("https://") for item in case["resolution_plan"]["official_sources"]))
        self.assertTrue(any(event["event_type"] == "outcome_updated" for event in case["timeline"]))

    def test_print_passport_is_standalone_and_escapes_case_content(self):
        # Replace merchant text with hostile HTML to exercise output escaping.
        saved = self.client.post("/api/cases", json={
            "issue_type": "Other payment issue",
            "merchant": "<script>alert('x')</script>",
            "amount": 1,
            "payment_date": "",
            "language_code": "en-IN",
            "payment_status": "unknown",
            "contacted_support": False,
            "description": "Please help me with a refund.",
        })
        self.assertEqual(saved.status_code, 201, saved.text)
        hostile_id = saved.json()["case_id"]
        response = self.client.get(f"/api/cases/{hostile_id}/passport/print")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        self.assertIn("no-store", response.headers.get("cache-control", ""))
        self.assertIn("Resolution Passport", response.text)
        self.assertIn("&lt;script&gt;", response.text)
        self.assertNotIn("<script>alert('x')</script>", response.text)
        self.assertIn("Print / Save as PDF", response.text)

    def test_outcome_is_persisted_and_timeline_marks_it_user_reported(self):
        response = self.client.put(f"/api/cases/{self.case_id}/outcome", json={
            "outcome_code": "resolved",
            "details": "The merchant says the refund has arrived.",
            "reference": "REF-9988",
        })
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["outcome"]["outcome_code"], "resolved")
        self.assertEqual(body["outcome"]["provenance"], "user_reported")
        self.assertEqual(body["case_stage"], "Resolved (user-reported)")
        event = next(event for event in body["timeline"] if event["event_type"] == "outcome_updated")
        self.assertTrue(event["metadata"]["user_reported"])
        self.assertIn("has not been independently verified", event["message"])
        persisted = self.client.get(f"/api/cases/{self.case_id}").json()
        self.assertEqual(persisted["outcome"]["reference"], "REF-9988")

    def test_outcome_updates_are_validated(self):
        response = self.client.put(f"/api/cases/{self.case_id}/outcome", json={
            "outcome_code": "verified_by_bank",
            "details": "This value is not an allowed user-reported outcome.",
            "reference": "",
        })
        self.assertEqual(response.status_code, 422)

    def test_outcome_does_not_leak_to_or_modify_an_unknown_case(self):
        response = self.client.put("/api/cases/BR-DOESNOTEXIST/outcome", json={
            "outcome_code": "still_pending", "details": "", "reference": "",
        })
        self.assertEqual(response.status_code, 404)

    def test_pwa_never_caches_api_or_user_case_responses(self):
        root = main.FRONTEND_DIR
        manifest = self.client.get("/manifest.webmanifest")
        service_worker = self.client.get("/sw.js")
        icon = self.client.get("/assets/bolkeresolve-icon-192.png")
        self.assertEqual(manifest.status_code, 200)
        self.assertEqual(service_worker.status_code, 200)
        self.assertEqual(icon.status_code, 200)
        self.assertIn("Resolution Passport", manifest.text)
        self.assertIn("url.pathname.startsWith('/api/')", service_worker.text)
        self.assertIn("Case, auth, evidence, voice and provider endpoints are deliberately network-only", service_worker.text)
        self.assertIn("bolkeresolve-icon-512.png", service_worker.text)
        self.assertTrue((root / "sw.js").is_file())


if __name__ == "__main__":
    unittest.main()
