"""Tests for document-derived case provenance and the optional case inbox bridge.

All evidence/email inputs in these tests are synthetic. The OCR implementation is mocked
at the API boundary so the tests stay deterministic across hosts without Tesseract.
"""
from __future__ import annotations

import base64
import json
import os
import unittest
import uuid
from unittest.mock import patch

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from backend import main


class EvidenceReviewAndInboxBridgeTests(unittest.TestCase):
    def setUp(self):
        self.auth_was_required = main.AUTH_REQUIRED
        main.AUTH_REQUIRED = False
        self.client = TestClient(main.app)
        created = self.client.post("/api/cases", json={
            "issue_type": "Refund not received",
            "merchant": "Zomato",
            "amount": 350,
            "payment_date": "2026-10-10",
            "language_code": "en-IN",
            "payment_status": "refund_pending",
            "contacted_support": True,
            "description": "My ₹350 Zomato refund has not arrived after the promised timeline.",
        })
        self.assertEqual(created.status_code, 201, created.text)
        self.case_id = created.json()["case_id"]
        self._env_names = (
            "BOLKE_INBOUND_EMAIL_DOMAIN", "BOLKE_INBOUND_EMAIL_ENCRYPTION_KEY",
            "BOLKE_INBOUND_WEBHOOK_TOKEN", "BOLKE_INBOUND_WEBHOOK_USERNAME",
            "BOLKE_INBOUND_WEBHOOK_PASSWORD", "BOLKE_INBOUND_EMAIL_RETENTION_DAYS",
        )
        self.env_before = {name: os.environ.get(name) for name in self._env_names}
        os.environ.update({
            "BOLKE_INBOUND_EMAIL_DOMAIN": "inbound.example.test",
            "BOLKE_INBOUND_EMAIL_ENCRYPTION_KEY": Fernet.generate_key().decode("ascii"),
            "BOLKE_INBOUND_WEBHOOK_TOKEN": "synthetic-test-webhook-token-with-sufficient-entropy-98342",
            "BOLKE_INBOUND_WEBHOOK_USERNAME": "",
            "BOLKE_INBOUND_WEBHOOK_PASSWORD": "",
            "BOLKE_INBOUND_EMAIL_RETENTION_DAYS": "14",
        })

    def tearDown(self):
        for name, value in self.env_before.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        self.client.close()
        main.AUTH_REQUIRED = self.auth_was_required

    def upload_synthetic_png(self):
        from PIL import Image
        import io
        stream = io.BytesIO()
        Image.new("RGB", (32, 32), color="white").save(stream, format="PNG")
        response = self.client.post(
            f"/api/cases/{self.case_id}/evidence",
            files={"file": ("synthetic-receipt.png", stream.getvalue(), "image/png")},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["evidence"][-1]["evidence_id"]

    def test_document_review_surfaces_mismatch_without_persisting_raw_ocr(self):
        evidence_id = self.upload_synthetic_png()
        extracted_text = "Zomato refund amount INR 850; refund not received on 12 October 2026."
        with patch("backend.main.extract_evidence_text", return_value={"text": extracted_text, "method": "synthetic_test_ocr", "pages_read": 1}):
            response = self.client.post(f"/api/cases/{self.case_id}/evidence/{evidence_id}/review")
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertFalse(data["raw_document_text_saved"])
        self.assertEqual(data["fields"]["amount"]["value"], 850.0)
        self.assertTrue(data["fields"]["amount"]["mismatch"])
        self.assertEqual(data["fields"]["merchant"]["value"], "Zomato")
        with main.get_db() as con:
            row = con.execute("SELECT candidates_json, conflicts_json FROM evidence_fact_reviews WHERE review_id=?", (data["review_id"],)).fetchone()
        self.assertNotIn(extracted_text, row["candidates_json"])
        self.assertNotIn("Zomato refund amount", row["candidates_json"])
        self.assertNotIn("raw_document_text", row["candidates_json"])

    def test_confirm_document_facts_requires_explicit_confirmation_and_only_applies_selected_fields(self):
        evidence_id = self.upload_synthetic_png()
        with patch("backend.main.extract_evidence_text", return_value={
            "text": "Zomato refund amount INR 850; refund not received on 12 October 2026.",
            "method": "synthetic_test_ocr", "pages_read": 1,
        }):
            preview = self.client.post(f"/api/cases/{self.case_id}/evidence/{evidence_id}/review").json()
        review_id = preview["review_id"]
        rejected = self.client.post(f"/api/cases/{self.case_id}/evidence-review/confirm", json={
            "review_id": review_id, "accepted_fields": ["amount"], "apply_fields": ["amount"], "confirmed": False,
        })
        self.assertEqual(rejected.status_code, 400)
        bad_fields = self.client.post(f"/api/cases/{self.case_id}/evidence-review/confirm", json={
            "review_id": review_id, "accepted_fields": ["amount"], "apply_fields": ["merchant"], "confirmed": True,
        })
        self.assertEqual(bad_fields.status_code, 422)
        confirmed = self.client.post(f"/api/cases/{self.case_id}/evidence-review/confirm", json={
            "review_id": review_id, "accepted_fields": ["amount", "merchant"], "apply_fields": ["amount"], "confirmed": True,
        })
        self.assertEqual(confirmed.status_code, 201, confirmed.text)
        self.assertEqual(confirmed.json()["applied_fields"], ["amount"])
        case = confirmed.json()["case"]
        self.assertEqual(float(case["amount"]), 850.0)
        source_amount = next(item for item in case["evidence_fact_sources"] if item["field_key"] == "amount")
        self.assertTrue(source_amount["applied_to_case"])
        self.assertIn("authenticity not independently verified", source_amount["source_label"])
        source_merchant = next(item for item in case["evidence_fact_sources"] if item["field_key"] == "merchant")
        self.assertFalse(source_merchant["applied_to_case"])
        with main.get_db() as con:
            review_row = con.execute("SELECT status FROM evidence_fact_reviews WHERE review_id=?", (review_id,)).fetchone()
        self.assertEqual(review_row["status"], "confirmed")
        passport = self.client.get(f"/api/cases/{self.case_id}/passport.json")
        self.assertEqual(passport.status_code, 200, passport.text)
        self.assertEqual(passport.json()["format_version"], "1.5")
        self.assertTrue(any(item["field"] == "amount" and item["source_authenticity_verified"] is False for item in passport.json()["case"]["document_fact_sources"]))
        printed = self.client.get(f"/api/cases/{self.case_id}/passport/print")
        self.assertIn("Facts confirmed from uploaded evidence", printed.text)
        self.assertNotIn("Zomato refund amount INR 850; refund not received", printed.text)

    def test_evidence_review_cannot_confirm_a_field_not_in_the_preview(self):
        evidence_id = self.upload_synthetic_png()
        with patch("backend.main.extract_evidence_text", return_value={"text": "Zomato refund amount INR 850.", "method": "synthetic_test_ocr"}):
            preview = self.client.post(f"/api/cases/{self.case_id}/evidence/{evidence_id}/review").json()
        response = self.client.post(f"/api/cases/{self.case_id}/evidence-review/confirm", json={
            "review_id": preview["review_id"], "accepted_fields": ["payment_date"], "apply_fields": [], "confirmed": True,
        })
        self.assertEqual(response.status_code, 422)

    def test_html_email_fallback_removes_script_content_and_scrubs_sensitive_text(self):
        body = main._safe_email_body({
            "TextBody": "",
            "HtmlBody": "<html><head><script>malicious browser instructions</script></head>"
                        "<body><p>Your refund was initiated.</p>"
                        "<p>Never share your OTP 123456 or UPI PIN 9876.</p></body></html>",
        })
        self.assertIn("Your refund was initiated", body)
        self.assertNotIn("malicious browser instructions", body)
        self.assertNotIn("123456", body)
        self.assertNotIn("9876", body)

    def test_email_attachment_sizes_and_retention_settings_are_bounded(self):
        self.assertEqual(main._safe_nonnegative_size("120"), 120)
        self.assertEqual(main._safe_nonnegative_size("-1"), 0)
        self.assertEqual(main._safe_nonnegative_size("999999999999999"), 0)
        self.assertEqual(main._safe_nonnegative_size("12.5"), 0)
        old = os.environ.get("BOLKE_INBOUND_EMAIL_RETENTION_DAYS")
        try:
            os.environ["BOLKE_INBOUND_EMAIL_RETENTION_DAYS"] = "0"
            self.assertEqual(main.inbound_email_retention_days(), 1)
            os.environ["BOLKE_INBOUND_EMAIL_RETENTION_DAYS"] = "900"
            self.assertEqual(main.inbound_email_retention_days(), 30)
            os.environ["BOLKE_INBOUND_EMAIL_RETENTION_DAYS"] = "not-a-number"
            self.assertEqual(main.inbound_email_retention_days(), 14)
        finally:
            if old is None:
                os.environ.pop("BOLKE_INBOUND_EMAIL_RETENTION_DAYS", None)
            else:
                os.environ["BOLKE_INBOUND_EMAIL_RETENTION_DAYS"] = old

    def test_case_inbox_starts_encrypted_and_private_and_accepts_provider_parsed_message(self):
        capability = self.client.get("/api/cases/{}/inbox".format(self.case_id))
        self.assertEqual(capability.status_code, 200, capability.text)
        self.assertTrue(capability.json()["enabled"])
        created = self.client.post(f"/api/cases/{self.case_id}/inbox")
        self.assertEqual(created.status_code, 201, created.text)
        address = created.json()["address"]
        self.assertTrue(address.endswith("@inbound.example.test"))
        local_part = address.split("@", 1)[0]
        self.assertLessEqual(len(local_part), 64)
        self.assertRegex(local_part, r"^br-[a-f0-9]{60}$")
        payload = {
            "To": address,
            "From": "Support Team <reply@merchant.example>",
            "Subject": "Refund has been initiated for order 12345",
            "TextBody": "Your refund has been initiated. Please allow 5 to 7 business days.",
            "MessageID": f"synthetic-{uuid.uuid4().hex}@merchant.example",
            "Attachments": [{"Name": "refund-reference.pdf", "ContentType": "application/pdf", "ContentLength": 123, "Content": "U0hPVUxEX05PVF9CRV9TVE9SRUQ="}],
        }
        headers = {"Authorization": "Bearer synthetic-test-webhook-token-with-sufficient-entropy-98342"}
        accepted = self.client.post("/api/webhooks/inbound-email", json=payload, headers=headers)
        self.assertEqual(accepted.status_code, 200, accepted.text)
        self.assertTrue(accepted.json()["pending_review"])
        duplicate = self.client.post("/api/webhooks/inbound-email", json=payload, headers=headers)
        self.assertTrue(duplicate.json()["duplicate"])
        inbox = self.client.get(f"/api/cases/{self.case_id}/inbox").json()
        self.assertEqual(inbox["pending_count"], 1)
        message = inbox["messages"][0]
        self.assertFalse(message["sender_identity_verified"])
        self.assertFalse(message["attachments"][0]["imported"])
        self.assertNotIn("U0hPVUxEX05PVF9CRV9TVE9SRUQ=", json.dumps(inbox))
        with main.get_db() as con:
            saved = con.execute("SELECT body_ciphertext, subject_ciphertext FROM inbound_email_messages WHERE inbound_id=?", (message["inbound_id"],)).fetchone()
        self.assertNotIn("Your refund has been initiated", saved["body_ciphertext"])
        self.assertNotIn("Refund has been initiated", saved["subject_ciphertext"])
        preview = self.client.post(f"/api/cases/{self.case_id}/inbox/messages/{message['inbound_id']}/preview")
        self.assertEqual(preview.status_code, 200, preview.text)
        self.assertEqual(preview.json()["review"]["category"], "refund_claimed_initiated")
        no_confirm = self.client.post(f"/api/cases/{self.case_id}/inbox/messages/{message['inbound_id']}/confirm", json={"confirmed": False})
        self.assertEqual(no_confirm.status_code, 400)
        confirmed = self.client.post(f"/api/cases/{self.case_id}/inbox/messages/{message['inbound_id']}/confirm", json={"confirmed": True, "reference": "SUP-1234"})
        self.assertEqual(confirmed.status_code, 201, confirmed.text)
        self.assertFalse(confirmed.json()["raw_message_retained"])
        self.assertEqual(confirmed.json()["review"]["category"], "refund_claimed_initiated")
        with main.get_db() as con:
            saved = con.execute("SELECT body_ciphertext, subject_ciphertext, attachments_json, status FROM inbound_email_messages WHERE inbound_id=?", (message["inbound_id"],)).fetchone()
        self.assertEqual(saved["body_ciphertext"], "")
        self.assertEqual(saved["subject_ciphertext"], "")
        self.assertEqual(saved["attachments_json"], "[]")
        self.assertEqual(saved["status"], "confirmed")
        persisted = self.client.get(f"/api/cases/{self.case_id}").json()
        event = next(item for item in persisted["timeline"] if item["event_type"] == "response_received")
        self.assertTrue(event["metadata"]["raw_reply_retained"] is False)
        self.assertNotIn("Your refund has been initiated", event["message"])

    def test_inbound_webhook_rejects_bad_auth_and_unknown_alias_without_leaking_case(self):
        created = self.client.post(f"/api/cases/{self.case_id}/inbox")
        self.assertEqual(created.status_code, 201, created.text)
        response = self.client.post("/api/webhooks/inbound-email", json={"To": created.json()["address"], "TextBody": "refund update"})
        self.assertEqual(response.status_code, 401)
        unknown = self.client.post("/api/webhooks/inbound-email", json={"To": "br-" + "x" * 60 + "@inbound.example.test", "TextBody": "refund update"}, headers={"Authorization": "Bearer synthetic-test-webhook-token-with-sufficient-entropy-98342"})
        self.assertEqual(unknown.status_code, 200)
        self.assertFalse(unknown.json()["accepted"])
        self.assertNotIn(self.case_id, json.dumps(unknown.json()))

    def test_rotating_case_inbox_disables_the_previous_alias(self):
        created = self.client.post(f"/api/cases/{self.case_id}/inbox").json()
        rotated = self.client.post(f"/api/cases/{self.case_id}/inbox/rotate")
        self.assertEqual(rotated.status_code, 200, rotated.text)
        self.assertNotEqual(created["address"], rotated.json()["address"])
        headers = {"Authorization": "Bearer synthetic-test-webhook-token-with-sufficient-entropy-98342"}
        response = self.client.post("/api/webhooks/inbound-email", json={"To": created["address"], "TextBody": "Old inbox message", "MessageID": uuid.uuid4().hex}, headers=headers)
        self.assertFalse(response.json()["accepted"])
        newer = self.client.get(f"/api/cases/{self.case_id}/inbox").json()
        self.assertEqual(newer["address"], rotated.json()["address"])
        self.assertEqual(newer["pending_count"], 0)

    def test_case_inbox_discards_raw_text_and_attachment_metadata(self):
        created = self.client.post(f"/api/cases/{self.case_id}/inbox").json()
        payload = {
            "To": created["address"], "From": "support@merchant.example", "Subject": "Need invoice",
            "TextBody": "Please upload your invoice so we can review the refund.", "MessageID": uuid.uuid4().hex,
            "Attachments": [{"Name": "invoice.pdf", "ContentType": "application/pdf", "ContentLength": 100}],
        }
        headers = {"Authorization": "Bearer synthetic-test-webhook-token-with-sufficient-entropy-98342"}
        self.client.post("/api/webhooks/inbound-email", json=payload, headers=headers)
        message = self.client.get(f"/api/cases/{self.case_id}/inbox").json()["messages"][0]
        response = self.client.delete(f"/api/cases/{self.case_id}/inbox/messages/{message['inbound_id']}")
        self.assertEqual(response.status_code, 200, response.text)
        with main.get_db() as con:
            row = con.execute("SELECT body_ciphertext, subject_ciphertext, attachments_json, status FROM inbound_email_messages WHERE inbound_id=?", (message["inbound_id"],)).fetchone()
        self.assertEqual(row["body_ciphertext"], "")
        self.assertEqual(row["subject_ciphertext"], "")
        self.assertEqual(row["attachments_json"], "[]")
        self.assertEqual(row["status"], "discarded")


    def test_public_config_only_exposes_bridge_readiness_not_secrets(self):
        response = self.client.get("/api/config")
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertTrue(data["case_inbox_bridge_available"])
        self.assertNotIn(os.environ["BOLKE_INBOUND_EMAIL_ENCRYPTION_KEY"], response.text)
        self.assertNotIn(os.environ["BOLKE_INBOUND_WEBHOOK_TOKEN"], response.text)
        self.assertIn("no-store", response.headers.get("cache-control", ""))

    def test_inbound_bridge_supports_strong_http_basic_auth(self):
        os.environ["BOLKE_INBOUND_WEBHOOK_TOKEN"] = ""
        os.environ["BOLKE_INBOUND_WEBHOOK_USERNAME"] = "bolke-hook-user"
        os.environ["BOLKE_INBOUND_WEBHOOK_PASSWORD"] = "synthetic-basic-password-strong-2026"
        created = self.client.post(f"/api/cases/{self.case_id}/inbox")
        self.assertEqual(created.status_code, 201, created.text)
        payload = {"To": created.json()["address"], "TextBody": "Support has received your request.", "MessageID": uuid.uuid4().hex}
        encoded = base64.b64encode(b"bolke-hook-user:synthetic-basic-password-strong-2026").decode("ascii")
        accepted = self.client.post("/api/webhooks/inbound-email", json=payload, headers={"Authorization": f"Basic {encoded}"})
        self.assertEqual(accepted.status_code, 200, accepted.text)
        self.assertTrue(accepted.json()["pending_review"])
        bad = self.client.post("/api/webhooks/inbound-email", json=payload, headers={"Authorization": "Basic not-base64!"})
        self.assertEqual(bad.status_code, 401)

    def test_retention_purges_expired_pending_email_when_case_inbox_is_opened(self):
        created = self.client.post(f"/api/cases/{self.case_id}/inbox")
        self.assertEqual(created.status_code, 201, created.text)
        alias = created.json()["address"]
        payload = {"To": alias, "TextBody": "Synthetic old message awaiting review.", "MessageID": uuid.uuid4().hex}
        headers = {"Authorization": "Bearer synthetic-test-webhook-token-with-sufficient-entropy-98342"}
        self.client.post("/api/webhooks/inbound-email", json=payload, headers=headers)
        with main.get_db() as con:
            con.execute("UPDATE inbound_email_messages SET received_at='2000-01-01T00:00:00+00:00' WHERE case_id=?", (self.case_id,))
        inbox = self.client.get(f"/api/cases/{self.case_id}/inbox")
        self.assertEqual(inbox.status_code, 200, inbox.text)
        self.assertEqual(inbox.json()["pending_count"], 0)
        with main.get_db() as con:
            count = con.execute("SELECT COUNT(*) FROM inbound_email_messages WHERE case_id=?", (self.case_id,)).fetchone()[0]
        self.assertEqual(count, 0)

    def test_case_inbox_rejects_weak_webhook_credentials(self):
        old = os.environ.get("BOLKE_INBOUND_WEBHOOK_TOKEN")
        try:
            os.environ["BOLKE_INBOUND_WEBHOOK_TOKEN"] = "weak"
            status = main.inbound_email_capability()
            self.assertFalse(status["enabled"])
            self.assertFalse(status["webhook_auth_configured"])
        finally:
            if old is None:
                os.environ.pop("BOLKE_INBOUND_WEBHOOK_TOKEN", None)
            else:
                os.environ["BOLKE_INBOUND_WEBHOOK_TOKEN"] = old

    def test_inbound_case_apis_are_private_when_auth_is_enabled(self):
        unauthenticated = TestClient(main.app)
        old_auth = main.AUTH_REQUIRED
        try:
            main.AUTH_REQUIRED = True
            response = unauthenticated.get(f"/api/cases/{self.case_id}/inbox")
            self.assertEqual(response.status_code, 401)
        finally:
            main.AUTH_REQUIRED = old_auth
            unauthenticated.close()

if __name__ == "__main__":
    unittest.main()
