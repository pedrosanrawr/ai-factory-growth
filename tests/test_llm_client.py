"""Offline tests for the shared Gemini LLM client."""

import json
import unittest
from unittest.mock import MagicMock, patch

import services.llm_client as llm_client


class TestLLMClient(unittest.TestCase):
    def tearDown(self):
        llm_client.get_llm_client.cache_clear()

    def test_is_llm_configured_without_a_key(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}, clear=False):
            self.assertFalse(llm_client.is_llm_configured())

    def test_is_llm_configured_with_a_key(self):
        with patch.dict(
            "os.environ",
            {"GEMINI_API_KEY": "test-key"},
            clear=False,
        ):
            self.assertTrue(llm_client.is_llm_configured())

    def test_get_llm_client_requires_a_key(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}, clear=False):
            with self.assertRaises(llm_client.LLMConfigurationError) as error:
                llm_client.get_llm_client()

        self.assertIn("GEMINI_API_KEY", str(error.exception))

    @patch("services.llm_client.genai.Client")
    def test_get_llm_client_creates_client_with_key(self, mock_client):
        with patch.dict(
            "os.environ",
            {
                "GEMINI_API_KEY": "test-key",
                "LLM_MODEL": "gemini-3.6-flash",
            },
            clear=False,
        ):
            client = llm_client.get_llm_client()

        mock_client.assert_called_once_with(api_key="test-key")
        self.assertIs(client, mock_client.return_value)

    def test_ask_llm_rejects_empty_prompt(self):
        with self.assertRaises(ValueError):
            llm_client.ask_llm(
                system_prompt="",
                user_prompt="Hello",
            )

    @patch("services.llm_client.get_llm_client")
    def test_ask_llm_returns_text_response(self, mock_get_client):
        interaction = MagicMock()
        interaction.output_text = "Gemini connection successful."

        mock_get_client.return_value.interactions.create.return_value = interaction

        with patch.dict(
            "os.environ",
            {"GEMINI_API_KEY": "test-key"},
            clear=False,
        ):
            result = llm_client.ask_llm(
                system_prompt="You are a test assistant.",
                user_prompt="Reply with exactly: Gemini connection successful.",
            )

        self.assertEqual(result, "Gemini connection successful.")

    @patch("services.llm_client.get_llm_client")
    def test_ask_llm_json_returns_valid_json(self, mock_get_client):
        interaction = MagicMock()
        interaction.output_text = json.dumps(
            {
                "score": 5,
                "reason": "Strong competitive position.",
            }
        )

        mock_get_client.return_value.interactions.create.return_value = interaction

        schema = {
            "type": "object",
            "properties": {
                "score": {"type": "integer"},
                "reason": {"type": "string"},
            },
            "required": ["score", "reason"],
        }

        with patch.dict(
            "os.environ",
            {"GEMINI_API_KEY": "test-key"},
            clear=False,
        ):
            result = llm_client.ask_llm_json(
                system_prompt="Analyze the company.",
                user_prompt="Return a moat assessment.",
                schema=schema,
            )

        self.assertTrue(result.ok)
        self.assertEqual(result.data["score"], 5)
        self.assertEqual(
            result.data["reason"],
            "Strong competitive position.",
        )
        self.assertIsNone(result.error_type)

    @patch("services.llm_client.get_llm_client")
    def test_ask_llm_json_uses_json_response_format(self, mock_get_client):
        interaction = MagicMock()
        interaction.output_text = '{"score": 3}'

        mock_get_client.return_value.interactions.create.return_value = interaction

        schema = {
            "type": "object",
            "properties": {
                "score": {"type": "integer"},
            },
            "required": ["score"],
        }

        with patch.dict(
            "os.environ",
            {"GEMINI_API_KEY": "test-key"},
            clear=False,
        ):
            result = llm_client.ask_llm_json(
                system_prompt="Analyze.",
                user_prompt="Return JSON.",
                schema=schema,
            )

        self.assertTrue(result.ok)

        call_kwargs = (
            mock_get_client.return_value.interactions.create.call_args.kwargs
        )

        self.assertEqual(
            call_kwargs["response_format"]["type"],
            "text",
        )
        self.assertEqual(
            call_kwargs["response_format"]["mime_type"],
            "application/json",
        )
        self.assertEqual(
            call_kwargs["response_format"]["schema"],
            schema,
        )

    def test_ask_llm_json_rejects_invalid_schema(self):
        with patch.dict(
            "os.environ",
            {"GEMINI_API_KEY": "test-key"},
            clear=False,
        ):
            result = llm_client.ask_llm_json(
                system_prompt="Analyze.",
                user_prompt="Return JSON.",
                schema={},
            )

        self.assertFalse(result.ok)
        self.assertEqual(
            result.error_type,
            llm_client.LLMErrorType.INVALID_INPUT,
        )
        self.assertIsNotNone(result.error)

    @patch("services.llm_client.get_llm_client")
    def test_ask_llm_json_handles_malformed_json(self, mock_get_client):
        interaction = MagicMock()
        interaction.output_text = "this is not valid JSON"

        mock_get_client.return_value.interactions.create.return_value = interaction

        schema = {
            "type": "object",
            "properties": {
                "score": {"type": "integer"},
            },
            "required": ["score"],
        }

        with patch.dict(
            "os.environ",
            {"GEMINI_API_KEY": "test-key"},
            clear=False,
        ):
            result = llm_client.ask_llm_json(
                system_prompt="Analyze.",
                user_prompt="Return JSON.",
                schema=schema,
            )

        self.assertFalse(result.ok)
        self.assertEqual(
            result.error_type,
            llm_client.LLMErrorType.MALFORMED_RESPONSE,
        )
        self.assertIsNone(result.data)

    @patch("services.llm_client.get_llm_client")
    def test_ask_llm_json_handles_timeout(self, mock_get_client):
        mock_get_client.return_value.interactions.create.side_effect = (
            TimeoutError("request timed out")
        )

        schema = {
            "type": "object",
            "properties": {
                "score": {"type": "integer"},
            },
            "required": ["score"],
        }

        with patch.dict(
            "os.environ",
            {"GEMINI_API_KEY": "test-key"},
            clear=False,
        ):
            result = llm_client.ask_llm_json(
                system_prompt="Analyze.",
                user_prompt="Return JSON.",
                schema=schema,
            )

        self.assertFalse(result.ok)
        self.assertEqual(
            result.error_type,
            llm_client.LLMErrorType.TIMEOUT,
        )
        self.assertIsNone(result.data)

    @patch("services.llm_client.get_llm_client")
    def test_ask_llm_json_handles_provider_failure(self, mock_get_client):
        mock_get_client.return_value.interactions.create.side_effect = (
            RuntimeError("provider unavailable")
        )

        schema = {
            "type": "object",
            "properties": {
                "score": {"type": "integer"},
            },
            "required": ["score"],
        }

        with patch.dict(
            "os.environ",
            {"GEMINI_API_KEY": "test-key"},
            clear=False,
        ):
            result = llm_client.ask_llm_json(
                system_prompt="Analyze.",
                user_prompt="Return JSON.",
                schema=schema,
            )

        self.assertFalse(result.ok)
        self.assertEqual(
            result.error_type,
            llm_client.LLMErrorType.PROVIDER,
        )
        self.assertIsNone(result.data)


if __name__ == "__main__":
    unittest.main()