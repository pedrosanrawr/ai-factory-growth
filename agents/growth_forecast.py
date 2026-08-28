"""
Agent 5: Growth Forecast Agent
Owner: Don

GOAL:
Read and validate each company's pre-filled 3-year AI-driven growth
forecast percentage from the CSV. The value was determined during
research — this agent does not recalculate it. It only validates
the number is within a reasonable range before passing it forward
to the Risk Adjustment Agent.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VARIABLES YOU WILL READ FROM THE RECORD:
- record["growth_forecast_pct"]  →  float, pre-filled from CSV
  This is the estimated 3-year CAGR % driven by AI Factory demand.
  Examples: 45.0 (NVIDIA), 60.0 (Credo), 15.0 (Fluor)

VARIABLES YOU WILL FILL/CONFIRM:
- record["growth_forecast_pct"]  →  same field, validated and clamped

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VALIDATION RULE:
  Growth % must be between -100.0 and 500.0.
  Anything outside this range is a data entry error — clamp it.
    growth = max(-100.0, min(500.0, growth))

  -100% lower bound = a company cannot lose more than all of its growth
   500% upper bound = prevents unrealistic outliers from dominating the ranking

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT TO DO:
1. Loop through every record.
2. Get the value: growth = record.get("growth_forecast_pct", 0.0)
3. Convert to float safely using try/except — default to 0.0 if invalid.
4. Clamp: growth = max(-100.0, min(500.0, growth))
5. Write back: record["growth_forecast_pct"] = round(growth, 4)
6. Return the updated list.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORKED EXAMPLES:

  NVIDIA (NVDA):
    growth_forecast_pct in CSV = 45.0
    After validation            = 45.0  (unchanged, within range)

  Credo (CRDO):
    growth_forecast_pct in CSV = 60.0
    After validation            = 60.0  (unchanged, within range)

  Bad data edge case:
    growth_forecast_pct in CSV = "N/A"
    After validation            = 0.0   (defaulted)

  Out-of-range edge case:
    growth_forecast_pct in CSV = 999.0
    After validation            = 500.0 (clamped to maximum)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INPUT:  list[dict]  — records from Margin Analysis Agent
OUTPUT: list[dict]  — same records, growth_forecast_pct validated

DO NOT:
- Recalculate growth % from growth_catalysts text.
- Change the value unless it is outside -100 to 500.
- Change any other field in the record.
- Crash if the value is not a number — use try/except.
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
