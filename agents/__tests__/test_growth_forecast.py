"""Tests for agents/growth_forecast.py (Sprint 5 — LLM integration)."""

import unittest
from unittest.mock import patch

from services.llm_client import LLMResult
from agents.growth_forecast import (
    _to_float,
    _clamp,
    _validate_response,
    _validate_evidence_ids,
    run,
    FORECAST_MIN,
    FORECAST_MAX,
)


# ---------------------------------------------------------------------------
# Helper tests
# ---------------------------------------------------------------------------


class TestToFloat(unittest.TestCase):
    def test_valid_float(self) -> None:
        self.assertEqual(_to_float(45.0), 45.0)

    def test_valid_int(self) -> None:
        self.assertEqual(_to_float(42), 42.0)

    def test_valid_string_number(self) -> None:
        self.assertEqual(_to_float("33.5"), 33.5)

    def test_none_returns_default(self) -> None:
        self.assertEqual(_to_float(None), 0.0)

    def test_invalid_string_returns_default(self) -> None:
        self.assertEqual(_to_float("N/A"), 0.0)

    def test_nan_returns_default(self) -> None:
        self.assertEqual(_to_float(float("nan")), 0.0)

    def test_inf_returns_default(self) -> None:
        self.assertEqual(_to_float(float("inf")), 0.0)

    def test_custom_default(self) -> None:
        self.assertEqual(_to_float(None, -1.0), -1.0)


class TestClamp(unittest.TestCase):
    def test_within_range_unchanged(self) -> None:
        self.assertEqual(_clamp(45.0, FORECAST_MIN, FORECAST_MAX), 45.0)

    def test_above_max_clamped(self) -> None:
        self.assertEqual(_clamp(999.0, FORECAST_MIN, FORECAST_MAX), FORECAST_MAX)

    def test_below_min_clamped(self) -> None:
        self.assertEqual(_clamp(-200.0, FORECAST_MIN, FORECAST_MAX), FORECAST_MIN)

    def test_at_boundaries(self) -> None:
        self.assertEqual(_clamp(FORECAST_MIN, FORECAST_MIN, FORECAST_MAX), FORECAST_MIN)
        self.assertEqual(_clamp(FORECAST_MAX, FORECAST_MIN, FORECAST_MAX), FORECAST_MAX)


class TestValidateResponse(unittest.TestCase):
    def test_valid_response(self) -> None:
        data = {
            "forecast_pct": 45.0,
            "rationale": "Strong AI demand.",
            "confidence": 0.85,
            "evidence_ids": ["https://example.com"],
        }
        result = _validate_response(data)
        self.assertIsNotNone(result)
        forecast, rationale, confidence, evidence_ids = result
        self.assertEqual(forecast, 45.0)
        self.assertEqual(rationale, "Strong AI demand.")
        self.assertEqual(confidence, 0.85)
        self.assertEqual(evidence_ids, ["https://example.com"])

    def test_missing_forecast_returns_none(self) -> None:
        data = {"rationale": "test", "confidence": 0.5, "evidence_ids": []}
        self.assertIsNone(_validate_response(data))

    def test_non_dict_returns_none(self) -> None:
        self.assertIsNone(_validate_response("invalid"))
        self.assertIsNone(_validate_response([1, 2, 3]))

    def test_empty_rationale_gets_default(self) -> None:
        data = {"forecast_pct": 30.0, "rationale": "", "confidence": 0.5, "evidence_ids": []}
        result = _validate_response(data)
        self.assertIsNotNone(result)
        self.assertEqual(result[1], "No rationale provided.")

    def test_confidence_clamped_to_0_1(self) -> None:
        data = {"forecast_pct": 30.0, "rationale": "ok", "confidence": 1.5, "evidence_ids": []}
        result = _validate_response(data)
        self.assertIsNotNone(result)
        self.assertEqual(result[2], 1.0)

    def test_evidence_ids_non_list_defaults(self) -> None:
        data = {"forecast_pct": 30.0, "rationale": "ok", "confidence": 0.5, "evidence_ids": "bad"}
        result = _validate_response(data)
        self.assertIsNotNone(result)
        self.assertEqual(result[3], [])


class TestEvidenceCitationValidation(unittest.TestCase):
    def test_accepts_only_urls_already_stored_on_the_record(self) -> None:
        evidence = [{"url": "https://sec.gov/filing"}]
        self.assertEqual(
            _validate_evidence_ids(["https://sec.gov/filing"], evidence),
            ["https://sec.gov/filing"],
        )
        self.assertIsNone(_validate_evidence_ids(["https://example.com"], evidence))
        self.assertIsNone(_validate_evidence_ids([], evidence))


# ---------------------------------------------------------------------------
# Integration tests 
# ---------------------------------------------------------------------------


class TestRunFallback(unittest.TestCase):
    """When LLM is not configured, fallback to CSV value."""

    @patch("agents.growth_forecast.is_llm_configured", return_value=False)
    def test_fallback_keeps_csv_value(self, _mock) -> None:
        records = [{"growth_forecast_pct": 45.0, "company": "NVIDIA"}]
        result = run(records)
        self.assertEqual(result[0]["growth_forecast_pct"], 45.0)
        self.assertEqual(result[0]["analysis_status"], "fallback")

    @patch("agents.growth_forecast.is_llm_configured", return_value=False)
    def test_fallback_clamps_out_of_range(self, _mock) -> None:
        records = [{"growth_forecast_pct": 999.0, "company": "Test"}]
        result = run(records)
        self.assertEqual(result[0]["growth_forecast_pct"], FORECAST_MAX)
        self.assertEqual(result[0]["analysis_status"], "fallback")

    @patch("agents.growth_forecast.is_llm_configured", return_value=False)
    def test_fallback_handles_bad_data(self, _mock) -> None:
        records = [{"growth_forecast_pct": "N/A", "company": "Test"}]
        result = run(records)
        self.assertEqual(result[0]["growth_forecast_pct"], 0.0)
        self.assertEqual(result[0]["analysis_status"], "fallback")

    @patch("agents.growth_forecast.is_llm_configured", return_value=False)
    def test_fallback_handles_missing_field(self, _mock) -> None:
        records = [{"company": "Test"}]
        result = run(records)
        self.assertEqual(result[0]["growth_forecast_pct"], 0.0)
        self.assertEqual(result[0]["analysis_status"], "fallback")

    def test_fallback_sets_research_as_of(self) -> None:
        records = [{"growth_forecast_pct": 45.0, "company": "NVIDIA"}]
        result = run(records)
        self.assertIn("research_as_of", result[0])
        self.assertTrue(len(result[0]["research_as_of"]) > 0)

    @patch("agents.growth_forecast.is_llm_configured", return_value=False)
    def test_fallback_sets_confidence_none(self, _mock) -> None:
        records = [{"growth_forecast_pct": 45.0, "company": "NVIDIA"}]
        result = run(records)
        self.assertIsNone(result[0]["analysis_confidence"])


class TestRunMultipleRecords(unittest.TestCase):
    """Test processing multiple records in fallback mode."""

    @patch("agents.growth_forecast.is_llm_configured", return_value=False)
    def test_multiple_records(self, _mock) -> None:
        records = [
            {"growth_forecast_pct": 45.0, "company": "NVIDIA"},
            {"growth_forecast_pct": 60.0, "company": "Credo"},
            {"growth_forecast_pct": -200.0, "company": "Bad"},
            {"growth_forecast_pct": "invalid", "company": "Invalid"},
        ]
        result = run(records)
        self.assertEqual(result[0]["growth_forecast_pct"], 45.0)
        self.assertEqual(result[1]["growth_forecast_pct"], 60.0)
        self.assertEqual(result[2]["growth_forecast_pct"], FORECAST_MIN)
        self.assertEqual(result[3]["growth_forecast_pct"], 0.0)

    @patch("agents.growth_forecast.is_llm_configured", return_value=False)
    def test_all_records_get_fallback_status(self, _mock) -> None:
        records = [
            {"growth_forecast_pct": 45.0, "company": "A"},
            {"growth_forecast_pct": 60.0, "company": "B"},
        ]
        result = run(records)
        for record in result:
            self.assertEqual(record["analysis_status"], "fallback")


class TestEvidenceGroundedLlmRun(unittest.TestCase):
    @patch("agents.growth_forecast.is_llm_configured", return_value=True)
    @patch("agents.growth_forecast.ask_llm_json")
    def test_uses_only_existing_evidence_citations(self, mock_ask, _mock_configured):
        url = "https://sec.gov/filing"
        mock_ask.return_value = LLMResult.success(
            {
                "forecast_pct": 55.0,
                "rationale": "Demand is supported by the filing.",
                "confidence": 0.8,
                "evidence_ids": [url],
            }
        )
        record = {
            "company": "NVIDIA",
            "growth_forecast_pct": 45.0,
            "evidence": [{"url": url, "claim": "Data-center revenue grew."}],
        }

        result = run([record])[0]

        self.assertEqual(result["growth_forecast_pct"], 55.0)
        self.assertEqual(result["growth_evidence_ids"], [url])
        self.assertEqual(result["analysis_status"], "needs_review")

    @patch("agents.growth_forecast.is_llm_configured", return_value=True)
    @patch("agents.growth_forecast.ask_llm_json")
    def test_rejects_model_citations_not_in_stored_evidence(self, mock_ask, _mock_configured):
        mock_ask.return_value = LLMResult.success(
            {
                "forecast_pct": 55.0,
                "rationale": "Unsupported claim.",
                "confidence": 0.8,
                "evidence_ids": ["https://invented.example/source"],
            }
        )
        record = {
            "company": "NVIDIA",
            "growth_forecast_pct": 45.0,
            "evidence": [{"url": "https://sec.gov/filing"}],
        }

        result = run([record])[0]

        self.assertEqual(result["growth_forecast_pct"], 45.0)
        self.assertEqual(result["analysis_status"], "fallback")


if __name__ == "__main__":
    unittest.main()
