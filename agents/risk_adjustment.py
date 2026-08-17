"""
Agent 6: Risk Adjustment Agent
Owner: De Jesus

GOAL:
Adjust each company's raw Growth Forecast % downward based on its
risk profile. The adjusted growth % is what the Ranking Agent will
use in the TAFGS formula — NOT the raw growth_forecast_pct.

This agent also uses the Efficiency Score to slightly reduce the
risk penalty for more operationally efficient companies.

VARIABLES YOU WILL READ FROM THE RECORD:
- record["growth_forecast_pct"]  →  float, raw growth % from Growth Forecast Agent
- record["concentration_risk"]   →  float (0.0–1.0), from CSV
- record["cyclicality_risk"]     →  float (0.0–1.0), from CSV
- record["execution_risk"]       →  float (0.0–1.0), from CSV
- record["eff_score"]            →  int (1–5), from CSV

VARIABLES YOU WILL FILL:
- record["risk_multiplier"]    →  float (computed discount factor)
- record["adjusted_growth_pct"] →  float (growth after risk adjustment)

FORMULA (step by step):

  Step 1: Average Risk Score
    avg_risk = (concentration_risk + cyclicality_risk + execution_risk) / 3

  Step 2: Base Risk Multiplier
    base_multiplier = 1 - (avg_risk * 0.3)
    — This caps the maximum discount at 30%
      (if avg_risk = 1.0, base_multiplier = 0.70 = 30% discount)

  Step 3: Efficiency Modifier
    eff_modifier = 1 + ((eff_score - 1) / 4) * 0.1
    — eff_score=1 → modifier=1.00 (no bonus)
    — eff_score=5 → modifier=1.10 (10% bonus, less penalty)

  Step 4: Final Risk Multiplier
    risk_multiplier = base_multiplier * eff_modifier

  Step 5: Adjusted Growth %
    adjusted_growth_pct = growth_forecast_pct * risk_multiplier

WORKED EXAMPLES:

  NVIDIA (NVDA):
    avg_risk = (0.8 + 0.3 + 0.3) / 3 = 0.467
    base_multiplier = 1 - (0.467 * 0.3) = 0.860
    eff_modifier = 1 + ((5-1)/4) * 0.1 = 1.10
    risk_multiplier = 0.860 * 1.10 = 0.946
    adjusted_growth_pct = 45.0 * 0.946 = 42.57%

  Fluor (FLR):
    avg_risk = (0.5 + 0.6 + 0.8) / 3 = 0.633
    base_multiplier = 1 - (0.633 * 0.3) = 0.810
    eff_modifier = 1 + ((1-1)/4) * 0.1 = 1.00
    risk_multiplier = 0.810 * 1.00 = 0.810
    adjusted_growth_pct = 15.0 * 0.810 = 12.15%

WHAT TO DO:
1. Loop through every record.
2. Get the 5 input values (use .get() with defaults).
3. Clamp risk sub-scores to 0.0–1.0 using max(0.0, min(1.0, value)).
4. Apply the 5-step formula above.
5. Round risk_multiplier to 4 decimal places.
6. Round adjusted_growth_pct to 4 decimal places.
7. Write both back into the record.
8. Return the updated list.

INPUT:  list[dict]  — records from Growth Forecast Agent
OUTPUT: list[dict]  — same records, risk_multiplier and
                      adjusted_growth_pct filled in

DO NOT:
- Modify growth_forecast_pct — only write into adjusted_growth_pct.
- Apply a global risk_discount_pct from the sidebar here —
  that is handled separately by the Ranking Agent.
- Change any other field.
- Crash if values are missing — use .get() with defaults.
"""

def run(records: list[dict]) -> list[dict]:
    # TODO: implement this agent
    # Loop, apply 5-step formula, fill risk_multiplier
    # and adjusted_growth_pct, return records
    return records


def _clamp(value, lo=0.0, hi=1.0) -> float:
    """Clamp a value between lo and hi, safely handling non-numeric input."""
    try:
        return max(lo, min(hi, float(value)))
    except (ValueError, TypeError):
        return lo