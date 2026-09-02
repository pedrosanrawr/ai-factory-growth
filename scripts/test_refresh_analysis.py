import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import refresh_analysis
from services.research_snapshot import load_snapshot


class TestRefreshAnalysis(unittest.TestCase):
    @patch("scripts.refresh_analysis.analyze_research")
    @patch("scripts.refresh_analysis.ingest_companies")
    @patch("scripts.refresh_analysis.is_llm_configured", return_value=True)
    def test_publishes_only_offline_analysis_results(self, _configured, ingest, analyze) -> None:
        record = {
            "company": "Example Corp (EXM)",
            "evidence": [{"url": "https://example.com/source", "claim": "Example claim.", "published_date": "2026-09-01"}],
            "moat_score": 4,
            "growth_forecast_pct": 25.0,
            "analysis_status": "needs_review",
            "_combined_llm_analysis": True,
        }
        ingest.return_value = [record]
        analyze.return_value = [record]

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "latest.json"
            self.assertEqual(refresh_analysis.main(["--output", str(output)]), 0)
            snapshot = load_snapshot(output)

        self.assertEqual(snapshot["Example Corp (EXM)"]["moat_score"], 4)

    @patch("scripts.refresh_analysis.is_llm_configured", return_value=False)
    def test_leaves_existing_snapshot_when_gemini_is_not_configured(self, _configured) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "latest.json"
            output.write_text('{"records": {"Existing": {}}}', encoding="utf-8")
            self.assertEqual(refresh_analysis.main(["--output", str(output)]), 0)
            self.assertIn("Existing", load_snapshot(output))


if __name__ == "__main__":
    unittest.main()
