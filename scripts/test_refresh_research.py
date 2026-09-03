import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import refresh_research as refresh
from services.evidence_store import EvidenceStore


def _document(url: str = "https://www.sec.gov/Archives/edgar/data/1/a.htm") -> dict:
    return {
        "title": "Acme Corp - 10-K",
        "url": url,
        "source_type": "sec_filing",
        "publication_date": "2026-06-01",
        "retrieved_at": "2026-09-01T00:00:00+00:00",
        "supporting_text": "Acme disclosed an AI infrastructure contract.",
    }


class TestRefreshResearch(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        self.csv_path = root / "companies.csv"
        self.store_path = root / "evidence_store.json"
        self.report_path = root / "report.json"
        self.csv_path.write_text(
            "Company Name + Ticker,Primary AI Factory Role,Source Links\n"
            '"Acme Corp (ACME)",Compute/Server,""\n',
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_dry_run_stages_without_writing_files_or_cache(self) -> None:
        with patch.object(refresh.research_sources, "fetch_company_research", return_value=[_document()]) as fetch:
            self.assertEqual(
                refresh.main(["--input-csv", str(self.csv_path), "--evidence-store", str(self.store_path), "--dry-run"]),
                0,
            )

        self.assertFalse(self.store_path.exists())
        self.assertFalse(self.report_path.exists())
        self.assertEqual(fetch.call_args.kwargs["use_cache"], False)

    def test_staged_report_contains_reviewable_candidate(self) -> None:
        with patch.object(refresh.research_sources, "fetch_company_research", return_value=[_document()]):
            report = refresh.build_change_report(["Acme Corp (ACME)"], EvidenceStore(str(self.store_path)))

        company = report["companies"][0]
        self.assertEqual(company["analysis_status"], "needs_review")
        self.assertEqual(company["candidate_evidence"][0]["status"], "needs_review")

    def test_select_batch_uses_one_indexed_csv_order(self) -> None:
        companies = ["One", "Two", "Three", "Four", "Five"]
        self.assertEqual(refresh._select_batch(companies, 2, 2), ["Three", "Four"])

    def test_select_batch_rejects_invalid_values(self) -> None:
        with self.assertRaises(ValueError):
            refresh._select_batch(["One"], 0, 1)

    def test_approved_write_updates_csv_and_evidence_store_after_backup(self) -> None:
        with patch.object(refresh.research_sources, "fetch_company_research", return_value=[_document()]):
            report = refresh.build_change_report(["Acme Corp (ACME)"], EvidenceStore(str(self.store_path)))
        refresh.write_report(report, self.report_path)

        result = refresh.apply_approved_write(
            json.loads(self.report_path.read_text(encoding="utf-8")),
            input_csv=self.csv_path,
            evidence_store_path=self.store_path,
            backup_dir=Path(self.directory.name) / "backups",
        )

        self.assertTrue(Path(result["csv_backup"]).exists())
        self.assertEqual(len(EvidenceStore(str(self.store_path)).get("Acme Corp (ACME)")), 1)
        self.assertIn("sec.gov", self.csv_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
