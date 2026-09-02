import unittest
from unittest.mock import patch

from frontend.components import render_ranking_table
from frontend.page import run_pipeline


class TestFrontendPipeline(unittest.TestCase):
    @patch("frontend.page.run_workflow")
    def test_renders_provider_backed_workflow_output(self, run_workflow) -> None:
        row = {
            "company": "Example Compute (EXM.US)",
            "role": "Compute/Server",
            "segment_weight": 0.4,
            "revenue_exposure_pct": 0.0,
            "moat": 4,
            "margin_pct": 31.5,
            "growth_pct": 20.0,
            "eff_score": 3,
            "primary_risk": "Execution",
            "status": "Profitable",
            "margin_score": 4,
            "moat_notes": "Evidence-backed analysis pending review.",
            "growth_catalysts": "AI server demand.",
            "risk_notes": "Customer concentration.",
            "source_links": "",
            "tafgs": 2.4,
        }
        run_workflow.return_value = {
            "ingestion_rows": [row],
            "ranked_rows": [row],
            "agent_summary": "Risk Discount of 10% applied.",
        }
        ingestion_rows, ranked_rows, summary = run_pipeline(
            risk_discount=10,
            power_weight=1.2,
            ranking_priority="TAFGS Score",
            role_filter=[],
        )

        self.assertEqual(len(ingestion_rows), 1)
        self.assertEqual(len(ranked_rows), 1)
        self.assertEqual(ranked_rows[0]["company"], "Example Compute (EXM.US)")
        self.assertIn("segment_weight", ranked_rows[0])
        self.assertIn("revenue_exposure_pct", ranked_rows[0])
        self.assertIn("moat_notes", ranked_rows[0])
        self.assertIn("source_links", ranked_rows[0])
        self.assertIn("Risk Discount of 10%", summary)
        table_html = render_ranking_table(ranked_rows, "TAFGS Score", summary)
        self.assertIn("Profile</th>", table_html)
        self.assertIn("profile-view-link", table_html)
        self.assertNotIn("?profile=", table_html)
        self.assertIn('href="#company-profile-0"', table_html)
        self.assertIn("profile-modal-close", table_html)
        self.assertIn("profile-modal-body", table_html)
        self.assertIn('profile-modal-backdrop" aria-hidden="true', table_html)

    @patch("frontend.page.run_workflow")
    def test_controls_are_forwarded_to_the_workflow(self, run_workflow) -> None:
        run_workflow.return_value = {
            "ingestion_rows": [],
            "ranked_rows": [],
            "agent_summary": "summary",
        }
        base_rows, base_ranked, _ = run_pipeline(10, 1.2, "TAFGS Score", [])
        no_discount_rows, _, _ = run_pipeline(0, 1.2, "TAFGS Score", [])
        _, high_power_ranked, _ = run_pipeline(10, 2.0, "TAFGS Score", [])
        _, networking_ranked, _ = run_pipeline(
            10, 1.2, "TAFGS Score", ["Networking"]
        )

        self.assertEqual(base_rows, [])
        self.assertEqual(base_ranked, [])
        self.assertEqual(no_discount_rows, [])
        self.assertEqual(high_power_ranked, [])
        self.assertEqual(networking_ranked, [])
        self.assertEqual(
            run_workflow.call_args_list[-1].kwargs["role_filter"], ["Networking"]
        )


if __name__ == "__main__":
    unittest.main()
