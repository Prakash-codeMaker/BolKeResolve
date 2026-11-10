"""Tests for condition-aware commitment extraction and reconciliation.

These tests use synthetic statements only. A transcript, uploaded document, or
user-confirmed event is never treated as independent proof of an organisation's
identity or actions.
"""
from __future__ import annotations

import unittest
from datetime import date
from fastapi.testclient import TestClient

from backend import main
from backend.commitments import extract_commitment_candidate, evaluate_commitment


STATEMENT = (
    "Once the return is scanned at the warehouse, we will initiate the "
    "₹1,200 refund within five business days."
)


def make_commitment_candidate(text: str = STATEMENT) -> dict:
    result = extract_commitment_candidate(text)
    if not result.get("candidate"):
        raise AssertionError(f"Expected candidate for test fixture: {result}")
    candidate = dict(result["candidate"])
    candidate["source_type"] = "support_call_transcript"
    return candidate


class CommitmentExtractionTests(unittest.TestCase):
    def test_conditional_statement_extracts_action_amount_condition_and_clock_rule(self):
        result = extract_commitment_candidate(STATEMENT)
        self.assertTrue(result["can_confirm"])
        candidate = result["candidate"]
        self.assertEqual(candidate["speech_act"], "conditional_process_commitment")
        self.assertEqual(candidate["action_code"], "initiate_refund")
        self.assertEqual(candidate["amount_minor_units"], 120000)
        self.assertEqual(candidate["condition_text"], "return is scanned at the warehouse")
        self.assertEqual(candidate["trigger_type"], "condition_met")
        self.assertEqual(candidate["duration_value"], 5)
        self.assertEqual(candidate["duration_max_value"], 5)
        self.assertEqual(candidate["duration_unit"], "day")
        self.assertEqual(candidate["day_type"], "business_day")
        self.assertIn("not a verified company promise", result["notice"])
        self.assertFalse(result["privacy"]["raw_recording_saved"])

    def test_hinglish_conditional_statement_is_extractable_as_a_candidate(self):
        result = extract_commitment_candidate(
            "Return scan hone ke baad hum 5 business days mein refund initiate kar denge."
        )
        self.assertTrue(result["can_confirm"])
        candidate = result["candidate"]
        self.assertEqual(candidate["speech_act"], "conditional_process_commitment")
        self.assertEqual(candidate["action_code"], "initiate_refund")
        self.assertEqual(candidate["trigger_type"], "condition_met")
        self.assertEqual(candidate["duration_value"], 5)

    def test_hedged_statement_is_not_upgraded_to_a_guarantee(self):
        candidate = extract_commitment_candidate("We may process your refund in five business days.")["candidate"]
        self.assertEqual(candidate["speech_act"], "estimated_timeline")
        self.assertEqual(candidate["qualifier"], "may")

    def test_negated_promise_is_preserved_for_manual_review_without_a_deadline(self):
        preview = extract_commitment_candidate(
            "We will not initiate the refund within five business days."
        )
        self.assertTrue(preview["can_confirm"])
        self.assertEqual(preview["candidate"]["speech_act"], "unclassified_statement")
        self.assertEqual(preview["candidate"]["action_code"], "negative_or_refusal")
        self.assertTrue(any("negated promise" in warning for warning in preview["warnings"]))
        evaluation = evaluate_commitment(preview["candidate"], [], today=date(2026, 10, 29))
        self.assertEqual(evaluation["status"], "statement_needs_manual_review")
        self.assertIsNone(evaluation["estimated_due_date"])

    def test_qualifier_in_a_later_sentence_does_not_weaken_prior_commitment(self):
        candidate = extract_commitment_candidate(
            "We will initiate your refund within five business days. You may check the status in the app."
        )["candidate"]
        self.assertEqual(candidate["speech_act"], "process_commitment")
        self.assertEqual(candidate["qualifier"], "stated_by_speaker")

    def test_qualifier_in_an_earlier_unrelated_sentence_does_not_weaken_promise(self):
        candidate = extract_commitment_candidate(
            "You may contact support for updates. We will initiate your refund within five business days."
        )["candidate"]
        self.assertEqual(candidate["speech_act"], "process_commitment")
        self.assertEqual(candidate["qualifier"], "stated_by_speaker")

    def test_unless_exception_is_not_silently_treated_as_unconditional_promise(self):
        preview = extract_commitment_candidate(
            "We will initiate the refund unless the item is found to be damaged."
        )
        self.assertTrue(preview["can_confirm"])
        self.assertEqual(preview["candidate"]["speech_act"], "unclassified_statement")
        self.assertEqual(preview["candidate"]["action_code"], "user_reviewed_action")
        self.assertTrue(any("exception" in warning.lower() for warning in preview["warnings"]))
        evaluation = evaluate_commitment(preview["candidate"], [], today=date(2026, 10, 29))
        self.assertEqual(evaluation["status"], "statement_needs_manual_review")
        self.assertIsNone(evaluation["estimated_due_date"])

    def test_negation_in_unrelated_later_sentence_does_not_reverse_promise(self):
        candidate = extract_commitment_candidate(
            "We will initiate your refund within five business days. We will not share your personal details."
        )["candidate"]
        self.assertEqual(candidate["speech_act"], "process_commitment")
        self.assertEqual(candidate["action_code"], "initiate_refund")

    def test_unactionable_text_is_not_promoted_to_a_commitment(self):
        result = extract_commitment_candidate("Thank you for contacting customer support.")
        self.assertFalse(result["can_confirm"])
        self.assertIsNone(result["candidate"])

    def test_business_day_date_is_an_estimate_excluding_weekends_only(self):
        commitment = make_commitment_candidate()
        events = [{"relation": "triggers", "event_date_confirmed": "2026-10-29"}]
        evaluation = evaluate_commitment(commitment, events, today=date(2026, 10, 29))
        self.assertEqual(evaluation["trigger_date"], "2026-10-29")
        self.assertEqual(evaluation["estimated_due_date"], {"earliest": "2026-11-05", "latest": "2026-11-05"})
        self.assertIn("holidays", evaluation["due_date_note"])
        self.assertIn("not a legal deadline", evaluation["due_date_note"])

    def test_no_confirmed_trigger_date_means_no_clock_or_due_date(self):
        commitment = make_commitment_candidate()
        events = [{"relation": "triggers", "event_date_confirmed": ""}]
        evaluation = evaluate_commitment(commitment, events, today=date(2026, 10, 29))
        self.assertEqual(evaluation["status"], "condition_unknown")
        self.assertIsNone(evaluation["estimated_due_date"])
        self.assertEqual(evaluation["clock_status"], "not_established")

    def test_superseding_statement_is_preserved_as_a_review_event(self):
        commitment = make_commitment_candidate()
        evaluation = evaluate_commitment(
            commitment,
            [
                {"relation": "triggers", "event_date_confirmed": "2026-10-29"},
                {"relation": "supersedes", "source_excerpt_redacted": "We now need 10 business days."},
            ],
            today=date(2026, 10, 29),
        )
        self.assertEqual(evaluation["status"], "commitment_qualified")
        self.assertIn("replace its earlier statement", evaluation["next_action"])
        self.assertEqual(evaluation["estimated_due_date"]["latest"], "2026-11-05")

    def test_conflict_keeps_both_statements_visible_and_needs_review(self):
        commitment = make_commitment_candidate()
        events = [
            {"relation": "supports", "source_excerpt_redacted": STATEMENT},
            {"relation": "contradicts", "source_excerpt_redacted": "We cannot confirm that the return was scanned."},
        ]
        evaluation = evaluate_commitment(commitment, events, today=date(2026, 10, 29))
        self.assertEqual(evaluation["status"], "conflict_needs_review")
        self.assertEqual(evaluation["conflict_count"], 1)
        self.assertIn("Keep both statements", evaluation["next_action"])
        self.assertEqual(len(events), 2)  # evaluation must not overwrite supplied history

    def test_claimed_fulfilment_is_not_independent_proof(self):
        commitment = make_commitment_candidate()
        evaluation = evaluate_commitment(commitment, [{"relation": "fulfils"}], today=date(2026, 10, 29))
        self.assertEqual(evaluation["status"], "reported_fulfilment_needs_check")
        self.assertIn("not proof", evaluation["next_action"])

    def test_hour_level_promise_is_not_given_a_false_date_only_deadline(self):
        commitment = make_commitment_candidate("We will initiate the refund within 5 hours from today.")
        commitment["statement_date"] = "2026-10-29"
        commitment["trigger_type"] = "statement_date"
        evaluation = evaluate_commitment(commitment, [], today=date(2026, 10, 29))
        self.assertEqual(evaluation["status"], "triggered_duration_unclear")
        self.assertIsNone(evaluation["estimated_due_date"])
        self.assertIn("hours-level", evaluation["next_action"])

    def test_five_business_day_refund_promise_from_october_twentieth_may_have_passed(self):
        commitment = make_commitment_candidate(
            "We will initiate your ₹850 refund within 5 business days from today."
        )
        commitment["statement_date"] = "2026-10-20"
        commitment["trigger_type"] = "statement_date"
        evaluation = evaluate_commitment(commitment, [], today=date(2026, 11, 10))
        self.assertEqual(evaluation["estimated_due_date"], {"earliest": "2026-10-27", "latest": "2026-10-27"})
        self.assertEqual(evaluation["status"], "stated_period_may_have_passed")
        self.assertIn("not a legal deadline", evaluation["due_date_note"])
        self.assertIn("Check the original source", evaluation["next_action"])


class CommitmentApiTests(unittest.TestCase):
    def setUp(self):
        self.auth_state = main.AUTH_REQUIRED
        main.AUTH_REQUIRED = False
        self.client = TestClient(main.app)
        response = self.client.post("/api/cases", json={
            "issue_type": "Refund not received",
            "description": "My returned order refund has not arrived.",
            "merchant": "Example Shop",
            "amount": 1200,
            "payment_date": "2026-10-20",
            "language_code": "hi-IN",
            "payment_status": "refund_pending",
            "contacted_support": True,
        })
        self.assertEqual(response.status_code, 201, response.text)
        self.case_id = response.json()["case_id"]

    def tearDown(self):
        try:
            self.client.delete(f"/api/cases/{self.case_id}")
        except Exception:
            pass
        self.client.close()
        main.AUTH_REQUIRED = self.auth_state

    def _preview(self, text: str = STATEMENT):
        return self.client.post(f"/api/cases/{self.case_id}/commitments/preview", json={
            "text": text,
            "source_type": "support_call_transcript",
        })

    def _confirm_payload(self, candidate: dict | None = None) -> dict:
        candidate = candidate or make_commitment_candidate()
        return {
            "confirmed": True,
            "source_type": candidate.get("source_type", "support_call_transcript"),
            "source_label": "Synthetic reviewed support call",
            "source_excerpt": candidate["statement_excerpt"],
            "speech_act": candidate["speech_act"],
            "action_code": candidate["action_code"],
            "action_text": candidate["action_text"],
            "amount_minor_units": candidate["amount_minor_units"],
            "currency": candidate["currency"],
            "condition_text": candidate["condition_text"],
            "trigger_type": candidate["trigger_type"],
            "duration_value": candidate["duration_value"],
            "duration_max_value": candidate["duration_max_value"],
            "duration_unit": candidate["duration_unit"],
            "day_type": candidate["day_type"],
            "qualifier": candidate["qualifier"],
            "statement_date": candidate.get("statement_date", ""),
        }

    def test_preview_does_not_persist_a_candidate(self):
        marker = "SYNTHETIC_PRIVATE_TRANSCRIPT_MARKER_4912"
        before = self.client.get(f"/api/cases/{self.case_id}").json()
        response = self._preview(f"{marker}. {STATEMENT}")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["can_confirm"])
        after = self.client.get(f"/api/cases/{self.case_id}").json()
        self.assertEqual(after["commitments"], [])
        self.assertEqual(len(after["timeline"]), len(before["timeline"]))
        self.assertNotIn(marker, after["description"])

    def test_confirmation_is_required_before_persistence(self):
        payload = self._confirm_payload()
        payload["confirmed"] = False
        response = self.client.post(f"/api/cases/{self.case_id}/commitments/confirm", json=payload)
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(self.client.get(f"/api/cases/{self.case_id}").json()["commitments"], [])

    def test_commitment_persists_and_does_not_claim_source_authenticity(self):
        response = self.client.post(
            f"/api/cases/{self.case_id}/commitments/confirm",
            json=self._confirm_payload(),
        )
        self.assertEqual(response.status_code, 201, response.text)
        commitment = response.json()
        self.assertEqual(commitment["condition_text"], "return is scanned at the warehouse")
        self.assertFalse(commitment["source_authenticity_verified"])
        self.assertEqual(commitment["evaluation"]["status"], "condition_unknown")
        self.assertEqual(len(commitment["events"]), 1)

    def test_user_can_save_condition_while_unsure_what_starts_the_clock(self):
        payload = self._confirm_payload()
        payload["trigger_type"] = "unspecified"
        response = self.client.post(f"/api/cases/{self.case_id}/commitments/confirm", json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["trigger_type"], "unspecified")
        self.assertEqual(response.json()["evaluation"]["status"], "condition_unknown")
        self.assertIsNone(response.json()["evaluation"]["estimated_due_date"])

    def test_reconcile_starts_clock_only_when_user_records_trigger_date(self):
        saved = self.client.post(
            f"/api/cases/{self.case_id}/commitments/confirm",
            json=self._confirm_payload(),
        )
        self.assertEqual(saved.status_code, 201, saved.text)
        commitment_id = saved.json()["commitment_id"]
        no_date = self.client.post(f"/api/cases/{self.case_id}/commitments/{commitment_id}/reconcile", json={
            "event_text": "The user reports that the return scan is complete.",
            "relation": "triggers",
            "evidence_status": "user_reported",
        })
        self.assertEqual(no_date.status_code, 201, no_date.text)
        self.assertIsNone(no_date.json()["evaluation"]["estimated_due_date"])
        with_date = self.client.post(f"/api/cases/{self.case_id}/commitments/{commitment_id}/reconcile", json={
            "event_text": "Tracking page reviewed by user; return scan shown on this date.",
            "relation": "triggers",
            "evidence_status": "document_reviewed_by_user",
            "event_date_confirmed": "2026-10-29",
        })
        self.assertEqual(with_date.status_code, 201, with_date.text)
        self.assertEqual(with_date.json()["evaluation"]["estimated_due_date"]["latest"], "2026-11-05")
        self.assertEqual(with_date.json()["evaluation"]["status"], "clock_running")
        self.assertFalse(with_date.json()["source_authenticity_verified"])
        self.assertEqual(len(with_date.json()["events"]), 3)

    def test_contradictory_update_does_not_overwrite_original_commitment(self):
        saved = self.client.post(
            f"/api/cases/{self.case_id}/commitments/confirm",
            json=self._confirm_payload(),
        )
        commitment_id = saved.json()["commitment_id"]
        response = self.client.post(f"/api/cases/{self.case_id}/commitments/{commitment_id}/reconcile", json={
            "event_text": "The merchant now says it cannot confirm the return scan.",
            "relation": "contradicts",
            "evidence_status": "document_reviewed_by_user",
        })
        self.assertEqual(response.status_code, 201, response.text)
        data = response.json()
        self.assertEqual(data["evaluation"]["status"], "conflict_needs_review")
        self.assertEqual(data["source_excerpt_redacted"], STATEMENT)
        self.assertEqual(data["events"][-1]["relation"], "contradicts")

    def test_reconcile_rejects_evidence_id_not_attached_to_this_case(self):
        saved = self.client.post(
            f"/api/cases/{self.case_id}/commitments/confirm",
            json=self._confirm_payload(),
        )
        commitment_id = saved.json()["commitment_id"]
        # A random ID is not enough to attach an arbitrary file to this case.
        response = self.client.post(f"/api/cases/{self.case_id}/commitments/{commitment_id}/reconcile", json={
            "event_text": "Another case's evidence should not attach here.",
            "relation": "supports",
            "evidence_id": "not-owned-by-this-case",
        })
        self.assertEqual(response.status_code, 404, response.text)

    def test_future_condition_date_is_rejected(self):
        saved = self.client.post(
            f"/api/cases/{self.case_id}/commitments/confirm",
            json=self._confirm_payload(),
        )
        commitment_id = saved.json()["commitment_id"]
        response = self.client.post(f"/api/cases/{self.case_id}/commitments/{commitment_id}/reconcile", json={
            "event_text": "The return will be scanned next week.",
            "relation": "triggers",
            "event_date_confirmed": "2099-01-01",
        })
        self.assertEqual(response.status_code, 422, response.text)

    def test_portable_passport_contains_commitment_and_history(self):
        saved = self.client.post(
            f"/api/cases/{self.case_id}/commitments/confirm",
            json=self._confirm_payload(),
        )
        commitment_id = saved.json()["commitment_id"]
        updated = self.client.post(f"/api/cases/{self.case_id}/commitments/{commitment_id}/reconcile", json={
            "event_text": "Synthetic conflicting message for export test.",
            "relation": "contradicts",
        })
        self.assertEqual(updated.status_code, 201, updated.text)
        export = self.client.get(f"/api/cases/{self.case_id}/passport.json")
        self.assertEqual(export.status_code, 200, export.text)
        passport = export.json()
        self.assertEqual(passport["format_version"], "1.5")
        commitments = passport["case"]["commitments"]
        self.assertEqual(len(commitments), 1)
        self.assertEqual(len(commitments[0]["events"]), 2)
        self.assertFalse(commitments[0]["source_authenticity_verified"])
        self.assertEqual(commitments[0]["evaluation"]["status"], "conflict_needs_review")
        printed = self.client.get(f"/api/cases/{self.case_id}/passport/print")
        self.assertEqual(printed.status_code, 200, printed.text)
        self.assertIn("Commitments &amp; conditions", printed.text)
        self.assertIn("conflicting information", printed.text.lower())

    def test_delete_removes_commitment_record(self):
        saved = self.client.post(
            f"/api/cases/{self.case_id}/commitments/confirm",
            json=self._confirm_payload(),
        )
        commitment_id = saved.json()["commitment_id"]
        response = self.client.delete(f"/api/cases/{self.case_id}/commitments/{commitment_id}")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.client.get(f"/api/cases/{self.case_id}").json()["commitments"], [])


    def test_promise_to_proof_demo_preserves_reported_follow_up_without_marking_refund_verified(self):
        preview = self._preview("We will initiate your ₹850 refund within 5 business days from today.")
        self.assertEqual(preview.status_code, 200, preview.text)
        candidate = dict(preview.json()["candidate"])
        candidate["statement_date"] = "2026-10-20"
        candidate["trigger_type"] = "statement_date"
        saved = self.client.post(
            f"/api/cases/{self.case_id}/commitments/confirm",
            json=self._confirm_payload(candidate),
        )
        self.assertEqual(saved.status_code, 201, saved.text)
        commitment_id = saved.json()["commitment_id"]
        self.assertEqual(saved.json()["evaluation"]["estimated_due_date"]["latest"], "2026-10-27")
        self.assertEqual(saved.json()["evaluation"]["status"], "stated_period_may_have_passed")

        follow_up = self.client.post(
            f"/api/cases/{self.case_id}/commitments/{commitment_id}/reconcile",
            json={
                "event_text": "Fictional user report (synthetic): I checked the account on 10 November 2026, and the ₹850 refund has not appeared.",
                "relation": "unknown",
                "evidence_status": "user_reported",
                "event_date_claimed": "2026-11-10",
            },
        )
        self.assertEqual(follow_up.status_code, 201, follow_up.text)
        result = follow_up.json()
        self.assertEqual(result["events"][-1]["evidence_status"], "user_reported")
        self.assertEqual(result["events"][-1]["event_date_claimed"], "2026-11-10")
        self.assertEqual(result["evaluation"]["status"], "stated_period_may_have_passed")
        self.assertFalse(result["source_authenticity_verified"])
        passport = self.client.get(f"/api/cases/{self.case_id}/passport.json")
        self.assertEqual(passport.status_code, 200, passport.text)
        exported = passport.json()["case"]["commitments"][0]
        self.assertEqual(exported["events"][-1]["evidence_status"], "user_reported")
        self.assertFalse(exported["source_authenticity_verified"])


if __name__ == "__main__":
    unittest.main()
