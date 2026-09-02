"""Tests for agents/moat_analysis.py — evidence-grounded moat analysis.

Covers: valid LLM output, invalid score, invalid citations, malformed
LLM response, LLM unavailable, CSV-only fallback, and field isolation.
"""

import unittest
from unittest.mock import patch

from agents.moat_analysis import run, _clamp_score, _clamp_confidence, _validate_evidence_ids
from schema import empty_record
from services.llm_client import LLMResult, LLMErrorType


def _make_record(**overrides) -> dict:
    """Build a record with sensible defaults and optional overrides."""
    record = empty_record()
    record.update({
        "company": "TestCorp",
        "role": "Compute/Server",
        "short_description": "A test company",
        "moat_notes": "Strong IP portfolio",
        "moat_score": 3,
        "evidence": [
            {
                "url": "https://example.com/report1",
                "title": "Annual Report",
                "retrieved_date": "2026-08-01",
                "claim": "Market leader in GPUs",
                "source_type": "10-K",
                "status": "needs_review",
            },
            {
                "url": "https://example.com/report2",
                "title": "Press Release",
                "retrieved_date": "2026-08-15",
                "claim": "Announced new AI chip",
                "source_type": "press_release",
                "status": "verified",
            },
        ],
    })
    record.update(overrides)
    return record


def _valid_llm_data() -> dict:
    """Return a valid LLM response payload."""
    return {
        "moat_score": 4,
        "rationale": "Strong IP and switching costs in the GPU market.",
        "confidence": 0.85,
        "evidence_ids": [
            "https://example.com/report1",
            "https://example.com/report2",
        ],
    }


class TestClampScore(unittest.TestCase):
    """Unit tests for _clamp_score helper."""

    def test_valid_range(self) -> None:
        """Scores within 0-5 are returned unchanged."""
        self.assertEqual(_clamp_score(0), 0)
        self.assertEqual(_clamp_score(3), 3)
        self.assertEqual(_clamp_score(5), 5)

    def test_clamps_above(self) -> None:
        """Scores above 5 are clamped to 5."""
        self.assertEqual(_clamp_score(9), 5)

    def test_clamps_below(self) -> None:
        """Scores below 0 are clamped to 0."""
        self.assertEqual(_clamp_score(-2), 0)

    def test_string_conversion(self) -> None:
        """Numeric strings are converted before clamping."""
        self.assertEqual(_clamp_score("3"), 3)

    def test_invalid_returns_zero(self) -> None:
        """Non-numeric or None values default to 0."""
        self.assertEqual(_clamp_score("N/A"), 0)
        self.assertEqual(_clamp_score(None), 0)


class TestClampConfidence(unittest.TestCase):
    """Unit tests for _clamp_confidence helper."""

    def test_valid_range(self) -> None:
        """Confidence within 0.0-1.0 is returned unchanged."""
        self.assertAlmostEqual(_clamp_confidence(0.5), 0.5)

    def test_clamps_above(self) -> None:
        """Confidence above 1.0 is clamped to 1.0."""
        self.assertAlmostEqual(_clamp_confidence(1.5), 1.0)

    def test_clamps_below(self) -> None:
        """Confidence below 0.0 is clamped to 0.0."""
        self.assertAlmostEqual(_clamp_confidence(-0.3), 0.0)

    def test_invalid_returns_zero(self) -> None:
        """Non-numeric values default to 0.0."""
        self.assertAlmostEqual(_clamp_confidence("bad"), 0.0)


class TestValidateEvidenceIds(unittest.TestCase):
    """Unit tests for _validate_evidence_ids helper."""

    def setUp(self) -> None:
        """Set up evidence list for validation tests."""
        self.evidence = [
            {"url": "https://example.com/a"},
            {"url": "https://example.com/b"},
        ]

    def test_valid_ids(self) -> None:
        """All IDs matching stored evidence URLs are accepted."""
        result = _validate_evidence_ids(
            ["https://example.com/a", "https://example.com/b"],
            self.evidence,
        )
        self.assertEqual(result, ["https://example.com/a", "https://example.com/b"])

    def test_unknown_id_returns_none(self) -> None:
        """An ID not in the evidence list causes rejection."""
        result = _validate_evidence_ids(
            ["https://example.com/a", "https://unknown.com/fake"],
            self.evidence,
        )
        self.assertIsNone(result)

    def test_empty_ids_returns_empty_list(self) -> None:
        """An empty evidence_ids list is valid."""
        result = _validate_evidence_ids([], self.evidence)
        self.assertEqual(result, [])

    def test_non_list_returns_none(self) -> None:
        """A non-list evidence_ids value causes rejection."""
        result = _validate_evidence_ids("not-a-list", self.evidence)
        self.assertIsNone(result)

    def test_non_string_id_returns_none(self) -> None:
        """A non-string element in evidence_ids causes rejection."""
        result = _validate_evidence_ids([123], self.evidence)
        self.assertIsNone(result)


class TestMoatAnalysisValidLLM(unittest.TestCase):
    """Tests for successful LLM-backed moat analysis."""

    @patch("agents.moat_analysis.is_llm_configured", return_value=True)
    @patch("agents.moat_analysis.ask_llm_json")
    def test_valid_llm_output_updates_record(
        self, mock_ask, _mock_configured
    ) -> None:
        """Valid LLM response writes score, rationale, confidence, IDs."""
        mock_ask.return_value = LLMResult.success(_valid_llm_data())

        record = _make_record()
        result = run([record])

        self.assertIs(result[0], record)
        self.assertEqual(record["moat_score"], 4)
        self.assertEqual(
            record["moat_rationale"],
            "Strong IP and switching costs in the GPU market.",
        )
        self.assertAlmostEqual(record["analysis_confidence"], 0.85)
        self.assertEqual(
            record["moat_evidence_ids"],
            ["https://example.com/report1", "https://example.com/report2"],
        )
        # At least one evidence item is "verified"
        self.assertEqual(record["analysis_status"], "verified")

    @patch("agents.moat_analysis.is_llm_configured", return_value=True)
    @patch("agents.moat_analysis.ask_llm_json")
    def test_partial_evidence_ids_accepted(
        self, mock_ask, _mock_configured
    ) -> None:
        """LLM citing only a subset of available evidence is valid."""
        data = _valid_llm_data()
        data["evidence_ids"] = ["https://example.com/report1"]
        mock_ask.return_value = LLMResult.success(data)

        record = _make_record()
        run([record])

        self.assertEqual(record["moat_score"], 4)
        self.assertEqual(record["moat_evidence_ids"], ["https://example.com/report1"])

    @patch("agents.moat_analysis.is_llm_configured", return_value=True)
    @patch("agents.moat_analysis.ask_llm_json")
    def test_empty_evidence_ids_accepted(
        self, mock_ask, _mock_configured
    ) -> None:
        """LLM returning no evidence IDs is valid."""
        data = _valid_llm_data()
        data["evidence_ids"] = []
        mock_ask.return_value = LLMResult.success(data)

        record = _make_record()
        run([record])

        self.assertEqual(record["moat_score"], 4)
        self.assertEqual(record["moat_evidence_ids"], [])


class TestMoatAnalysisInvalidCitations(unittest.TestCase):
    """Tests for LLM responses with invalid evidence citations."""

    @patch("agents.moat_analysis.is_llm_configured", return_value=True)
    @patch("agents.moat_analysis.ask_llm_json")
    def test_fabricated_citation_triggers_fallback(
        self, mock_ask, _mock_configured
    ) -> None:
        """Fabricated URL in evidence_ids triggers CSV fallback."""
        data = _valid_llm_data()
        data["evidence_ids"] = ["https://fabricated.com/fake-source"]
        mock_ask.return_value = LLMResult.success(data)

        record = _make_record(moat_score=2)
        run([record])

        # Falls back to the original CSV score (clamped)
        self.assertEqual(record["moat_score"], 2)
        self.assertEqual(record["analysis_status"], "fallback")
        self.assertNotIn("moat_rationale", record)

    @patch("agents.moat_analysis.is_llm_configured", return_value=True)
    @patch("agents.moat_analysis.ask_llm_json")
    def test_mixed_valid_and_invalid_citations_triggers_fallback(
        self, mock_ask, _mock_configured
    ) -> None:
        """One valid and one fabricated citation still triggers fallback."""
        data = _valid_llm_data()
        data["evidence_ids"] = [
            "https://example.com/report1",
            "https://fabricated.com/bogus",
        ]
        mock_ask.return_value = LLMResult.success(data)

        record = _make_record(moat_score=3)
        run([record])

        self.assertEqual(record["moat_score"], 3)
        self.assertEqual(record["analysis_status"], "fallback")


class TestMoatAnalysisMalformedLLM(unittest.TestCase):
    """Tests for malformed or failed LLM responses."""

    @patch("agents.moat_analysis.is_llm_configured", return_value=True)
    @patch("agents.moat_analysis.ask_llm_json")
    def test_llm_failure_preserves_csv_score(
        self, mock_ask, _mock_configured
    ) -> None:
        """Provider failure preserves the existing CSV moat_score."""
        mock_ask.return_value = LLMResult.failure(
            LLMErrorType.PROVIDER, "Gemini provider request failed."
        )

        record = _make_record(moat_score=4)
        run([record])

        self.assertEqual(record["moat_score"], 4)
        self.assertEqual(record["analysis_status"], "fallback")

    @patch("agents.moat_analysis.is_llm_configured", return_value=True)
    @patch("agents.moat_analysis.ask_llm_json")
    def test_timeout_preserves_csv_score(
        self, mock_ask, _mock_configured
    ) -> None:
        """Timeout preserves the existing CSV moat_score."""
        mock_ask.return_value = LLMResult.failure(
            LLMErrorType.TIMEOUT, "Gemini request timed out."
        )

        record = _make_record(moat_score=2)
        run([record])

        self.assertEqual(record["moat_score"], 2)
        self.assertEqual(record["analysis_status"], "fallback")

    @patch("agents.moat_analysis.is_llm_configured", return_value=True)
    @patch("agents.moat_analysis.ask_llm_json")
    def test_config_error_preserves_csv_score(
        self, mock_ask, _mock_configured
    ) -> None:
        """Configuration error preserves the existing CSV moat_score."""
        mock_ask.return_value = LLMResult.failure(
            LLMErrorType.CONFIGURATION, "GEMINI_API_KEY is missing."
        )

        record = _make_record(moat_score=1)
        run([record])

        self.assertEqual(record["moat_score"], 1)
        self.assertEqual(record["analysis_status"], "fallback")

    @patch("agents.moat_analysis.is_llm_configured", return_value=True)
    @patch("agents.moat_analysis.ask_llm_json")
    def test_empty_rationale_triggers_fallback(
        self, mock_ask, _mock_configured
    ) -> None:
        """Empty rationale from LLM triggers CSV fallback."""
        data = _valid_llm_data()
        data["rationale"] = ""
        mock_ask.return_value = LLMResult.success(data)

        record = _make_record(moat_score=3)
        run([record])

        self.assertEqual(record["moat_score"], 3)
        self.assertEqual(record["analysis_status"], "fallback")


class TestMoatAnalysisLLMUnavailable(unittest.TestCase):
    """Tests for when LLM is not configured at all."""

    @patch("agents.moat_analysis.is_llm_configured", return_value=False)
    def test_no_api_key_uses_csv_only(self, _mock_configured) -> None:
        """Without an API key, scores pass through with clamping only."""
        records = [
            {"moat_score": 0},
            {"moat_score": "3"},
            {"moat_score": 5},
        ]

        result = run(records)

        self.assertIs(result, records)
        self.assertEqual([r["moat_score"] for r in result], [0, 3, 5])

    @patch("agents.moat_analysis.is_llm_configured", return_value=False)
    def test_no_api_key_clamps_out_of_range(self, _mock_configured) -> None:
        """Without an API key, out-of-range scores are clamped."""
        records = [
            {"moat_score": -2},
            {"moat_score": 9},
            {"moat_score": "N/A"},
        ]

        result = run(records)

        self.assertEqual([r["moat_score"] for r in result], [0, 5, 0])


class TestMoatAnalysisNoEvidence(unittest.TestCase):
    """Tests for records with no evidence — should skip LLM even if configured."""

    @patch("agents.moat_analysis.is_llm_configured", return_value=True)
    @patch("agents.moat_analysis.ask_llm_json")
    def test_no_evidence_skips_llm(self, mock_ask, _mock_configured) -> None:
        """Records with empty evidence skip the LLM call entirely."""
        record = _make_record(evidence=[], moat_score=2)
        run([record])

        mock_ask.assert_not_called()
        self.assertEqual(record["moat_score"], 2)


class TestMoatAnalysisFieldIsolation(unittest.TestCase):
    """Tests that unrelated record fields are not modified."""

    @patch("agents.moat_analysis.is_llm_configured", return_value=True)
    @patch("agents.moat_analysis.ask_llm_json")
    def test_does_not_change_unrelated_fields(
        self, mock_ask, _mock_configured
    ) -> None:
        """LLM analysis does not modify company, role, or other scores."""
        mock_ask.return_value = LLMResult.success(_valid_llm_data())

        record = _make_record(
            company="Example Corp",
            role="Networking",
            growth_forecast_pct=45.0,
            tafgs_score=12.5,
        )
        run([record])

        self.assertEqual(record["company"], "Example Corp")
        self.assertEqual(record["role"], "Networking")
        self.assertEqual(record["growth_forecast_pct"], 45.0)
        self.assertEqual(record["tafgs_score"], 12.5)

    @patch("agents.moat_analysis.is_llm_configured", return_value=False)
    def test_csv_fallback_does_not_change_unrelated_fields(
        self, _mock_configured
    ) -> None:
        """CSV-only fallback does not modify company or role."""
        record = {"company": "Example Corp", "role": "Networking", "moat_score": 4}
        run([record])

        self.assertEqual(record["company"], "Example Corp")
        self.assertEqual(record["role"], "Networking")


class TestMoatAnalysisMultipleRecords(unittest.TestCase):
    """Tests for processing multiple records with mixed outcomes."""

    @patch("agents.moat_analysis.is_llm_configured", return_value=True)
    @patch("agents.moat_analysis.ask_llm_json")
    def test_per_record_independence(
        self, mock_ask, _mock_configured
    ) -> None:
        """One record failing LLM should not affect another succeeding."""
        good_data = _valid_llm_data()
        bad_result = LLMResult.failure(LLMErrorType.PROVIDER, "Failed")
        good_result = LLMResult.success(good_data)

        mock_ask.side_effect = [bad_result, good_result]

        record_a = _make_record(company="FailCorp", moat_score=1)
        record_b = _make_record(company="SuccessCorp", moat_score=2)

        run([record_a, record_b])

        # FailCorp: fallback
        self.assertEqual(record_a["moat_score"], 1)
        self.assertEqual(record_a["analysis_status"], "fallback")

        # SuccessCorp: LLM result applied
        self.assertEqual(record_b["moat_score"], 4)
        self.assertEqual(record_b["analysis_status"], "verified")


class TestMoatAnalysisUnexpectedException(unittest.TestCase):
    """Tests for unexpected exceptions during LLM analysis."""

    @patch("agents.moat_analysis.is_llm_configured", return_value=True)
    @patch("agents.moat_analysis.ask_llm_json", side_effect=RuntimeError("unexpected"))
    def test_unexpected_error_triggers_fallback(
        self, _mock_ask, _mock_configured
    ) -> None:
        """Unexpected RuntimeError triggers CSV fallback gracefully."""
        record = _make_record(moat_score=3)
        run([record])

        self.assertEqual(record["moat_score"], 3)
        self.assertEqual(record["analysis_status"], "fallback")


if __name__ == "__main__":
    unittest.main()
