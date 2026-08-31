import unittest

from frontend.components import render_ranking_table
from frontend.page import run_pipeline


class TestFrontendPipeline(unittest.TestCase):
    def test_runs_all_agents_against_the_real_csv(self) -> None:
        ingestion_rows, ranked_rows, summary = run_pipeline(
            risk_discount=10,
            power_weight=1.2,
            ranking_priority="TAFGS Score",
            role_filter=[],
        )

        self.assertEqual(len(ingestion_rows), 20)
        self.assertEqual(len(ranked_rows), 20)
        self.assertEqual(ranked_rows[0]["company"], "NVIDIA Corporation (NVDA)")
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
        self.assertIn('profile-modal-backdrop" aria-hidden="true', table_html)

    def test_controls_affect_the_expected_pipeline_stage(self) -> None:
        base_rows, base_ranked, _ = run_pipeline(10, 1.2, "TAFGS Score", [])
        no_discount_rows, _, _ = run_pipeline(0, 1.2, "TAFGS Score", [])
        _, high_power_ranked, _ = run_pipeline(10, 2.0, "TAFGS Score", [])
        _, networking_ranked, _ = run_pipeline(
            10, 1.2, "TAFGS Score", ["Networking"]
        )

        self.assertNotEqual(base_rows[0]["growth_pct"], no_discount_rows[0]["growth_pct"])
        self.assertNotEqual(base_ranked[0]["tafgs"], high_power_ranked[0]["tafgs"])
        self.assertTrue(networking_ranked)
        self.assertTrue(all(row["role"] == "Networking" for row in networking_ranked))


if __name__ == "__main__":
    unittest.main()
