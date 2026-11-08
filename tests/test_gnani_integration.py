"""Contract tests for the Gnani API adapters; no live API key or network is used."""
from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch

_TEST_DATA = tempfile.TemporaryDirectory(prefix="bolke-gnani-test-")
os.environ["BOLKE_DATA_DIR"] = _TEST_DATA.name

from fastapi.testclient import TestClient  # noqa: E402
from backend import main  # noqa: E402


class FakeResponse:
    def __init__(self, status_code=200, *, json_data=None, content=b"", headers=None):
        self.status_code = status_code
        self._json_data = json_data
        self.content = content
        self.headers = headers or {}

    def json(self):
        return self._json_data


class FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if url.endswith("/stt/v3"):
            return FakeResponse(
                json_data={
                    "success": True,
                    "transcript": "My UPI payment failed and ₹850 was debited.",
                    "model": "prisma-v2.5",
                    "request_id": "synthetic-request-123",
                },
                headers={"content-type": "application/json"},
            )
        return FakeResponse(content=b"RIFFsynthetic-audio", headers={"content-type": "audio/wav"})


class GnaniContractTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)
        self.key_patch = patch.dict(os.environ, {"GNANI_API_KEY": "synthetic-test-key"})
        self.key_patch.start()
        self.auth_state = main.AUTH_REQUIRED
        main.AUTH_REQUIRED = False
        main._VOICE_ATTEMPTS.clear()
        self.fake = FakeAsyncClient()
        self.client_patch = patch.object(main.httpx, "AsyncClient", return_value=self.fake)
        self.client_patch.start()

    def tearDown(self):
        self.client_patch.stop()
        self.key_patch.stop()
        main.AUTH_REQUIRED = self.auth_state
        main._VOICE_ATTEMPTS.clear()
        self.client.close()

    def test_guided_voice_config_matches_authenticated_transcription_access(self):
        self.client.cookies.clear()
        with patch.object(main, "AUTH_REQUIRED", True), patch.dict(
            os.environ,
            {"GNANI_API_KEY": "synthetic-test-key", "BOLKE_PUBLIC_VOICE_ENABLED": "false"},
        ):
            with patch.object(main, "lookup_session_user", return_value=None):
                anonymous = self.client.get("/api/config")
            self.assertEqual(anonymous.status_code, 200, anonymous.text)
            self.assertFalse(anonymous.json()["guided_voice_enabled"])

            self.client.cookies.set(main.SESSION_COOKIE_NAME, "synthetic-session-token")
            with patch.object(main, "lookup_session_user", return_value="user-123"):
                authenticated = self.client.get("/api/config")
            self.assertEqual(authenticated.status_code, 200, authenticated.text)
            self.assertTrue(authenticated.json()["guided_voice_enabled"], authenticated.text)

            self.client.cookies.clear()
            with patch.dict(os.environ, {"BOLKE_PUBLIC_VOICE_ENABLED": "true"}), patch.object(main, "lookup_session_user", return_value=None):
                public_voice = self.client.get("/api/config")
            self.assertTrue(public_voice.json()["guided_voice_enabled"])

            with patch.dict(os.environ, {"GNANI_API_KEY": "", "BOLKE_PUBLIC_VOICE_ENABLED": "true"}), patch.object(main, "lookup_session_user", return_value="user-123"):
                no_provider = self.client.get("/api/config")
            self.assertFalse(no_provider.json()["guided_voice_enabled"])

    def test_tts_rate_limit_stops_extra_paid_api_requests(self):
        main._VOICE_ATTEMPTS.clear()
        with patch.dict(os.environ, {"BOLKE_TTS_LIMIT_PER_MINUTE": "2"}):
            first = self.client.post("/api/voice/speak", json={"text": "One short reply.", "language_code": "hi-en"})
            second = self.client.post("/api/voice/speak", json={"text": "Another short reply.", "language_code": "hi-en"})
            third = self.client.post("/api/voice/speak", json={"text": "Do not send this one.", "language_code": "hi-en"})
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(second.status_code, 200, second.text)
        self.assertEqual(third.status_code, 429, third.text)
        self.assertEqual(third.headers.get("retry-after"), "60")
        self.assertEqual(len(self.fake.calls), 2, "the throttled call must not be sent to Gnani")

    def test_timbre_v3_uses_universal_voice_for_local_language(self):
        with patch.dict(os.environ, {"GNANI_TTS_MODEL": "timbre-v3.0", "GNANI_TTS_V3_VOICE": "Shivani"}):
            response = self.client.post("/api/voice/speak", json={"text": "कृपया अपने बैंक ऐप में शिकायत दर्ज करें।", "language_code": "hi-IN"})
        self.assertEqual(response.status_code, 200, response.text)
        _, call = self.fake.calls[-1]
        self.assertEqual(call["json"]["model"], "timbre-v3.0")
        self.assertEqual(call["json"]["voice"], "Shivani")
        self.assertEqual(call["json"]["language"], "hi-IN")

    def test_hinglish_uses_timbre_v25_poorvi_when_v3_does_not_list_hinglish_locale(self):
        with patch.dict(os.environ, {"GNANI_TTS_MODEL": "timbre-v3.0", "GNANI_TTS_V3_VOICE": "Shivani"}):
            response = self.client.post("/api/voice/speak", json={"text": "Aap apne UPI app mein complaint register karein.", "language_code": "hi-en"})
        self.assertEqual(response.status_code, 200, response.text)
        _, call = self.fake.calls[-1]
        self.assertEqual(call["json"]["model"], "timbre-v2.5")
        self.assertEqual(call["json"]["voice"], "Poorvi")
        self.assertEqual(call["json"]["language"], "hi-en")

    def test_transcription_sends_documented_multipart_contract_and_returns_reviewable_text(self):
        response = self.client.post(
            "/api/voice/transcribe",
            files={"audio_file": ("synthetic.wav", b"RIFF synthetic wav bytes", "audio/wav")},
            data={"language_code": "hi-IN"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["transcript"], "My UPI payment failed and ₹850 was debited.")
        self.assertIn("Review the transcript", body["note"])
        self.assertEqual(body.get("detected_language_code", ""), "")
        self.assertNotIn("model", body)
        self.assertNotIn("source", body)
        self.assertNotIn("provider_language_code", body)
        self.assertEqual(body["extracted_facts"]["fields"]["amount"]["value"], 850.0)
        self.assertEqual(body["extracted_facts"]["fields"]["issue_type"]["value"], "Failed UPI payment")
        self.assertIn("not verified transaction facts", body["extracted_facts"]["notice"])
        url, call = self.fake.calls[0]
        self.assertEqual(url, "https://api.vachana.ai/stt/v3")
        self.assertEqual(call["headers"]["X-API-Key-ID"], "synthetic-test-key")
        self.assertEqual(call["data"]["language_code"], "hi-IN")
        self.assertEqual(call["data"]["model"], "prisma-v3.0")
        self.assertEqual(call["data"]["format"], "codemix")
        self.assertEqual(call["files"]["audio_file"][0], "synthetic.wav")
        self.assertNotIn("synthetic-test-key", response.text)

    def test_auto_language_detection_uses_prisma_v3_auto_lid_and_code_mix_contract(self):
        response = self.client.post(
            "/api/voice/transcribe",
            files={"audio_file": ("synthetic.wav", b"RIFF synthetic wav bytes", "audio/wav")},
            data={"language_code": "auto"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertNotIn("recognition_mode", body)
        self.assertNotIn("requested_language_code", body)
        url, call = self.fake.calls[0]
        self.assertEqual(url, "https://api.vachana.ai/stt/v3")
        self.assertEqual(call["data"]["language_code"], "indic-auto")
        self.assertEqual(call["data"]["model"], "prisma-v3.0")
        self.assertEqual(call["data"]["format"], "codemix")
        self.assertNotIn("provider_language_code", body)
        self.assertNotIn("model", body)
        self.assertNotIn("source", body)
        self.assertNotIn("itn_native_numerals", call["data"])
        self.assertTrue(call["headers"]["X-API-Request-ID"].startswith("bk-"))

    def test_auto_detection_provider_validation_error_is_explained_without_leaking_secrets(self):
        class BrokenClient(FakeAsyncClient):
            async def post(self, url, **kwargs):
                self.calls.append((url, kwargs))
                return FakeResponse(
                    status_code=400,
                    json_data={"error": {"type": "INVALID_LANGUAGE_CODE", "message": "Unsupported language_code list"}},
                    headers={"content-type": "application/json"},
                )

        broken = BrokenClient()
        with patch.object(main.httpx, "AsyncClient", return_value=broken):
            response = self.client.post(
                "/api/voice/transcribe",
                files={"audio_file": ("synthetic.wav", b"RIFF synthetic wav bytes", "audio/wav")},
                data={"language_code": "auto"},
            )
        self.assertEqual(response.status_code, 502)
        detail = response.json()["detail"].lower()
        self.assertIn("automatic speech-language detection is unavailable", detail)
        self.assertIn("prisma v3.0", detail)
        self.assertNotIn("gnani", detail)
        self.assertNotIn("unsupported language_code list", detail)
        self.assertNotIn("synthetic-test-key", response.text)

    def test_auto_mode_silently_retries_english_when_first_result_is_english_phonetically_rendered_in_devanagari(self):
        class ScriptMismatchClient(FakeAsyncClient):
            def __init__(self):
                super().__init__()
                self.count = 0

            async def post(self, url, **kwargs):
                self.calls.append((url, kwargs))
                if url.endswith("/stt/v3"):
                    self.count += 1
                    transcript = (
                        "आई आई हेव नॉट गॉट दी रिफंड बैक ऑफ 850 फ्रॉम जोमैटो"
                        if self.count == 1 else
                        "I have not got the refund back of 850 from Zomato"
                    )
                    return FakeResponse(json_data={"success": True, "transcript": transcript, "model": "prisma-v2.5"})
                return FakeResponse(content=b"RIFFaudio", headers={"content-type": "audio/wav"})

        mismatch = ScriptMismatchClient()
        with patch.object(main.httpx, "AsyncClient", return_value=mismatch):
            response = self.client.post(
                "/api/voice/transcribe",
                files={"audio_file": ("synthetic.wav", b"RIFF synthetic wav bytes", "audio/wav")},
                data={"language_code": "auto"},
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("I have not got", response.json()["transcript"])
        self.assertEqual(len(mismatch.calls), 2)
        self.assertEqual(mismatch.calls[0][1]["data"]["language_code"], "indic-auto")
        self.assertEqual(mismatch.calls[0][1]["data"]["model"], "prisma-v3.0")
        self.assertEqual(mismatch.calls[1][1]["data"]["language_code"], "en-IN")
        self.assertEqual(mismatch.calls[1][1]["data"]["model"], "prisma-v3.0")

    def test_english_selected_but_asr_returns_devanagari_phonetics_is_made_readable_and_extractable(self):
        class PhoneticEnglishClient(FakeAsyncClient):
            async def post(self, url, **kwargs):
                self.calls.append((url, kwargs))
                if url.endswith("/stt/v3"):
                    return FakeResponse(json_data={
                        "success": True,
                        "transcript": "आई आई हेव नॉट गॉट दी रिफंड बैक ऑफ 850 फ्रॉम जोमैटो",
                        "model": "provider-model-is-internal",
                    })
                return FakeResponse(content=b"RIFFaudio", headers={"content-type": "audio/wav"})

        fake = PhoneticEnglishClient()
        with patch.object(main.httpx, "AsyncClient", return_value=fake):
            response = self.client.post(
                "/api/voice/transcribe",
                files={"audio_file": ("synthetic.wav", b"RIFF synthetic wav bytes", "audio/wav")},
                data={"language_code": "en-IN"},
            )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertIn("I I have not got the refund back of 850 from Zomato", body["transcript"])
        self.assertNotIn("model", body)
        fields = body["extracted_facts"]["fields"]
        self.assertEqual(fields["merchant"]["value"], "Zomato")
        self.assertEqual(fields["amount"]["value"], 850.0)
        self.assertEqual(fields["issue_type"]["value"], "Refund not received")
        self.assertNotIn("provider-model-is-internal", response.text)

    def test_typed_story_extraction_endpoint_fills_hindi_rendered_speech_facts(self):
        response = self.client.post("/api/extraction/preview", json={
            "description": "आई आई हेव नॉट गॉट दी रिफंड बैक ऑफ 850 फ्रॉम जोमैटो दैट दी फूड ऑर्डर वाज़ कैंसल्ड"
        })
        self.assertEqual(response.status_code, 200, response.text)
        facts = response.json()["extracted_facts"]["fields"]
        self.assertEqual(facts["merchant"]["value"], "Zomato")
        self.assertEqual(facts["amount"]["value"], 850.0)
        self.assertEqual(facts["issue_type"]["value"], "Refund not received")

    def test_long_phonetic_english_transcript_extracts_all_core_zomato_refund_facts(self):
        description = (
            "आई आई हेव नॉट गॉट दी रिफंड बैक ऑफ 850 फ्रॉम जोमैटो दट दी फूड ऑर्डर वाज़ कैंसल्ड "
            "दे लाइक गिव मी दी रिफंड बैक इन थ्री डेज़ बट इट हैज़ बीन मोर दैन सेवन डेज़ "
            "आई हैव नॉट गॉट दी रिफंड बैक प्लीज़ हेल्प मी इन दिस इश्यू इन दी बेस्ट पॉसिबल"
        )
        response = self.client.post("/api/extraction/preview", json={"description": description})
        self.assertEqual(response.status_code, 200, response.text)
        fields = response.json()["extracted_facts"]["fields"]
        self.assertEqual(fields["merchant"]["value"], "Zomato")
        self.assertEqual(fields["amount"]["value"], 850.0)
        self.assertEqual(fields["issue_type"]["value"], "Refund not received")
        self.assertEqual(fields["payment_status"]["value"], "refund_pending")
        # The transcript also says it tried to contact support, in English phonetics.
        story_with_support = description + " आई ट्राय टू कॉन्टैक्ट देम थ्रू दी कॉन्टैक्ट सपोर्ट बट दे आर नॉट आंसरिंग"
        support_fields = self.client.post("/api/extraction/preview", json={"description": story_with_support}).json()["extracted_facts"]["fields"]
        self.assertTrue(support_fields["contacted_support"]["value"])

    def test_hinglish_speech_uses_timbre_poorvi_and_expected_output_contract(self):
        response = self.client.post(
            "/api/voice/speak",
            json={"text": "Namaste, your next step is ready.", "language_code": "hi-en"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.content.startswith(b"RIFF"))
        url, call = self.fake.calls[0]
        self.assertEqual(url, "https://api.vachana.ai/api/v1/tts/inference")
        self.assertEqual(call["headers"]["X-API-Key-ID"], "synthetic-test-key")
        self.assertEqual(call["json"]["model"], "timbre-v2.5")
        self.assertEqual(call["json"]["voice"], "Poorvi")
        self.assertEqual(call["json"]["language"], "hi-en")
        self.assertEqual(response.headers["content-type"], "audio/wav")

    def test_unsupported_audio_format_error_is_provider_neutral(self):
        response = self.client.post(
            "/api/voice/transcribe",
            files={"audio_file": ("complaint.txt", b"not an audio file", "text/plain")},
            data={"language_code": "en-IN"},
        )
        self.assertEqual(response.status_code, 415)
        detail = response.json()["detail"].lower()
        self.assertIn("file type is not supported", detail)
        self.assertNotIn("gnani", detail)
        self.assertNotIn("api", detail)

    def test_provider_failure_is_reported_as_gateway_error(self):
        class BrokenClient(FakeAsyncClient):
            async def post(self, url, **kwargs):
                self.calls.append((url, kwargs))
                return FakeResponse(status_code=429, json_data={"error": {"message": "rate limited"}}, headers={"content-type": "application/json"})

        broken = BrokenClient()
        with patch.object(main.httpx, "AsyncClient", return_value=broken):
            response = self.client.post(
                "/api/voice/transcribe",
                files={"audio_file": ("synthetic.wav", b"RIFF synthetic wav bytes", "audio/wav")},
                data={"language_code": "hi-IN"},
            )
        self.assertEqual(response.status_code, 502)
        self.assertIn("try again", response.json()["detail"].lower())
        self.assertNotIn("gnani", response.json()["detail"].lower())


if __name__ == "__main__":
    unittest.main()
