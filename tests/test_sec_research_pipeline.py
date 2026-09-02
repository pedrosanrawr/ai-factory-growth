"""Offline contract tests for SEC-only discovery and enrichment."""

import unittest
from unittest.mock import patch

from services.research_enrichment import enrich_records
from services.research_sources import _latest_annual_value, discover_ai_factory_companies


class FakeEdgarSource:
    def __init__(self, **_kwargs):
        pass

    def search(self, _query, start_date=None):
        return [
            {
                "company": "Example Compute",
                "cik": "0000123456",
                "url": "https://www.sec.gov/Archives/example.htm",
                "title": "Example Compute - 10-K",
                "source_type": "sec_filing",
                "publication_date": "2026-01-01",
                "retrieved_at": "2026-09-02T00:00:00+00:00",
                "supporting_text": "AI data center demand.",
            }
        ]


class TestSecDiscovery(unittest.TestCase):
    @patch("services.research_sources.EdgarFullTextSearchSource", FakeEdgarSource)
    def test_deduplicates_discovered_companies_across_roles(self):
        candidates = discover_ai_factory_companies(
            max_results_per_role=2,
            listing_lookup=lambda _cik: {"tickers": [], "exchanges": []},
        )

        self.assertEqual(len(candidates), 0)

    @patch("services.research_sources.EdgarFullTextSearchSource", FakeEdgarSource)
    def test_keeps_only_currently_listed_sec_companies(self):
        candidates = discover_ai_factory_companies(
            max_results_per_role=2,
            listing_lookup=lambda _cik: {"tickers": ["EXM"], "exchanges": ["Nasdaq"]},
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["company"], "Example Compute")
        self.assertEqual(candidates[0]["cik"], "0000123456")
        self.assertEqual(candidates[0]["ticker"], "EXM")
        self.assertEqual(len(candidates[0]["discovery_documents"]), 5)

    def test_selects_the_latest_annual_fact(self):
        value, filed = _latest_annual_value(
            {
                "OperatingIncomeLoss": {
                    "units": {
                        "USD": [
                            {"form": "10-Q", "fy": 2025, "filed": "2025-05-01", "val": 10},
                            {"form": "10-K", "fy": 2024, "filed": "2025-02-01", "val": 100},
                            {"form": "10-K", "fy": 2025, "filed": "2026-02-01", "val": 150},
                        ]
                    }
                }
            },
            ("OperatingIncomeLoss",),
        )
        self.assertEqual(value, 150.0)
        self.assertEqual(filed, "2026-02-01")


class TestSecResearchEnrichment(unittest.TestCase):
    @patch("services.research_enrichment.fetch_company_research", return_value=[])
    @patch("services.research_enrichment.store_evidence")
    @patch("services.research_enrichment.fetch_company_facts")
    def test_adds_company_facts_as_reviewable_evidence(self, facts, store_evidence, _research):
        facts.return_value = {
            "operating_margin_pct": 31.5,
            "publication_date": "2026-02-01",
            "retrieved_at": "2026-09-02T00:00:00+00:00",
            "url": "https://data.sec.gov/api/xbrl/companyfacts/CIK0000123456.json",
            "title": "SEC Company Facts: CIK 0000123456",
            "source_type": "other",
            "supporting_text": "SEC XBRL annual operating income and revenue facts.",
        }
        store_evidence.side_effect = lambda _company, evidence: evidence
        record = {
            "company": "Example Compute",
            "cik": "0000123456",
            "operating_margin_pct": 0.0,
            "evidence": [],
        }

        enriched = enrich_records([record])[0]

        self.assertEqual(enriched["operating_margin_pct"], 31.5)
        self.assertEqual(enriched["analysis_status"], "needs_review")
        self.assertEqual(enriched["evidence"][0]["status"], "needs_review")
        self.assertIn("data.sec.gov", enriched["evidence"][0]["url"])


if __name__ == "__main__":
    unittest.main()
