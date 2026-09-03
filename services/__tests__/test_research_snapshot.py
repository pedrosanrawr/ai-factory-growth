import tempfile
import unittest
from pathlib import Path

from services.research_snapshot import apply_snapshot, load_snapshot, snapshot_entry, write_snapshot


def _record() -> dict:
    return {
        "company": "Example Corp (EXM)",
        "evidence": [{"url": "https://example.com/source", "claim": "Example claim.", "published_date": "2026-09-01"}],
        "moat_score": 4,
        "growth_forecast_pct": 25.0,
        "analysis_status": "needs_review",
    }


class TestResearchSnapshot(unittest.TestCase):
    def test_applies_only_when_evidence_matches(self) -> None:
        source = _record()
        target = _record()
        target["moat_score"] = 1
        apply_snapshot(target, {source["company"]: snapshot_entry(source)})
        self.assertEqual(target["moat_score"], 4)
        self.assertTrue(target["_cached_llm_analysis"])

        target["evidence"][0]["url"] = "https://example.com/new-source"
        target["moat_score"] = 1
        apply_snapshot(target, {source["company"]: snapshot_entry(source)})
        self.assertEqual(target["moat_score"], 1)
        self.assertNotIn("_cached_llm_analysis", target)

    def test_round_trips_snapshot_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "latest.json"
            write_snapshot({"Example Corp (EXM)": snapshot_entry(_record())}, path)
            self.assertIn("Example Corp (EXM)", load_snapshot(path))


if __name__ == "__main__":
    unittest.main()
