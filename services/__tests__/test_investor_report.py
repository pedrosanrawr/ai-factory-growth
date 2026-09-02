import unittest

from services.investor_report import build_investor_report_pdf


class TestInvestorReport(unittest.TestCase):
    def test_generates_a_pdf_from_ranked_rows(self) -> None:
        pdf = build_investor_report_pdf(
            [{"rank": 1, "company": "Example Corp (EXM)", "role": "Networking", "moat": 4, "margin_pct": 31.5, "growth_pct": 20.0, "tafgs": 2.4, "primary_risk": "Execution", "short_description": "Example profile.", "moat_notes": "Strong switching costs.", "growth_catalysts": "AI demand.", "risk_notes": "Customer concentration.", "source_links": "https://example.com"}],
            ranking_priority="TAFGS Score",
            agent_summary="Risk Discount of 10% applied.",
        )
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 1000)


if __name__ == "__main__":
    unittest.main()
