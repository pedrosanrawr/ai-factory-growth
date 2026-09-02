"""Tests for scripts/refresh_research.py.

Covers: dry run (no disk writes), no-change refresh, proposed-change
report staging, report JSON serialization, and the approved-write path
(backup + CSV/evidence-store update), per the module TODOs.

No live network calls: services.research_sources.fetch_company_research
is monkeypatched everywhere.
"""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.evidence_store import EvidenceStore
from scripts import refresh_research as rr

CSV_HEADER = "Company Name + Ticker,Primary AI Factory Role,Source Links\r\n"


def _write_csv(path: str, rows: list[tuple[str, str, str]]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(CSV_HEADER)
        for company, role, links in rows:
            f.write(f'"{company}",{role},"{links}"\r\n')


def _sample_document(url="https://www.sec.gov/Archives/edgar/data/1/a.htm", title="Acme Corp - 10-K"):
    return {
        "title": title,
        "url": url,
        "source_type": "sec_filing",
        "publication_date": "2026-06-01",
        "retrieved_at": "2026-09-01T00:00:00+00:00",
        "supporting_text": "Acme disclosed a new hyperscaler supply agreement.",
    }


class RefreshResearchTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.csv_path = os.path.join(self.tmpdir, "companies.csv")
        self.evidence_path = os.path.join(self.tmpdir, "evidence_store.json")
        self.report_path = os.path.join(self.tmpdir, "report.json")
        self.backup_dir = os.path.join(self.tmpdir, "backups")
        _write_csv(self.csv_path, [("Acme Corp (ACME)", "Compute/Server", "")])

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)


class DryRunTests(RefreshResearchTestCase):
    def test_dry_run_writes_nothing_to_disk(self):
        with patch.object(rr.research_sources, "fetch_company_research", return_value=[_sample_document()]):
            exit_code = rr.main(
                [
                    "--input-csv",
                    self.csv_path,
                    "--evidence-store",
                    self.evidence_path,
                    "--dry-run",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertFalse(os.path.exists(self.evidence_path))
        # CSV must be untouched.
        with open(self.csv_path, "rb") as f:
            self.assertEqual(
                f.read(),
                (CSV_HEADER + '"Acme Corp (ACME)",Compute/Server,""\r\n').encode("utf-8"),
            )
        # No report files should appear anywhere under tmpdir either.
        self.assertEqual(list(Path(self.tmpdir).rglob("*.json")), [])


class NoChangeTests(RefreshResearchTestCase):
    def test_no_new_documents_marks_unavailable(self):
        """A company with no existing evidence and no fetched documents is
        'unavailable', not falsely reported as having a change."""
        with patch.object(rr.research_sources, "fetch_company_research", return_value=[]):
            store = EvidenceStore(path=self.evidence_path)
            report = rr.build_change_report(["Acme Corp (ACME)"], store)

        self.assertEqual(report["summary"]["companies_with_new_evidence"], 0)
        self.assertEqual(report["companies"][0]["analysis_status"], "unavailable")
        self.assertEqual(report["companies"][0]["new_evidence_count"], 0)

    def test_already_known_document_is_no_change(self):
        """Fetching a document that's already stored for this company
        produces zero *new* evidence and a 'no_change' status."""
        document = _sample_document()
        store = EvidenceStore(path=self.evidence_path)
        kwargs = rr._document_to_evidence_kwargs("Acme Corp (ACME)", document, "2026-09-01")
        from services.evidence_store import make_evidence_item

        store.put("Acme Corp (ACME)", [make_evidence_item(**kwargs)])

        with patch.object(rr.research_sources, "fetch_company_research", return_value=[document]):
            report = rr.build_change_report(["Acme Corp (ACME)"], store)

        result = report["companies"][0]
        self.assertEqual(result["new_evidence_count"], 0)
        self.assertEqual(result["analysis_status"], "no_change")
        self.assertEqual(result["existing_evidence_count"], 1)


class ProposedChangeReportTests(RefreshResearchTestCase):
    def test_new_document_is_staged_as_needs_review(self):
        with patch.object(rr.research_sources, "fetch_company_research", return_value=[_sample_document()]):
            store = EvidenceStore(path=self.evidence_path)
            report = rr.build_change_report(["Acme Corp (ACME)"], store)

        result = report["companies"][0]
        self.assertEqual(result["new_evidence_count"], 1)
        self.assertEqual(result["analysis_status"], "needs_review")
        self.assertEqual(result["candidate_evidence"][0]["status"], "needs_review")
        self.assertIn("sec.gov", result["candidate_evidence"][0]["url"])
        # Staging never touches the evidence store.
        self.assertEqual(EvidenceStore(path=self.evidence_path).get("Acme Corp (ACME)"), [])

    def test_document_missing_url_is_skipped_not_fabricated(self):
        broken_document = _sample_document(url="")
        with patch.object(rr.research_sources, "fetch_company_research", return_value=[broken_document]):
            store = EvidenceStore(path=self.evidence_path)
            report = rr.build_change_report(["Acme Corp (ACME)"], store)

        self.assertEqual(report["companies"][0]["new_evidence_count"], 0)

    def test_staging_writes_report_file_but_not_canonical_files(self):
        with patch.object(rr.research_sources, "fetch_company_research", return_value=[_sample_document()]):
            exit_code = rr.main(
                [
                    "--input-csv",
                    self.csv_path,
                    "--evidence-store",
                    self.evidence_path,
                    "--output-report",
                    self.report_path,
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertTrue(os.path.exists(self.report_path))
        self.assertFalse(os.path.exists(self.evidence_path))
        with open(self.csv_path, "r", encoding="utf-8") as f:
            self.assertNotIn("sec.gov", f.read())


class ReportSerializationTests(RefreshResearchTestCase):
    def test_report_round_trips_through_json(self):
        with patch.object(rr.research_sources, "fetch_company_research", return_value=[_sample_document()]):
            store = EvidenceStore(path=self.evidence_path)
            report = rr.build_change_report(["Acme Corp (ACME)"], store)

        rr.write_report(report, self.report_path)
        reloaded = json.loads(Path(self.report_path).read_text())

        self.assertEqual(reloaded["research_as_of"], report["research_as_of"])
        self.assertEqual(len(reloaded["companies"]), 1)
        self.assertIn("generated_at", reloaded)
        self.assertIn("summary", reloaded)
        self.assertEqual(
            reloaded["companies"][0]["candidate_evidence"][0]["url"],
            report["companies"][0]["candidate_evidence"][0]["url"],
        )


class ApprovedWriteTests(RefreshResearchTestCase):
    def test_approve_write_requires_a_staged_report(self):
        with self.assertRaises(SystemExit):
            rr.main(["--approve-write"])

    def test_approve_write_updates_csv_and_evidence_store_with_backup(self):
        with patch.object(rr.research_sources, "fetch_company_research", return_value=[_sample_document()]):
            store = EvidenceStore(path=self.evidence_path)
            report = rr.build_change_report(["Acme Corp (ACME)"], store)
        rr.write_report(report, self.report_path)

        result = rr.apply_approved_write(
            report,
            input_csv=self.csv_path,
            evidence_store_path=self.evidence_path,
            backup_dir=self.backup_dir,
        )

        # Backups: CSV existed so it's backed up; evidence store did not
        # exist yet, so there's nothing to back up.
        self.assertIsNotNone(result["csv_backup"])
        self.assertTrue(os.path.exists(result["csv_backup"]))
        self.assertIsNone(result["evidence_store_backup"])

        # Evidence store now has the merged, still-needs_review item.
        merged = EvidenceStore(path=self.evidence_path).get("Acme Corp (ACME)")
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["status"], "needs_review")

        # CSV's Source Links column was updated for the matching row only.
        with open(self.csv_path, "r", encoding="utf-8") as f:
            csv_text = f.read()
        self.assertIn("sec.gov", csv_text)
        self.assertIn("Acme Corp (ACME)", csv_text)

    def test_approve_write_backs_up_existing_evidence_store(self):
        EvidenceStore(path=self.evidence_path).put("Acme Corp (ACME)", [])
        with patch.object(rr.research_sources, "fetch_company_research", return_value=[_sample_document()]):
            store = EvidenceStore(path=self.evidence_path)
            report = rr.build_change_report(["Acme Corp (ACME)"], store)

        result = rr.apply_approved_write(
            report,
            input_csv=self.csv_path,
            evidence_store_path=self.evidence_path,
            backup_dir=self.backup_dir,
        )
        self.assertIsNotNone(result["evidence_store_backup"])
        self.assertTrue(os.path.exists(result["evidence_store_backup"]))

    def test_approve_write_never_marks_evidence_verified(self):
        with patch.object(rr.research_sources, "fetch_company_research", return_value=[_sample_document()]):
            store = EvidenceStore(path=self.evidence_path)
            report = rr.build_change_report(["Acme Corp (ACME)"], store)

        rr.apply_approved_write(
            report,
            input_csv=self.csv_path,
            evidence_store_path=self.evidence_path,
            backup_dir=self.backup_dir,
        )
        merged = EvidenceStore(path=self.evidence_path).get("Acme Corp (ACME)")
        self.assertTrue(all(item["status"] != "verified" for item in merged))


if __name__ == "__main__":
    unittest.main()
