"""Tests for signed, idempotent WhatsApp and case-event workflows.

All Meta sends are mocked. These tests never contact the real WhatsApp service.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import tempfile
import unittest
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlsplit

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

_TEST_DATA = tempfile.TemporaryDirectory(prefix="bolke-whatsapp-test-")
os.environ.setdefault("BOLKE_DATA_DIR", _TEST_DATA.name)

from backend import main, whatsapp  # noqa: E402

CASE_PAYLOAD = {
    "issue_type": "Other payment issue",
    "merchant": "Zomato",
    "amount": 850,
    "payment_date": "",
    "language_code": "en-IN",
    "payment_status": "refund_pending",
    "contacted_support": True,
    "description": "I ordered food from Zomato for ₹850 but my refund has not arrived after seven days.",
}


class WhatsAppWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.auth_state = main.AUTH_REQUIRED
        main.AUTH_REQUIRED = False
        self.client = TestClient(main.app)
        self.phone_key = Fernet.generate_key().decode("ascii")
        self.env = patch.dict(os.environ, {
            "WHATSAPP_BUSINESS_NUMBER": "919000000001",
            "WHATSAPP_ACCESS_TOKEN": "test-access-token",
            "WHATSAPP_PHONE_NUMBER_ID": "phone-id-test",
            "WHATSAPP_APP_SECRET": "test-app-secret",
            "WHATSAPP_VERIFY_TOKEN": "test-verify-token",
            "WHATSAPP_PHONE_ENCRYPTION_KEY": self.phone_key,
            "WHATSAPP_GRAPH_API_VERSION": "v26.0",
            "WHATSAPP_WEBHOOK_LEASE_SECONDS": "180",
            "BOLKE_PRIVACY_POLICY_URL": "https://bolke.test/privacy.html",
            "BOLKE_SUPPORT_EMAIL": "support@bolke.test",
            "BOLKE_SUPPORT_URL": "",
            "WHATSAPP_REMINDER_TEMPLATE_NAME": "",
        })
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.client.close()
        main.AUTH_REQUIRED = self.auth_state

    def create_case(self):
        response = self.client.post("/api/cases", json=CASE_PAYLOAD)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["case_id"]

    def webhook_body(self, message_id: str, sender: str, text: str) -> bytes:
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{"changes": [{"field": "messages", "value": {
                "metadata": {"phone_number_id": "phone-id-test"},
                "messages": [{"from": sender, "id": message_id, "type": "text", "text": {"body": text}}],
            }}]}],
        }
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    def post_signed(self, message_id: str, sender: str, text: str):
        raw = self.webhook_body(message_id, sender, text)
        signature = "sha256=" + hmac.new(b"test-app-secret", raw, hashlib.sha256).hexdigest()
        return self.client.post("/api/webhooks/whatsapp", content=raw, headers={
            "content-type": "application/json",
            "X-Hub-Signature-256": signature,
        })

    def test_webhook_verification_challenge(self):
        response = self.client.get("/api/webhooks/whatsapp", params={
            "hub.mode": "subscribe", "hub.verify_token": "test-verify-token", "hub.challenge": "challenge-123",
        })
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.text, "challenge-123")
        rejected = self.client.get("/api/webhooks/whatsapp", params={
            "hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "challenge-123",
        })
        self.assertEqual(rejected.status_code, 403)

    def test_webhook_rejects_invalid_hmac_signature(self):
        raw = self.webhook_body("wamid-invalid-sig", "919111222333", "START")
        response = self.client.post("/api/webhooks/whatsapp", content=raw, headers={
            "content-type": "application/json", "X-Hub-Signature-256": "sha256=00",
        })
        self.assertEqual(response.status_code, 401)

    @patch("backend.main.whatsapp_service.send_guided_reply", new_callable=AsyncMock)
    def test_signed_whatsapp_story_requires_save_then_creates_normal_case(self, send_message):
        send_message.return_value = {"accepted": True, "message_id": "wamid-out"}
        sender = "919123456789"
        preexisting_ids = {c["case_id"] for c in self.client.get("/api/cases").json()}
        start = self.post_signed("wamid-start-test", sender, "START")
        self.assertEqual(start.status_code, 200, start.text)
        self.assertIn("opt", send_message.await_args.args[1].lower())
        story = self.post_signed("wamid-story-test", sender, "I ordered food from Zomato for ₹850 but my refund has not arrived after seven days and support isn't replying.")
        self.assertEqual(story.status_code, 200, story.text)
        self.assertIn("Reply SAVE", send_message.await_args.args[1])
        # No case should be created until the explicit SAVE confirmation.
        before_ids = {c["case_id"] for c in self.client.get("/api/cases").json()}
        self.assertEqual(before_ids, preexisting_ids, "A case should not be created before the explicit SAVE confirmation.")
        saved = self.post_signed("wamid-save-test", sender, "SAVE")
        self.assertEqual(saved.status_code, 200, saved.text)
        self.assertIn("Your case BR-", send_message.await_args.args[1])
        listed = self.client.get("/api/cases").json()
        created_case = next(c for c in listed if c["case_id"] not in preexisting_ids)
        self.assertEqual(created_case["merchant"], "Zomato")
        self.assertEqual(float(created_case["amount"]), 850.0)
        self.assertEqual(created_case["issue_type"], "Refund not received")
        with main.get_db() as con:
            saved_events = con.execute("SELECT event_type, channel, actor FROM timeline WHERE case_id=?", (created_case["case_id"],)).fetchall()
            contact = con.execute("SELECT phone_ciphertext, phone_hash FROM whatsapp_contacts LIMIT 1").fetchone()
            seen = con.execute("SELECT status FROM whatsapp_webhook_messages WHERE message_id='wamid-save-test'").fetchone()
        self.assertTrue(any(e["channel"] == "whatsapp" and e["actor"] == "user" for e in saved_events))
        self.assertTrue(contact["phone_ciphertext"] != sender)
        self.assertEqual(len(contact["phone_hash"]), 64)
        self.assertEqual(seen["status"], "sent")
        # Retried duplicate deliveries do not generate an additional user-facing reply.
        before_calls = send_message.await_count
        duplicate = self.post_signed("wamid-save-test", sender, "SAVE")
        self.assertEqual(duplicate.status_code, 200, duplicate.text)
        self.assertEqual(send_message.await_count, before_calls)

    @patch("backend.main.whatsapp_service.send_guided_reply", new_callable=AsyncMock)
    def test_case_linked_conversation_reply_is_tracked_for_delivery_receipts(self, send_reply):
        send_reply.return_value = {"accepted": True, "message_id": "wamid-conversation-reply"}
        sender = "919555666777"
        self.assertEqual(self.post_signed("wamid-track-start", sender, "START").status_code, 200)
        self.assertEqual(self.post_signed("wamid-track-story", sender, "I ordered from Zomato for ₹850 and the refund has not arrived after seven days.").status_code, 200)
        saved = self.post_signed("wamid-track-save", sender, "SAVE")
        self.assertEqual(saved.status_code, 200, saved.text)
        with main.get_db() as con:
            row = con.execute("SELECT case_id, purpose, status FROM whatsapp_outbound_messages WHERE message_id='wamid-conversation-reply'").fetchone()
        self.assertIsNotNone(row)
        self.assertTrue(row["case_id"].startswith("BR-"))
        self.assertEqual((row["purpose"], row["status"]), ("conversation_reply", "accepted"))

    def test_case_event_changes_stage_and_appends_a_user_reported_event(self):
        case_id = self.create_case()
        response = self.client.post(f"/api/cases/{case_id}/events", json={
            "event_type": "contacted_support", "details": "I used the in-app support chat today", "reference": "NCH-TEST-123",
        })
        self.assertEqual(response.status_code, 201, response.text)
        body = response.json()
        self.assertEqual(body["case_stage"], "Contacted support")
        event = next(e for e in body["timeline"] if e["event_type"] == "contacted_support")
        self.assertEqual(event["actor"], "user")
        self.assertEqual(event["channel"], "web")
        self.assertTrue(event["metadata"]["user_reported"])
        self.assertEqual(event["metadata"]["reference_provided"], "NCH-TEST-123")

    def test_case_event_refuses_unknown_event_type(self):
        case_id = self.create_case()
        response = self.client.post(f"/api/cases/{case_id}/events", json={"event_type": "bank_verified"})
        self.assertEqual(response.status_code, 422)

    def test_whatsapp_case_pairing_code_is_single_case_scoped_and_short_lived(self):
        case_id = self.create_case()
        response = self.client.post(f"/api/cases/{case_id}/whatsapp-link")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["case_id"], case_id)
        self.assertEqual(body["expires_in_seconds"], 600)
        parsed = urlsplit(body["whatsapp_url"])
        self.assertEqual(parsed.netloc, "wa.me")
        self.assertEqual(parsed.path, "/919000000001")
        self.assertTrue(parse_qs(parsed.query)["text"][0].startswith("LINK "))
        self.assertEqual(len(body["code"]), 8)
        with main.get_db() as con:
            row = con.execute("SELECT token_hash, expires_at, consumed_at FROM whatsapp_link_tokens WHERE case_id=?", (case_id,)).fetchone()
        self.assertEqual(row["token_hash"], hashlib.sha256(body["code"].encode("ascii")).hexdigest())
        self.assertGreater(row["expires_at"], int(__import__("time").time()))
        self.assertEqual(row["consumed_at"], "")

    @patch("backend.whatsapp.send_template_message", new_callable=AsyncMock)
    def test_due_followup_reminder_uses_template_and_records_api_acceptance(self, send_template):
        import asyncio
        from datetime import datetime
        from zoneinfo import ZoneInfo
        from scripts.send_whatsapp_reminders import send_due_reminders

        send_template.return_value = {"accepted": True, "message_id": "wamid-reminder-accepted"}
        case_id = self.create_case()
        phone = "919333444555"
        phone_hash = whatsapp.phone_fingerprint(phone)
        ciphertext = whatsapp.encrypt_phone(phone)
        stamp = main.now_iso()
        today = datetime.now(ZoneInfo(os.getenv("BOLKE_TIMEZONE", "Asia/Kolkata"))).date().isoformat()
        with main.get_db() as con:
            con.execute(
                "INSERT INTO whatsapp_contacts (phone_hash, phone_ciphertext, owner_id, consent_at, enabled, created_at, updated_at) VALUES (?, ?, NULL, ?, 1, ?, ?)",
                (phone_hash, ciphertext, stamp, stamp, stamp),
            )
            con.execute(
                "INSERT INTO whatsapp_case_links (phone_hash, case_id, created_at) VALUES (?, ?, ?)",
                (phone_hash, case_id, stamp),
            )
            con.execute(
                "INSERT INTO case_followups (case_id, due_date, note, completed, created_at, updated_at, reminder_sent_for) VALUES (?, ?, '', 0, ?, ?, '')",
                (case_id, today, stamp, stamp),
            )
        with patch.dict(os.environ, {"WHATSAPP_REMINDER_TEMPLATE_NAME": "bolke_followup_due", "WHATSAPP_REMINDER_TEMPLATE_LANGUAGE": "en_US"}):
            accepted, failed = asyncio.run(send_due_reminders())
        self.assertEqual((accepted, failed), (1, 0))
        send_template.assert_awaited_once()
        self.assertEqual(send_template.await_args.args[1], "bolke_followup_due")
        self.assertEqual(send_template.await_args.args[3], [case_id, today])
        with main.get_db() as con:
            followup = con.execute("SELECT updated_at, reminder_sent_for FROM case_followups WHERE case_id=?", (case_id,)).fetchone()
            event = con.execute("SELECT event_type, message, metadata_json FROM timeline WHERE case_id=? AND event_type='reminder_sent'", (case_id,)).fetchone()
            outbound = con.execute("SELECT status, purpose FROM whatsapp_outbound_messages WHERE message_id='wamid-reminder-accepted'").fetchone()
            claim = con.execute("SELECT status, attempts FROM reminder_delivery_claims WHERE case_id=? AND followup_updated_at=?", (case_id, stamp)).fetchone()
        self.assertEqual(followup["reminder_sent_for"], followup["updated_at"])
        self.assertIn("not independently confirmed", event["message"])
        self.assertEqual(json.loads(event["metadata_json"])["message_id"], "wamid-reminder-accepted")
        self.assertEqual((outbound["status"], outbound["purpose"]), ("accepted", "reminder"))
        self.assertEqual((claim["status"], claim["attempts"]), ("accepted", 1))

    def test_reminder_claim_prevents_overlapping_scheduler_runs(self):
        from datetime import date
        from scripts.send_whatsapp_reminders import claim_reminder

        case_id = self.create_case()
        stamp = main.now_iso()
        with main.get_db() as con:
            con.execute(
                "INSERT INTO case_followups (case_id, due_date, note, completed, created_at, updated_at, reminder_sent_for) VALUES (?, ?, '', 0, ?, ?, '')",
                (case_id, date.today().isoformat(), stamp, stamp),
            )
        self.assertTrue(claim_reminder(case_id, stamp))
        self.assertFalse(claim_reminder(case_id, stamp), "A second overlapping worker should not claim the active lease.")
        with main.get_db() as con:
            row = con.execute("SELECT attempts, status FROM reminder_delivery_claims WHERE case_id=? AND followup_updated_at=?", (case_id, stamp)).fetchone()
        self.assertEqual((row["attempts"], row["status"]), (1, "sending"))

    def test_status_parser_extracts_receipt_without_recipient_phone(self):
        payload = {"entry": [{"changes": [{"field": "messages", "value": {"statuses": [
            {"id": "wamid-status-1", "status": "delivered", "timestamp": "1792500000", "recipient_id": "919999999999"},
            {"id": "wamid-status-2", "status": "failed", "errors": [{"code": 131026, "title": "Undeliverable"}]},
            {"id": "ignored", "status": "unknown"},
        ]}}]}]}
        parsed = whatsapp.parse_status_updates(payload)
        self.assertEqual([item["status"] for item in parsed], ["delivered", "failed"])
        self.assertEqual(parsed[1]["error_code"], "131026")
        self.assertNotIn("recipient_id", parsed[0])

    def test_signed_delivery_receipts_update_timeline_once_and_never_downgrade(self):
        case_id = self.create_case()
        stamp = main.now_iso()
        with main.get_db() as con:
            con.execute(
                "INSERT INTO whatsapp_outbound_messages (message_id, case_id, purpose, status, created_at, updated_at, error_code) VALUES (?, ?, 'reminder', 'accepted', ?, ?, '')",
                ("wamid-delivery-test", case_id, stamp, stamp),
            )

        def post_status(status: str):
            raw = json.dumps({"object": "whatsapp_business_account", "entry": [{"changes": [{"field": "messages", "value": {
                "metadata": {"phone_number_id": "phone-id-test"},
                "statuses": [{"id": "wamid-delivery-test", "status": status, "timestamp": "1792500000"}],
            }}]}]}, separators=(",", ":")).encode("utf-8")
            signature = "sha256=" + hmac.new(b"test-app-secret", raw, hashlib.sha256).hexdigest()
            return self.client.post("/api/webhooks/whatsapp", content=raw, headers={"content-type": "application/json", "X-Hub-Signature-256": signature})

        delivered = post_status("delivered")
        self.assertEqual(delivered.status_code, 200, delivered.text)
        self.assertEqual(delivered.json()["statuses_processed"], 1)
        duplicate = post_status("delivered")
        self.assertEqual(duplicate.status_code, 200, duplicate.text)
        self.assertEqual(duplicate.json()["statuses_processed"], 0)
        older = post_status("sent")
        self.assertEqual(older.json()["statuses_processed"], 0)
        with main.get_db() as con:
            outbound = con.execute("SELECT status FROM whatsapp_outbound_messages WHERE message_id='wamid-delivery-test'").fetchone()
            events = con.execute("SELECT event_type, metadata_json FROM timeline WHERE case_id=? AND event_type='whatsapp_delivered'", (case_id,)).fetchall()
        self.assertEqual(outbound["status"], "delivered")
        self.assertEqual(len(events), 1)
        self.assertEqual(json.loads(events[0]["metadata_json"])["provider"], "meta_whatsapp_cloud_api")

    def test_audio_message_parser_keeps_media_id_for_voice_note_transcription(self):
        payload = {"entry": [{"changes": [{"field": "messages", "value": {"metadata": {"phone_number_id": "phone-id-test"}, "messages": [{
            "from": "919111222333", "id": "wamid-audio", "type": "audio",
            "audio": {"id": "media-123", "mime_type": "audio/ogg; codecs=opus", "voice": True},
        }]}}]}]}
        parsed = whatsapp.parse_inbound_messages(payload)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].message_type, "audio")
        self.assertEqual(parsed[0].media_id, "media-123")
        self.assertEqual(parsed[0].mime_type, "audio/ogg; codecs=opus")

    @patch("backend.main.transcribe_whatsapp_voice_note", new_callable=AsyncMock)
    @patch("backend.main.whatsapp_service.send_guided_reply", new_callable=AsyncMock)
    def test_opted_in_whatsapp_voice_note_uses_gnani_transcript_in_case_flow(self, send_reply, transcribe):
        send_reply.return_value = {"accepted": True, "message_id": "wamid-audio-reply"}
        transcribe.return_value = "I ordered from Zomato for ₹850 and my refund has not arrived after seven days."
        sender = "919444555666"
        started = self.post_signed("wamid-audio-start", sender, "START")
        self.assertEqual(started.status_code, 200, started.text)
        payload = {"object": "whatsapp_business_account", "entry": [{"changes": [{"field": "messages", "value": {
            "metadata": {"phone_number_id": "phone-id-test"},
            "messages": [{"from": sender, "id": "wamid-audio-story", "type": "audio", "audio": {"id": "media-audio-1", "mime_type": "audio/ogg; codecs=opus", "voice": True}}],
        }}]}]}
        raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        signature = "sha256=" + hmac.new(b"test-app-secret", raw, hashlib.sha256).hexdigest()
        response = self.client.post("/api/webhooks/whatsapp", content=raw, headers={"content-type": "application/json", "X-Hub-Signature-256": signature})
        self.assertEqual(response.status_code, 200, response.text)
        transcribe.assert_awaited_once()
        self.assertIn("Reply SAVE", send_reply.await_args.args[1])

    @patch("backend.main.whatsapp_service.send_guided_reply", new_callable=AsyncMock)
    def test_whatsapp_language_preference_is_saved_for_voice_notes(self, send_reply):
        send_reply.return_value = {"accepted": True, "message_id": "wamid-language-test"}
        sender = "919777888999"
        started = self.post_signed("wamid-lang-start", sender, "START")
        self.assertEqual(started.status_code, 200, started.text)
        changed = self.post_signed("wamid-lang-change", sender, "LANG EN")
        self.assertEqual(changed.status_code, 200, changed.text)
        with main.get_db() as con:
            phone_hash = whatsapp.phone_fingerprint(sender)
            row = con.execute("SELECT language_code FROM whatsapp_sessions WHERE phone_hash=?", (phone_hash,)).fetchone()
        self.assertEqual(row["language_code"], "en-IN")

    def test_interactive_reply_uses_button_id_not_display_title(self):
        payload = {"entry": [{"changes": [{"field": "messages", "value": {"metadata": {"phone_number_id": "phone-id-test"}, "messages": [{
            "from": "919111222333", "id": "wamid-button", "type": "interactive",
            "interactive": {"type": "button_reply", "button_reply": {"id": "SAVE_CASE", "title": "Save case"}},
        }]}}]}]}
        parsed = whatsapp.parse_inbound_messages(payload)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].text, "SAVE_CASE")
        self.assertEqual(parsed[0].message_type, "interactive")

    def test_guided_reply_selects_native_buttons_for_save_confirmation(self):
        import asyncio
        with patch("backend.whatsapp.send_interactive_buttons", new_callable=AsyncMock) as send_buttons:
            send_buttons.return_value = {"accepted": True, "message_id": "wamid-buttons"}
            result = asyncio.run(whatsapp.send_guided_reply(
                "919123456789",
                "I understood this:\n• Refund not received\n\nReply SAVE to create the case, EDIT to rewrite your story, or CANCEL to discard it.",
            ))
        self.assertTrue(result["accepted"])
        send_buttons.assert_awaited_once()
        buttons = send_buttons.await_args.args[2]
        self.assertEqual([button["id"] for button in buttons], ["SAVE_CASE", "EDIT_STORY", "CANCEL_CASE"])

    def test_public_config_does_not_expose_whatsapp_secrets(self):
        response = self.client.get("/api/config")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["whatsapp_cloud_api_ready"])
        self.assertFalse(body["twilio_whatsapp_configured"])
        self.assertIn("whatsapp_provider_preference", body)
        self.assertNotIn("access_token", body)
        self.assertNotIn("app_secret", body)
        self.assertNotIn("phone_encryption_key", body)


    @patch("backend.main.whatsapp_service.send_guided_reply", new_callable=AsyncMock)
    def test_failed_state_processing_is_recoverable_on_meta_retry(self, send_reply):
        send_reply.return_value = {"accepted": True, "message_id": "wamid-retry-out"}
        sender = "919222333444"
        with patch("backend.main._whatsapp_handle_message", side_effect=RuntimeError("temporary test failure")):
            first = self.post_signed("wamid-retry-recover", sender, "START")
        self.assertEqual(first.status_code, 503)
        with main.get_db() as con:
            row = con.execute("SELECT status, lease_until, attempts FROM whatsapp_webhook_messages WHERE message_id='wamid-retry-recover'").fetchone()
        self.assertEqual(row["status"], "processing")
        self.assertEqual(row["lease_until"], 0)
        retry = self.post_signed("wamid-retry-recover", sender, "START")
        self.assertEqual(retry.status_code, 200, retry.text)
        with main.get_db() as con:
            row = con.execute("SELECT status, attempts, last_error_type FROM whatsapp_webhook_messages WHERE message_id='wamid-retry-recover'").fetchone()
            contact = con.execute("SELECT enabled FROM whatsapp_contacts WHERE phone_hash=?", (whatsapp.phone_fingerprint(sender),)).fetchone()
        self.assertEqual(row["status"], "sent")
        self.assertEqual(row["attempts"], 2)
        self.assertEqual(row["last_error_type"], "")
        self.assertEqual(contact["enabled"], 1)
        send_reply.assert_awaited_once()

    @patch("backend.main.whatsapp_service.send_guided_reply", new_callable=AsyncMock)
    def test_explicit_unsubscribe_phrase_disables_contact(self, send_reply):
        send_reply.return_value = {"accepted": True, "message_id": "wamid-unsubscribe"}
        sender = "919777888999"
        self.assertEqual(self.post_signed("wamid-unsubscribe-start", sender, "START").status_code, 200)
        response = self.post_signed("wamid-unsubscribe-phrase", sender, "Please stop messaging me")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("opted out", send_reply.await_args.args[1].lower())
        phone_hash = whatsapp.phone_fingerprint(sender)
        with main.get_db() as con:
            contact = con.execute("SELECT enabled FROM whatsapp_contacts WHERE phone_hash=?", (phone_hash,)).fetchone()
        self.assertEqual(contact["enabled"], 0)

    @patch("backend.main.whatsapp_service.send_guided_reply", new_callable=AsyncMock)
    def test_link_first_prompts_start_without_consuming_one_time_code(self, send_reply):
        send_reply.return_value = {"accepted": True, "message_id": "wamid-link-needs-start"}
        case_id = self.create_case()
        link = self.client.post(f"/api/cases/{case_id}/whatsapp-link")
        self.assertEqual(link.status_code, 200, link.text)
        sender = "919777888998"
        response = self.post_signed("wamid-link-first", sender, f"LINK {link.json()['code']}")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("reply START", send_reply.await_args.args[1])
        self.assertIn("not been used", send_reply.await_args.args[1])
        with main.get_db() as con:
            token = con.execute("SELECT consumed_at FROM whatsapp_link_tokens WHERE case_id=?", (case_id,)).fetchone()
        self.assertEqual(token["consumed_at"], "")

    @patch("backend.main.whatsapp_service.send_guided_reply", new_callable=AsyncMock)
    def test_stopped_contact_must_send_start_before_linking_case(self, send_reply):
        send_reply.return_value = {"accepted": True, "message_id": "wamid-link-reoptin"}
        case_id = self.create_case()
        token_response = self.client.post(f"/api/cases/{case_id}/whatsapp-link")
        self.assertEqual(token_response.status_code, 200, token_response.text)
        code = token_response.json()["code"]
        sender = "919444555666"
        self.assertEqual(self.post_signed("wamid-reoptin-start", sender, "START").status_code, 200)
        self.assertEqual(self.post_signed("wamid-reoptin-stop", sender, "STOP").status_code, 200)
        blocked = self.post_signed("wamid-reoptin-link", sender, f"LINK {code}")
        self.assertEqual(blocked.status_code, 200, blocked.text)
        self.assertIn("reply START", send_reply.await_args.args[1])
        phone_hash = whatsapp.phone_fingerprint(sender)
        with main.get_db() as con:
            contact = con.execute("SELECT enabled FROM whatsapp_contacts WHERE phone_hash=?", (phone_hash,)).fetchone()
            link = con.execute("SELECT consumed_at FROM whatsapp_link_tokens WHERE token_hash=?", (hashlib.sha256(code.encode('ascii')).hexdigest(),)).fetchone()
        self.assertEqual(contact["enabled"], 0)
        self.assertEqual(link["consumed_at"], "")


    def _twilio_env(self):
        return patch.dict(os.environ, {
            "TWILIO_ACCOUNT_SID": "AC" + "1" * 32,
            "TWILIO_AUTH_TOKEN": "twilio-test-auth-token",
            "TWILIO_WHATSAPP_FROM": "whatsapp:+14155238886",
            "TWILIO_WEBHOOK_PUBLIC_URL": "https://bolke.test/api/webhooks/twilio/whatsapp",
            "TWILIO_STATUS_CALLBACK_URL": "https://bolke.test/api/webhooks/twilio/whatsapp/status",
            "BOLKE_WHATSAPP_PROVIDER": "twilio",
        })

    def _post_twilio_signed(self, data):
        return self.client.post(
            "/api/webhooks/twilio/whatsapp",
            data=data,
            headers={"X-Twilio-Signature": "unit-test-signature"},
        )

    @patch("backend.main.twilio_service.verify_webhook_signature", return_value=False)
    def test_twilio_webhook_rejects_invalid_signature(self, verify_signature):
        with self._twilio_env():
            response = self._post_twilio_signed({
                "MessageSid": "SM-invalid-signature",
                "From": "whatsapp:+919123456789",
                "To": "whatsapp:+14155238886",
                "Body": "START",
                "NumMedia": "0",
            })
        self.assertEqual(response.status_code, 401, response.text)
        verify_signature.assert_called_once()

    @patch("backend.main.twilio_service.verify_webhook_signature", return_value=True)
    @patch("backend.main.twilio_service.send_text_message", new_callable=AsyncMock)
    def test_twilio_sandbox_reuses_shared_case_flow_and_sends_text_replies(self, send_text, verify_signature):
        send_text.side_effect = [
            {"accepted": True, "message_id": "SM-start-reply", "provider": "twilio", "status": "queued"},
            {"accepted": True, "message_id": "SM-story-reply", "provider": "twilio", "status": "queued"},
            {"accepted": True, "message_id": "SM-save-reply", "provider": "twilio", "status": "queued"},
        ]
        sender = "whatsapp:+919123456789"
        with self._twilio_env():
            before_ids = {c["case_id"] for c in self.client.get("/api/cases").json()}
            start = self._post_twilio_signed({
                "MessageSid": "SM-incoming-start", "From": sender,
                "To": "whatsapp:+14155238886", "Body": "START", "NumMedia": "0",
            })
            self.assertEqual(start.status_code, 200, start.text)
            self.assertIn("<Response>", start.text)
            self.assertIn("text only", send_text.await_args_list[0].args[1].lower())
            self.assertIn("do not send voice notes", send_text.await_args_list[0].args[1].lower())
            story = self._post_twilio_signed({
                "MessageSid": "SM-incoming-story", "From": sender,
                "To": "whatsapp:+14155238886", "Body": "I ordered food from Zomato for 850 rupees but my refund has not arrived after seven days.", "NumMedia": "0",
            })
            self.assertEqual(story.status_code, 200, story.text)
            self.assertIn("SAVE", send_text.await_args.args[1])
            self.assertEqual({c["case_id"] for c in self.client.get("/api/cases").json()}, before_ids)
            saved = self._post_twilio_signed({
                "MessageSid": "SM-incoming-save", "From": sender,
                "To": "whatsapp:+14155238886", "Body": "SAVE", "NumMedia": "0",
            })
            self.assertEqual(saved.status_code, 200, saved.text)
            self.assertIn("Your case BR-", send_text.await_args.args[1])
            after_cases = self.client.get("/api/cases").json()
            new_case = next(item for item in after_cases if item["case_id"] not in before_ids)
            self.assertEqual(new_case["merchant"], "Zomato")
            phone_hash = whatsapp.phone_fingerprint("919123456789")
            with main.get_db() as con:
                inbound = con.execute("SELECT provider, status FROM whatsapp_webhook_messages WHERE message_id='twilio:SM-incoming-save'").fetchone()
                outbound = con.execute("SELECT provider, status, case_id FROM whatsapp_outbound_messages WHERE message_id='twilio:SM-save-reply'").fetchone()
                contact = con.execute("SELECT enabled, consent_at FROM whatsapp_contacts WHERE phone_hash=?", (phone_hash,)).fetchone()
            self.assertEqual((inbound["provider"], inbound["status"]), ("twilio", "sent"))
            self.assertEqual((outbound["provider"], outbound["status"], outbound["case_id"]), ("twilio", "accepted", new_case["case_id"]))
            self.assertEqual(contact["enabled"], 1)
            self.assertTrue(contact["consent_at"])
            self.assertEqual(send_text.await_count, 3)

    @patch("backend.main.twilio_service.verify_webhook_signature", return_value=True)
    @patch("backend.main.twilio_service.send_text_message", new_callable=AsyncMock)
    def test_twilio_media_is_explained_without_breaking_consent_flow(self, send_text, verify_signature):
        send_text.return_value = {"accepted": True, "message_id": "SM-media-reply", "provider": "twilio", "status": "queued"}
        with self._twilio_env():
            response = self._post_twilio_signed({
                "MessageSid": "SM-incoming-media", "From": "whatsapp:+919123456789",
                "To": "whatsapp:+14155238886", "Body": "", "NumMedia": "1",
                "MediaUrl0": "https://example.test/audio.ogg", "MediaContentType0": "audio/ogg",
            })
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("START", send_text.await_args.args[1])
        self.assertIn("not opted in", send_text.await_args.args[1].lower())

    @patch("backend.main.twilio_service.verify_webhook_signature", return_value=True)
    def test_twilio_status_callback_updates_tracked_case_message_and_never_downgrades(self, verify_signature):
        case_id = self.create_case()
        now = main.now_iso()
        with main.get_db() as con:
            con.execute(
                "INSERT INTO whatsapp_outbound_messages (message_id, case_id, purpose, status, created_at, updated_at, error_code, provider) VALUES (?, ?, 'conversation_reply', 'accepted', ?, ?, '', 'twilio')",
                ("twilio:SM-status-test", case_id, now, now),
            )
        callback_data = {
            "MessageSid": "SM-status-test", "MessageStatus": "delivered",
            "AccountSid": "AC" + "1" * 32, "To": "whatsapp:+919123456789",
            "From": "whatsapp:+14155238886",
        }
        with self._twilio_env():
            delivered = self.client.post(
                "/api/webhooks/twilio/whatsapp/status", data=callback_data,
                headers={"X-Twilio-Signature": "unit-test-signature"},
            )
            self.assertEqual(delivered.status_code, 200, delivered.text)
            callback_data["MessageStatus"] = "sent"
            stale = self.client.post(
                "/api/webhooks/twilio/whatsapp/status", data=callback_data,
                headers={"X-Twilio-Signature": "unit-test-signature"},
            )
            self.assertEqual(stale.status_code, 200, stale.text)
        with main.get_db() as con:
            row = con.execute("SELECT status, error_code FROM whatsapp_outbound_messages WHERE message_id='twilio:SM-status-test'").fetchone()
            events = con.execute("SELECT event_type, metadata_json FROM timeline WHERE case_id=? AND source='provider_status_webhook'", (case_id,)).fetchall()
        self.assertEqual(row["status"], "delivered")
        self.assertEqual(row["error_code"], "")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "whatsapp_delivered")
        self.assertEqual(json.loads(events[0]["metadata_json"])["provider"], "twilio")

    def test_twilio_mode_case_link_uses_sandbox_sender_and_explicit_test_notice(self):
        case_id = self.create_case()
        with self._twilio_env():
            response = self.client.post(f"/api/cases/{case_id}/whatsapp-link")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        parsed = urlsplit(body["whatsapp_url"])
        self.assertEqual(body["provider"], "twilio")
        self.assertTrue(body["sandbox_join_required"])
        self.assertIn("not a production", body["setup_hint"].lower())
        self.assertEqual(parsed.netloc, "wa.me")
        self.assertEqual(parsed.path, "/14155238886")
        self.assertTrue(parse_qs(parsed.query)["text"][0].startswith("LINK "))

    def test_twilio_sender_uses_form_encoded_api_and_status_callback(self):
        import asyncio
        from backend import twilio_whatsapp

        calls = {}

        class FakeResponse:
            status_code = 201
            def json(self):
                return {"sid": "SM-api-test", "status": "queued"}

        class FakeAsyncClient:
            def __init__(self, *args, **kwargs):
                calls["timeout"] = kwargs.get("timeout")
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                return False
            async def post(self, url, *, auth, data):
                calls.update({"url": url, "auth": auth, "data": data})
                return FakeResponse()

        with self._twilio_env(), patch("backend.twilio_whatsapp.httpx.AsyncClient", FakeAsyncClient):
            result = asyncio.run(twilio_whatsapp.send_text_message("919123456789", "hello from test"))
        self.assertTrue(result["accepted"])
        self.assertEqual(result["message_id"], "SM-api-test")
        self.assertEqual(result["provider"], "twilio")
        self.assertTrue(calls["url"].endswith("/Accounts/AC" + "1" * 32 + "/Messages.json"))
        self.assertEqual(calls["auth"], ("AC" + "1" * 32, "twilio-test-auth-token"))
        self.assertEqual(calls["data"]["To"], "whatsapp:+919123456789")
        self.assertEqual(calls["data"]["From"], "whatsapp:+14155238886")
        self.assertEqual(calls["data"]["Body"], "hello from test")
        self.assertEqual(calls["data"]["StatusCallback"], "https://bolke.test/api/webhooks/twilio/whatsapp/status")

    def test_twilio_inbound_parser_normalizes_sender_and_flags_media(self):
        from backend.twilio_whatsapp import parse_inbound_form
        text_message = parse_inbound_form({
            "MessageSid": "SM-text", "From": "whatsapp:+919340297104",
            "To": "whatsapp:+14155238886", "Body": "START", "NumMedia": "0",
        })
        self.assertIsNotNone(text_message)
        self.assertEqual((text_message.provider, text_message.sender, text_message.message_type, text_message.text),
                         ("twilio", "919340297104", "text", "START"))
        media_message = parse_inbound_form({
            "MessageSid": "SM-media", "From": "whatsapp:+919340297104",
            "To": "whatsapp:+14155238886", "Body": "", "NumMedia": "1",
            "MediaContentType0": "audio/ogg",
        })
        self.assertEqual(media_message.message_type, "unsupported_media")
        self.assertIsNone(parse_inbound_form({"From": "+919340297104", "Body": "START"}))



if __name__ == "__main__":
    unittest.main()
