"""DON work file: evidence-grounded three-year growth analysis.

Steps:
1. Keep ``run(records)`` and the existing ``[-100, 500]`` range guard.
2. Supply company context, growth catalysts, dated evidence, and CSV forecast
   to the structured Gemini helper.
3. Request forecast, concise rationale, confidence, and evidence reference IDs.
4. Validate the response, then clamp the numeric forecast using this module.
5. On missing evidence or a failed/invalid LLM response, retain the CSV value
   and record a fallback status.
6. Add tests for valid, malformed, out-of-range, missing-evidence, and
   fallback cases.

Do not rank records or alter the risk-adjustment or TAFGS formulas.
Done when the forecast is citation-backed, range-safe, and CSV compatible.
"""

import math


def _to_float(value, default: float = 0.0) -> float:
    """Safe float parser with default fallback."""
    try:
        parsed = float(value) if value is not None else default
        return parsed if math.isfinite(parsed) else default
    except (ValueError, TypeError):
        return default


def run(records: list[dict]) -> list[dict]:
    """Validate and clamp growth_forecast_pct to [-100, 500] range."""
    for record in records:
        growth = _to_float(record.get("growth_forecast_pct", 0.0), 0.0)
        growth = max(-100.0, min(500.0, growth))
        record["growth_forecast_pct"] = round(growth, 4)

    return records
