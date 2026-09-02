import unittest

from agents.report import run
from schema import empty_record


def make_record() -> dict:
    record = empty_record()
    record.update(
        {
            "company": "Example Corp (EXM)",
            "role": "Networking",
            "moat_score": 4,
            "operating_margin_pct": 25.5,
            "adjusted_growth_pct": 18.2,
            "eff_score": 4,
            "margin_score": 4,
            "tafgs_score": 2.912,
            "status": "Profitable",
            "moat_notes": "Strong ecosystem.",
            "growth_catalysts": "New data-center demand.",
            "risk_notes": "Customer concentration.",
        }
    )
    return record


class TestReport(unittest.TestCase):
    def test_builds_profile_and_sets_highest_risk(self) -> None:
        record = make_record()
        record.update(
            {
                "concentration_risk": 0.4,
                "cyclicality_risk": 0.8,
                "execution_risk": 0.5,
            }
        )

        profiles, summary = run(
            [record], risk_discount_pct=15, power_efficiency_weight=1.5
        )

        self.assertEqual(record["primary_risk"], "Cyclicality")
        self.assertEqual(profiles[0]["company"], "Example Corp (EXM)")
        self.assertEqual(profiles[0]["growth_pct"], 18.2)
        self.assertEqual(profiles[0]["primary_risk"], "Cyclicality")
        self.assertEqual(profiles[0]["tafgs"], 2.912)
        self.assertEqual(
            summary,
            "Risk Discount of 15% and Power Efficiency Weight of 1.5x "
            "applied globally across scores.",
        )

    def test_uses_concentration_for_tied_or_missing_risks(self) -> None:
        tied_record = make_record()
        tied_record.update(
            {
                "concentration_risk": 0.5,
                "cyclicality_risk": 0.5,
                "execution_risk": 0.2,
            }
        )
        missing_record = make_record()

        profiles, _ = run([tied_record, missing_record])

        self.assertEqual(profiles[0]["primary_risk"], "Concentration")
        self.assertEqual(profiles[1]["primary_risk"], "Concentration")


class TestReportEvidenceFields(unittest.TestCase):
    """Research-refresh fields must be additive: every pre-existing key
    stays present and unchanged, and the new keys pass through as-is."""

    def test_default_record_gets_unavailable_evidence_fields(self) -> None:
        record = make_record()
        profiles, _ = run([record])

        profile = profiles[0]
        # Pre-existing keys untouched.
        for key in (
            "company", "role", "short_description", "revenue_exposure_pct",
            "segment_weight", "moat", "margin_pct", "growth_pct", "eff_score",
            "primary_risk", "status", "margin_score", "tafgs", "moat_notes",
            "growth_catalysts", "risk_notes", "source_links",
        ):
            self.assertIn(key, profile)

        # New keys default sensibly for a record that hasn't been researched.
        self.assertEqual(profile["research_as_of"], "")
        self.assertEqual(profile["analysis_status"], "unavailable")
        self.assertIsNone(profile["analysis_confidence"])
        self.assertEqual(profile["evidence"], [])

    def test_verified_record_passes_through_evidence_and_confidence(self) -> None:
        record = make_record()
        evidence_item = {
            "url": "https://www.sec.gov/Archives/edgar/data/1/a.htm",
            "title": "Example Corp - 10-K",
            "retrieved_date": "2026-09-01",
            "status": "verified",
        }
        record.update(
            {
                "research_as_of": "2026-09-01",
                "analysis_status": "verified",
                "analysis_confidence": 0.92,
                "evidence": [evidence_item],
            }
        )

        profiles, _ = run([record])
        profile = profiles[0]

        self.assertEqual(profile["research_as_of"], "2026-09-01")
        self.assertEqual(profile["analysis_status"], "verified")
        self.assertEqual(profile["analysis_confidence"], 0.92)
        self.assertEqual(profile["evidence"], [evidence_item])

    def test_needs_review_status_passes_through_without_confidence(self) -> None:
        record = make_record()
        record.update({"analysis_status": "needs_review", "analysis_confidence": None})

        profiles, _ = run([record])

        self.assertEqual(profiles[0]["analysis_status"], "needs_review")
        self.assertIsNone(profiles[0]["analysis_confidence"])


if __name__ == "__main__":
    unittest.main()
