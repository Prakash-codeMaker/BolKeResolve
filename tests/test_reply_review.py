"""Tests for conservative support-reply interpretation and data provenance."""
import unittest
from fastapi.testclient import TestClient

from backend import main
from backend.resolution import review_support_reply


class ReplyInterpretationUnitTests(unittest.TestCase):
    def test_refund_initiated_is_not_treated_as_credit_verified(self):
        result = review_support_reply("Your refund has been initiated. Please wait 5 business days.")
        self.assertEqual(result["category"], "refund_claimed_initiated")
        self.assertIn("does not independently confirm", result["interpretation"])
        self.assertTrue(result["user_confirmation_required"])
        self.assertFalse(result["is_automatic_decision"])

    def test_reply_saying_credited_still_requires_user_account_check(self):
        result = review_support_reply("The refund amount has been credited to your account.")
        self.assertEqual(result["category"], "refund_claimed_credited")
        self.assertIn("Check your own bank", result["next_step"])

    def test_request_for_otp_is_urgent(self):
        result = review_support_reply("Please share your OTP to release the refund.")
        self.assertEqual(result["category"], "credential_or_remote_access_request")
        self.assertEqual(result["priority"], "urgent")
        self.assertIn("Do not share OTPs", result["next_step"])

    def test_legitimate_warning_about_otp_is_not_flagged_as_a_request(self):
        result = review_support_reply("We will never ask you to share your OTP or UPI PIN.")
        self.assertNotEqual(result["category"], "credential_or_remote_access_request")

    def test_document_request_is_classified_without_inventing_resolution(self):
        result = review_support_reply("Please upload the invoice and transaction receipt for review.")
        self.assertEqual(result["category"], "more_information_requested")
        self.assertIn("relevant information", result["next_step"])

    def test_rejection_and_acknowledgement_are_distinct(self):
        rejected = review_support_reply("Your complaint has been rejected. Please review the reason.")
        ack = review_support_reply("We have received your complaint. Ticket number 12345.")
        self.assertEqual(rejected["category"], "rejected_or_closed")
        self.assertEqual(ack["category"], "acknowledgement_only")

    def test_conflicting_refund_and_rejection_signals_fall_back_safely(self):
        result = review_support_reply("Your refund has been initiated, but your complaint has been rejected.")
        self.assertEqual(result["category"], "mixed_or_conflicting_reply")
        self.assertIn("Read the full original message", result["next_step"])

    def test_unclear_reply_falls_back_to_manual_review(self):
        result = review_support_reply("Thank you for contacting us. We appreciate your patience.")
        self.assertEqual(result["category"], "needs_manual_review")
        self.assertTrue(result["user_confirmation_required"])

    def test_hinglish_refund_initiation_is_not_treated_as_credit_verified(self):
        result = review_support_reply("Refund initiate kar diya hai. 5 business days wait karein.")
        self.assertEqual(result["category"], "refund_claimed_initiated")
        self.assertTrue(result["user_confirmation_required"])
        self.assertIn("reference", result["next_step"])
        self.assertNotIn("has reached your account", result["interpretation"])

    def test_hinglish_credential_request_is_flagged_urgently(self):
        result = review_support_reply("Apna OTP batao to refund release hoga.")
        self.assertEqual(result["category"], "credential_or_remote_access_request")
        self.assertEqual(result["priority"], "urgent")

    def test_hinglish_documents_request_is_classified(self):
        result = review_support_reply("Invoice aur transaction proof bhejein, hum review karenge.")
        self.assertEqual(result["category"], "more_information_requested")

    def test_hinglish_waiting_time_is_classified(self):
        result = review_support_reply("Ticket register ho gayi hai, 5 din wait karein.")
        self.assertEqual(result["category"], "waiting_period_stated")

    def test_hinglish_safety_warning_is_not_flagged_as_a_credential_request(self):
        result = review_support_reply("Apna OTP kisi ko mat batao; bank kabhi nahi maangega.")
        self.assertNotEqual(result["category"], "credential_or_remote_access_request")


class ReplyReviewAPITests(unittest.TestCase):
    def setUp(self):
        self.auth_state = main.AUTH_REQUIRED
        main.AUTH_REQUIRED = False
        self.client = TestClient(main.app)
        response = self.client.post("/api/cases", json={
            "issue_type": "Refund not received",
            "description": "My cancelled order refund has not reached me yet.",
            "merchant": "Example Shop",
            "amount": 850,
            "payment_date": "2026-10-10",
            "language_code": "hi-IN",
            "payment_status": "refund_pending",
            "contacted_support": True,
        })
        self.assertEqual(response.status_code, 201, response.text)
        self.case_id = response.json()["case_id"]

    def tearDown(self):
        self.client.close()
        main.AUTH_REQUIRED = self.auth_state

    def test_case_exposes_provenance_labels_for_reported_facts(self):
        response = self.client.get(f"/api/cases/{self.case_id}")
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        provenance = {item["field"]: item for item in data["fact_provenance"]}
        self.assertEqual(provenance["amount"]["origin"], "Entered by you")
        self.assertIn("not independently verified", provenance["amount"]["status"])
        self.assertEqual(provenance["description"]["origin"], "Your words")

    def test_preview_does_not_persist_raw_reply_but_confirmation_saves_only_summary(self):
        raw_marker = "UNIQUE_PRIVATE_REPLY_MARKER_91427"
        reply = f"{raw_marker}: Your refund has been initiated; please allow 5 business days."
        before = self.client.get(f"/api/cases/{self.case_id}").json()
        preview = self.client.post(f"/api/cases/{self.case_id}/reply-review/preview", json={"reply_text": reply})
        self.assertEqual(preview.status_code, 200, preview.text)
        self.assertFalse(preview.json()["privacy"]["raw_reply_saved"])
        self.assertNotIn(raw_marker, preview.text)
        after_preview = self.client.get(f"/api/cases/{self.case_id}").json()
        self.assertEqual(len(after_preview["timeline"]), len(before["timeline"]))
        saved = self.client.post(f"/api/cases/{self.case_id}/reply-review/confirm", json={
            "reply_text": reply, "reference": "REF-ABC-123", "confirmed": True,
        })
        self.assertEqual(saved.status_code, 201, saved.text)
        self.assertFalse(saved.json()["raw_reply_saved"])
        self.assertNotIn(raw_marker, saved.text)
        reread = self.client.get(f"/api/cases/{self.case_id}")
        self.assertEqual(reread.status_code, 200)
        self.assertNotIn(raw_marker, reread.text)
        data = reread.json()
        reviewed = [event for event in data["timeline"] if event.get("metadata", {}).get("reply_interpretation_confirmed")]
        self.assertEqual(len(reviewed), 1)
        self.assertEqual(reviewed[0]["metadata"]["reply_review_category"], "refund_claimed_initiated")
        self.assertFalse(reviewed[0]["metadata"]["raw_reply_retained"])
        self.assertEqual(data["case_stage"], "Awaiting response")

        passport_response = self.client.get(f"/api/cases/{self.case_id}/passport.json")
        self.assertEqual(passport_response.status_code, 200, passport_response.text)
        passport = passport_response.json()
        passport_events = passport["case"]["timeline"]
        exported_review = next(event for event in passport_events if event["metadata"].get("reply_interpretation_confirmed"))
        self.assertEqual(exported_review["metadata"]["reply_review_category"], "refund_claimed_initiated")
        self.assertNotIn(raw_marker, passport_response.text)

    def test_confirmation_requires_explicit_user_confirmation(self):
        response = self.client.post(f"/api/cases/{self.case_id}/reply-review/confirm", json={
            "reply_text": "Your refund has been initiated and should arrive shortly.", "confirmed": False,
        })
        self.assertEqual(response.status_code, 400)
