import unittest

from backend.security import scrub_sensitive_text
from backend.main import TTS_DEFAULT_VOICE, TTS_VOICES_BY_LANGUAGE


class SensitiveTextScrubberTests(unittest.TestCase):
    def test_removes_otp_pin_and_password(self):
        result = scrub_sensitive_text("UPI PIN is 1234; OTP: 123456; password: SecretPass123")
        self.assertNotIn("1234", result.text)
        self.assertNotIn("123456", result.text)
        self.assertNotIn("SecretPass123", result.text)
        self.assertIn("OTP/PIN", result.redacted_types)
        self.assertIn("password", result.redacted_types)

    def test_removes_aadhaar_pan_phone_and_account_numbers(self):
        result = scrub_sensitive_text(
            "Aadhaar 1234 5678 9012, PAN ABCDE1234F, phone number 9876543210, account number 123456789012"
        )
        self.assertNotIn("1234 5678 9012", result.text)
        self.assertNotIn("ABCDE1234F", result.text)
        self.assertNotIn("9876543210", result.text)
        self.assertNotIn("123456789012", result.text)
        self.assertGreaterEqual(len(result.redacted_types), 4)

    def test_redacts_valid_payment_card_and_preserves_sentence_spacing(self):
        result = scrub_sensitive_text("My card is 4111 1111 1111 1111 used for a ₹850 payment.")
        self.assertIn("[REDACTED CARD] used", result.text)
        self.assertNotIn("4111 1111 1111 1111", result.text)
        self.assertIn("payment card", result.redacted_types)

    def test_does_not_redact_normal_payment_amount_or_refund_story(self):
        story = "I paid ₹850 yesterday, the order was cancelled, and the refund is pending."
        result = scrub_sensitive_text(story)
        self.assertEqual(result.text, story)
        self.assertEqual(result.redacted_types, [])

    def test_timbre_v25_default_voices_match_official_language_catalog(self):
        self.assertEqual(TTS_DEFAULT_VOICE["hi-IN"], "Nalini")
        self.assertEqual(TTS_DEFAULT_VOICE["en-IN"], "Kaveri")
        self.assertEqual(TTS_DEFAULT_VOICE["hi-en"], "Poorvi")
        self.assertEqual(TTS_DEFAULT_VOICE["mr-IN"], "Zahira")
        self.assertEqual(set(TTS_DEFAULT_VOICE), set(TTS_VOICES_BY_LANGUAGE))
        for language, voice in TTS_DEFAULT_VOICE.items():
            self.assertIn(voice, TTS_VOICES_BY_LANGUAGE[language])


if __name__ == "__main__":
    unittest.main()
