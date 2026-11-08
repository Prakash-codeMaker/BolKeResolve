"""Live Resolution Room integration tests; no external Gnani call is made."""
from __future__ import annotations

import os
import tempfile
import unittest
import zipfile
import io
import json
from unittest.mock import patch

_TEST_DATA = tempfile.TemporaryDirectory(prefix="bolke-live-room-test-")
os.environ["BOLKE_DATA_DIR"] = _TEST_DATA.name

from fastapi.testclient import TestClient  # noqa: E402
from backend import main  # noqa: E402


class LiveResolutionRoomTests(unittest.TestCase):
    def setUp(self):
        self.auth_state = main.AUTH_REQUIRED
        main.AUTH_REQUIRED = False
        self.client = TestClient(main.app)
        response = self.client.post("/api/cases", json={
            "issue_type": "Other payment issue",
            "merchant": "",
            "amount": None,
            "payment_date": "",
            "language_code": "hi-IN",
            "payment_status": "unknown",
            "contacted_support": None,
            "description": "Mere paise UPI se kat gaye lekin recipient ko nahi mile.",
        })
        self.assertEqual(response.status_code, 201, response.text)
        self.case_id = response.json()["case_id"]

    def tearDown(self):
        self.client.close()
        main.AUTH_REQUIRED = self.auth_state


    def test_create_case_classifies_razorpay_gateway_funds_flow_as_merchant_settlement(self):
        story = (
            "We have not got the refund of 350 rupees from Razorpay; I made several customer payments.\n"
            "When I try to extract it from Razorpay to our business account, it does not work.\n"
            "They promised four days, but more than twelve days have passed."
        )
        response = self.client.post("/api/cases", json={
            "issue_type": "Other payment issue",
            "merchant": "Razorpay",
            "amount": 350,
            "payment_date": "",
            "language_code": "en-IN",
            "payment_status": "refund_pending",
            "contacted_support": None,
            "description": story,
        })
        self.assertEqual(response.status_code, 201, response.text)
        case = response.json()
        self.assertEqual(case["issue_type"], "Merchant settlement not credited")
        resolution = case["resolution"]
        self.assertEqual(resolution["classification"]["issue_type"], "Merchant settlement not credited")
        self.assertIn("merchant_gateway_settlement", [item["id"] for item in resolution["rulebook"]["matched_rules"]])
        route_ids = [item["id"] for item in resolution["support_destinations"]]
        self.assertEqual(route_ids, ["razorpay"])
        self.assertNotIn("national_consumer_helpline", route_ids)
        self.assertIn("Settlement ID", resolution["suggested_support_draft"]["message"])
        self.assertIn("UTR", resolution["suggested_support_draft"]["message"])

    def test_live_room_creates_persistent_draft_before_any_story_or_media(self):
        # A live session starts with a real case id; evidence never has to wait in page memory.
        response = self.client.post("/api/live-room/cases", json={
            "language_code": "hi-IN", "session_id": "lr_draft_before_media", "started_at": "2026-10-31T10:00:00+05:30"
        })
        self.assertEqual(response.status_code, 201, response.text)
        case = response.json()
        self.assertTrue(case["case_id"].startswith("BR-"))
        self.assertEqual(case["case_stage"], "Draft — collecting details")
        self.assertIn("issue description is being collected", case["description"])
        self.assertTrue(any(event["event_type"] == "live_room_session_started" for event in case["timeline"]))
        self.assertTrue(any(item["case_id"] == case["case_id"] for item in self.client.get("/api/cases").json()))

    def test_automatic_language_draft_does_not_assume_hindi_and_transcript_updates_language(self):
        draft = self.client.post("/api/live-room/cases", json={
            "language_code": "indic-auto", "session_id": "lr_auto_language_test"
        })
        self.assertEqual(draft.status_code, 201, draft.text)
        case = draft.json()
        self.assertEqual(case["language_code"], "en-IN")  # Neutral placeholder until the first transcript.
        self.assertEqual(case["speech_language_mode"], "auto")
        created = next(event for event in case["timeline"] if event["event_type"] == "live_room_draft_created")
        self.assertEqual(created["metadata"]["speech_language_mode"], "auto")

        turn = self.client.post(f"/api/cases/{case['case_id']}/live-room/turn", json={
            "text": "मेरे खाते से पैसे कट गए लेकिन रिफंड नहीं मिला।",
            "language_code": "hi-IN", "session_id": "lr_auto_language_test", "input_source": "live_speech"
        })
        self.assertEqual(turn.status_code, 200, turn.text)
        self.assertEqual(turn.json()["language_code"], "hi-IN")
        event = next(item for item in turn.json()["timeline"] if item["event_type"] == "live_room_user_turn")
        self.assertEqual(event["metadata"]["language_code"], "hi-IN")

    def test_first_live_transcript_replaces_draft_placeholder_and_is_saved(self):
        draft = self.client.post("/api/live-room/cases", json={
            "language_code": "en-IN", "session_id": "lr_draft_first_turn"
        })
        case_id = draft.json()["case_id"]
        turn = self.client.post(f"/api/cases/{case_id}/live-room/turn", json={
            "text": "My UPI payment was debited but the merchant did not receive it.",
            "language_code": "en-IN", "session_id": "lr_draft_first_turn", "input_source": "live_speech"
        })
        self.assertEqual(turn.status_code, 200, turn.text)
        self.assertEqual(turn.json()["description"], "My UPI payment was debited but the merchant did not receive it.")
        self.assertNotIn("issue description is being collected", turn.json()["description"])
        event = next(item for item in turn.json()["timeline"] if item["event_type"] == "live_room_user_turn")
        self.assertEqual(event["metadata"]["input_source"], "live_speech")

    def test_flipkart_refund_story_generates_specific_follow_up_without_reasking_support_contact(self):
        draft = self.client.post("/api/live-room/cases", json={
            "language_code": "indic-auto", "session_id": "lr_flipkart_refund_case"
        })
        self.assertEqual(draft.status_code, 201, draft.text)
        case_id = draft.json()["case_id"]
        story = (
            "We have not got the refund back or ₹6,000 from Flipkart yet. We ordered something "
            "three weeks ago and have already contacted support, but we have got no response to date. "
            "Please help us get it back."
        )
        turn = self.client.post(f"/api/cases/{case_id}/live-room/turn", json={
            "text": story, "language_code": "en-IN", "session_id": "lr_flipkart_refund_case",
            "input_source": "live_speech",
        })
        self.assertEqual(turn.status_code, 200, turn.text)
        saved = turn.json()
        self.assertEqual(saved["merchant"], "Flipkart")
        self.assertEqual(float(saved["amount"]), 6000.0)
        self.assertEqual(saved["contacted_support"], 1)
        self.assertEqual(saved["issue_type"], "Refund not received")

        guidance = self.client.post(f"/api/cases/{case_id}/live-room/guidance", json={
            "language_code": "en-IN", "session_id": "lr_flipkart_refund_case", "finish_intake": True,
        })
        self.assertEqual(guidance.status_code, 200, guidance.text)
        body = guidance.json()["guidance_text"]
        self.assertIn("already contacted Flipkart", body)
        self.assertEqual(guidance.json()["workflow"]["stage"], "existing_support_no_response")
        self.assertEqual(guidance.json()["workflow"]["facts"]["merchant"], "Flipkart")
        self.assertEqual(guidance.json()["workflow"]["facts"]["amount"], 6000.0)
        self.assertEqual(guidance.json()["workflow"]["facts"]["elapsed"], "three weeks")
        self.assertTrue(guidance.json()["workflow"]["facts"]["support_contacted"])
        self.assertIsNone(guidance.json()["workflow"]["next_question"])
        self.assertIn("do not open a duplicate ticket", body.lower())
        self.assertNotIn("What happened to the order", body)
        self.assertNotIn("Have you already contacted", body)


    def test_meesho_six_thousand_two_day_promise_over_six_days_generates_case_specific_action(self):
        session = "lr_meesho_overdue_two_day_promise"
        draft = self.client.post("/api/live-room/cases", json={
            "language_code": "indic-auto", "session_id": session, "allow_ai_assistance": False,
        })
        self.assertEqual(draft.status_code, 201, draft.text)
        case_id = draft.json()["case_id"]

        first_turn = self.client.post(f"/api/cases/{case_id}/live-room/turn", json={
            "text": "I have not got the refund back of 6,000 rupees from Meesho.",
            "language_code": "en-IN", "session_id": session, "input_source": "live_speech",
        })
        self.assertEqual(first_turn.status_code, 200, first_turn.text)
        first_guidance = self.client.post(f"/api/cases/{case_id}/live-room/guidance", json={
            "language_code": "en-IN", "session_id": session, "finish_intake": True,
        })
        self.assertEqual(first_guidance.status_code, 200, first_guidance.text)
        self.assertEqual(first_guidance.json()["workflow"]["next_question"]["field"], "order_outcome")

        answer = self.client.post(f"/api/cases/{case_id}/live-room/turn", json={
            "text": (
                "Some of the products were not available, so they were not able to deliver it. "
                "They told me to give the refund back in two days, but it has been more than six days "
                "and I have not got the refund back."
            ),
            "language_code": "en-IN", "session_id": session, "input_source": "live_speech",
        })
        self.assertEqual(answer.status_code, 200, answer.text)
        workflow = answer.json()["resolution"]["adaptive_workflow"]
        self.assertEqual(workflow["status"], "action")
        self.assertEqual(workflow["stage"], "overdue_refund_promise")
        self.assertIsNone(workflow["next_question"])
        self.assertEqual(workflow["facts"]["merchant"], "Meesho")
        self.assertEqual(workflow["facts"]["amount"], 6000.0)
        self.assertEqual(workflow["facts"]["order_outcome"], "merchant_unable_to_fulfil")
        self.assertEqual(workflow["facts"]["promised_days"], 2)
        self.assertEqual(workflow["facts"]["elapsed_days"], 6)
        self.assertEqual(workflow["support_destinations"][0]["id"], "meesho")
        self.assertIn("₹6,000", workflow["support_draft"]["message"])
        self.assertIn("two days", workflow["support_draft"]["message"])
        self.assertIn("More than 6 days", workflow["support_draft"]["message"])
        self.assertIn("refund initiation date", workflow["message"])
        self.assertNotIn("What happened to the order", workflow["message"])

        # A fresh case read must preserve the action rather than reintroducing
        # the old intake question from legacy resolution fields.
        refreshed = self.client.post(f"/api/cases/{case_id}/live-room/guidance", json={
            "language_code": "en-IN", "session_id": session,
        })
        self.assertEqual(refreshed.status_code, 200, refreshed.text)
        self.assertEqual(refreshed.json()["workflow"]["stage"], "overdue_refund_promise")
        self.assertIsNone(refreshed.json()["workflow"]["next_question"])

    def test_flipkart_whole_order_answer_advances_to_refund_status_and_never_resurrects_old_question(self):
        session = "lr_whole_order_flow"
        draft = self.client.post("/api/live-room/cases", json={
            "language_code": "indic-auto", "session_id": session,
        })
        self.assertEqual(draft.status_code, 201, draft.text)
        case_id = draft.json()["case_id"]
        story = (
            "I have not got the ₹3,000 refund from Flipkart. The order was cancelled "
            "because products were unavailable. Support said they are in the procedure to "
            "give the refund back, but it has been more than seven days."
        )
        saved_story = self.client.post(f"/api/cases/{case_id}/live-room/turn", json={
            "text": story, "language_code": "en-IN", "session_id": session, "input_source": "live_speech",
        })
        self.assertEqual(saved_story.status_code, 200, saved_story.text)
        started = self.client.post(f"/api/cases/{case_id}/live-room/guidance", json={
            "language_code": "en-IN", "session_id": session, "finish_intake": True,
        })
        self.assertEqual(started.status_code, 200, started.text)
        self.assertEqual(started.json()["workflow"]["next_question"]["field"], "refund_scope")

        answer = self.client.post(f"/api/cases/{case_id}/live-room/turn", json={
            "text": "Whole order ma'am", "language_code": "en-IN", "session_id": session, "input_source": "live_speech",
        })
        self.assertEqual(answer.status_code, 200, answer.text)
        workflow = answer.json()["resolution"]["adaptive_workflow"]
        self.assertEqual(workflow["facts"]["refund_scope"], "full_order")
        self.assertEqual(workflow["facts"]["refund_status"], "pending")
        self.assertEqual(workflow["next_question"]["field"], "promised_timeline")
        self.assertEqual(answer.json()["resolution"]["next_question"]["field"], "promised_timeline")
        self.assertNotIn("refund_scope", workflow["next_question"]["field"])

        refreshed = self.client.post(f"/api/cases/{case_id}/live-room/guidance", json={
            "language_code": "en-IN", "session_id": session,
        })
        self.assertEqual(refreshed.status_code, 200, refreshed.text)
        self.assertEqual(refreshed.json()["workflow"]["next_question"]["field"], "promised_timeline")

    def test_evidence_is_saved_to_live_draft_with_capture_provenance_and_hash(self):
        draft = self.client.post("/api/live-room/cases", json={
            "language_code": "hi-IN", "session_id": "lr_evidence_before_story"
        })
        case_id = draft.json()["case_id"]
        jpeg = b"\xff\xd8\xff" + b"synthetic-image-bytes" * 4
        upload = self.client.post(
            f"/api/cases/{case_id}/evidence",
            files={"file": ("camera-proof.jpg", jpeg, "image/jpeg")},
            data={"capture_source": "camera_photo", "session_id": "lr_evidence_before_story", "captured_at": "2026-10-31T10:02:00+05:30"},
        )
        self.assertEqual(upload.status_code, 201, upload.text)
        evidence = upload.json()["evidence"][-1]
        self.assertEqual(evidence["capture_source"], "camera_photo")
        self.assertEqual(evidence["session_id"], "lr_evidence_before_story")
        self.assertEqual(evidence["sha256"], __import__("hashlib").sha256(jpeg).hexdigest())
        event = next(item for item in upload.json()["timeline"] if item["event_type"] == "evidence")
        self.assertEqual(event["metadata"]["capture_source"], "camera_photo")
        self.assertEqual(event["metadata"]["evidence_id"], upload.json()["uploaded_evidence_id"])

    def test_audio_only_webm_is_stored_as_audio_and_reopens_with_audio_mime(self):
        import struct
        # Minimal EBML-prefixed WebM-like bytes exercise MIME routing; the upload
        # validator checks the container signature and not media authenticity.
        content = b"\x1a\x45\xdf\xa3" + b"audio-only-webm-test"
        response = self.client.post(
            f"/api/cases/{self.case_id}/evidence",
            files={"file": ("support-call.webm", content, "audio/webm")},
            data={"capture_source": "audio_recording"},
        )
        self.assertEqual(response.status_code, 201, response.text)
        evidence_id = response.json()["uploaded_evidence_id"]
        detail = self.client.get(f"/api/cases/{self.case_id}")
        self.assertEqual(detail.status_code, 200)
        stored = next(item for item in detail.json()["evidence"] if item["evidence_id"] == evidence_id)
        self.assertEqual(stored["mime_type"], "audio/webm")
        preview = self.client.get(f"/api/cases/{self.case_id}/evidence/{evidence_id}?inline=true")
        self.assertEqual(preview.status_code, 200)
        self.assertIn("audio/webm", preview.headers.get("content-type", ""))

    def test_evidence_endpoint_supports_inline_preview_and_separate_download(self):
        draft = self.client.post("/api/live-room/cases", json={"language_code": "en-IN", "session_id": "lr_inline_preview"})
        case_id = draft.json()["case_id"]
        jpeg = b"\xff\xd8\xff" + b"preview-image" * 5
        uploaded = self.client.post(
            f"/api/cases/{case_id}/evidence",
            files={"file": ("preview.jpg", jpeg, "image/jpeg")},
            data={"capture_source": "camera_photo", "session_id": "lr_inline_preview"},
        )
        evidence_id = uploaded.json()["uploaded_evidence_id"]
        inline = self.client.get(f"/api/cases/{case_id}/evidence/{evidence_id}?inline=true")
        download = self.client.get(f"/api/cases/{case_id}/evidence/{evidence_id}")
        self.assertEqual(inline.status_code, 200)
        self.assertEqual(download.status_code, 200)
        self.assertEqual(inline.content, jpeg)
        self.assertEqual(download.content, jpeg)
        self.assertIn("inline", inline.headers.get("content-disposition", ""))
        self.assertIn("attachment", download.headers.get("content-disposition", ""))
        ranged = self.client.get(f"/api/cases/{case_id}/evidence/{evidence_id}?inline=true", headers={"Range": "bytes=0-7"})
        self.assertEqual(ranged.status_code, 206)
        self.assertEqual(ranged.content, jpeg[:8])
        self.assertIn("bytes 0-7/", ranged.headers.get("content-range", ""))

    def test_complete_evidence_bundle_contains_passport_manifest_and_original_bytes(self):
        draft = self.client.post("/api/live-room/cases", json={
            "language_code": "en-IN", "session_id": "lr_bundle_download_01"
        })
        case_id = draft.json()["case_id"]
        jpg = b"\xff\xd8\xff" + b"bundle-image" * 5
        uploaded = self.client.post(
            f"/api/cases/{case_id}/evidence",
            files={"file": ("receipt.jpg", jpg, "image/jpeg")},
            data={"capture_source": "screen_capture", "session_id": "lr_bundle_download_01"},
        )
        self.assertEqual(uploaded.status_code, 201, uploaded.text)
        response = self.client.get(f"/api/cases/{case_id}/evidence-bundle.zip")
        self.assertEqual(response.status_code, 200, response.text[:300])
        self.assertEqual(response.headers.get("content-type"), "application/zip")
        # Both sides of a live resolution are represented in the export transcript.
        saved_turn = self.client.post(f"/api/cases/{case_id}/live-room/turn", json={
            "text": "The merchant promised a refund.", "language_code": "en-IN",
            "session_id": "lr_bundle_download_01", "input_source": "typed"
        })
        self.assertEqual(saved_turn.status_code, 200, saved_turn.text)
        with main.get_db() as con:
            main.record_case_event(con, case_id, "live_room_agent_guidance", "BolKeResolve guidance: Ask the merchant for the refund reference.", main.now_iso(), actor="assistant", channel="live_room")
        response = self.client.get(f"/api/cases/{case_id}/evidence-bundle.zip")
        self.assertEqual(response.status_code, 200, response.text[:300])
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            names = archive.namelist()
            self.assertIn("case/Resolution-Passport.json", names)
            manifest_name = next(name for name in names if name.endswith("manifest.json"))
            manifest = json.loads(archive.read(manifest_name))
            exhibit = manifest["exhibits"][0]
            self.assertEqual(exhibit["capture_source"], "screen_capture")
            self.assertEqual(__import__("hashlib").sha256(archive.read(exhibit["archive_path"])).hexdigest(), exhibit["sha256"])
            self.assertEqual(archive.read(exhibit["archive_path"]), jpg)
            transcript = archive.read("02-Conversation/Conversation-Transcript.txt").decode("utf-8")
            self.assertIn("The merchant promised a refund.", transcript)
            self.assertIn("Ask the merchant for the refund reference.", transcript)

    def test_conversation_turn_correction_is_append_only_and_survives_case_reload(self):
        draft = self.client.post("/api/live-room/cases", json={
            "language_code": "en-IN", "session_id": "lr_turn_correction_01"
        })
        case_id = draft.json()["case_id"]
        saved = self.client.post(f"/api/cases/{case_id}/live-room/turn", json={
            "text": "The refund was promised on Friday.", "language_code": "en-IN",
            "session_id": "lr_turn_correction_01", "input_source": "live_speech"
        })
        self.assertEqual(saved.status_code, 200, saved.text)
        original = saved.json()["conversation_turns"][0]
        corrected = self.client.patch(f"/api/cases/{case_id}/conversation-turns/{original['turn_id']}", json={
            "text": "The refund was promised by Friday, not on Friday."
        })
        self.assertEqual(corrected.status_code, 201, corrected.text)
        case = corrected.json()["case"]
        self.assertEqual(len(case["conversation_turns"]), 2)
        versions = {item["turn_id"]: item for item in case["conversation_turns"]}
        self.assertEqual(versions[original["turn_id"]]["text"], "The refund was promised on Friday.")
        replacement = next(item for item in case["conversation_turns"] if item.get("supersedes_turn_id"))
        self.assertEqual(replacement["supersedes_turn_id"], original["turn_id"])
        self.assertEqual(replacement["text"], "The refund was promised by Friday, not on Friday.")
        self.assertTrue(any(event["event_type"] == "conversation_turn_corrected" for event in case["timeline"]))

    def test_share_export_contains_only_selected_originals_and_redacts_text_reports(self):
        draft = self.client.post("/api/live-room/cases", json={
            "language_code": "en-IN", "session_id": "lr_share_export_01"
        })
        case_id = draft.json()["case_id"]
        story = "Please contact me at prakash.demo@example.test or 9876543210 about the refund."
        saved = self.client.post(f"/api/cases/{case_id}/live-room/turn", json={
            "text": story, "language_code": "en-IN", "session_id": "lr_share_export_01", "input_source": "typed"
        })
        self.assertEqual(saved.status_code, 200, saved.text)
        first_bytes = b"\xff\xd8\xffshare-selected" * 3
        second_bytes = b"\xff\xd8\xffnot-selected" * 3
        first = self.client.post(f"/api/cases/{case_id}/evidence", files={"file": ("selected.jpg", first_bytes, "image/jpeg")})
        second = self.client.post(f"/api/cases/{case_id}/evidence", files={"file": ("not-selected.jpg", second_bytes, "image/jpeg")})
        self.assertEqual(first.status_code, 201, first.text)
        self.assertEqual(second.status_code, 201, second.text)
        first_id = first.json()["uploaded_evidence_id"]
        response = self.client.get(f"/api/cases/{case_id}/evidence-bundle.zip?mode=share&include_evidence={first_id}&redact_text=true")
        self.assertEqual(response.status_code, 200, response.text[:300])
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            names = archive.namelist()
            self.assertIn("00-Readme/Case-Summary.pdf", names)
            self.assertIn("00-Readme/Export-Manifest.json", names)
            self.assertIn("00-Readme/Evidence-Index.csv", names)
            self.assertIn("00-Readme/Case-Facts.json", names)
            self.assertIn("00-Readme/File-Hashes-SHA256.txt", names)
            self.assertIn("01-Case-History/Timeline.pdf", names)
            self.assertIn("02-Conversation/Conversation-Transcript.pdf", names)
            self.assertIn("02-Conversation/Conversation-Transcript.txt", names)
            self.assertIn("case/Resolution-Passport.json", names, "legacy export path remains available")
            originals = [name for name in names if name.startswith("03-Original-Evidence/")]
            self.assertEqual(len(originals), 1)
            self.assertEqual(archive.read(originals[0]), first_bytes)
            self.assertNotIn(second_bytes, [archive.read(name) for name in originals])
            transcript = archive.read("02-Conversation/Conversation-Transcript.txt").decode("utf-8")
            self.assertIn("[REDACTED EMAIL]", transcript)
            self.assertIn("[REDACTED PHONE]", transcript)
            self.assertTrue(archive.read("00-Readme/Case-Summary.pdf").startswith(b"%PDF"))
            manifest = json.loads(archive.read("00-Readme/Export-Manifest.json"))
            self.assertEqual(manifest["mode"], "share")
            self.assertTrue(manifest["text_redaction_requested"])
            self.assertFalse(manifest["original_evidence_redacted"])
        refreshed = self.client.get(f"/api/cases/{case_id}").json()
        self.assertTrue(any(item["export_mode"] == "share" for item in refreshed["exports"]))
        with main.get_db() as con:
            audit_count = con.execute("SELECT COUNT(*) FROM audit_events WHERE case_id=? AND event_type='case_export_created'", (case_id,)).fetchone()[0]
        self.assertGreaterEqual(audit_count, 1)

    def test_preview_and_download_are_recorded_without_changing_original_file(self):
        file_bytes = b"\xff\xd8\xffaudit-view" * 3
        uploaded = self.client.post(f"/api/cases/{self.case_id}/evidence", files={"file": ("view.jpg", file_bytes, "image/jpeg")})
        evidence_id = uploaded.json()["uploaded_evidence_id"]
        self.assertEqual(self.client.get(f"/api/cases/{self.case_id}/evidence/{evidence_id}?inline=true").content, file_bytes)
        self.assertEqual(self.client.get(f"/api/cases/{self.case_id}/evidence/{evidence_id}").content, file_bytes)
        case = self.client.get(f"/api/cases/{self.case_id}").json()
        event_types = [event["event_type"] for event in case["timeline"]]
        self.assertIn("evidence_previewed", event_types)
        self.assertIn("evidence_downloaded", event_types)
        with main.get_db() as con:
            count = con.execute("SELECT COUNT(*) FROM audit_events WHERE case_id=? AND target_id=?", (self.case_id, evidence_id)).fetchone()[0]
        self.assertEqual(count, 2)

    def test_print_report_contains_exhibit_register_and_evidence_bundle_link(self):
        draft = self.client.post("/api/live-room/cases", json={
            "language_code": "en-IN", "session_id": "lr_print_case_01"
        })
        case_id = draft.json()["case_id"]
        jpg = b"\xff\xd8\xff" + b"print-image" * 5
        self.client.post(f"/api/cases/{case_id}/evidence", files={"file": ("receipt.jpg", jpg, "image/jpeg")})
        response = self.client.get(f"/api/cases/{case_id}/passport/print")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("Evidence register", response.text)
        self.assertIn("E-001", response.text)
        self.assertIn("Download complete case + evidence bundle", response.text)
        self.assertIn("receipt.jpg", response.text)

    def test_live_user_turn_is_saved_and_recalculates_existing_guidance(self):
        response = self.client.post(f"/api/cases/{self.case_id}/live-room/turn", json={
            "text": "The app shows pending, and my bank account was debited yesterday.",
            "language_code": "en-IN",
            "session_id": "lr_test_001",
        })
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertIn("recommended_steps", payload["resolution"])
        events = [e for e in payload["timeline"] if e["event_type"] == "live_room_user_turn"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["actor"], "user")
        self.assertEqual(events[0]["channel"], "live_room")
        self.assertEqual(events[0]["metadata"]["session_id"], "lr_test_001")

    def test_agent_guidance_is_explicitly_marked_as_generated_not_external_reply(self):
        response = self.client.post(f"/api/cases/{self.case_id}/live-room/guidance", json={
            "language_code": "en-IN",
            "session_id": "lr_test_002",
            "finish_intake": True,
        })
        self.assertEqual(response.status_code, 200, response.text)
        event = next(e for e in response.json()["case"]["timeline"] if e["event_type"] == "live_room_agent_guidance")
        self.assertEqual(event["actor"], "assistant")
        self.assertIn("not an external organisation response", event["metadata"]["provenance"])
        self.assertIn("Which payment app", response.json()["guidance_text"])

    def test_guidance_translation_is_opt_in_and_persisted_for_the_live_case(self):
        from unittest.mock import AsyncMock
        draft = self.client.post("/api/live-room/cases", json={
            "language_code": "hi-IN", "session_id": "lr_translation_optin", "allow_ai_assistance": True,
        })
        case_id = draft.json()["case_id"]
        self.client.post(f"/api/cases/{case_id}/live-room/turn", json={
            "text": "Mere UPI payment se paise kat gaye lekin merchant ko nahi mile.",
            "language_code": "hi-IN", "session_id": "lr_translation_optin", "input_source": "live_speech",
        })
        with patch.object(main.agent_assist, "configured", return_value=True), patch.object(
            main.agent_assist, "localize_guidance", new=AsyncMock(return_value="पहले अपने UPI ऐप में शिकायत दर्ज करें।")
        ) as translate:
            response = self.client.post(f"/api/cases/{case_id}/live-room/guidance", json={
                "language_code": "hi-IN", "session_id": "lr_translation_optin", "finish_intake": True,
            })
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["translation_status"], "translated")
        self.assertEqual(response.json()["language_code"], "hi-IN")
        self.assertIn("पहले अपने UPI ऐप", response.json()["guidance_text"])
        translate.assert_awaited_once()
        event = next(e for e in response.json()["case"]["timeline"] if e["event_type"] == "live_room_agent_guidance")
        self.assertEqual(event["metadata"]["translation_status"], "translated")
        self.assertEqual(event["metadata"]["language_code"], "hi-IN")

    def test_guidance_does_not_call_external_translation_without_consent(self):
        from unittest.mock import AsyncMock
        draft = self.client.post("/api/live-room/cases", json={
            "language_code": "hi-IN", "session_id": "lr_translation_no_consent", "allow_ai_assistance": False,
        })
        case_id = draft.json()["case_id"]
        with patch.object(main.agent_assist, "configured", return_value=True), patch.object(
            main.agent_assist, "localize_guidance", new=AsyncMock()
        ) as translate:
            response = self.client.post(f"/api/cases/{case_id}/live-room/guidance", json={
                "language_code": "hi-IN", "session_id": "lr_translation_no_consent",
            })
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["translation_status"], "consent_required")
        translate.assert_not_awaited()

    def test_visual_ai_uses_minimum_case_context_and_only_confirmed_candidates_update_case(self):
        from unittest.mock import AsyncMock
        from PIL import Image
        draft = self.client.post("/api/live-room/cases", json={
            "language_code": "hi-IN", "session_id": "lr_vision_context", "allow_ai_assistance": True,
        })
        case_id = draft.json()["case_id"]
        self.client.post(f"/api/cases/{case_id}/live-room/turn", json={
            "text": "Mere UPI payment se 1200 rupaye kat gaye lekin Zomato ko nahi mile.",
            "language_code": "hi-IN", "session_id": "lr_vision_context", "input_source": "live_speech",
        })
        image_buffer = io.BytesIO()
        Image.new("RGB", (128, 96), "white").save(image_buffer, format="PNG")
        uploaded = self.client.post(f"/api/cases/{case_id}/evidence", files={
            "file": ("payment-proof.png", image_buffer.getvalue(), "image/png")
        }, data={"capture_source": "camera_photo", "session_id": "lr_vision_context"})
        self.assertEqual(uploaded.status_code, 201, uploaded.text)
        evidence_id = uploaded.json()["uploaded_evidence_id"]
        analysis_result = {
            "document_type": "UPI payment screenshot",
            "summary": "The screenshot shows a payment amount and a pending status.",
            "facts": {"merchant": "Zomato", "amount": 1200, "payment_status": "pending"},
            "fact_confidence": {"merchant": "high", "amount": "high", "payment_status": "medium"},
            "observations": ["The visible status text says pending."],
            "missing_information": ["A complete transaction reference is not visible."],
            "suggested_question": "Does your bank app show the same status?",
            "security_warning": False,
            "model": "test-vision-model",
        }
        with patch.object(main.agent_assist, "configured", return_value=True), patch.object(
            main.agent_assist, "analyze_image", new=AsyncMock(return_value=analysis_result)
        ) as analyze:
            preview = self.client.post(f"/api/cases/{case_id}/live-room/evidence/{evidence_id}/analyze", json={
                "consent_to_external_processing": True,
                "question": "Compare this with my payment story.",
            })
        self.assertEqual(preview.status_code, 200, preview.text)
        kwargs = analyze.await_args.kwargs
        self.assertIn("Mere UPI payment", kwargs["case_context"])
        self.assertIn("1200", kwargs["case_context"])
        before_confirmation = self.client.post(f"/api/cases/{case_id}/live-room/guidance", json={"language_code": "en-IN", "session_id": "lr_vision_context", "finish_intake": True})
        self.assertEqual(before_confirmation.status_code, 200, before_confirmation.text)
        before_event = next(e for e in before_confirmation.json()["case"]["timeline"] if e["event_type"] == "live_room_agent_guidance")
        self.assertFalse(before_event["metadata"]["confirmed_evidence_context_used"])
        self.assertTrue(preview.json()["notice"].startswith("The selected image and minimum relevant case details"))
        confirmation = self.client.post(f"/api/cases/{case_id}/live-room/evidence-analysis/confirm", json={
            "analysis_id": preview.json()["analysis_id"], "confirmed": True,
            "accepted_fields": ["merchant", "amount", "payment_status"], "apply_fields": ["merchant", "amount"],
        })
        self.assertEqual(confirmation.status_code, 201, confirmation.text)
        self.assertEqual(confirmation.json()["case"]["merchant"], "Zomato")
        self.assertEqual(float(confirmation.json()["case"]["amount"]), 1200.0)
        confirmed_event = next(e for e in confirmation.json()["case"]["timeline"] if e["event_type"] == "live_room_evidence_analysis_confirmed")
        self.assertEqual(confirmed_event["metadata"]["confirmed_fields"]["payment_status"], "pending")
        self.assertIn("source exhibit", confirmed_event["message"].lower())
        guidance = self.client.post(f"/api/cases/{case_id}/live-room/guidance", json={"language_code": "en-IN", "session_id": "lr_vision_context"})
        self.assertEqual(guidance.status_code, 200, guidance.text)
        guidance_event = next(e for e in guidance.json()["case"]["timeline"] if e["event_type"] == "live_room_agent_guidance")
        self.assertTrue(guidance_event["metadata"]["confirmed_evidence_context_used"])

    def test_visual_analysis_never_routes_on_unconfirmed_ai_summary(self):
        # The model may describe an image, but only explicitly confirmed fields
        # are allowed into the rule-engine context.
        draft = self.client.post("/api/live-room/cases", json={"language_code": "en-IN", "session_id": "lr_unconfirmed_summary"})
        case_id = draft.json()["case_id"]
        self.client.post(f"/api/cases/{case_id}/live-room/turn", json={"text": "My refund is still missing from the merchant.", "language_code": "en-IN", "session_id": "lr_unconfirmed_summary"})
        with main.get_db() as con:
            con.execute("INSERT INTO timeline (event_id,case_id,event_type,message,created_at,actor,channel,source,metadata_json) VALUES (?,?,?,?,?,?,?,?,?)", (
                "unconfirmed-summary-test", case_id, "live_room_evidence_analysis_confirmed", "Model summary only", main.now_iso(), "assistant", "live_room", "test",
                json.dumps({"confirmed_fields": {}, "confirmed_summary": "The model guessed the merchant is Fraud Store."}),
            ))
            context = main._confirmed_live_evidence_context(con, case_id)
        self.assertNotIn("Fraud Store", context)

    def test_visual_ai_requires_explicit_per_image_consent(self):
        response = self.client.post(f"/api/cases/{self.case_id}/live-room/evidence/does-not-matter/analyze", json={
            "consent_to_external_processing": False,
        })
        self.assertEqual(response.status_code, 400)

    def test_live_user_turn_scrubs_sensitive_looking_values_before_storage(self):
        response = self.client.post(f"/api/cases/{self.case_id}/live-room/turn", json={
            "text": "Support asked me to share OTP 123456 before my refund.",
            "language_code": "en-IN",
            "session_id": "lr_test_003",
            "input_source": "imported_call_recording",
        })
        self.assertEqual(response.status_code, 200, response.text)
        events = [e for e in response.json()["timeline"] if e["event_type"] == "live_room_user_turn"]
        self.assertTrue(events)
        self.assertNotIn("123456", events[0]["message"])
        self.assertEqual(events[0]["metadata"]["input_source"], "imported_call_recording")
        self.assertIn("uploaded recording", events[0]["metadata"]["provenance"])

    def test_live_user_turn_rejects_unknown_language(self):
        response = self.client.post(f"/api/cases/{self.case_id}/live-room/turn", json={
            "text": "A sufficiently long statement.", "language_code": "xx-XX"
        })
        self.assertEqual(response.status_code, 400)

    def test_short_webm_video_evidence_is_stored_in_same_case(self):
        content = b"\x1aE\xdf\xa3" + b"synthetic-webm-payload" * 5
        response = self.client.post(
            f"/api/cases/{self.case_id}/evidence",
            files={"file": ("support-clip.webm", content, "video/webm")},
        )
        self.assertEqual(response.status_code, 201, response.text)
        payload = response.json()
        self.assertEqual(payload["evidence"][-1]["mime_type"], "video/webm")
        self.assertEqual(payload["uploaded_evidence_id"], payload["evidence"][-1]["evidence_id"])

    def test_invalid_webm_signature_is_rejected(self):
        response = self.client.post(
            f"/api/cases/{self.case_id}/evidence",
            files={"file": ("bad.webm", b"not-a-webm-file", "video/webm")},
        )
        self.assertEqual(response.status_code, 400)

    def test_imported_support_audio_is_saved_to_the_same_case(self):
        # Minimal RIFF/WAVE signature; this test verifies storage routing, not audio decoding.
        wav = b"RIFF" + (36).to_bytes(4, "little") + b"WAVE" + b"fmt " + b"\x10\x00\x00\x00" + b"\x01\x00\x01\x00" + b"\x80>\x00\x00" + b"\x00}\x00\x00" + b"\x02\x00\x10\x00" + b"data" + b"\x00\x00\x00\x00"
        response = self.client.post(
            f"/api/cases/{self.case_id}/evidence",
            files={"file": ("support-call.wav", wav, "audio/wav")},
        )
        self.assertEqual(response.status_code, 201, response.text)
        evidence = next(item for item in response.json()["evidence"] if item["original_name"] == "support-call.wav")
        self.assertEqual(evidence["mime_type"], "audio/wav")
        self.assertEqual(evidence["size_bytes"], len(wav))

    def test_live_session_start_and_end_are_recorded_in_existing_case_timeline(self):
        started = self.client.post(f"/api/cases/{self.case_id}/live-room/session-event", json={
            "event": "started", "session_id": "lr_lifecycle_01", "started_at": "2026-10-31T10:00:00+05:30"
        })
        self.assertEqual(started.status_code, 200, started.text)
        ended = self.client.post(f"/api/cases/{self.case_id}/live-room/session-event", json={
            "event": "ended", "session_id": "lr_lifecycle_01"
        })
        self.assertEqual(ended.status_code, 200, ended.text)
        events = ended.json()["timeline"]
        start_event = next(event for event in events if event["event_type"] == "live_room_session_started")
        end_event = next(event for event in events if event["event_type"] == "live_room_session_ended")
        self.assertEqual(start_event["metadata"]["session_id"], "lr_lifecycle_01")
        self.assertEqual(start_event["metadata"]["started_at_client"], "2026-10-31T10:00:00+05:30")
        self.assertEqual(end_event["metadata"]["session_id"], "lr_lifecycle_01")

    def test_live_room_events_are_preserved_in_resolution_passport(self):
        self.client.post(f"/api/cases/{self.case_id}/live-room/turn", json={
            "text": "The merchant said the refund will be checked tomorrow.",
            "language_code": "en-IN",
            "session_id": "lr_export_01",
        })
        self.client.post(f"/api/cases/{self.case_id}/live-room/guidance", json={
            "language_code": "en-IN",
            "session_id": "lr_export_01",
            "finish_intake": True,
        })
        passport = self.client.get(f"/api/cases/{self.case_id}/passport.json")
        self.assertEqual(passport.status_code, 200, passport.text)
        events = passport.json()["case"]["timeline"]
        self.assertTrue(any(event["event_type"] == "live_room_user_turn" for event in events))
        self.assertTrue(any(event["event_type"] == "live_room_agent_guidance" for event in events))


    def test_case_interpretation_consent_is_separate_and_persisted(self):
        draft = self.client.post("/api/live-room/cases", json={
            "language_code": "en-IN", "session_id": "lr_case_ai_consent", "allow_ai_case_interpretation": True,
        })
        self.assertEqual(draft.status_code, 201, draft.text)
        case_id = draft.json()["case_id"]
        with main.get_db() as con:
            self.assertTrue(main._live_room_case_interpretation_consent(con, case_id))
            event = con.execute("SELECT metadata_json FROM timeline WHERE case_id=? AND event_type='live_room_case_ai_consent' ORDER BY rowid DESC LIMIT 1", (case_id,)).fetchone()
            metadata = json.loads(event["metadata_json"])
            self.assertIn("raw audio and images are not included", metadata["scope"])
        updated = self.client.post(f"/api/cases/{case_id}/live-room/case-ai-consent", json={
            "allowed": False, "session_id": "lr_case_ai_consent_off",
        })
        self.assertEqual(updated.status_code, 200, updated.text)
        with main.get_db() as con:
            self.assertFalse(main._live_room_case_interpretation_consent(con, case_id))

    def test_consented_semantic_interpreter_advances_from_natural_language_answer(self):
        from unittest.mock import AsyncMock
        draft = self.client.post("/api/live-room/cases", json={
            "language_code": "en-IN", "session_id": "lr_semantic_scope", "allow_ai_case_interpretation": True,
        })
        case_id = draft.json()["case_id"]
        story = "My Meesho refund of ₹3,000 has not arrived. The order was cancelled. Support says they are processing it."
        self.client.post(f"/api/cases/{case_id}/live-room/turn", json={
            "text": story, "language_code": "en-IN", "session_id": "lr_semantic_scope",
        })
        finished = self.client.post(f"/api/cases/{case_id}/live-room/guidance", json={
            "language_code": "en-IN", "session_id": "lr_semantic_scope", "finish_intake": True,
        })
        self.assertEqual(finished.status_code, 200, finished.text)
        self.assertEqual(finished.json()["workflow"]["next_question"]["field"], "refund_scope")
        latest = "The refund covers everything in the order."
        self.client.post(f"/api/cases/{case_id}/live-room/turn", json={
            "text": latest, "language_code": "en-IN", "session_id": "lr_semantic_scope",
        })
        interpretation = {
            "intent": "answer_current_question", "issue_family": "refund",
            "summary": "You report a ₹3,000 Meesho refund for the cancelled full order; support says it is processing.",
            "fact_updates": [
                {"field": "refund_scope", "value": "full_order", "evidence_quote": "refund covers everything in the order", "confidence": 0.98},
                {"field": "refund_status", "value": "pending", "evidence_quote": "Support says they are processing it", "confidence": 0.98},
                {"field": "support_contacted", "value": "yes", "evidence_quote": "Support says they are processing it", "confidence": 0.98},
            ],
            "different_issue": False, "question_rewrite": "", "action_explanation": "", "language": "English",
        }
        with patch.object(main.agent_assist, "configured", return_value=True), patch.object(
            main.agent_assist, "interpret_case_conversation", new=AsyncMock(return_value=interpretation)
        ) as interpret, patch.object(
            main.agent_assist, "compose_case_guidance", new=AsyncMock(return_value="I understand this covers the entire ₹3,000 Meesho order. What refund date or working-day window did support give you?")
        ) as compose:
            response = self.client.post(f"/api/cases/{case_id}/live-room/guidance", json={
                "language_code": "en-IN", "session_id": "lr_semantic_scope",
            })
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["case_interpretation_used"])
        self.assertEqual(response.json()["workflow"]["facts"]["refund_scope"], "full_order")
        self.assertEqual(response.json()["workflow"]["next_question"]["field"], "promised_timeline")
        self.assertIn("entire ₹3,000 Meesho order", response.json()["guidance_text"])
        interpret.assert_awaited_once()
        compose.assert_awaited_once()

    def test_semantic_new_issue_reclassifies_instead_of_staying_in_old_refund_playbook(self):
        from unittest.mock import AsyncMock
        draft = self.client.post("/api/live-room/cases", json={
            "language_code": "en-IN", "session_id": "lr_semantic_new_issue", "allow_ai_case_interpretation": True,
        })
        case_id = draft.json()["case_id"]
        story = "My Meesho refund of ₹3,000 has not arrived. The order was cancelled."
        self.client.post(f"/api/cases/{case_id}/live-room/turn", json={"text": story, "language_code": "en-IN", "session_id": "lr_semantic_new_issue"})
        self.client.post(f"/api/cases/{case_id}/live-room/guidance", json={"language_code": "en-IN", "session_id": "lr_semantic_new_issue", "finish_intake": True})
        latest = "Actually, this is a separate Google Pay UPI transfer. The money was debited but the recipient was not credited."
        self.client.post(f"/api/cases/{case_id}/live-room/turn", json={"text": latest, "language_code": "en-IN", "session_id": "lr_semantic_new_issue"})
        interpretation = {
            "intent": "new_issue", "issue_family": "payment_transaction",
            "summary": "This new issue concerns a Google Pay UPI transfer debited without recipient credit.",
            "fact_updates": [
                {"field": "issue_family", "value": "payment_transaction", "evidence_quote": "separate Google Pay UPI transfer", "confidence": 0.99},
                {"field": "payment_app", "value": "Google Pay", "evidence_quote": "Google Pay UPI transfer", "confidence": 0.99},
                {"field": "payment_method", "value": "UPI", "evidence_quote": "UPI transfer", "confidence": 0.99},
                {"field": "transaction_status", "value": "debit_no_credit", "evidence_quote": "money was debited but the recipient was not credited", "confidence": 0.99},
            ],
            "different_issue": True, "question_rewrite": "", "action_explanation": "", "language": "English",
        }
        with patch.object(main.agent_assist, "configured", return_value=True), patch.object(
            main.agent_assist, "interpret_case_conversation", new=AsyncMock(return_value=interpretation)
        ), patch.object(
            main.agent_assist, "compose_case_guidance", new=AsyncMock(return_value="This is a separate UPI transfer issue. What date did the payment occur?"),
        ):
            response = self.client.post(f"/api/cases/{case_id}/live-room/guidance", json={"language_code": "en-IN", "session_id": "lr_semantic_new_issue"})
        self.assertEqual(response.status_code, 200, response.text)
        workflow = response.json()["workflow"]
        self.assertEqual(workflow["facts"]["issue_family"], "payment_transaction")
        self.assertEqual(workflow["facts"]["merchant"], "")
        self.assertIsNone(workflow["facts"]["amount"])
        self.assertEqual(workflow["stage"], "upi_intake")
        self.assertNotEqual(workflow["stage"], "refund_intake")

    def test_existing_support_no_reply_changes_overdue_refund_action_and_does_not_replay_old_step(self):
        session = "lr_support_no_reply_update"
        draft = self.client.post("/api/live-room/cases", json={
            "language_code": "indic-auto", "session_id": session, "allow_ai_assistance": False,
        })
        self.assertEqual(draft.status_code, 201, draft.text)
        case_id = draft.json()["case_id"]
        story = (
            "I have not received the ₹6,000 refund from Meesho. The entire order was cancelled "
            "because products were unavailable. Support promised the refund in 2 days, but more than 6 days have passed."
        )
        first = self.client.post(f"/api/cases/{case_id}/live-room/turn", json={
            "text": story, "language_code": "en-IN", "session_id": session, "input_source": "live_speech",
        })
        self.assertEqual(first.status_code, 200, first.text)
        initial = self.client.post(f"/api/cases/{case_id}/live-room/guidance", json={
            "language_code": "en-IN", "session_id": session, "finish_intake": True,
        })
        self.assertEqual(initial.status_code, 200, initial.text)
        self.assertEqual(initial.json()["workflow"]["stage"], "overdue_refund_promise")

        update = self.client.post(f"/api/cases/{case_id}/live-room/turn", json={
            "text": "I have contacted them but still not got a reply back. Any more follow up can I do?",
            "language_code": "en-IN", "session_id": session, "input_source": "live_speech",
        })
        self.assertEqual(update.status_code, 200, update.text)
        workflow = update.json()["resolution"]["adaptive_workflow"]
        self.assertTrue(workflow["facts"]["support_contacted"])
        self.assertEqual(workflow["facts"]["support_reference"], "no_response_or_reference")
        self.assertEqual(workflow["stage"], "existing_support_no_response")
        self.assertIn("same existing support conversation", workflow["current_step"]["detail"].lower())
        self.assertIn("earlier contact", workflow["support_draft"]["message"].lower())
        self.assertNotEqual(workflow["message"], initial.json()["workflow"]["message"])

        refreshed = self.client.post(f"/api/cases/{case_id}/live-room/guidance", json={
            "language_code": "en-IN", "session_id": session,
        })
        self.assertEqual(refreshed.status_code, 200, refreshed.text)
        self.assertEqual(refreshed.json()["workflow"]["stage"], "existing_support_no_response")
        self.assertIn("do not open a duplicate ticket", refreshed.json()["workflow"]["message"].lower())

    def test_reopened_case_collects_update_before_advancing_workflow(self):
        draft = self.client.post("/api/live-room/cases", json={"language_code": "en-IN", "session_id": "lr_resume_case"})
        case_id = draft.json()["case_id"]
        story = "Meesho refund of ₹3,000 not received. The return was picked up. Refund initiated."
        self.client.post(f"/api/cases/{case_id}/live-room/turn", json={"text": story, "language_code": "en-IN", "session_id": "lr_resume_case"})
        finished = self.client.post(f"/api/cases/{case_id}/live-room/guidance", json={"language_code": "en-IN", "session_id": "lr_resume_case", "finish_intake": True})
        self.assertEqual(finished.status_code, 200, finished.text)
        started = self.client.post(f"/api/cases/{case_id}/live-room/session-event", json={"event": "started", "session_id": "lr_resume_again"})
        self.assertTrue(started.json()["resolution"]["adaptive_workflow"]["collecting_update"])
        turn = self.client.post(f"/api/cases/{case_id}/live-room/turn", json={"text": "Meesho support replied that the refund will be credited in 5 working days.", "language_code": "en-IN", "session_id": "lr_resume_again"})
        self.assertEqual(turn.json()["resolution"]["adaptive_workflow"]["status"], "collecting_update")
        still_collecting = self.client.post(f"/api/cases/{case_id}/live-room/guidance", json={"language_code": "en-IN", "session_id": "lr_resume_again"})
        self.assertEqual(still_collecting.json()["workflow"]["status"], "collecting_update")
        advanced = self.client.post(f"/api/cases/{case_id}/live-room/guidance", json={"language_code": "en-IN", "session_id": "lr_resume_again", "finish_intake": True})
        self.assertNotEqual(advanced.json()["workflow"]["status"], "collecting_update")

    def test_live_room_static_assets_and_capture_permissions_are_served(self):
        home = self.client.get("/")
        worklet = self.client.get("/live-pcm-processor.js")
        css = self.client.get("/live-room.css")
        self.assertEqual(home.status_code, 200)
        self.assertIn('id="liveRoomView"', home.text)
        self.assertIn('id="liveRoomScreenPreview"', home.text)
        self.assertIn('id="liveRoomEvidenceBundleButton"', home.text)
        self.assertIn('id="liveRoomLanguageModeLabel"', home.text)
        self.assertIn('id="liveRoomGuidanceChecklist"', home.text)
        self.assertIn('id="liveRoomFollowupForm"', home.text)
        app_js = (main.FRONTEND_DIR / "app.js").read_text(encoding="utf-8")
        self.assertIn("liveRoomQueueUserText", app_js)
        self.assertIn("liveRoomNormalizeLanguageCode", app_js)
        self.assertIn("liveRoomSaveChecklist", app_js)
        self.assertIn("firstFrame=await liveRoomCanvasFile", app_js)
        self.assertIn("captureSource", app_js) if "captureSource" in app_js else self.assertIn("capture_source", app_js)
        self.assertIn("event.code===4403", app_js)
        self.assertIn("event.code===4429", app_js)
        self.assertIn("liveRoomIsLowInformationUtterance", app_js)
        self.assertIn("if(captureIntent)", app_js)
        self.assertIn("action.dataset.liveIntentAction=kind", app_js)
        self.assertIn("liveRoomOfferCaptureFromIntent('record a clip of the shared screen')", app_js)
        self.assertIn("grid-column:1/-1", css.text)
        self.assertIn("bolkeresolve-shell-v47", (main.FRONTEND_DIR / "sw.js").read_text(encoding="utf-8"))
        self.assertEqual(worklet.status_code, 200)
        self.assertIn("bolke-pcm-processor", worklet.text)
        self.assertEqual(css.status_code, 200)
        self.assertIn("live-room-workspace", css.text)
        self.assertIn("camera=(self)", home.headers.get("permissions-policy", ""))
        self.assertIn("wss:", home.headers.get("content-security-policy", ""))

    def test_live_stt_websocket_reports_missing_provider_key_without_faking_transcription(self):
        with patch.dict(os.environ, {"GNANI_API_KEY": ""}):
            with self.client.websocket_connect(
                "/api/live-room/voice?language_code=indic-auto&sample_rate=48000&voice_profile=laptop",
                headers={"origin": "http://testserver"},
            ) as socket:
                message = socket.receive_json()
                self.assertEqual(message["type"], "error")
                self.assertIn("not configured", message["message"])

    def test_live_stt_proxy_uses_documented_prisma_stream_parameters_without_real_network(self):
        import asyncio
        import json as json_module
        from unittest.mock import AsyncMock

        captured = {}

        class FakeProviderSocket:
            async def recv(self):
                return json_module.dumps({"type": "connected"})

            async def send(self, payload):
                return None

            async def close(self):
                return None

            async def __aiter__(self):
                while True:
                    await asyncio.sleep(60)
                    yield json_module.dumps({"type": "processing"})

        async def fake_connect(uri, **kwargs):
            captured["uri"] = uri
            captured.update(kwargs)
            return FakeProviderSocket()

        with patch.dict(os.environ, {"GNANI_API_KEY": "test-key-not-real", "GNANI_STT_MODEL": "prisma-v2.5"}), patch.object(
            main.websockets, "connect", new=AsyncMock(side_effect=fake_connect)
        ):
            with self.client.websocket_connect(
                "/api/live-room/voice?language_code=indic-auto&sample_rate=48000&voice_profile=laptop",
                headers={"origin": "http://testserver"},
            ) as socket:
                message = socket.receive_json()
                self.assertEqual(message["type"], "connected")
                socket.close()

        self.assertEqual(captured["uri"], "wss://api.vachana.ai/stt/v3/stream")
        headers = captured["additional_headers"]
        self.assertEqual(headers["X-API-Key-ID"], "test-key-not-real")
        self.assertEqual(headers["language_code"], "indic-auto")
        self.assertEqual(headers["model"], "prisma-v3.0")
        self.assertEqual(headers["format"], "transcribe")
        self.assertEqual(headers["x-sample-rate"], "48000")
        self.assertEqual(headers["x-vad-threshold"], "0.62")
        self.assertEqual(headers["x-min-silence-ms"], "600")
        self.assertEqual(headers["x-min-segment-ms"], "100")
        self.assertEqual(headers["x-idle-timeout-sec"], "300")


if __name__ == "__main__":
    unittest.main()
