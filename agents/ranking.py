"""
Agent 7: Ranking Agent
Owner: Flores

GOAL:
Compute the final TAFGS score for each company using the formula
defined in the project brief, then sort all companies by the selected
ranking priority and assign final ranks (1 = best).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TAFGS FORMULA (from the project brief — this is the core formula,
do not change it):

  TAFGS = (Moat Score × Operating Margin Score) × Forecast AI-Driven Growth

  In code:
    base_tafgs = moat_score * margin_score * (adjusted_growth_pct / 100)

  NOTE: adjusted_growth_pct is divided by 100 to convert from % to decimal.
  NOTE: Use adjusted_growth_pct (from Risk Adjustment Agent) — NOT
        the raw growth_forecast_pct from the CSV.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ADDITIONAL CONFIGURATION — Power Efficiency Weighting:
  The UI provides a Power Efficiency Weighting slider (1.0–2.0x).
  This is an ADDITIONAL multiplier applied ON TOP of the base TAFGS
  — it does not replace or modify the core brief formula above.
  Think of it as a configurable boost that rewards companies with
  higher Efficiency Scores when the user increases the weight.

  efficiency_factor = 1 + ((clamp(eff_score, 1, 5) - 1) / 4) *
                          (clamp(power_efficiency_weight, 1.0, 2.0) - 1)
  tafgs_score = base_tafgs * efficiency_factor

  Behavior of efficiency_factor at default weight (1.2x):
    eff_score=1 → factor=1.00  (no boost — lowest efficiency)
    eff_score=3 → factor=1.10  (10% boost)
    eff_score=5 → factor=1.20  (20% boost — highest efficiency)

  Behavior at weight=1.0x:
    efficiency_factor always = 1.00 regardless of eff_score
    → pure brief formula, no boost applied

  Behavior at weight=2.0x:
    eff_score=1 → factor=1.00  (no boost)
    eff_score=5 → factor=2.00  (100% boost — maximum amplification)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VARIABLES YOU WILL READ FROM THE RECORD:
- record["moat_score"]            →  int (0–5), from Moat Analysis Agent
- record["margin_score"]          →  int (1–5), from Margin Analysis Agent
- record["adjusted_growth_pct"]   →  float, from Risk Adjustment Agent
- record["eff_score"]             →  int (1–5), from CSV
- record["operating_margin_pct"]  →  float, needed to determine Status field

VARIABLES YOU WILL FILL:
- record["tafgs_score"]  →  float (final score after brief formula + config)
- record["rank"]         →  int (1 = highest tafgs_score)
- record["status"]       →  str ("Profitable" or "Unprofitable")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STATUS FIELD:
  Fill this before sorting:
    record["status"] = "Profitable" if record["operating_margin_pct"] > 0
                       else "Unprofitable"

SORTING OPTIONS (based on ranking_priority parameter):
  "Profitability First" → sort by (status=="Profitable" DESC, tafgs_score DESC)
  "Growth % (Highest)"  → sort by adjusted_growth_pct DESC
  "TAFGS Score"         → sort by tafgs_score DESC (default)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT TO DO:
1. Loop through every record:
   a. Fill record["status"] based on operating_margin_pct
   b. Compute base_tafgs = moat_score * margin_score * (adjusted_growth_pct / 100)
   c. Compute efficiency_factor using eff_score and power_efficiency_weight
   d. Compute tafgs_score = base_tafgs * efficiency_factor
   e. Write tafgs_score into record["tafgs_score"]
2. Sort the full list based on ranking_priority.
3. Take the top 20: top_20 = sorted_records[:20]
4. Assign ranks: for i, record in enumerate(top_20): record["rank"] = i + 1
5. Return top_20 only — NOT the full list.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORKED EXAMPLES (at default power_efficiency_weight=1.2):

  NVIDIA (NVDA) — eff_score=5:
    base_tafgs        = 5 * 5 * (42.57/100)       = 10.643
    efficiency_factor = 1 + ((5-1)/4) * (1.2-1)   = 1.20
    tafgs_score       = 10.643 * 1.20              = 12.771

  Broadcom (AVGO) — eff_score=4:
    base_tafgs        = 5 * 5 * (32.20/100)        = 8.050
    efficiency_factor = 1 + ((4-1)/4) * (1.2-1)    = 1.15
    tafgs_score       = 8.050 * 1.15               = 9.258

  Fluor (FLR) — eff_score=1:
    base_tafgs        = 3 * 1 * (12.15/100)        = 0.365
    efficiency_factor = 1 + ((1-1)/4) * (1.2-1)    = 1.00
    tafgs_score       = 0.365 * 1.00               = 0.365

  At weight=1.0 (pure brief formula, no boost):
    NVIDIA: base_tafgs = 10.643, efficiency_factor = 1.00 → tafgs = 10.643
    Fluor:  base_tafgs = 0.365,  efficiency_factor = 1.00 → tafgs = 0.365

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DO NOT:
- Return more than 20 records.
- Use growth_forecast_pct (raw) — always use adjusted_growth_pct.
- Apply risk_discount_pct here — that is already baked into
  adjusted_growth_pct by the Risk Adjustment Agent.
- Remove or modify the core brief formula (base_tafgs) — the
  efficiency_factor is additive on top of it, not a replacement.
"""

def run(records: list[dict],
        ranking_priority: str = "TAFGS Score",
        power_efficiency_weight: float = 1.2) -> list[dict]:
    # TODO: implement this agent
    # 1. Loop: fill status, compute base_tafgs, compute efficiency_factor,
    #    compute tafgs_score, write into record
    # 2. Sort by ranking_priority
    # 3. Slice top 20, assign ranks
    # 4. Return top 20
    return records


def _clamp(value, lo, hi):
    """Clamp a value between lo and hi, safely handling non-numeric input."""
    try:
        return max(lo, min(hi, float(value)))
    except (ValueError, TypeError):
        return lo