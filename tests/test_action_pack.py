"""Regression tests for the case action pack, checklists, follow-ups and editable drafts."""
from __future__ import annotations

import os
import tempfile
import unittest
from datetime import date, timedelta

_TEST_DATA = tempfile.TemporaryDirectory(prefix="bolke-action-pack-test-")
os.environ["BOLKE_DATA_DIR"] = _TEST_DATA.name

from fastapi.testclient import TestClient  # noqa: E402
from backend import main  # noqa: E402


class ActionPackApiTests(unittest.TestCase):
    def setUp(self):
        self.auth_state = main.AUTH_REQUIRED
        main.AUTH_REQUIRED = False
        self.client = TestClient(main.app)
        response = self.client.post("/api/cases", json={
            "issue_type": "Other payment issue",
            "merchant": "Zomato",
            "amount": 850,
            "payment_date": "",
            "language_code": "en-IN",
            "payment_status": "refund_pending",
            "contacted_support": True,
            "description": "I have not got the refund back from Zomato for my cancelled order. They promised it in two to three days, but it has been more than seven days.",
        })
        self.assertEqual(response.status_code, 201, response.text)
        self.case = response.json()
        self.case_id = self.case["case_id"]

    def tearDown(self):
        self.client.close()
        main.AUTH_REQUIRED = self.auth_state

    def test_action_pack_is_tailored_and_exportable(self):
        result = self.client.get(f"/api/cases/{self.case_id}/action-pack")
        self.assertEqual(result.status_code, 200, result.text)
        pack = result.json()
        self.assertEqual(pack["issue_type"], "Refund not received")
        self.assertGreaterEqual(pack["readiness"]["required_total"], 3)
        self.assertTrue(any(item["key"] == "refund_cancel_confirmation" for item in pack["evidence_checklist"]))
        self.assertIn("Zomato", pack["export_text"])
        self.assertIn("OFFICIAL SOURCES TO REVIEW", pack["export_text"])
        self.assertIn("queried by BolKeResolve", pack["export_text"])

    def test_checklist_state_persists_and_updates_readiness(self):
        before = self.client.get(f"/api/cases/{self.case_id}/action-pack").json()
        key = "refund_order_record"
        response = self.client.patch(f"/api/cases/{self.case_id}/checklist/{key}", json={"checked": True})
        self.assertEqual(response.status_code, 200, response.text)
        after = response.json()["action_pack"]
        self.assertTrue(next(item for item in after["evidence_checklist"] if item["key"] == key)["checked"])
        self.assertGreater(after["readiness"]["percent"], before["readiness"]["percent"])
        persisted = self.client.get(f"/api/cases/{self.case_id}").json()
        self.assertTrue(persisted["checklist_state"][key])

    def test_unknown_checklist_key_is_rejected(self):
        response = self.client.patch(f"/api/cases/{self.case_id}/checklist/not-a-real-task", json={"checked": True})
        self.assertEqual(response.status_code, 404)

    def test_follow_up_date_note_and_completion_persist(self):
        due = (date.today() + timedelta(days=2)).isoformat()
        response = self.client.put(f"/api/cases/{self.case_id}/follow-up", json={
            "due_date": due, "note": "Follow up if no response", "completed": False,
        })
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["follow_up"]["due_date"], due)
        self.assertEqual(body["action_pack"]["follow_up"]["status"], "upcoming")
        self.assertIn("Follow up if no response", body["action_pack"]["export_text"])
        completed = self.client.put(f"/api/cases/{self.case_id}/follow-up", json={
            "due_date": due, "note": "Follow up if no response", "completed": True,
        })
        self.assertEqual(completed.status_code, 200, completed.text)
        self.assertEqual(completed.json()["action_pack"]["follow_up"]["status"], "completed")

    def test_follow_up_rejects_invalid_calendar_date(self):
        response = self.client.put(f"/api/cases/{self.case_id}/follow-up", json={
            "due_date": "2026-02-31", "note": "Try later", "completed": False,
        })
        self.assertEqual(response.status_code, 422)

    def test_support_draft_can_be_edited_and_saved(self):
        prepared = self.client.post(f"/api/cases/{self.case_id}/draft", json={"language": "en"})
        self.assertEqual(prepared.status_code, 200, prepared.text)
        revised_text = "Hello Zomato Support Team, please share the status of my ₹850 refund and provide a complaint reference."
        saved = self.client.put(f"/api/cases/{self.case_id}/draft", json={"text": revised_text})
        self.assertEqual(saved.status_code, 200, saved.text)
        self.assertEqual(saved.json()["support_draft"], revised_text)
        self.assertTrue(any(item["event_type"] == "draft_edited" for item in saved.json()["timeline"]))

    def test_refund_draft_asks_for_initiation_reference_and_timeline(self):
        draft = main.make_support_draft({
            "case_id": "BR-TEST123", "issue_type": "Refund not received", "merchant": "Zomato",
            "amount": 850, "payment_date": "2026-10-11", "payment_status": "refund_pending",
            "contacted_support": True,
            "description": "My ₹850 refund from Zomato has not arrived after seven days.",
        }, "en")
        self.assertIn("Subject: Request to review a refund that has not arrived", draft)
        self.assertIn("₹850", draft)
        self.assertIn("11 Oct 2026", draft)
        self.assertIn("Confirm whether the refund has been initiated", draft)
        self.assertIn("refund reference and expected credit date", draft)
        self.assertIn("I have contacted support already", draft)
        self.assertNotIn("independently verified", draft)
        self.assertNotIn("BR-TEST123", draft)

    def test_draft_omits_unknown_facts_instead_of_inventing_placeholders(self):
        draft = main.make_support_draft({
            "case_id": "BR-TEST124", "issue_type": "Duplicate charge", "merchant": "",
            "amount": None, "payment_date": "", "payment_status": "unknown",
            "contacted_support": None, "description": "I think I was charged twice for one order.",
        }, "en")
        self.assertIn("Hello Support Team", draft)
        self.assertIn("Review the charges and confirm whether a duplicate payment occurred", draft)
        self.assertNotIn("Amount at issue", draft)
        self.assertNotIn("Payment date", draft)
        self.assertNotIn("Status shown in the app", draft)
        self.assertNotIn("I have contacted support", draft)
        self.assertNotIn("your service", draft)

    def test_draft_has_issue_specific_failed_upi_request(self):
        draft = main.make_support_draft({
            "case_id": "BR-TEST125", "issue_type": "Failed UPI payment", "merchant": "PhonePe",
            "amount": 500, "payment_date": "", "payment_status": "failed",
            "contacted_support": False, "description": "My UPI payment failed but money was deducted.",
        }, "en")
        self.assertIn("Confirm the transaction outcome against your records", draft)
        self.assertIn("reversal status", draft)
        self.assertIn("I have not contacted support yet", draft)
        self.assertNotIn("refund reference", draft)

    def test_draft_is_available_in_hindi_and_hinglish_with_specific_request(self):
        case = {
            "case_id": "BR-TEST126", "issue_type": "Refund not received", "merchant": "Zomato",
            "amount": 50, "payment_date": "", "payment_status": "refund_pending",
            "contacted_support": None, "description": "Mera refund abhi tak nahi aaya.",
        }
        hindi = main.make_support_draft(case, "hi")
        hinglish = main.make_support_draft(case, "hinglish")
        self.assertIn("विषय: रिफंड न मिलने की जाँच का अनुरोध — Zomato", hindi)
        self.assertIn("Mere paas", hinglish)
        self.assertIn("कृपया पुष्टि करें कि रिफंड शुरू किया गया है या नहीं", hindi)
        self.assertIn("रिफंड की बताई गई समय-सीमा बीत गई है", hindi)
        self.assertIn("Please confirm karein ki refund initiate hua hai ya nahi", hinglish)
        self.assertIn("expected credit date", hinglish)

    def test_follow_up_reminder_can_be_cleared(self):
        future_date = (date.today() + timedelta(days=2)).isoformat()
        saved = self.client.put(f"/api/cases/{self.case_id}/follow-up", json={"due_date": future_date, "note": "Check reply", "completed": False})
        self.assertEqual(saved.status_code, 200, saved.text)
        cleared = self.client.put(f"/api/cases/{self.case_id}/follow-up", json={"due_date": "", "note": "", "completed": False})
        self.assertEqual(cleared.status_code, 200, cleared.text)
        self.assertEqual(cleared.json()["follow_up"]["due_date"], "")
        self.assertEqual(cleared.json()["action_pack"]["follow_up"]["status"], "not_set")

    def test_workspace_exposes_prep_kit_editable_draft_and_export_actions(self):
        app_js = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        stylesheet = (main.FRONTEND_DIR / "design-v2.css").read_text(encoding="utf-8")
        self.assertIn("data-tab-panel=\"prep\"", app_js)
        self.assertIn("data-checklist-key", app_js)
        self.assertIn("data-action=\"download-pack\"", app_js)
        self.assertIn("data-action=\"save-draft\"", app_js)
        self.assertIn("caseFollowupForm", app_js)
        self.assertIn("action-pack-card", stylesheet)
        self.assertIn("draft-output-editor", stylesheet)


if __name__ == "__main__":
    unittest.main()
