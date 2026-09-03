"""Tests for the one-request-per-company Gemini analysis stage."""

import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from agents import research_analysis
from services.llm_client import LLMResult


def make_record():
    return {
        "company": "Example Compute",
        "cik": "0000123456",
        "role": "Compute/Server",
        "evidence": [{"url": "https://sec.gov/example", "status": "needs_review", "claim": "AI server demand."}],
    }


def analysis_payload():
    return {
        "moat_score": 4,
        "moat_rationale": "Switching costs are meaningful.",
        "growth_forecast_pct": 25.0,
        "growth_rationale": "Demand is supported by the cited filing.",
        "concentration_risk": 0.3,
        "cyclicality_risk": 0.2,
        "execution_risk": 0.4,
        "risk_rationale": "Execution remains the largest risk.",
        "confidence": 0.7,
        "evidence_ids": ["https://sec.gov/example"],
    }


class TestResearchAnalysis(unittest.TestCase):
    @patch("agents.research_analysis.MIN_REQUEST_INTERVAL_SECONDS", 0)
    @patch("agents.research_analysis.is_llm_configured", return_value=True)
    @patch("agents.research_analysis.ask_llm_json")
    def test_uses_one_call_and_reuses_cached_result(self, ask, _configured):
        ask.return_value = LLMResult.success(analysis_payload())
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            "os.environ", {"LLM_ANALYSIS_CACHE_PATH": str(Path(directory) / "cache.json")}
        ):
            first = research_analysis.run([make_record()])[0]
            second = research_analysis.run([make_record()])[0]

        self.assertEqual(ask.call_count, 1)
        self.assertTrue(first["_combined_llm_analysis"])
        self.assertTrue(first["_combined_llm_attempted"])
        self.assertEqual(first["analysis_status"], "needs_review")
        self.assertEqual(second["growth_forecast_pct"], 25.0)
        self.assertEqual(ask.call_args.kwargs["max_tokens"], 2048)

    def test_response_schema_limits_variable_length_output(self) -> None:
        properties = research_analysis.RESPONSE_SCHEMA["properties"]
        self.assertEqual(properties["moat_rationale"]["maxLength"], 600)
        self.assertEqual(properties["evidence_ids"]["maxItems"], 3)

    @patch("agents.research_analysis.MIN_REQUEST_INTERVAL_SECONDS", 0)
    @patch("agents.research_analysis.is_llm_configured", return_value=True)
    @patch("agents.research_analysis.ask_llm_json")
    def test_rejects_unknown_citations_without_caching(self, ask, _configured):
        bad = analysis_payload()
        bad["evidence_ids"] = ["https://invented.example"]
        ask.return_value = LLMResult.success(bad)
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            "os.environ", {"LLM_ANALYSIS_CACHE_PATH": str(Path(directory) / "cache.json")}
        ):
            record = research_analysis.run([make_record()])[0]

        self.assertNotIn("_combined_llm_analysis", record)
        self.assertTrue(record["_combined_llm_attempted"])
        self.assertEqual(ask.call_count, 1)

    @patch("agents.research_analysis.time.sleep")
    @patch("agents.research_analysis.MIN_REQUEST_INTERVAL_SECONDS", 0)
    @patch("agents.research_analysis.is_llm_configured", return_value=True)
    @patch("agents.research_analysis.ask_llm_json")
    def test_retries_once_after_the_provider_retry_delay(self, ask, _configured, sleep):
        ask.side_effect = [
            LLMResult.failure("provider", "Error 429: Please retry in 2.0s."),
            LLMResult.success(analysis_payload()),
        ]
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            "os.environ", {"LLM_ANALYSIS_CACHE_PATH": str(Path(directory) / "cache.json")}
        ):
            record = research_analysis.run([make_record()])[0]

        self.assertEqual(ask.call_count, 2)
        sleep.assert_called_with(2.5)
        self.assertTrue(record["_combined_llm_analysis"])


if __name__ == "__main__":
    unittest.main()
