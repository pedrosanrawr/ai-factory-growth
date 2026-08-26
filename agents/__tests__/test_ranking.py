import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.ranking import _clamp, run


def _make_records(n):
    return [
        {
            "company": f"Co{i}",
            "moat_score": (i % 5),
            "margin_score": (i % 5) + 1,
            "adjusted_growth_pct": float(i),
            "eff_score": (i % 5) + 1,
            "operating_margin_pct": 1.0,
        }
        for i in range(n)
    ]


class TestWorkedExamples(unittest.TestCase):
    def test_nvidia(self):
        record = {
            "company": "NVDA",
            "moat_score": 5,
            "margin_score": 5,
            "adjusted_growth_pct": 42.57,
            "eff_score": 5,
            "operating_margin_pct": 55.0,
        }
        result = run([record])[0]
        self.assertAlmostEqual(result["tafgs_score"], 12.771, delta=0.001)
        self.assertEqual(result["status"], "Profitable")
        self.assertEqual(result["rank"], 1)

    def test_broadcom(self):
        record = {
            "company": "AVGO",
            "moat_score": 5,
            "margin_score": 5,
            "adjusted_growth_pct": 32.20,
            "eff_score": 4,
            "operating_margin_pct": 40.0,
        }
        result = run([record])[0]
        self.assertAlmostEqual(result["tafgs_score"], 9.258, delta=0.001)

    def test_fluor(self):
        record = {
            "company": "FLR",
            "moat_score": 3,
            "margin_score": 1,
            "adjusted_growth_pct": 12.15,
            "eff_score": 1,
            "operating_margin_pct": 2.5,
        }
        result = run([record])[0]
        self.assertAlmostEqual(result["tafgs_score"], 0.365, delta=0.001)

    def test_weight_1_0_removes_boost_entirely(self):
        nvda = {
            "company": "NVDA",
            "moat_score": 5,
            "margin_score": 5,
            "adjusted_growth_pct": 42.57,
            "eff_score": 5,
            "operating_margin_pct": 55.0,
        }
        fluor = {
            "company": "FLR",
            "moat_score": 3,
            "margin_score": 1,
            "adjusted_growth_pct": 12.15,
            "eff_score": 1,
            "operating_margin_pct": 2.5,
        }
        results = run([nvda, fluor], power_efficiency_weight=1.0)
        by_company = {r["company"]: r for r in results}
        self.assertAlmostEqual(by_company["NVDA"]["tafgs_score"], 10.643, delta=0.001)
        self.assertAlmostEqual(by_company["FLR"]["tafgs_score"], 0.365, delta=0.001)

    def test_weight_2_0_gives_max_boost_at_eff_score_5(self):
        record = {
            "company": "NVDA",
            "moat_score": 5,
            "margin_score": 5,
            "adjusted_growth_pct": 42.57,
            "eff_score": 5,
            "operating_margin_pct": 55.0,
        }
        result = run([record], power_efficiency_weight=2.0)[0]
        # base_tafgs 10.6425 * efficiency_factor 2.0
        self.assertAlmostEqual(result["tafgs_score"], 21.285, delta=0.001)

    def test_weight_2_0_gives_no_boost_at_eff_score_1(self):
        record = {
            "company": "FLR",
            "moat_score": 3,
            "margin_score": 1,
            "adjusted_growth_pct": 12.15,
            "eff_score": 1,
            "operating_margin_pct": 2.5,
        }
        result = run([record], power_efficiency_weight=2.0)[0]
        self.assertAlmostEqual(result["tafgs_score"], 0.365, delta=0.001)


# ---------------------------------------------------------------------------
# Status field
# ---------------------------------------------------------------------------


class TestStatusField(unittest.TestCase):
    def test_profitable_when_margin_positive(self):
        record = {
            "company": "A",
            "moat_score": 3,
            "margin_score": 3,
            "adjusted_growth_pct": 10,
            "eff_score": 3,
            "operating_margin_pct": 5.0,
        }
        result = run([record])[0]
        self.assertEqual(result["status"], "Profitable")

    def test_unprofitable_when_margin_zero_or_negative(self):
        zero_margin = {
            "company": "A",
            "moat_score": 3,
            "margin_score": 3,
            "adjusted_growth_pct": 10,
            "eff_score": 3,
            "operating_margin_pct": 0.0,
        }
        negative_margin = {
            "company": "B",
            "moat_score": 3,
            "margin_score": 3,
            "adjusted_growth_pct": 10,
            "eff_score": 3,
            "operating_margin_pct": -4.0,
        }
        results = run([zero_margin, negative_margin], ranking_priority="TAFGS Score")
        by_company = {r["company"]: r for r in results}
        self.assertEqual(by_company["A"]["status"], "Unprofitable")
        self.assertEqual(by_company["B"]["status"], "Unprofitable")


# ---------------------------------------------------------------------------
# Sorting options
# ---------------------------------------------------------------------------


class TestSorting(unittest.TestCase):
    def setUp(self):
        self.mixed_companies = [
            {
                "company": "HighTafgsLoss",
                "moat_score": 5,
                "margin_score": 5,
                "adjusted_growth_pct": 45.0,
                "eff_score": 5,
                "operating_margin_pct": -2.0,
            },
            {
                "company": "LowTafgsProfit",
                "moat_score": 2,
                "margin_score": 2,
                "adjusted_growth_pct": 10.0,
                "eff_score": 2,
                "operating_margin_pct": 3.0,
            },
            {
                "company": "HighGrowthLowScore",
                "moat_score": 1,
                "margin_score": 1,
                "adjusted_growth_pct": 48.0,
                "eff_score": 1,
                "operating_margin_pct": 1.0,
            },
            {
                "company": "MidAllAround",
                "moat_score": 3,
                "margin_score": 3,
                "adjusted_growth_pct": 20.0,
                "eff_score": 3,
                "operating_margin_pct": 6.0,
            },
        ]

    def test_sort_by_tafgs_score_default(self):
        results = run(self.mixed_companies, ranking_priority="TAFGS Score")
        scores = [r["tafgs_score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_sort_by_growth_pct_highest(self):
        results = run(self.mixed_companies, ranking_priority="Growth % (Highest)")
        growths = [r["adjusted_growth_pct"] for r in results]
        self.assertEqual(growths, sorted(growths, reverse=True))
        self.assertEqual(
            results[0]["company"], "HighGrowthLowScore"
        )  # 48.0% is the highest

    def test_sort_by_profitability_first(self):
        results = run(self.mixed_companies, ranking_priority="Profitability First")
        statuses = [r["status"] for r in results]
        # All "Profitable" entries must come before any "Unprofitable" entry
        first_unprofitable = (
            statuses.index("Unprofitable")
            if "Unprofitable" in statuses
            else len(statuses)
        )
        self.assertTrue(all(s == "Profitable" for s in statuses[:first_unprofitable]))
        self.assertNotEqual(
            results[0]["company"], "HighTafgsLoss"
        )  # unprofitable, despite highest tafgs

    def test_unrecognized_ranking_priority_falls_back_to_tafgs_score(self):
        results = run(self.mixed_companies, ranking_priority="Some Typo")
        scores = [r["tafgs_score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))


# ---------------------------------------------------------------------------
# Top-20 slicing and rank assignment
# ---------------------------------------------------------------------------


class TestTopTwentyAndRanks(unittest.TestCase):
    def test_returns_at_most_20_records(self):
        results = run(_make_records(25))
        self.assertEqual(len(results), 20)

    def test_returns_fewer_than_20_when_input_is_smaller(self):
        results = run(_make_records(5))
        self.assertEqual(len(results), 5)

    def test_ranks_are_sequential_starting_at_1(self):
        results = run(_make_records(25))
        self.assertEqual([r["rank"] for r in results], list(range(1, 21)))

    def test_top_20_are_the_actual_highest_scores(self):
        records = _make_records(25)
        results = run(records)  # default power_efficiency_weight=1.2

        # Recompute tafgs_score independently, including the efficiency
        # boost (run()'s default weight is 1.2, not 1.0), and check the
        # returned set matches the 20 highest, not just any 20.
        def independent_tafgs(r):
            base = (
                r["moat_score"] * r["margin_score"] * (r["adjusted_growth_pct"] / 100)
            )
            eff = _clamp(r["eff_score"], 1, 5)
            factor = 1 + ((eff - 1) / 4) * (_clamp(1.2, 1.0, 2.0) - 1)
            return base * factor

        independent_scores = sorted(
            (independent_tafgs(r) for r in records), reverse=True
        )[:20]
        returned_scores = sorted((r["tafgs_score"] for r in results), reverse=True)
        for expected, actual in zip(independent_scores, returned_scores):
            self.assertAlmostEqual(actual, expected, delta=0.01)


# ---------------------------------------------------------------------------
# Robustness / non-mutation
# ---------------------------------------------------------------------------


class TestRobustness(unittest.TestCase):
    def test_run_does_not_mutate_input(self):
        records = _make_records(5)
        original_copy = [dict(r) for r in records]
        run(records)
        self.assertEqual(records, original_copy)

    def test_missing_fields_default_gracefully_without_crashing(self):
        record = {"company": "Incomplete Co"}  # everything else missing
        result = run([record])[0]
        self.assertEqual(result["tafgs_score"], 0.0)
        self.assertEqual(result["status"], "Unprofitable")
        self.assertEqual(result["rank"], 1)


# ---------------------------------------------------------------------------
# _clamp
# ---------------------------------------------------------------------------


class TestClamp(unittest.TestCase):
    def test_within_range_returns_value_unchanged(self):
        self.assertEqual(_clamp(3, 1, 5), 3.0)

    def test_caps_above_range(self):
        self.assertEqual(_clamp(9, 1, 5), 5.0)

    def test_floors_below_range(self):
        self.assertEqual(_clamp(-3, 1, 5), 1.0)

    def test_handles_non_numeric_input(self):
        self.assertEqual(_clamp("not a number", 1, 5), 1)
        self.assertEqual(_clamp(None, 1, 5), 1)


if __name__ == "__main__":
    unittest.main()
