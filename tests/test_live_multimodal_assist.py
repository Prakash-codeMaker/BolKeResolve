"""Contract tests for opt-in live guidance translation and visual assistance."""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from backend import agent_assist


class FakeResponse:
    status_code = 200

    def __init__(self, text: str):
        self._text = text

    def json(self):
        return {"output_text": self._text}


class FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if any(item.get("type") == "input_image" for item in kwargs["json"]["input"][0]["content"]):
            text = (
                '{"document_type":"UPI screenshot","summary":"Visible payment status reads pending.",'
                '"facts":{"merchant":"Demo Store","amount":"₹1,200","payment_date":"2026-10-30",'
                '"payment_status":"pending","reference_suffix":"1234"},'
                '"fact_confidence":{"merchant":"high","amount":"high","payment_date":"medium",'
                '"payment_status":"high","reference_suffix":"medium"},'
                '"observations":["A pending label is visible."],"missing_information":["Bank-side status is unknown."],'
                '"suggested_question":"Does your bank app show the same status?","security_warning":false}'
            )
        else:
            text = "पहले अपने UPI ऐप में शिकायत दर्ज करें।"
        return FakeResponse(text)


class LiveMultimodalAssistTests(unittest.IsolatedAsyncioTestCase):
    async def test_guidance_translation_uses_responses_api_without_response_storage(self):
        fake = FakeAsyncClient()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "not-a-real-key", "BOLKE_MULTIMODAL_MODEL": "gpt-6-astra"}), patch.object(
            agent_assist.httpx, "AsyncClient", return_value=fake
        ):
            translated = await agent_assist.localize_guidance("Your next step is to contact the UPI app.", "hi-IN")
        self.assertIn("पहले", translated)
        url, call = fake.calls[0]
        self.assertTrue(url.endswith("/v1/responses"))
        self.assertEqual(call["json"]["model"], "gpt-6-astra")
        self.assertFalse(call["json"]["store"])
        self.assertIn("Do not add advice", call["json"]["instructions"])
        # The key must be present only in the transport Authorization header, never the prompt/body.
        self.assertEqual(call["headers"]["Authorization"], "Bearer not-a-real-key")
        self.assertNotIn("not-a-real-key", str(call["json"]))

    async def test_vision_analysis_receives_image_and_minimum_case_context_and_masks_reference(self):
        fake = FakeAsyncClient()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "not-a-real-key"}), patch.object(
            agent_assist.httpx, "AsyncClient", return_value=fake
        ):
            result = await agent_assist.analyze_image(
                image_data_url="data:image/jpeg;base64,ZmFrZQ==",
                language_code="hi-IN",
                case_context="User says ₹1,200 was debited but Demo Store did not receive it.",
                question="Compare the receipt to the story.",
            )
        self.assertEqual(result["facts"]["amount"], 1200.0)
        self.assertEqual(result["facts"]["reference_suffix"], "1234")
        self.assertEqual(result["fact_confidence"]["merchant"], "high")
        self.assertIn("not independently authenticated", result["provider_notice"])
        content = fake.calls[0][1]["json"]["input"][0]["content"]
        self.assertTrue(any(item.get("type") == "input_image" for item in content))
        prompt = next(item["text"] for item in content if item.get("type") == "input_text")
        self.assertIn("Demo Store", prompt)
        self.assertIn("Compare the visible evidence", prompt)
        self.assertFalse(fake.calls[0][1]["json"]["store"])

    async def test_semantic_interpretation_falls_back_when_model_rejects_strict_schema(self):
        import json
        from unittest.mock import AsyncMock
        payload = {
            "intent": "answer_current_question", "issue_family": "refund", "summary": "The full order refund is pending.",
            "fact_updates": [{"field": "refund_scope", "value": "full_order", "evidence_quote": "whole order", "confidence": 0.95}],
            "different_issue": False, "question_rewrite": "", "action_explanation": "", "language": "English",
        }
        with patch.dict(os.environ, {"OPENAI_API_KEY": "not-a-real-key"}), patch.object(
            agent_assist, "_responses_call", new=AsyncMock(side_effect=[RuntimeError("strict schema unavailable"), json.dumps(payload)])
        ) as call:
            result = await agent_assist.interpret_case_conversation(
                conversation="User: I want refund for whole order.", latest_turn="I want refund for whole order.",
                current_facts={}, current_question={"field": "refund_scope"}, workflow_context={}, language_code="en-IN",
            )
        self.assertEqual(result["fact_updates"][0]["field"], "refund_scope")
        self.assertEqual(call.await_count, 2)
        self.assertIsNone(call.await_args.kwargs.get("text_format"))

    async def test_semantic_fact_updates_require_exact_user_quote(self):
        interpretation = {"fact_updates": [
            {"field": "refund_scope", "value": "full_order", "evidence_quote": "whole order", "confidence": 0.99},
            {"field": "refund_status", "value": "pending", "evidence_quote": "refund is pending", "confidence": 0.99},
        ]}
        facts, applied = agent_assist.apply_quoted_case_fact_updates({}, interpretation, "I mean the whole order ma'am.")
        self.assertEqual(facts.get("refund_scope"), "full_order")
        self.assertNotIn("refund_status", facts)
        self.assertEqual(len(applied), 1)

    async def test_localization_does_not_call_external_service_for_english(self):
        with patch.object(agent_assist, "_responses_call") as call:
            original = "Your next step is to contact your bank."
            result = await agent_assist.localize_guidance(original, "en-IN")
        self.assertEqual(result, original)
        call.assert_not_called()

    async def test_missing_provider_key_is_an_explicit_configuration_error(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            self.assertFalse(agent_assist.configured())
            with self.assertRaisesRegex(RuntimeError, "not configured"):
                await agent_assist.localize_guidance("Contact support.", "hi-IN")


if __name__ == "__main__":
    unittest.main()
