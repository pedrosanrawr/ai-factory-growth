import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from agents.risk_adjustment import run, _clamp
from schema import empty_record

def make_record(**overrides) -> dict:
    """Start from the shared schema's blank record, override fields per test."""
    record = empty_record()
    record.update(
        {
            "growth_forecast_pct": 20.0,
            "concentration_risk": 0.5,
            "cyclicality_risk": 0.4,
            "execution_risk": 0.3,
            "eff_score": 3,
        }
    )
    record.update(overrides)
    return record


class TestClamp(unittest.TestCase):
    """_clamp() should keep values within the given bounds."""

    def test_within_range_unchanged(self):
        self.assertEqual(_clamp(0.5), 0.5)

    def test_above_range_clamped_to_hi(self):
        self.assertEqual(_clamp(1.5), 1.0)

    def test_below_range_clamped_to_lo(self):
        self.assertEqual(_clamp(-0.5), 0.0)

    def test_non_numeric_falls_back_to_lo(self):
        self.assertEqual(_clamp("n/a"), 0.0)

    def test_none_falls_back_to_lo(self):
        self.assertEqual(_clamp(None), 0.0)

    def test_custom_bounds(self):
        self.assertEqual(_clamp(50, lo=0, hi=30), 30)
        self.assertEqual(_clamp(-5, lo=0, hi=30), 0)
        self.assertEqual(_clamp(15, lo=0, hi=30), 15)


class TestWorkedExamplesAtDefaultDiscount(unittest.TestCase):
    """Reproduce the spec's worked examples at risk_discount_pct=10 exactly."""

    def test_nvidia(self):
        record = make_record(
            company="NVIDIA",
            growth_forecast_pct=45.0,
            concentration_risk=0.8,
            cyclicality_risk=0.3,
            execution_risk=0.3,
            eff_score=5,
        )
        out = run([record], risk_discount_pct=10.0)[0]
        self.assertEqual(out["risk_multiplier"], 0.946)
        self.assertAlmostEqual(out["adjusted_growth_pct"], 38.31, places=2)

    def test_fluor(self):
        record = make_record(
            company="Fluor",
            growth_forecast_pct=15.0,
            concentration_risk=0.5,
            cyclicality_risk=0.6,
            execution_risk=0.8,
            eff_score=1,
        )
        out = run([record], risk_discount_pct=10.0)[0]
        self.assertEqual(out["risk_multiplier"], 0.81)
        self.assertAlmostEqual(out["adjusted_growth_pct"], 10.94, places=1)


class TestWorkedExamplesAtZeroDiscount(unittest.TestCase):
    """Same companies with no global discount applied."""

    def test_nvidia_zero_discount(self):
        record = make_record(
            growth_forecast_pct=45.0,
            concentration_risk=0.8,
            cyclicality_risk=0.3,
            execution_risk=0.3,
            eff_score=5,
        )
        out = run([record], risk_discount_pct=0.0)[0]
        self.assertAlmostEqual(out["adjusted_growth_pct"], 42.57, places=2)

    def test_fluor_zero_discount(self):
        record = make_record(
            growth_forecast_pct=15.0,
            concentration_risk=0.5,
            cyclicality_risk=0.6,
            execution_risk=0.8,
            eff_score=1,
        )
        out = run([record], risk_discount_pct=0.0)[0]
        self.assertAlmostEqual(out["adjusted_growth_pct"], 12.15, places=2)


class TestFormulaSteps(unittest.TestCase):
    """Check each intermediate step directly, independent of the worked examples."""

    def test_zero_risk_zero_discount_no_change(self):
        # avg_risk=0 -> base_multiplier=1.0; eff_score=1 -> eff_modifier=1.0;
        # global_discount=1.0 at 0% -> growth passes through unchanged.
        record = make_record(
            growth_forecast_pct=30.0,
            concentration_risk=0.0,
            cyclicality_risk=0.0,
            execution_risk=0.0,
            eff_score=1,
        )
        out = run([record], risk_discount_pct=0.0)[0]
        self.assertEqual(out["risk_multiplier"], 1.0)
        self.assertEqual(out["adjusted_growth_pct"], 30.0)

    def test_max_risk_caps_base_discount_at_30_percent(self):
        # avg_risk=1.0 -> base_multiplier=0.70
        record = make_record(
            concentration_risk=1.0, cyclicality_risk=1.0, execution_risk=1.0, eff_score=1
        )
        out = run([record], risk_discount_pct=0.0)[0]
        self.assertEqual(out["risk_multiplier"], 0.7)

    def test_max_eff_score_gives_ten_percent_bonus(self):
        # eff_score=5 -> eff_modifier=1.10, combined with zero risk -> multiplier=1.10
        record = make_record(
            concentration_risk=0.0, cyclicality_risk=0.0, execution_risk=0.0, eff_score=5
        )
        out = run([record], risk_discount_pct=0.0)[0]
        self.assertEqual(out["risk_multiplier"], 1.1)

    def test_global_discount_at_thirty_percent(self):
        record = make_record(
            growth_forecast_pct=100.0,
            concentration_risk=0.0,
            cyclicality_risk=0.0,
            execution_risk=0.0,
            eff_score=1,
        )
        out = run([record], risk_discount_pct=30.0)[0]
        # risk_multiplier=1.0, global_discount=0.70
        self.assertEqual(out["adjusted_growth_pct"], 70.0)


class TestClampingOfInputs(unittest.TestCase):
    """Out-of-range risk sub-scores and slider values must be clamped, not rejected."""

    def test_risk_subscores_above_one_are_clamped(self):
        record = make_record(
            concentration_risk=5.0, cyclicality_risk=5.0, execution_risk=5.0, eff_score=1
        )
        out = run([record], risk_discount_pct=0.0)[0]
        # avg_risk clamps to 1.0 each -> base_multiplier = 0.70, same as max-risk case
        self.assertEqual(out["risk_multiplier"], 0.7)

    def test_risk_subscores_below_zero_are_clamped(self):
        record = make_record(
            concentration_risk=-2.0, cyclicality_risk=-2.0, execution_risk=-2.0, eff_score=1
        )
        out = run([record], risk_discount_pct=0.0)[0]
        # avg_risk clamps to 0.0 each -> base_multiplier = 1.00
        self.assertEqual(out["risk_multiplier"], 1.0)

    def test_global_discount_above_thirty_is_capped(self):
        out_over = run([make_record(growth_forecast_pct=100.0)], risk_discount_pct=999.0)[0]
        out_capped = run([make_record(growth_forecast_pct=100.0)], risk_discount_pct=30.0)[0]
        self.assertEqual(out_over["adjusted_growth_pct"], out_capped["adjusted_growth_pct"])

    def test_global_discount_below_zero_is_floored(self):
        out_under = run([make_record(growth_forecast_pct=100.0)], risk_discount_pct=-50.0)[0]
        out_floored = run([make_record(growth_forecast_pct=100.0)], risk_discount_pct=0.0)[0]
        self.assertEqual(out_under["adjusted_growth_pct"], out_floored["adjusted_growth_pct"])

    def test_non_numeric_global_discount_falls_back_to_default(self):
        out_bad = run([make_record(growth_forecast_pct=100.0)], risk_discount_pct="oops")[0]
        out_default = run([make_record(growth_forecast_pct=100.0)], risk_discount_pct=10.0)[0]
        self.assertEqual(out_bad["adjusted_growth_pct"], out_default["adjusted_growth_pct"])


class TestSafeDefaultsAndNoCrash(unittest.TestCase):
    """run() must never crash on missing or malformed record fields."""

    def test_blank_schema_record_does_not_crash(self):
        # empty_record() straight from schema.py, no overrides at all.
        out = run([empty_record()], risk_discount_pct=10.0)[0]
        self.assertIn("risk_multiplier", out)
        self.assertIn("adjusted_growth_pct", out)
        self.assertEqual(out["adjusted_growth_pct"], 0.0)

    def test_missing_keys_entirely_does_not_crash(self):
        out = run([{}], risk_discount_pct=10.0)[0]
        self.assertIn("risk_multiplier", out)
        self.assertIn("adjusted_growth_pct", out)
        self.assertEqual(out["adjusted_growth_pct"], 0.0)

    def test_non_numeric_growth_forecast_falls_back_to_zero(self):
        record = make_record(growth_forecast_pct="n/a")
        out = run([record], risk_discount_pct=10.0)[0]
        self.assertEqual(out["adjusted_growth_pct"], 0.0)

    def test_eff_score_out_of_bounds_is_clamped(self):
        record = make_record(eff_score=99)
        out = run([record], risk_discount_pct=0.0)[0]
        # eff_score clamps to 5 -> same as an explicit eff_score=5 record
        expected = run([make_record(eff_score=5)], risk_discount_pct=0.0)[0]
        self.assertEqual(out["risk_multiplier"], expected["risk_multiplier"])

    def test_eff_score_below_one_is_clamped(self):
        record = make_record(eff_score=-10)
        out = run([record], risk_discount_pct=0.0)[0]
        expected = run([make_record(eff_score=1)], risk_discount_pct=0.0)[0]
        self.assertEqual(out["risk_multiplier"], expected["risk_multiplier"])

    def test_missing_eff_score_defaults_to_one(self):
        record = make_record()
        del record["eff_score"]
        out = run([record], risk_discount_pct=0.0)[0]
        expected = run([make_record(eff_score=1)], risk_discount_pct=0.0)[0]
        self.assertEqual(out["risk_multiplier"], expected["risk_multiplier"])


class TestDoesNotMutateOtherFields(unittest.TestCase):
    """Per the spec: only risk_multiplier and adjusted_growth_pct may be written;
    growth_forecast_pct and unrelated schema fields must be left untouched."""

    def test_growth_forecast_pct_unchanged(self):
        record = make_record(growth_forecast_pct=45.0)
        out = run([record], risk_discount_pct=10.0)[0]
        self.assertEqual(out["growth_forecast_pct"], 45.0)

    def test_unrelated_schema_fields_untouched(self):
        record = make_record(company="NVIDIA", role="Compute/Server", moat_score=5)
        out = run([record], risk_discount_pct=10.0)[0]
        self.assertEqual(out["company"], "NVIDIA")
        self.assertEqual(out["role"], "Compute/Server")
        self.assertEqual(out["moat_score"], 5)

    def test_rounded_to_four_decimal_places(self):
        record = make_record(
            growth_forecast_pct=33.333,
            concentration_risk=0.37,
            cyclicality_risk=0.61,
            execution_risk=0.29,
            eff_score=4,
        )
        out = run([record], risk_discount_pct=13.0)[0]
        self.assertEqual(out["risk_multiplier"], round(out["risk_multiplier"], 4))
        self.assertEqual(out["adjusted_growth_pct"], round(out["adjusted_growth_pct"], 4))


class TestMultipleRecordsAndListReturn(unittest.TestCase):
    """run() should process every record and return the same list object shape."""

    def test_all_records_processed(self):
        records = [
            make_record(growth_forecast_pct=45.0),
            make_record(growth_forecast_pct=15.0),
            make_record(growth_forecast_pct=20.0),
        ]
        out = run(records, risk_discount_pct=10.0)
        self.assertEqual(len(out), 3)
        for r in out:
            self.assertIn("risk_multiplier", r)
            self.assertIn("adjusted_growth_pct", r)

    def test_empty_list_returns_empty_list(self):
        self.assertEqual(run([], risk_discount_pct=10.0), [])

    def test_default_risk_discount_pct_is_ten(self):
        out_default = run([make_record(growth_forecast_pct=100.0)])[0]
        out_explicit = run([make_record(growth_forecast_pct=100.0)], risk_discount_pct=10.0)[0]
        self.assertEqual(out_default["adjusted_growth_pct"], out_explicit["adjusted_growth_pct"])


if __name__ == "__main__":
    unittest.main()