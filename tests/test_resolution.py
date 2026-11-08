import os
import tempfile
import unittest
from pathlib import Path

# Import the app against an isolated database so tests never touch a developer's local cases.
_TEST_DATA = tempfile.TemporaryDirectory(prefix="bolke-test-")
os.environ["BOLKE_DATA_DIR"] = _TEST_DATA.name

from fastapi.testclient import TestClient  # noqa: E402
from backend import main  # noqa: E402
from backend.main import app  # noqa: E402
from backend.resolution import build_resolution, classify_issue  # noqa: E402


class ResolutionPlaybookTests(unittest.TestCase):
    def test_failed_upi_recommends_bank_contact_with_source(self):
        result = build_resolution(
            "Failed UPI payment",
            "My UPI transaction failed and ₹850 was debited.",
            amount=850,
            payment_status="failed",
        )
        self.assertEqual(result["classification"]["issue_type"], "Failed UPI payment")
        self.assertTrue(any("one hour" in (step["title"] + " " + step["detail"]) for step in result["recommended_steps"]))
        self.assertTrue(any(s["id"] == "npci_upi_faq" for s in result["official_sources"]))

    def test_missing_delivery_is_not_misclassified_as_pending_payment(self):
        issue, _, _ = classify_issue(
            "Other payment issue",
            "I paid for my order, but the food delivery has not arrived.",
        )
        self.assertEqual(issue, "Order paid but not received")

    def test_pending_upi_with_recipient_not_credited_is_still_payment_route(self):
        issue, _, _ = classify_issue(
            "Other payment issue",
            "My UPI payment is pending and the recipient has not received the money.",
        )
        self.assertEqual(issue, "UPI payment pending / recipient not credited")

    def test_pending_payment_is_not_same_as_refund_pending(self):
        pending, _, _ = classify_issue(
            "Failed UPI payment", "UPI transaction pending; amount debited, recipient not credited", "pending"
        )
        refund, _, _ = classify_issue(
            "Refund not received", "My order refund is pending for two days", "refund_pending"
        )
        self.assertEqual(pending, "UPI payment pending / recipient not credited")
        self.assertEqual(refund, "Refund not received")
        # Even if a caller selected generic 'pending', refund wording should not become a UPI transfer case.
        mixed, _, _ = classify_issue("Other payment issue", "My refund is pending and the order was cancelled", "pending")
        self.assertEqual(mixed, "Refund not received")

    def test_razorpay_merchant_settlement_uses_gateway_status_question_not_order_refund(self):
        story = (
            "I have not got the refund of 350 rupees from Razorpay. Several payments. "
            "I extract it from Razorpay to our account. They told me four days, but more than twelve days have passed."
        )
        result = build_resolution("Other payment issue", story, merchant="Razorpay", amount=350, payment_status="refund_pending")
        self.assertEqual(result["classification"]["issue_type"], "Merchant settlement not credited")
        self.assertEqual(result["next_question"]["field"], "settlement_status")
        self.assertIn("Settlements", result["next_question"]["prompt"])
        self.assertIn("merchant_gateway_settlement", [item["id"] for item in result["rulebook"]["matched_rules"]])
        settlement_sources = {source["id"] for item in result["rulebook"]["matched_rules"] for source in item["sources"]}
        self.assertIn("razorpay_settlement_faq", settlement_sources)
        self.assertIn("settlement id", " ".join(step["detail"] for step in result["recommended_steps"]).lower())

    def test_gateway_customer_refund_to_buyer_is_not_misclassified_as_merchant_settlement(self):
        issue, _, _ = classify_issue(
            "Other payment issue",
            "I issued a refund to my customer through Razorpay but the customer has not received the refund.",
        )
        self.assertEqual(issue, "Refund not received")

    def test_suspected_fraud_is_urgent(self):
        result = build_resolution(
            "Other payment issue", "I did not make this transaction and think it may be fraud.", payment_status="unknown"
        )
        self.assertEqual(result["urgency"]["level"], "urgent")
        self.assertTrue(any(s["id"] == "cybercrime_1930" for s in result["official_sources"]))
        self.assertIn("1930", " ".join(step["detail"] for step in result["recommended_steps"]))

    def test_hindi_devanagari_descriptions_get_reasonable_first_pass_routes(self):
        failed, _, _ = classify_issue("Other payment issue", "यूपीआई पेमेंट फेल हो गया और पैसे कट गए")
        refund, _, _ = classify_issue("Other payment issue", "ऑर्डर कैंसल हुआ लेकिन रिफंड नहीं आया")
        duplicate, _, _ = classify_issue("Other payment issue", "मेरे खाते से दो बार पैसे कट गए")
        amount, _, _ = classify_issue("Other payment issue", "मुझसे गलत राशि ली गई, ज्यादा पैसे कटे")
        order, _, _ = classify_issue("Other payment issue", "ऑर्डर किया और पेमेंट किया लेकिन सामान नहीं आया")
        self.assertEqual(failed, "Failed UPI payment")
        self.assertEqual(refund, "Refund not received")
        self.assertEqual(duplicate, "Duplicate charge")
        self.assertEqual(amount, "Incorrect amount")
        self.assertEqual(order, "Order paid but not received")

    def test_received_refund_with_wrong_amount_is_not_misclassified_as_refund_missing(self):
        issue, confidence, _ = classify_issue(
            "Refund not received",
            "The refund arrived, but the amount is less than expected.",
        )
        self.assertEqual(issue, "Incorrect amount")
        self.assertEqual(confidence, "low")

    def test_received_refund_without_other_issue_is_not_assumed_missing(self):
        issue, confidence, _ = classify_issue(
            "Other payment issue",
            "The refund arrived yesterday and I want to understand the transaction.",
        )
        self.assertEqual(issue, "Other payment issue")
        self.assertEqual(confidence, "low")

    def test_refund_missing_intent_has_native_script_coverage_across_indic_languages(self):
        examples = [
            "परतावा आला नाही",
            "রিফান্ড আসেনি",
            "રિફંડ મળ્યું નથી",
            "ரீஃபண்ட் வரவில்லை",
            "రిఫండ్ రాలేదు",
            "ರಿಫಂಡ್ ಬಂದಿಲ್ಲ",
            "റീഫണ്ട് കിട്ടിയില്ല",
            "ਰਿਫੰਡ ਨਹੀਂ ਆਇਆ",
        ]
        for story in examples:
            with self.subTest(story=story):
                issue, _, _ = classify_issue("Other payment issue", story)
                self.assertEqual(issue, "Refund not received")

    def test_hindi_unknown_unauthorised_transaction_gets_urgent_route(self):
        result = build_resolution("Other payment issue", "मैंने यह लेन-देन नहीं किया, यह अनधिकृत लगता है")
        self.assertEqual(result["urgency"]["level"], "urgent")
        self.assertTrue(any(source["id"] == "cybercrime_1930" for source in result["official_sources"]))

    def test_uncertain_case_admits_low_confidence(self):
        result = build_resolution("Other payment issue", "Something looks wrong with a payment.")
        self.assertEqual(result["classification"]["confidence"], "low")
        self.assertTrue(result["missing_information"])
        self.assertTrue(result["limits"])

    def test_fastest_safe_path_asks_for_status_with_inline_choices(self):
        result = build_resolution(
            "Failed UPI payment", "My UPI payment failed and money was debited.",
            payment_status="unknown", contacted_support=False,
        )
        self.assertEqual(result["fastest_path"]["mode"], "clarify")
        self.assertEqual(result["next_question"]["id"], "confirm_payment_status")
        self.assertEqual([item["value"] for item in result["next_question"]["options"]], ["failed", "pending", "successful"])
        self.assertIn("different processes", result["next_question"]["why_it_matters"])

    def test_pending_status_answer_changes_a_failed_story_to_pending_route(self):
        result = build_resolution(
            "Failed UPI payment", "My UPI payment failed but the app now shows pending.",
            payment_status="pending", contacted_support=False,
        )
        self.assertEqual(result["classification"]["issue_type"], "UPI payment pending / recipient not credited")
        self.assertEqual(result["fastest_path"]["mode"], "clarify" if result["next_question"] else "act")
        self.assertEqual(result["recommended_steps"][0]["title"], "Check the transaction status in your UPI app")

    def test_story_and_successful_status_conflict_requires_confirmation(self):
        result = build_resolution(
            "Failed UPI payment", "My UPI payment failed but I think it is fixed.",
            payment_status="successful", contacted_support=False,
        )
        self.assertEqual(result["classification"]["confidence"], "low")
        self.assertEqual(result["classification"]["issue_type"], "Other payment issue")
        self.assertEqual(result["next_question"]["id"], "resolve_status_conflict")
        self.assertEqual({item["value"] for item in result["next_question"]["options"]}, {"failed", "pending"})

    def test_prior_support_contact_shifts_refund_to_existing_thread(self):
        result = build_resolution(
            "Refund not received", "My cancelled order refund has not arrived.",
            contacted_support=True,
        )
        self.assertIn("existing refund complaint", result["recommended_steps"][0]["title"].lower())
        self.assertEqual(result["fastest_path"]["mode"], "follow_up")

    def test_urgent_safety_path_never_waits_for_an_intake_question(self):
        result = build_resolution("Other payment issue", "I did not make this payment; it may be fraud.")
        self.assertEqual(result["fastest_path"]["mode"], "urgent")
        self.assertIsNone(result["next_question"])
        self.assertEqual(result["clarifying_question"], "")


class ResolutionApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

    def test_preview_returns_guidance_and_official_sources(self):
        response = self.client.post("/api/resolution/preview", json={
            "issue_type": "Refund not received",
            "description": "The online order was cancelled and my refund has not arrived.",
            "merchant": "Example Store",
            "payment_status": "refund_pending",
            "contacted_support": False,
        })
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertGreaterEqual(len(body["recommended_steps"]), 2)
        self.assertTrue(any("consumerhelpline.gov.in" in source["url"] for source in body["official_sources"]))
        self.assertIn("no bank or payment network", body["facts"]["statement"])

    def test_public_sample_demo_scenarios_return_source_backed_routes_without_saving_cases(self):
        previous_auth = main.AUTH_REQUIRED
        main.AUTH_REQUIRED = False
        try:
            before = self.client.get("/api/cases")
            self.assertEqual(before.status_code, 200, before.text)
            baseline_count = len(before.json())
            scenarios = [
                {
                    "issue_type": "Failed UPI payment", "merchant": "Sample UPI transaction", "amount": 1200,
                    "payment_status": "failed", "contacted_support": False,
                    "description": "Mere ₹1,200 account se debit hue, lekin UPI app mein transaction failed dikh raha hai. Refund abhi nahi aaya.",
                    "expected_issue": "Failed UPI payment", "expected_source_domain": "npci.org.in",
                },
                {
                    "issue_type": "Refund not received", "merchant": "Sample online merchant", "amount": 850,
                    "payment_status": "refund_pending", "contacted_support": True,
                    "description": "Maine ₹850 ka order cancel kiya tha. Merchant ne refund initiated bola, lekin refund abhi tak account mein nahi aaya. Support ko pehle contact kiya hai.",
                    "expected_issue": "Refund not received", "expected_source_domain": "consumerhelpline.gov.in",
                },
            ]
            for scenario in scenarios:
                with self.subTest(issue=scenario["expected_issue"]):
                    expected_issue = scenario.pop("expected_issue")
                    expected_domain = scenario.pop("expected_source_domain")
                    response = self.client.post("/api/resolution/preview", json=scenario)
                    self.assertEqual(response.status_code, 200, response.text)
                    body = response.json()
                    self.assertEqual(body["classification"]["issue_type"], expected_issue)
                    self.assertTrue(body["recommended_steps"])
                    self.assertTrue(any(expected_domain in source["url"] for source in body["official_sources"]))
                    self.assertIn("no bank or payment network", body["facts"]["statement"])
                    self.assertNotIn("case_id", body, "preview response should not imply a persisted case")
            after = self.client.get("/api/cases")
            self.assertEqual(after.status_code, 200, after.text)
            self.assertEqual(len(after.json()), baseline_count, "public sample scenarios must remain read-only")
        finally:
            main.AUTH_REQUIRED = previous_auth

    def test_preview_returns_merchant_specific_official_route_and_reviewable_draft(self):
        response = self.client.post("/api/resolution/preview", json={
            "issue_type": "Refund not received",
            "description": "Zomato promised the refund in 3 days but it is still missing after 8 days.",
            "merchant": "Zomato",
            "amount": 350,
            "payment_status": "refund_pending",
            "contacted_support": True,
        })
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["support_destinations"][0]["id"], "zomato")
        self.assertTrue(any(item["id"] == "national_consumer_helpline" for item in body["support_destinations"]))
        self.assertIn("Zomato", body["suggested_support_draft"]["message"])
        self.assertIn("₹350", body["suggested_support_draft"]["message"])
        self.assertIn("Draft only", body["suggested_support_draft"]["notice"])
        self.assertTrue(all(item["url"].startswith("https://") for item in body["support_destinations"]))

    def test_amounts_mentioned_in_story_are_confirmation_prompts_not_assumed_facts(self):
        unentered = build_resolution(
            "Other payment issue", "I expected ₹800 but ₹850 was debited.", amount=None,
        )
        self.assertEqual(unentered["facts"]["amounts_mentioned_in_story"], [800.0, 850.0])
        self.assertTrue(unentered["facts"]["amount_needs_confirmation"])
        self.assertIn("Confirm which amount in your story is the disputed amount", unentered["missing_information"])

        conflicting = build_resolution(
            "Incorrect amount", "The receipt says ₹800 but the account shows ₹850.", amount=850,
        )
        self.assertTrue(conflicting["facts"]["amount_needs_confirmation"])
        self.assertIn("Confirm which amount in your story is the disputed amount", conflicting["missing_information"])

        aligned = build_resolution(
            "Failed UPI payment", "₹850 was debited in a failed UPI transaction.", amount=850,
        )
        self.assertFalse(aligned["facts"]["amount_needs_confirmation"])

    def test_preview_redacts_sensitive_values_before_returning_guidance(self):
        response = self.client.post("/api/resolution/preview", json={
            "issue_type": "Failed UPI payment",
            "description": "UPI PIN is 1234. Payment failed and ₹850 was debited.",
            "payment_status": "failed",
        })
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertNotIn("1234", body["summary"])
        self.assertIn("privacy_notice", body)
        self.assertIn("OTP/PIN", body["privacy_notice"]["redacted_types"])

    def test_create_case_stores_resolution_and_progress(self):
        response = self.client.post("/api/cases", json={
            "issue_type": "Failed UPI payment",
            "merchant": "Test UPI app",
            "amount": 250,
            "payment_date": "2026-10-16",
            "language_code": "hi-IN",
            "payment_status": "failed",
            "contacted_support": False,
            "description": "UPI transaction failed but my bank account was debited.",
        })
        self.assertEqual(response.status_code, 201, response.text)
        case = response.json()
        self.assertEqual(case["case_stage"], "Needs next step")
        self.assertTrue(case["resolution"]["recommended_steps"])
        self.assertIn("npci_upi_faq", [s["id"] for s in case["resolution"]["official_sources"]])
        self.assertNotIn("owner_id", case)

        update = self.client.patch(f"/api/cases/{case['case_id']}/progress", json={
            "case_stage": "Contacted support",
            "note": "Called the support channel; acknowledgement saved privately.",
        })
        self.assertEqual(update.status_code, 200, update.text)
        updated = update.json()
        self.assertEqual(updated["case_stage"], "Contacted support")
        self.assertTrue(any(e["event_type"] == "progress" for e in updated["timeline"]))
        self.assertTrue(any("self-reported" in e["message"] for e in updated["timeline"]))

    def test_refresh_guidance_reclassifies_existing_zomato_refund_case(self):
        story = ("hey i have ordered ₹850 food item from zomato but due to certain reason "
                 "they were not able to lower it and they have tell me like they will give the "
                 "refund back in two to three days but it has been more than seven days i do not "
                 "get my refund back i try to contact them through the contact support but they "
                 "are not answering please help me to solve it")
        created = self.client.post("/api/cases", json={
            "issue_type": "Other payment issue", "merchant": "Zomato", "amount": 850,
            "payment_date": "", "language_code": "en-IN", "payment_status": "refund_pending",
            "contacted_support": True, "description": story,
        })
        self.assertEqual(created.status_code, 201, created.text)
        case_id = created.json()["case_id"]
        # Simulate an older saved case created before automatic issue reclassification existed.
        with main.get_db() as con:
            con.execute("UPDATE cases SET issue_type='Other payment issue' WHERE case_id=?", (case_id,))
        refreshed = self.client.post(f"/api/cases/{case_id}/refresh-guidance")
        self.assertEqual(refreshed.status_code, 200, refreshed.text)
        case = refreshed.json()
        self.assertEqual(case["issue_type"], "Refund not received")
        self.assertEqual(case["resolution"]["classification"]["issue_type"], "Refund not received")
        self.assertTrue(any(event["event_type"] == "guidance_refreshed" for event in case["timeline"]))

    def test_editing_case_facts_recalculates_the_guidance_plan(self):
        created = self.client.post("/api/cases", json={
            "issue_type": "Other payment issue", "merchant": "Test shop", "amount": 100,
            "language_code": "en-IN", "payment_status": "unknown",
            "description": "I am having a payment issue with my order.",
        })
        self.assertEqual(created.status_code, 201, created.text)
        case_id = created.json()["case_id"]
        updated = self.client.put(f"/api/cases/{case_id}", json={
            "issue_type": "Other payment issue", "merchant": "Zomato", "amount": 850,
            "payment_date": "", "language_code": "en-IN", "payment_status": "refund_pending",
            "contacted_support": True,
            "description": "Zomato cancelled my order and I have not received my refund.",
        })
        self.assertEqual(updated.status_code, 200, updated.text)
        case = updated.json()
        self.assertEqual(case["merchant"], "Zomato")
        self.assertEqual(case["issue_type"], "Refund not received")
        self.assertTrue(any(event["event_type"] == "details_updated" for event in case["timeline"]))

    def test_fastest_safe_path_answers_can_update_a_saved_case_in_sequence(self):
        created = self.client.post("/api/cases", json={
            "issue_type": "Failed UPI payment", "merchant": "Demo UPI app", "amount": 1200,
            "language_code": "en-IN", "payment_status": "unknown", "contacted_support": None,
            "description": "My UPI payment failed and money was debited.",
        })
        self.assertEqual(created.status_code, 201, created.text)
        case = created.json()
        case_id = case["case_id"]
        self.assertEqual(case["resolution"]["next_question"]["id"], "confirm_payment_status")

        status_answer = self.client.put(f"/api/cases/{case_id}", json={
            "issue_type": case["issue_type"], "merchant": case["merchant"], "amount": case["amount"],
            "payment_date": case["payment_date"], "language_code": case["language_code"],
            "payment_status": "failed", "contacted_support": None, "description": case["description"],
        })
        self.assertEqual(status_answer.status_code, 200, status_answer.text)
        updated = status_answer.json()
        self.assertEqual(updated["resolution"]["next_question"]["id"], "confirm_support_contact")
        self.assertEqual(updated["payment_status"], "failed")

        support_answer = self.client.put(f"/api/cases/{case_id}", json={
            "issue_type": updated["issue_type"], "merchant": updated["merchant"], "amount": updated["amount"],
            "payment_date": updated["payment_date"], "language_code": updated["language_code"],
            "payment_status": updated["payment_status"], "contacted_support": True,
            "description": updated["description"],
        })
        self.assertEqual(support_answer.status_code, 200, support_answer.text)
        final_case = support_answer.json()
        self.assertIsNone(final_case["resolution"]["next_question"])
        self.assertIn("existing", final_case["resolution"]["recommended_steps"][0]["title"].lower())
        self.assertTrue(any(event["event_type"] == "details_updated" for event in final_case["timeline"]))

    def test_evidence_upload_is_stored_and_retrievable_with_case_metadata(self):
        created = self.client.post("/api/cases", json={
            "issue_type": "Refund not received",
            "description": "A synthetic order refund has not arrived yet.",
            "merchant": "Demo shop",
            "payment_status": "refund_pending",
        })
        self.assertEqual(created.status_code, 201, created.text)
        case_id = created.json()["case_id"]
        # Only the signature is validated here; this fixture is not an actual image and
        # must never be represented as a valid PNG for a real-world upload.
        signature_fixture = b"\x89PNG\r\n\x1a\nsynthetic test bytes"
        uploaded = self.client.post(
            f"/api/cases/{case_id}/evidence",
            files={"file": ("synthetic-evidence.png", signature_fixture, "image/png")},
        )
        self.assertEqual(uploaded.status_code, 201, uploaded.text)
        evidence = uploaded.json()["evidence"]
        self.assertEqual(len(evidence), 1)
        evidence_id = evidence[0]["evidence_id"]
        fetched = self.client.get(f"/api/cases/{case_id}/evidence/{evidence_id}")
        self.assertEqual(fetched.status_code, 200, fetched.text)
        self.assertEqual(fetched.content, signature_fixture)

    def test_delete_case_removes_case_timeline_and_evidence_file(self):
        created = self.client.post("/api/cases", json={
            "issue_type": "Other payment issue",
            "description": "A synthetic case to verify deletion and retention behaviour.",
        })
        self.assertEqual(created.status_code, 201, created.text)
        case_id = created.json()["case_id"]
        upload_bytes = b"\x89PNG\r\n\x1a\nsynthetic test bytes"
        uploaded = self.client.post(
            f"/api/cases/{case_id}/evidence",
            files={"file": ("delete-test.png", upload_bytes, "image/png")},
        )
        self.assertEqual(uploaded.status_code, 201, uploaded.text)
        stored_name = uploaded.json()["evidence"][0]["evidence_id"] + ".png"
        stored_path = main.UPLOAD_DIR / stored_name
        self.assertTrue(stored_path.exists())
        deleted = self.client.delete(f"/api/cases/{case_id}")
        self.assertEqual(deleted.status_code, 200, deleted.text)
        self.assertTrue(deleted.json()["deleted"])
        self.assertFalse(stored_path.exists())
        self.assertEqual(self.client.get(f"/api/cases/{case_id}").status_code, 404)

    def test_evidence_upload_rejects_unsupported_extension_and_wrong_signature(self):
        created = self.client.post("/api/cases", json={
            "issue_type": "Other payment issue",
            "description": "A synthetic example payment issue for upload tests.",
        })
        case_id = created.json()["case_id"]
        unsupported = self.client.post(
            f"/api/cases/{case_id}/evidence",
            files={"file": ("note.txt", b"synthetic", "text/plain")},
        )
        wrong_signature = self.client.post(
            f"/api/cases/{case_id}/evidence",
            files={"file": ("image.png", b"not actually a png", "image/png")},
        )
        self.assertEqual(unsupported.status_code, 415)
        self.assertEqual(wrong_signature.status_code, 400)

    def test_invalid_calendar_date_is_rejected_for_preview_and_case_creation(self):
        preview = self.client.post("/api/resolution/preview", json={
            "issue_type": "Other payment issue",
            "description": "Synthetic description for a date validation test.",
            "payment_date": "2026-99-99",
        })
        create = self.client.post("/api/cases", json={
            "issue_type": "Other payment issue",
            "description": "Synthetic description for a date validation test.",
            "payment_date": "2026-99-99",
        })
        self.assertEqual(preview.status_code, 422)
        self.assertEqual(create.status_code, 422)

    def test_invalid_progress_status_is_rejected(self):
        response = self.client.patch("/api/cases/BR-DOESNTEXIST/progress", json={"case_stage": "Bank confirmed refund"})
        self.assertEqual(response.status_code, 422)

    def test_tts_rejects_mismatched_voice_before_calling_external_api(self):
        response = self.client.post("/api/voice/speak", json={"text": "Please check the next step.", "language_code": "mr-IN", "voice": "Nalini"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("not in the Timbre v2.5 catalog", response.json()["detail"])

    def test_hinglish_tts_locale_is_accepted_by_validator_without_api_key(self):
        # Correct locale/voice passes validation; the endpoint then reports missing credentials honestly.
        response = self.client.post("/api/voice/speak", json={"text": "Namaste, please check the next step.", "language_code": "hi-en"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("temporarily unavailable", response.json()["detail"].lower())
        self.assertNotIn("Gnani", response.json()["detail"])

    def test_health_reports_voice_requires_credentials(self):
        body = self.client.get("/api/health").json()
        self.assertTrue(body["resolution_engine_ready"])
        self.assertTrue(body["database_ready"])
        self.assertFalse(body["external_payment_verification"])
        self.assertIn("voice_input_configured", body)
        self.assertNotIn("voice_models", body)
        self.assertNotIn("gnani_stt_configured", body)


if __name__ == "__main__":
    unittest.main()
