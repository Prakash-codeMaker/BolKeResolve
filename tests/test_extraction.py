"""Offline tests for the reviewable speech-to-case extraction layer."""
from datetime import date
import unittest

from backend.extraction import extract_case_facts


class ExtractCaseFactsTests(unittest.TestCase):
    def test_zomato_refund_story_extracts_merchant_amount_issue_and_date(self):
        facts = extract_case_facts(
            "I used Zomato and did not get my 850 refund back. I used this on 12 October 2026.",
            today=date(2026, 10, 19),
        )
        fields = facts["fields"]
        self.assertEqual(fields["merchant"]["value"], "Zomato")
        self.assertEqual(fields["amount"]["value"], 850.0)
        self.assertEqual(fields["issue_type"]["value"], "Refund not received")
        self.assertEqual(fields["payment_status"]["value"], "refund_pending")
        self.assertEqual(fields["payment_date"]["value"], "2026-10-12")
        self.assertFalse(fields["payment_date"]["needs_confirmation"])

    def test_devanagari_speech_transcript_extracts_zomato_amount_and_missing_refund(self):
        text = "आई आई हेव नॉट गॉट दी रिफंड बैक ऑफ 850 फ्रॉम जोमैटो दैट दी फूड ऑर्डर वाज़ कैंसल्ड बट इट हैज़ बीन मोर देन सेवन डेज़ एंड आई हैव नॉट गॉट दी रिफंड बैक प्लीज हेल्प मी"
        fields = extract_case_facts(text)["fields"]
        self.assertEqual(fields["merchant"]["value"], "Zomato")
        self.assertEqual(fields["amount"]["value"], 850.0)
        self.assertEqual(fields["issue_type"]["value"], "Refund not received")
        self.assertEqual(fields["payment_status"]["value"], "refund_pending")

    def test_native_hindi_refund_story_extracts_when_amount_is_devanagari_number(self):
        text = "मुझे जोमैटो से ८५० रुपये का रिफंड अभी तक नहीं आया, सात दिन हो गए हैं।"
        fields = extract_case_facts(text)["fields"]
        self.assertEqual(fields["merchant"]["value"], "Zomato")
        self.assertEqual(fields["amount"]["value"], 850.0)
        self.assertEqual(fields["issue_type"]["value"], "Refund not received")
        self.assertEqual(fields["payment_status"]["value"], "refund_pending")

    def test_date_without_year_is_marked_for_confirmation(self):
        fields = extract_case_facts("My refund is missing from Zomato since 12 October", today=date(2026, 10, 19))["fields"]
        self.assertEqual(fields["payment_date"]["value"], "2026-10-12")
        self.assertTrue(fields["payment_date"]["needs_confirmation"])

    def test_two_explicit_amounts_are_not_guessed(self):
        facts = extract_case_facts("The receipt says ₹800, but ₹850 was charged.")
        self.assertIsNone(facts["fields"]["amount"]["value"])
        self.assertEqual(len(facts["conflicts"]), 1)
        self.assertIn("more than one amount", facts["conflicts"][0]["message"].lower())

    def test_explicit_payment_failure_and_support_contact_are_extracted(self):
        fields = extract_case_facts("My UPI payment failed, ₹850 was debited, and I already contacted support.")["fields"]
        self.assertEqual(fields["issue_type"]["value"], "Failed UPI payment")
        self.assertEqual(fields["payment_status"]["value"], "failed")
        self.assertIs(fields["contacted_support"]["value"], True)

    def test_support_not_contacted_is_distinguished_from_unknown(self):
        fields = extract_case_facts("My refund has not arrived; I have not contacted support yet.")["fields"]
        self.assertIs(fields["contacted_support"]["value"], False)
        second = extract_case_facts("My payment failed and support has not been contacted.")["fields"]
        self.assertIs(second["contacted_support"]["value"], False)

    def test_relative_date_is_not_fabricated_into_calendar_date(self):
        fields = extract_case_facts("My payment failed yesterday.", today=date(2026, 10, 19))["fields"]
        self.assertEqual(fields["payment_date"]["value"], "")
        self.assertTrue(fields["payment_date"]["needs_confirmation"])
        self.assertIn("yesterday", fields["payment_date"]["evidence"].lower())

    def test_razorpay_business_settlement_is_not_extracted_as_consumer_refund(self):
        text = (
            "I have not got the refund of 350 rupees from Razorpay. Several payments are in the gateway. "
            "When I try to extract it from Razorpay to our account, it does not work. "
            "They told me four days, but more than twelve days have passed."
        )
        fields = extract_case_facts(text)["fields"]
        self.assertEqual(fields["merchant"]["value"], "Razorpay")
        self.assertEqual(fields["amount"]["value"], 350.0)
        self.assertEqual(fields["issue_type"]["value"], "Merchant settlement not credited")
        self.assertEqual(fields["issue_family"]["value"], "merchant_settlement")

    def test_suspicious_payment_is_routed_to_safety_category(self):
        fields = extract_case_facts("I did not make this transaction and do not recognise it.")["fields"]
        self.assertEqual(fields["issue_type"]["value"], "Suspected fraud or unauthorised transaction")
        self.assertEqual(fields["payment_status"]["value"], "unauthorized")


if __name__ == "__main__":
    unittest.main()
