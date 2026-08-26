import unittest

from agents.growth_forecast import run


class TestGrowthForecast(unittest.TestCase):
    def test_passes_through_normal_values(self) -> None:
        records = [
            {"growth_forecast_pct": 45.0},
            {"growth_forecast_pct": 60.0},
            {"growth_forecast_pct": 20.0},
        ]

        result = run(records)

        self.assertIs(result, records)
        self.assertEqual(result[0]["growth_forecast_pct"], 45.0)
        self.assertEqual(result[1]["growth_forecast_pct"], 60.0)
        self.assertEqual(result[2]["growth_forecast_pct"], 20.0)

    def test_clamps_above_500(self) -> None:
        
        records = [{"growth_forecast_pct": 999.0}]

        result = run(records)

        self.assertEqual(result[0]["growth_forecast_pct"], 500.0)

    def test_clamps_below_negative_100(self) -> None:
        records = [{"growth_forecast_pct": -200.0}]

        result = run(records)

        self.assertEqual(result[0]["growth_forecast_pct"], -100.0)

    def test_defaults_bad_data_to_zero(self) -> None:
        records = [
            {"growth_forecast_pct": "N/A"},
            {"growth_forecast_pct": None},
            {"growth_forecast_pct": "invalid"},
        ]

        result = run(records)

        self.assertEqual(result[0]["growth_forecast_pct"], 0.0)
        self.assertEqual(result[1]["growth_forecast_pct"], 0.0)
        self.assertEqual(result[2]["growth_forecast_pct"], 0.0)

    def test_handles_missing_field(self) -> None:
        records = [{}]

        result = run(records)

        self.assertEqual(result[0]["growth_forecast_pct"], 0.0)

    def test_rounds_to_four_decimals(self) -> None:
        records = [{"growth_forecast_pct": 33.33333}]

        result = run(records)

        self.assertEqual(result[0]["growth_forecast_pct"], 33.3333)

    def test_does_not_modify_other_fields(self) -> None:
        records = [{"growth_forecast_pct": 45.0, "company": "NVIDIA"}]

        result = run(records)

        self.assertEqual(result[0]["company"], "NVIDIA")


if __name__ == "__main__":
    unittest.main()
