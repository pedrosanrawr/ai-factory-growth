"""Tests for the evidence/status UI added to the company-profile popup.

Covers rendering for each analysis_status the schema allows (verified,
needs_review, fallback, unavailable) plus the evidence list itself, per
the module TODOs in scripts/refresh_research.py.
"""
import unittest

from frontend.components import render_company_profile, research_status_badge


def _base_row(**overrides) -> dict:
    row = {
        "company": "Acme Corp (ACME)",
        "role": "Compute/Server",
        "short_description": "Example company.",
        "revenue_exposure_pct": 42.0,
        "segment_weight": 0.4,
        "tafgs": 3.21,
        "moat_notes": "Strong moat.",
        "growth_catalysts": "Backlog growth.",
        "risk_notes": "Customer concentration.",
        "source_links": "https://example.com/filing",
        "research_as_of": "2026-09-01",
        "analysis_status": "unavailable",
        "analysis_confidence": None,
        "evidence": [],
    }
    row.update(overrides)
    return row


def _evidence_item(status: str) -> dict:
    return {
        "url": "https://www.sec.gov/Archives/edgar/data/1/a.htm",
        "title": "Acme Corp - 10-K",
        "retrieved_date": "2026-09-01",
        "published_date": "2026-06-01",
        "excerpt": "New hyperscaler agreement disclosed.",
        "claim": "Acme signed a new hyperscaler supply agreement.",
        "source_type": "10-K",
        "status": status,
    }


class ResearchStatusBadgeTests(unittest.TestCase):
    def test_verified_badge_shows_confidence_when_available(self):
        html = research_status_badge("verified", 0.87)
        self.assertIn("Verified", html)
        self.assertIn("87%", html)
        self.assertIn("status-verified", html)

    def test_needs_review_badge(self):
        html = research_status_badge("needs_review")
        self.assertIn("Needs Review", html)
        self.assertIn("status-needs-review", html)

    def test_fallback_badge(self):
        html = research_status_badge("fallback")
        self.assertIn("Fallback (Unverified)", html)
        self.assertIn("status-fallback", html)

    def test_unknown_status_falls_back_to_understandable_label(self):
        html = research_status_badge("some_unexpected_value")
        self.assertIn("Research Unavailable", html)
        self.assertIn("status-unavailable", html)

    def test_blank_status_falls_back_to_understandable_label(self):
        html = research_status_badge("")
        self.assertIn("Research Unavailable", html)


class CompanyProfilePopupTests(unittest.TestCase):
    def test_verified_state_renders_evidence_and_badge(self):
        row = _base_row(analysis_status="verified", analysis_confidence=0.9, evidence=[_evidence_item("verified")])
        html = render_company_profile(row, 1)

        self.assertIn("status-verified", html)
        self.assertIn("Verified", html)
        self.assertIn("Acme Corp - 10-K", html)
        self.assertIn("evidence-link", html)
        self.assertIn("Evidence &amp; Refresh Status", html)

    def test_needs_review_state_renders_review_badge(self):
        row = _base_row(analysis_status="needs_review", evidence=[_evidence_item("needs_review")])
        html = render_company_profile(row, 1)

        self.assertIn("Needs Review", html)
        self.assertIn("status-needs-review", html)

    def test_fallback_state_renders_fallback_label(self):
        row = _base_row(analysis_status="fallback", evidence=[])
        html = render_company_profile(row, 1)

        self.assertIn("Fallback (Unverified)", html)
        self.assertIn("No evidence on file yet", html)

    def test_unavailable_state_with_no_evidence_shows_review_fallback_copy(self):
        row = _base_row(analysis_status="unavailable", evidence=[])
        html = render_company_profile(row, 1)

        self.assertIn("Research Unavailable", html)
        self.assertIn("pending its next research review", html)

    def test_missing_research_as_of_shows_understandable_placeholder(self):
        row = _base_row(research_as_of="")
        html = render_company_profile(row, 1)
        self.assertIn("Not yet researched", html)

    def test_evidence_items_are_html_escaped(self):
        malicious = _evidence_item("needs_review")
        malicious["title"] = '<script>alert(1)</script>'
        row = _base_row(analysis_status="needs_review", evidence=[malicious])
        html = render_company_profile(row, 1)

        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_existing_legacy_fields_still_render(self):
        """Preserve the pre-existing profile fields alongside the new ones."""
        row = _base_row()
        html = render_company_profile(row, 2)

        self.assertIn("#2", html)
        self.assertIn("Strong moat.", html)
        self.assertIn("Backlog growth.", html)
        self.assertIn("Customer concentration.", html)
        self.assertIn("example.com", html)


if __name__ == "__main__":
    unittest.main()
