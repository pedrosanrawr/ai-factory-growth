import unittest

from agents.moat_analysis import run
from schema import empty_record


class TestMoatAnalysis(unittest.TestCase):
    def test_keeps_valid_scores_and_returns_same_list(self) -> None:
        records = [{"moat_score": 0}, {"moat_score": "3"}, {"moat_score": 5}]

        result = run(records)

        self.assertIs(result, records)
        self.assertEqual([record["moat_score"] for record in result], [0, 3, 5])

    def test_clamps_out_of_range_and_invalid_scores(self) -> None:
        records = [
            {"moat_score": -2},
            {"moat_score": 9},
            {"moat_score": "N/A"},
            empty_record(),
        ]

        result = run(records)

        self.assertEqual([record["moat_score"] for record in result], [0, 5, 0, 0])

    def test_does_not_change_unrelated_fields(self) -> None:
        record = {"company": "Example Corp", "role": "Networking", "moat_score": 4}

        run([record])

        self.assertEqual(record["company"], "Example Corp")
        self.assertEqual(record["role"], "Networking")


if __name__ == "__main__":
    unittest.main()
