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
        self.assertIn("New Source", html)
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
        self.assertIn("evidence-pill", html)
        self.assertIn("Research Evidence", html)

    def test_needs_review_state_renders_review_badge(self):
        row = _base_row(analysis_status="needs_review", evidence=[_evidence_item("needs_review")])
        html = render_company_profile(row, 1)

        self.assertIn("New Source", html)
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

    def test_missing_research_as_of_shows_snapshot_placeholder(self):
        row = _base_row(research_as_of="")
        html = render_company_profile(row, 1)
        self.assertIn("Baseline data", html)

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

    def test_cached_analysis_rationales_replace_csv_narratives(self):
        row = _base_row(
            moat_rationale="Cached moat rationale.",
            growth_rationale="Cached growth rationale.",
            risk_rationale="Cached risk rationale.",
        )
        html = render_company_profile(row, 1)

        self.assertIn("Cached moat rationale.", html)
        self.assertIn("Cached growth rationale.", html)
        self.assertIn("Cached risk rationale.", html)
        self.assertNotIn("Strong moat.", html)

    def test_cached_analysis_hides_inline_citation_urls(self):
        row = _base_row(
            moat_rationale="As cited in https://example.com/a and https://example.com/b, its moat is durable.",
            growth_rationale="Growth is supported (Source: https://example.com/c).",
        )
        html = render_company_profile(row, 1)

        self.assertIn("Its moat is durable.", html)
        self.assertIn("Growth is supported.", html)
        self.assertNotIn("https://example.com/a", html)
        self.assertNotIn("https://example.com/c", html)

    def test_splits_accidentally_joined_source_urls(self):
        row = _base_row(source_links="https://www.sec.gov/filing.htm//www.fool.com/article")
        html = render_company_profile(row, 1)

        self.assertIn("sec.gov", html)
        self.assertIn("fool.com", html)

    def test_cached_gemini_analysis_shows_a_profile_badge(self):
        html = render_company_profile(_base_row(_cached_llm_analysis=True), 1)

        self.assertIn("AI Enriched", html)
        self.assertIn("llm-analysis-badge", html)

    def test_shows_source_links_and_compact_evidence_when_evidence_exists(self):
        row = _base_row(evidence=[_evidence_item("needs_review")])
        html = render_company_profile(row, 1)

        self.assertIn("Research Evidence", html)
        self.assertIn("Source Links</span>", html)
        self.assertIn("evidence-pill", html)


if __name__ == "__main__":
    unittest.main()
