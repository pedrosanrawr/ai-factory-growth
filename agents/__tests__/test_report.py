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


if __name__ == "__main__":
    unittest.main()
