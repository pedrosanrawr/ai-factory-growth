import logging
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

logging.getLogger("agents.risk_adjustment").setLevel(logging.CRITICAL)

from agents.risk_adjustment import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    _clamp,
    _valid_evidence_ids,
    enrich_risk_inputs,
    run,
)
from services.llm_client import LLMErrorType, LLMResult
from schema import empty_record


def make_record(**overrides) -> dict:
    """Start from the shared schema's blank record, override fields per test."""
    record = empty_record()
    record.update(
        {
            "growth_forecast_pct": 20.0,
            "concentration_risk": 0.5,
            "cyclicality_risk": 0.4,
            "execution_risk": 0.3,
            "eff_score": 3,
        }
    )
    record.update(overrides)
    return record

class TestClamp(unittest.TestCase):
    """_clamp() should keep values within the given bounds."""

    def test_within_range_unchanged(self):
        self.assertEqual(_clamp(0.5), 0.5)

    def test_above_range_clamped_to_hi(self):
        self.assertEqual(_clamp(1.5), 1.0)

    def test_below_range_clamped_to_lo(self):
        self.assertEqual(_clamp(-0.5), 0.0)

    def test_non_numeric_falls_back_to_lo(self):
        self.assertEqual(_clamp("n/a"), 0.0)

    def test_none_falls_back_to_lo(self):
        self.assertEqual(_clamp(None), 0.0)

    def test_custom_bounds(self):
        self.assertEqual(_clamp(50, lo=0, hi=30), 30)
        self.assertEqual(_clamp(-5, lo=0, hi=30), 0)
        self.assertEqual(_clamp(15, lo=0, hi=30), 15)


class TestWorkedExamplesAtDefaultDiscount(unittest.TestCase):
    """Reproduce the spec's worked examples at risk_discount_pct=10 exactly."""

    def test_nvidia(self):
        record = make_record(
            company="NVIDIA",
            growth_forecast_pct=45.0,
            concentration_risk=0.8,
            cyclicality_risk=0.3,
            execution_risk=0.3,
            eff_score=5,
        )
        out = run([record], risk_discount_pct=10.0)[0]
        self.assertEqual(out["risk_multiplier"], 0.946)
        self.assertAlmostEqual(out["adjusted_growth_pct"], 38.31, places=2)

    def test_fluor(self):
        record = make_record(
            company="Fluor",
            growth_forecast_pct=15.0,
            concentration_risk=0.5,
            cyclicality_risk=0.6,
            execution_risk=0.8,
            eff_score=1,
        )
        out = run([record], risk_discount_pct=10.0)[0]
        self.assertEqual(out["risk_multiplier"], 0.81)
        self.assertAlmostEqual(out["adjusted_growth_pct"], 10.94, places=1)


class TestWorkedExamplesAtZeroDiscount(unittest.TestCase):
    """Same companies with no global discount applied."""

    def test_nvidia_zero_discount(self):
        record = make_record(
            growth_forecast_pct=45.0,
            concentration_risk=0.8,
            cyclicality_risk=0.3,
            execution_risk=0.3,
            eff_score=5,
        )
        out = run([record], risk_discount_pct=0.0)[0]
        self.assertAlmostEqual(out["adjusted_growth_pct"], 42.57, places=2)

    def test_fluor_zero_discount(self):
        record = make_record(
            growth_forecast_pct=15.0,
            concentration_risk=0.5,
            cyclicality_risk=0.6,
            execution_risk=0.8,
            eff_score=1,
        )
        out = run([record], risk_discount_pct=0.0)[0]
        self.assertAlmostEqual(out["adjusted_growth_pct"], 12.15, places=2)


class TestFormulaSteps(unittest.TestCase):
    """Check each intermediate step directly, independent of the worked examples."""

    def test_zero_risk_zero_discount_no_change(self):
        record = make_record(
            growth_forecast_pct=30.0,
            concentration_risk=0.0,
            cyclicality_risk=0.0,
            execution_risk=0.0,
            eff_score=1,
        )
        out = run([record], risk_discount_pct=0.0)[0]
        self.assertEqual(out["risk_multiplier"], 1.0)
        self.assertEqual(out["adjusted_growth_pct"], 30.0)

    def test_max_risk_caps_base_discount_at_30_percent(self):
        record = make_record(
            concentration_risk=1.0, cyclicality_risk=1.0, execution_risk=1.0, eff_score=1
        )
        out = run([record], risk_discount_pct=0.0)[0]
        self.assertEqual(out["risk_multiplier"], 0.7)

    def test_max_eff_score_gives_ten_percent_bonus(self):
        record = make_record(
            concentration_risk=0.0, cyclicality_risk=0.0, execution_risk=0.0, eff_score=5
        )
        out = run([record], risk_discount_pct=0.0)[0]
        self.assertEqual(out["risk_multiplier"], 1.1)

    def test_global_discount_at_thirty_percent(self):
        record = make_record(
            growth_forecast_pct=100.0,
            concentration_risk=0.0,
            cyclicality_risk=0.0,
            execution_risk=0.0,
            eff_score=1,
        )
        out = run([record], risk_discount_pct=30.0)[0]
        self.assertEqual(out["adjusted_growth_pct"], 70.0)


class TestClampingOfInputs(unittest.TestCase):
    """Out-of-range risk sub-scores and slider values must be clamped, not rejected."""

    def test_risk_subscores_above_one_are_clamped(self):
        record = make_record(
            concentration_risk=5.0, cyclicality_risk=5.0, execution_risk=5.0, eff_score=1
        )
        out = run([record], risk_discount_pct=0.0)[0]
        self.assertEqual(out["risk_multiplier"], 0.7)

    def test_risk_subscores_below_zero_are_clamped(self):
        record = make_record(
            concentration_risk=-2.0, cyclicality_risk=-2.0, execution_risk=-2.0, eff_score=1
        )
        out = run([record], risk_discount_pct=0.0)[0]
        self.assertEqual(out["risk_multiplier"], 1.0)

    def test_global_discount_above_thirty_is_capped(self):
        out_over = run([make_record(growth_forecast_pct=100.0)], risk_discount_pct=999.0)[0]
        out_capped = run([make_record(growth_forecast_pct=100.0)], risk_discount_pct=30.0)[0]
        self.assertEqual(out_over["adjusted_growth_pct"], out_capped["adjusted_growth_pct"])

    def test_global_discount_below_zero_is_floored(self):
        out_under = run([make_record(growth_forecast_pct=100.0)], risk_discount_pct=-50.0)[0]
        out_floored = run([make_record(growth_forecast_pct=100.0)], risk_discount_pct=0.0)[0]
        self.assertEqual(out_under["adjusted_growth_pct"], out_floored["adjusted_growth_pct"])

    def test_non_numeric_global_discount_falls_back_to_default(self):
        out_bad = run([make_record(growth_forecast_pct=100.0)], risk_discount_pct="oops")[0]
        out_default = run([make_record(growth_forecast_pct=100.0)], risk_discount_pct=10.0)[0]
        self.assertEqual(out_bad["adjusted_growth_pct"], out_default["adjusted_growth_pct"])


class TestSafeDefaultsAndNoCrash(unittest.TestCase):
    """run() must never crash on missing or malformed record fields."""

    def test_blank_schema_record_does_not_crash(self):
        out = run([empty_record()], risk_discount_pct=10.0)[0]
        self.assertIn("risk_multiplier", out)
        self.assertIn("adjusted_growth_pct", out)
        self.assertEqual(out["adjusted_growth_pct"], 0.0)

    def test_missing_keys_entirely_does_not_crash(self):
        out = run([{}], risk_discount_pct=10.0)[0]
        self.assertIn("risk_multiplier", out)
        self.assertIn("adjusted_growth_pct", out)
        self.assertEqual(out["adjusted_growth_pct"], 0.0)

    def test_non_numeric_growth_forecast_falls_back_to_zero(self):
        record = make_record(growth_forecast_pct="n/a")
        out = run([record], risk_discount_pct=10.0)[0]
        self.assertEqual(out["adjusted_growth_pct"], 0.0)

    def test_eff_score_out_of_bounds_is_clamped(self):
        record = make_record(eff_score=99)
        out = run([record], risk_discount_pct=0.0)[0]
        expected = run([make_record(eff_score=5)], risk_discount_pct=0.0)[0]
        self.assertEqual(out["risk_multiplier"], expected["risk_multiplier"])

    def test_eff_score_below_one_is_clamped(self):
        record = make_record(eff_score=-10)
        out = run([record], risk_discount_pct=0.0)[0]
        expected = run([make_record(eff_score=1)], risk_discount_pct=0.0)[0]
        self.assertEqual(out["risk_multiplier"], expected["risk_multiplier"])

    def test_missing_eff_score_defaults_to_one(self):
        record = make_record()
        del record["eff_score"]
        out = run([record], risk_discount_pct=0.0)[0]
        expected = run([make_record(eff_score=1)], risk_discount_pct=0.0)[0]
        self.assertEqual(out["risk_multiplier"], expected["risk_multiplier"])


class TestDoesNotMutateOtherFields(unittest.TestCase):
    """Per the spec: only risk_multiplier and adjusted_growth_pct may be written;
    growth_forecast_pct and unrelated schema fields must be left untouched."""

    def test_growth_forecast_pct_unchanged(self):
        record = make_record(growth_forecast_pct=45.0)
        out = run([record], risk_discount_pct=10.0)[0]
        self.assertEqual(out["growth_forecast_pct"], 45.0)

    def test_unrelated_schema_fields_untouched(self):
        record = make_record(company="NVIDIA", role="Compute/Server", moat_score=5)
        out = run([record], risk_discount_pct=10.0)[0]
        self.assertEqual(out["company"], "NVIDIA")
        self.assertEqual(out["role"], "Compute/Server")
        self.assertEqual(out["moat_score"], 5)

    def test_run_does_not_touch_analysis_fields(self):
        # run() must never write analysis_status / analysis_confidence /
        # evidence / research_as_of -- that's enrich_risk_inputs()'s job.
        record = make_record(
            analysis_status="needs_review", analysis_confidence=0.6
        )
        out = run([record], risk_discount_pct=10.0)[0]
        self.assertEqual(out["analysis_status"], "needs_review")
        self.assertEqual(out["analysis_confidence"], 0.6)

    def test_rounded_to_four_decimal_places(self):
        record = make_record(
            growth_forecast_pct=33.333,
            concentration_risk=0.37,
            cyclicality_risk=0.61,
            execution_risk=0.29,
            eff_score=4,
        )
        out = run([record], risk_discount_pct=13.0)[0]
        self.assertEqual(out["risk_multiplier"], round(out["risk_multiplier"], 4))
        self.assertEqual(out["adjusted_growth_pct"], round(out["adjusted_growth_pct"], 4))


class TestMultipleRecordsAndListReturn(unittest.TestCase):
    """run() should process every record and return the same list object shape."""

    def test_all_records_processed(self):
        records = [
            make_record(growth_forecast_pct=45.0),
            make_record(growth_forecast_pct=15.0),
            make_record(growth_forecast_pct=20.0),
        ]
        out = run(records, risk_discount_pct=10.0)
        self.assertEqual(len(out), 3)
        for r in out:
            self.assertIn("risk_multiplier", r)
            self.assertIn("adjusted_growth_pct", r)

    def test_empty_list_returns_empty_list(self):
        self.assertEqual(run([], risk_discount_pct=10.0), [])

    def test_default_risk_discount_pct_is_ten(self):
        out_default = run([make_record(growth_forecast_pct=100.0)])[0]
        out_explicit = run([make_record(growth_forecast_pct=100.0)], risk_discount_pct=10.0)[0]
        self.assertEqual(out_default["adjusted_growth_pct"], out_explicit["adjusted_growth_pct"])

# ---------------------------------------------------------------------------
# _valid_evidence_ids() -- citation validation helper
# ---------------------------------------------------------------------------

class TestValidEvidenceIds(unittest.TestCase):
    def test_empty_list_is_invalid(self):
        record = make_record(evidence=[{"id": "e1"}])
        self.assertFalse(_valid_evidence_ids(record, []))

    def test_non_list_is_invalid(self):
        record = make_record(evidence=[{"id": "e1"}])
        self.assertFalse(_valid_evidence_ids(record, "e1"))
        self.assertFalse(_valid_evidence_ids(record, None))

    def test_unknown_id_is_invalid(self):
        record = make_record(evidence=[{"id": "e1"}])
        self.assertFalse(_valid_evidence_ids(record, ["e1", "e2-does-not-exist"]))

    def test_no_evidence_on_record_is_invalid(self):
        record = make_record(evidence=[])
        self.assertFalse(_valid_evidence_ids(record, ["e1"]))

    def test_known_ids_are_valid(self):
        record = make_record(evidence=[{"id": "e1"}, {"id": "e2"}])
        self.assertTrue(_valid_evidence_ids(record, ["e1"]))
        self.assertTrue(_valid_evidence_ids(record, ["e1", "e2"]))


# ---------------------------------------------------------------------------
# enrich_risk_inputs() -- Gemini-based evidence-grounded enrichment.
# ---------------------------------------------------------------------------

class TestEnrichUnavailable(unittest.TestCase):
    """No local Gemini API key configured -> untouched CSV values, 'unavailable'."""

    @patch("agents.risk_adjustment.is_llm_configured", return_value=False)
    @patch("agents.risk_adjustment.ask_llm_json")
    def test_unavailable_leaves_csv_risk_values_untouched(self, mock_ask, mock_configured):
        record = make_record(
            concentration_risk=0.8, cyclicality_risk=0.3, execution_risk=0.3
        )
        out = enrich_risk_inputs([record])[0]

        self.assertEqual(out["analysis_status"], "unavailable")
        self.assertIsNone(out["analysis_confidence"])
        self.assertEqual(out["concentration_risk"], 0.8)
        self.assertEqual(out["cyclicality_risk"], 0.3)
        self.assertEqual(out["execution_risk"], 0.3)
        mock_ask.assert_not_called()


class TestEnrichProviderFailure(unittest.TestCase):
    """Gemini configured but the call itself fails -> fallback, CSV values kept."""

    @patch("agents.risk_adjustment.is_llm_configured", return_value=True)
    @patch("agents.risk_adjustment.ask_llm_json")
    def test_provider_error_falls_back(self, mock_ask, mock_configured):
        mock_ask.return_value = LLMResult.failure(
            LLMErrorType.PROVIDER, "Gemini provider request failed."
        )
        record = make_record(
            concentration_risk=0.8, cyclicality_risk=0.3, execution_risk=0.3
        )
        out = enrich_risk_inputs([record])[0]

        self.assertEqual(out["analysis_status"], "fallback")
        self.assertIsNone(out["analysis_confidence"])
        self.assertEqual(out["concentration_risk"], 0.8)
        self.assertEqual(out["cyclicality_risk"], 0.3)
        self.assertEqual(out["execution_risk"], 0.3)

    @patch("agents.risk_adjustment.is_llm_configured", return_value=True)
    @patch("agents.risk_adjustment.ask_llm_json")
    def test_timeout_falls_back(self, mock_ask, mock_configured):
        mock_ask.return_value = LLMResult.failure(
            LLMErrorType.TIMEOUT, "Gemini request timed out."
        )
        record = make_record()
        out = enrich_risk_inputs([record])[0]
        self.assertEqual(out["analysis_status"], "fallback")

    @patch("agents.risk_adjustment.is_llm_configured", return_value=True)
    @patch("agents.risk_adjustment.ask_llm_json")
    def test_malformed_response_falls_back(self, mock_ask, mock_configured):
        mock_ask.return_value = LLMResult.failure(
            LLMErrorType.MALFORMED_RESPONSE, "The LLM returned malformed JSON."
        )
        record = make_record()
        out = enrich_risk_inputs([record])[0]
        self.assertEqual(out["analysis_status"], "fallback")

    @patch("agents.risk_adjustment.is_llm_configured", return_value=True)
    @patch("agents.risk_adjustment.ask_llm_json", side_effect=RuntimeError("boom"))
    def test_unexpected_exception_does_not_crash_pipeline(self, mock_ask, mock_configured):
        # Defensive: even if the shared client ever raised instead of
        # returning LLMResult, this agent must not propagate the crash.
        record = make_record(concentration_risk=0.4)
        out = enrich_risk_inputs([record])[0]
        self.assertEqual(out["analysis_status"], "fallback")
        self.assertEqual(out["concentration_risk"], 0.4)


class TestEnrichInvalidCitations(unittest.TestCase):
    """Gemini succeeds but cites evidence not present on the record -> fallback."""

    @patch("agents.risk_adjustment.is_llm_configured", return_value=True)
    @patch("agents.risk_adjustment.ask_llm_json")
    def test_unknown_evidence_id_falls_back(self, mock_ask, mock_configured):
        mock_ask.return_value = LLMResult.success(
            {
                "concentration_risk": 0.9,
                "cyclicality_risk": 0.9,
                "execution_risk": 0.9,
                "rationale": "Looks risky.",
                "confidence": 0.95,
                "evidence_ids": ["e-does-not-exist"],
            }
        )
        record = make_record(
            evidence=[{"id": "e1", "snippet": "10-K filing excerpt."}],
            concentration_risk=0.2,
            cyclicality_risk=0.2,
            execution_risk=0.2,
        )
        out = enrich_risk_inputs([record])[0]

        self.assertEqual(out["analysis_status"], "fallback")
        self.assertIsNone(out["analysis_confidence"])
        self.assertEqual(out["concentration_risk"], 0.2)
        self.assertEqual(out["cyclicality_risk"], 0.2)
        self.assertEqual(out["execution_risk"], 0.2)

    @patch("agents.risk_adjustment.is_llm_configured", return_value=True)
    @patch("agents.risk_adjustment.ask_llm_json")
    def test_empty_evidence_ids_falls_back(self, mock_ask, mock_configured):
        mock_ask.return_value = LLMResult.success(
            {
                "concentration_risk": 0.9,
                "cyclicality_risk": 0.9,
                "execution_risk": 0.9,
                "rationale": "No sources cited.",
                "confidence": 0.95,
                "evidence_ids": [],
            }
        )
        record = make_record(evidence=[{"id": "e1"}])
        out = enrich_risk_inputs([record])[0]
        self.assertEqual(out["analysis_status"], "fallback")


class TestEnrichSuccess(unittest.TestCase):
    """Gemini succeeds with verifiable citations -> risk values overwritten."""

    @patch("agents.risk_adjustment.is_llm_configured", return_value=True)
    @patch("agents.risk_adjustment.ask_llm_json")
    def test_high_confidence_is_verified(self, mock_ask, mock_configured):
        mock_ask.return_value = LLMResult.success(
            {
                "concentration_risk": 0.6,
                "cyclicality_risk": 0.4,
                "execution_risk": 0.2,
                "rationale": "Well-supported by the filing.",
                "confidence": 0.9,
                "evidence_ids": ["e1"],
            }
        )
        record = make_record(
            evidence=[{"id": "e1", "snippet": "10-K filing excerpt."}],
            concentration_risk=0.1,
            cyclicality_risk=0.1,
            execution_risk=0.1,
        )
        out = enrich_risk_inputs([record])[0]

        self.assertEqual(out["analysis_status"], "verified")
        self.assertEqual(out["analysis_confidence"], 0.9)
        self.assertEqual(out["concentration_risk"], 0.6)
        self.assertEqual(out["cyclicality_risk"], 0.4)
        self.assertEqual(out["execution_risk"], 0.2)
        self.assertNotEqual(out["research_as_of"], "")

    @patch("agents.risk_adjustment.is_llm_configured", return_value=True)
    @patch("agents.risk_adjustment.ask_llm_json")
    def test_low_confidence_needs_review(self, mock_ask, mock_configured):
        mock_ask.return_value = LLMResult.success(
            {
                "concentration_risk": 0.5,
                "cyclicality_risk": 0.5,
                "execution_risk": 0.5,
                "rationale": "Evidence is thin.",
                "confidence": 0.4,
                "evidence_ids": ["e1"],
            }
        )
        record = make_record(evidence=[{"id": "e1"}])
        out = enrich_risk_inputs([record])[0]

        self.assertEqual(out["analysis_status"], "needs_review")
        self.assertEqual(out["analysis_confidence"], 0.4)
        # even at low confidence, the (valid, cited) LLM values are used
        self.assertEqual(out["concentration_risk"], 0.5)

    @patch("agents.risk_adjustment.is_llm_configured", return_value=True)
    @patch("agents.risk_adjustment.ask_llm_json")
    def test_custom_confidence_threshold(self, mock_ask, mock_configured):
        mock_ask.return_value = LLMResult.success(
            {
                "concentration_risk": 0.5,
                "cyclicality_risk": 0.5,
                "execution_risk": 0.5,
                "rationale": "Moderate evidence.",
                "confidence": 0.6,
                "evidence_ids": ["e1"],
            }
        )
        record = make_record(evidence=[{"id": "e1"}])

        out_default = enrich_risk_inputs([make_record(**record)])[0]
        self.assertEqual(out_default["analysis_status"], "needs_review")

        out_custom = enrich_risk_inputs(
            [make_record(**record)], confidence_threshold=0.5
        )[0]
        self.assertEqual(out_custom["analysis_status"], "verified")  


class TestEnrichBoundsClamping(unittest.TestCase):
    """Out-of-range LLM output must be clamped, not trusted or rejected outright."""

    @patch("agents.risk_adjustment.is_llm_configured", return_value=True)
    @patch("agents.risk_adjustment.ask_llm_json")
    def test_out_of_range_subscores_are_clamped(self, mock_ask, mock_configured):
        mock_ask.return_value = LLMResult.success(
            {
                "concentration_risk": 5.0,
                "cyclicality_risk": -2.0,
                "execution_risk": 0.5,
                "rationale": "Out of range on purpose.",
                "confidence": 0.9,
                "evidence_ids": ["e1"],
            }
        )
        record = make_record(evidence=[{"id": "e1"}])
        out = enrich_risk_inputs([record])[0]

        self.assertEqual(out["concentration_risk"], 1.0)
        self.assertEqual(out["cyclicality_risk"], 0.0)
        self.assertEqual(out["execution_risk"], 0.5)
        self.assertEqual(out["analysis_status"], "verified")

    @patch("agents.risk_adjustment.is_llm_configured", return_value=True)
    @patch("agents.risk_adjustment.ask_llm_json")
    def test_out_of_range_confidence_is_clamped(self, mock_ask, mock_configured):
        mock_ask.return_value = LLMResult.success(
            {
                "concentration_risk": 0.3,
                "cyclicality_risk": 0.3,
                "execution_risk": 0.3,
                "rationale": "Overconfident on purpose.",
                "confidence": 3.0,
                "evidence_ids": ["e1"],
            }
        )
        record = make_record(evidence=[{"id": "e1"}])
        out = enrich_risk_inputs([record])[0]
        self.assertEqual(out["analysis_confidence"], 1.0)
        self.assertEqual(out["analysis_status"], "verified")


class TestEnrichMultipleRecords(unittest.TestCase):
    """Each record in the batch is evaluated independently."""

    @patch("agents.risk_adjustment.is_llm_configured", return_value=True)
    @patch("agents.risk_adjustment.ask_llm_json")
    def test_mixed_outcomes_across_records(self, mock_ask, mock_configured):
        success_result = LLMResult.success(
            {
                "concentration_risk": 0.7,
                "cyclicality_risk": 0.7,
                "execution_risk": 0.7,
                "rationale": "Solid evidence.",
                "confidence": 0.9,
                "evidence_ids": ["e1"],
            }
        )
        failure_result = LLMResult.failure(LLMErrorType.PROVIDER, "down")
        mock_ask.side_effect = [success_result, failure_result]

        good_record = make_record(evidence=[{"id": "e1"}], concentration_risk=0.1)
        bad_record = make_record(concentration_risk=0.2)

        out = enrich_risk_inputs([good_record, bad_record])

        self.assertEqual(out[0]["analysis_status"], "verified")
        self.assertEqual(out[0]["concentration_risk"], 0.7)
        self.assertEqual(out[1]["analysis_status"], "fallback")
        self.assertEqual(out[1]["concentration_risk"], 0.2)


class TestEnrichThenRunIntegration(unittest.TestCase):
    """The two-step pipeline: enrich_risk_inputs() feeds run() correctly,
    and neither step writes fields owned by the other."""

    @patch("agents.risk_adjustment.is_llm_configured", return_value=True)
    @patch("agents.risk_adjustment.ask_llm_json")
    def test_llm_derived_scores_flow_into_the_deterministic_formula(
        self, mock_ask, mock_configured
    ):
        mock_ask.return_value = LLMResult.success(
            {
                "concentration_risk": 0.8,
                "cyclicality_risk": 0.3,
                "execution_risk": 0.3,
                "rationale": "Matches the NVIDIA worked example.",
                "confidence": 0.95,
                "evidence_ids": ["e1"],
            }
        )
        record = make_record(
            company="NVIDIA",
            growth_forecast_pct=45.0,
            eff_score=5,
            evidence=[{"id": "e1"}],
            concentration_risk=0.0,
            cyclicality_risk=0.0,
            execution_risk=0.0,
        )

        records = enrich_risk_inputs([record])
        self.assertEqual(records[0]["analysis_status"], "verified")

        out = run(records, risk_discount_pct=10.0)[0]
        self.assertEqual(out["risk_multiplier"], 0.946)
        self.assertAlmostEqual(out["adjusted_growth_pct"], 38.31, places=2)
        self.assertEqual(out["analysis_status"], "verified")
        self.assertEqual(out["analysis_confidence"], 0.95)

    @patch("agents.risk_adjustment.is_llm_configured", return_value=False)
    @patch("agents.risk_adjustment.ask_llm_json")
    def test_unavailable_llm_still_produces_a_full_deterministic_result(
        self, mock_ask, mock_configured
    ):
        record = make_record(
            growth_forecast_pct=15.0,
            concentration_risk=0.5,
            cyclicality_risk=0.6,
            execution_risk=0.8,
            eff_score=1,
        )
        records = enrich_risk_inputs([record])
        self.assertEqual(records[0]["analysis_status"], "unavailable")

        out = run(records, risk_discount_pct=10.0)[0]
        self.assertEqual(out["risk_multiplier"], 0.81)
        self.assertAlmostEqual(out["adjusted_growth_pct"], 10.94, places=1)


if __name__ == "__main__":
    unittest.main()