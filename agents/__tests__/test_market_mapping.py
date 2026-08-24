import unittest

from agents.market_mapping import run
from schema import SEGMENT_WEIGHTS, empty_record


def make_record(role: str) -> dict:
    record = empty_record()
    record["role"] = role
    record["company"] = f"Test-{role}"
    return record


class TestMarketMapping(unittest.TestCase):
    def test_assigns_weight_for_every_known_role(self) -> None:
        records = [make_record(role) for role in SEGMENT_WEIGHTS]

        result = run(records)

        self.assertIs(result, records)
        for record in result:
            with self.subTest(role=record["role"]):
                self.assertEqual(
                    record["segment_weight"],
                    SEGMENT_WEIGHTS[record["role"]],
                )

    def test_assigns_zero_for_unknown_or_blank_role(self) -> None:
        records = [make_record("Software"), empty_record()]

        result = run(records)

        self.assertEqual(result[0]["segment_weight"], 0.0)
        self.assertEqual(result[1]["segment_weight"], 0.0)


if __name__ == "__main__":
    unittest.main()
