"""Tests for the LangGraph workflow and cross-validation gate."""

import unittest
from unittest.mock import patch

from workflow import build_workflow, cross_validate_records, run_workflow


class TestCrossValidation(unittest.TestCase):
    def test_corrects_invalid_agent_inputs_and_marks_verified_claim_for_review(self):
        records, errors = cross_validate_records(
            [
                {
                    "company": "Example Co",
                    "moat_score": 9,
                    "growth_forecast_pct": 999.0,
                    "concentration_risk": -1,
                    "cyclicality_risk": 2,
                    "execution_risk": "bad",
                    "analysis_confidence": 3,
                    "analysis_status": "verified",
                    "evidence": [{"url": "https://example.com/source", "status": "needs_review"}],
                }
            ]
        )
        record = records[0]

        self.assertEqual(record["moat_score"], 5)
        self.assertEqual(record["growth_forecast_pct"], 500.0)
        self.assertEqual(record["concentration_risk"], 0.0)
        self.assertEqual(record["cyclicality_risk"], 1.0)
        self.assertEqual(record["execution_risk"], 0.0)
        self.assertEqual(record["analysis_confidence"], 1.0)
        self.assertEqual(record["analysis_status"], "needs_review")
        self.assertTrue(errors)

    def test_keeps_supported_verified_analysis_unchanged(self):
        url = "https://example.com/source"
        records, errors = cross_validate_records(
            [
                {
                    "company": "Verified Co",
                    "moat_score": 4,
                    "growth_forecast_pct": 40.0,
                    "concentration_risk": 0.2,
                    "cyclicality_risk": 0.3,
                    "execution_risk": 0.4,
                    "analysis_status": "verified",
                    "analysis_confidence": 0.8,
                    "evidence": [{"url": url, "status": "verified"}],
                    "moat_evidence_ids": [url],
                }
            ]
        )

        self.assertEqual(records[0]["analysis_status"], "verified")
        self.assertEqual(errors, [])


class TestWorkflow(unittest.TestCase):
    def test_builds_a_compiled_graph(self):
        self.assertIsNotNone(build_workflow())

    @patch("workflow.enrich_records", side_effect=lambda records: records)
    @patch("workflow.ingest_companies")
    def test_runs_full_pipeline_and_returns_dashboard_outputs(self, ingest, _enrich):
        ingest.return_value = [
            {
                "company": "Example Co",
                "role": "Compute/Server",
                "operating_margin_pct": 35.0,
                "moat_score": 4,
                "growth_forecast_pct": 30.0,
                "concentration_risk": 0.2,
                "cyclicality_risk": 0.2,
                "execution_risk": 0.2,
                "eff_score": 3,
                "evidence": [],
            }
        ]
        state = run_workflow(risk_discount=10, power_weight=1.2, ranking_priority="TAFGS Score", role_filter=[])

        self.assertEqual(len(state["ingestion_rows"]), 1)
        self.assertEqual(len(state["ranked_rows"]), 1)
        self.assertIn("Risk Discount of 10%", state["agent_summary"])
        self.assertIn("validation_errors", state)


if __name__ == "__main__":
    unittest.main()
