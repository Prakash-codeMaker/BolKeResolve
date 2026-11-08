"""Tests for state-aware Resolution Completion Loop guidance."""
from __future__ import annotations
import os, tempfile, unittest
_TMP = tempfile.TemporaryDirectory(prefix="bolke-completion-loop-test-")
os.environ["BOLKE_DATA_DIR"] = _TMP.name
from fastapi.testclient import TestClient
from backend import main

class CompletionLoopTests(unittest.TestCase):
    def setUp(self):
        self.auth_state = main.AUTH_REQUIRED
        main.AUTH_REQUIRED = False
        self.client = TestClient(main.app)
        r = self.client.post('/api/cases', json={
            'issue_type':'Refund not received','merchant':'Example Shop','amount':850,
            'payment_date':'2026-10-20','language_code':'en-IN','payment_status':'refund_pending',
            'contacted_support':False,'description':'My refund has not arrived after the order cancellation.'})
        self.assertEqual(r.status_code, 201, r.text)
        self.case_id = r.json()['case_id']
    def tearDown(self):
        self.client.close(); main.AUTH_REQUIRED = self.auth_state
    def test_new_case_gets_first_contact_action_and_honesty_note(self):
        case = self.client.get(f'/api/cases/{self.case_id}').json()
        loop = case['completion_loop']
        self.assertEqual(loop['version'], 'completion-loop-v2-reply-aware')
        self.assertIn(loop['state'], {'prepare_first_contact','ready_to_contact'})
        self.assertTrue(loop['action']['title'])
        self.assertIn('does not receive live bank', loop['honesty_note'])
    def test_contacting_support_changes_next_action(self):
        r = self.client.post(f'/api/cases/{self.case_id}/events', json={'event_type':'contacted_support','details':'Sent a support request','reference':'TKT-100'})
        self.assertEqual(r.status_code, 201, r.text)
        loop = r.json()['completion_loop']
        self.assertEqual(loop['state'], 'waiting_for_response')
        self.assertEqual(loop['action']['target'], 'progress')
        self.assertTrue(any(item['event_type'] == 'contacted_support' for item in r.json()['timeline']))
    def test_no_response_changes_next_action_to_follow_up(self):
        r = self.client.put(f'/api/cases/{self.case_id}/outcome', json={'outcome_code':'no_response','details':'No reply received','reference':''})
        self.assertEqual(r.status_code, 200, r.text)
        loop = r.json()['completion_loop']
        self.assertEqual(loop['state'], 'needs_follow_up')
        self.assertEqual(loop['action']['target'], 'draft')
    def test_resolved_is_explicitly_reported_not_verified(self):
        r = self.client.put(f'/api/cases/{self.case_id}/outcome', json={'outcome_code':'resolved','details':'I see the credit in my app','reference':''})
        self.assertEqual(r.status_code, 200, r.text)
        loop = r.json()['completion_loop']
        self.assertEqual(loop['state'], 'reported_resolved')
        self.assertIn('reported by you', loop['action']['why'])

    def _confirm_reply(self, text):
        preview = self.client.post(f'/api/cases/{self.case_id}/reply-review/preview', json={'reply_text': text})
        self.assertEqual(preview.status_code, 200, preview.text)
        self.assertTrue(preview.json()['category'])
        confirmed = self.client.post(f'/api/cases/{self.case_id}/reply-review/confirm', json={
            'reply_text': text, 'reference': 'TKT-100', 'confirmed': True})
        self.assertEqual(confirmed.status_code, 201, confirmed.text)
        return confirmed.json()

    def test_refund_initiated_is_not_mistaken_for_generic_follow_up_or_resolution(self):
        result = self._confirm_reply('Your refund has been initiated and should reflect in 5 working days.')
        case = result['case']
        loop = case['completion_loop']
        self.assertEqual(loop['state'], 'awaiting_credit')
        self.assertEqual(case['case_stage'], 'Awaiting response')
        self.assertIn('does not mean the money has reached your account', loop['action']['detail'])
        self.assertEqual(loop['reply_context']['category'], 'refund_claimed_initiated')
        self.assertFalse(loop['reply_context']['raw_reply_retained'])
        self.assertFalse(result['raw_reply_saved'])

    def test_reply_requesting_documents_routes_to_evidence(self):
        result = self._confirm_reply('Please upload the invoice and supporting documents.')
        loop = result['case']['completion_loop']
        self.assertEqual(loop['state'], 'information_requested')
        self.assertEqual(loop['action']['target'], 'evidence')
        self.assertEqual(result['case']['case_stage'], 'Needs next step')

    def test_claimed_credit_requires_user_verification(self):
        result = self._confirm_reply('The refund amount has been credited to your account.')
        loop = result['case']['completion_loop']
        self.assertEqual(loop['state'], 'verify_credit')
        self.assertIn('check the amount yourself', loop['action']['detail'])
        self.assertNotEqual(loop['state'], 'reported_resolved')

    def test_potentially_unsafe_reply_prioritises_credential_safety(self):
        result = self._confirm_reply('Please share your OTP to release the refund.')
        loop = result['case']['completion_loop']
        self.assertEqual(loop['state'], 'safety_check')
        self.assertIn('Do not share credentials', loop['action']['title'])
        self.assertEqual(result['case']['case_stage'], 'Needs next step')

    def test_rejection_does_not_automatically_claim_rbi_eligibility(self):
        result = self._confirm_reply('Your refund request has been rejected and the case is closed.')
        loop = result['case']['completion_loop']
        self.assertEqual(loop['state'], 'review_rejection')
        self.assertIn('Not every merchant refund belongs with the RBI Ombudsman', loop['action']['detail'])

    def test_ambiguous_reply_stays_manual_review(self):
        result = self._confirm_reply('We have noted your concern.')
        loop = result['case']['completion_loop']
        self.assertEqual(loop['state'], 'manual_reply_review')
        self.assertIn('will not guess', loop['action']['detail'])

    def test_later_case_action_supersedes_reply_specific_guidance(self):
        self._confirm_reply('Your refund has been initiated and should reflect in 5 working days.')
        later = self.client.post(f'/api/cases/{self.case_id}/events', json={
            'event_type': 'still_waiting', 'details': 'Still waiting for the credit', 'reference': 'TKT-100'})
        self.assertEqual(later.status_code, 201, later.text)
        loop = later.json()['completion_loop']
        self.assertEqual(loop['state'], 'waiting_for_response')
        self.assertIsNone(loop['reply_context'])

    def test_under_review_reply_keeps_existing_case_open(self):
        result = self._confirm_reply('Your case is under review by our team.')
        loop = result['case']['completion_loop']
        self.assertEqual(loop['state'], 'waiting_for_decision')
        self.assertEqual(result['case']['case_stage'], 'Awaiting response')
        self.assertIn('not a completed resolution', loop['action']['why'])

    def test_waiting_period_reply_does_not_create_a_universal_legal_deadline(self):
        result = self._confirm_reply('Please allow 5 business days for the refund to reflect.')
        loop = result['case']['completion_loop']
        self.assertEqual(loop['state'], 'waiting_for_credit')
        self.assertIn('not a universal legal or regulatory deadline', loop['action']['detail'])

    def test_acknowledgement_only_reply_asks_for_expected_timeline(self):
        result = self._confirm_reply('We have received your complaint. Ticket number TKT-55.')
        loop = result['case']['completion_loop']
        self.assertEqual(loop['state'], 'awaiting_timeline')
        self.assertIn('ask when to expect an update', loop['action']['title'])

    def test_conflicting_reply_does_not_trigger_automatic_escalation(self):
        result = self._confirm_reply('Your refund has been initiated but the request is rejected and case closed.')
        loop = result['case']['completion_loop']
        self.assertEqual(loop['state'], 'reply_conflict')
        self.assertIn('Pause and clarify', loop['action']['title'])

    def test_frontend_renders_completion_loop_and_dynamic_action(self):
        html = self.client.get('/').text
        js = self.client.get('/app.js').text
        css = self.client.get('/styles.css').text
        self.assertIn('completion-loop-strip', js)
        self.assertIn('completionAction.target', js)
        self.assertIn('completion.reply_context', js)
        self.assertIn('.completion-loop-strip', css)

if __name__ == '__main__': unittest.main()
