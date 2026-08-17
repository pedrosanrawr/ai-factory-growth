"""
Agent 5: Growth Forecast Agent
Owner: Don

GOAL:
Read and validate each company's pre-filled 3-year AI-driven growth
forecast percentage. The growth_forecast_pct is already filled in the
CSV (you filled it in during research). This agent reads it, validates
the value is a reasonable number, and writes it into the record.

VARIABLE YOU WILL READ FROM THE RECORD:
- record["growth_forecast_pct"]  →  float, pre-filled from CSV
  This is the estimated 3-year CAGR % driven by AI Factory demand.
  Example: 45.0 for Nvidia, 15.0 for Fluor

VARIABLE YOU WILL FILL/CONFIRM:
- record["growth_forecast_pct"]  →  same field, validated

WHAT TO DO:
1. Loop through every record.
2. Get the growth value: growth = record.get("growth_forecast_pct", 0.0)
3. Convert to float safely using try/except.
4. Apply a sanity check — growth should be between -100% and 500%:
   growth = max(-100.0, min(500.0, growth))
5. Write back: record["growth_forecast_pct"] = round(growth, 4)
6. Return the updated list.

INPUT:  list[dict]  — records from Margin Analysis Agent
OUTPUT: list[dict]  — same records, growth_forecast_pct validated

EXAMPLE:
  NVIDIA  → growth_forecast_pct = 45.0   (stays 45.0, valid)
  Fluor   → growth_forecast_pct = 15.0   (stays 15.0, valid)
  Credo   → growth_forecast_pct = 60.0   (stays 60.0, valid)

DO NOT:
- Recalculate the growth % from growth_catalysts text.
- Change the value unless it is out of the -100 to 500 range.
- Change any other field in the record.
- Crash if the value is not a number — use try/except and default to 0.0.
"""

def run(records: list[dict]) -> list[dict]:
    # TODO: implement this agent
    # Loop, validate growth_forecast_pct, clamp to -100 to 500,
    # return records
    return records