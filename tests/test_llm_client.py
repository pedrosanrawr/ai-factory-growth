"""Offline tests for the shared LLM configuration layer."""

import unittest
from unittest.mock import patch

import services.llm_client as llm_client


class TestLLMClient(unittest.TestCase):
    def tearDown(self):
        llm_client.get_llm_client.cache_clear()

    def test_is_llm_configured_without_a_key(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}, clear=False):
            self.assertFalse(llm_client.is_llm_configured())

    def test_get_llm_client_requires_a_key(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}, clear=False):
            with self.assertRaises(llm_client.LLMConfigurationError) as error:
                llm_client.get_llm_client()

        self.assertIn("GEMINI_API_KEY", str(error.exception))
