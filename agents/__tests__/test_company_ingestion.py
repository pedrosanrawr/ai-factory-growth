import tempfile
import unittest
from pathlib import Path

import pandas as pd

from agents.company_ingestion import REQUIRED_COLUMNS, run


class TestCompanyIngestion(unittest.TestCase):
    def test_loads_and_maps_the_project_csv(self) -> None:
        records = run()

        self.assertEqual(len(records), 20)
        first = records[0]
        self.assertEqual(first["company"], "NVIDIA Corporation (NVDA)")
        self.assertEqual(first["role"], "Compute/Server")
        self.assertEqual(first["operating_margin_pct"], 60.38)
        self.assertEqual(first["revenue_exposure_pct"], 89.70)
        self.assertEqual(first["moat_score"], 5)
        self.assertEqual(first["growth_forecast_pct"], 45.0)
        self.assertEqual(first["eff_score"], 5)

    def test_skips_blank_rows_and_defaults_invalid_numbers(self) -> None:
        rows = [
            {
                "Company Name + Ticker": "Example Corp (EXM)",
                "Primary AI Factory Role": "Networking",
                "Operating Margin %": "not a number",
                "Revenue Exposure %": "~25.5% Direct",
                "Moat Score": "bad",
                "Growth Forecast %": "bad",
                "Concentration Risk": "bad",
                "Cyclicality Risk": 0.3,
                "Execution Risk": 0.4,
                "Efficiency Score": "bad",
            },
            {
                "Company Name + Ticker": "",
                "Primary AI Factory Role": "Networking",
                "Operating Margin %": 20.0,
                "Moat Score": 3,
                "Growth Forecast %": 10.0,
                "Concentration Risk": 0.2,
                "Cyclicality Risk": 0.3,
                "Execution Risk": 0.4,
                "Efficiency Score": 3,
            },
        ]

        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "companies.csv"
            pd.DataFrame(rows).to_csv(csv_path, index=False)
            records = run(str(csv_path))

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record["revenue_exposure_pct"], 25.5)
        self.assertEqual(record["operating_margin_pct"], 0.0)
        self.assertEqual(record["moat_score"], 0)
        self.assertEqual(record["growth_forecast_pct"], 0.0)
        self.assertEqual(record["concentration_risk"], 0.0)
        self.assertEqual(record["eff_score"], 0)

    def test_raises_when_required_column_is_missing(self) -> None:
        columns = [column for column in REQUIRED_COLUMNS if column != "Moat Score"]

        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "companies.csv"
            pd.DataFrame(columns=columns).to_csv(csv_path, index=False)

            with self.assertRaisesRegex(ValueError, "Moat Score"):
                run(str(csv_path))


if __name__ == "__main__":
    unittest.main()
