"""
Agent 6: Risk Adjustment Agent
Owner: De Jesus

GOAL:
Adjust each company's raw Growth Forecast % downward based on two
separate factors:
  1. Per-company risk profile (from research data — concentration,
     cyclicality, execution risk sub-scores)
  2. Global risk discount (from the UI sidebar slider — a configurable
     additional discount applied uniformly across all companies)

The adjusted growth % (adjusted_growth_pct) is what the Ranking Agent
will use in the TAFGS formula — NOT the raw growth_forecast_pct.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VARIABLES YOU WILL READ FROM THE RECORD:
- record["growth_forecast_pct"]  →  float, raw growth % from Growth Forecast Agent
- record["concentration_risk"]   →  float (0.0–1.0), from CSV
- record["cyclicality_risk"]     →  float (0.0–1.0), from CSV
- record["execution_risk"]       →  float (0.0–1.0), from CSV
- record["eff_score"]            →  int (1–5), from CSV

VARIABLES YOU WILL FILL:
- record["risk_multiplier"]      →  float (combined discount factor)
- record["adjusted_growth_pct"]  →  float (growth after all risk adjustments)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMULA (step by step):

  PART 1 — Per-company risk adjustment (from research data):

  Step 1: Average Risk Score
    avg_risk = (concentration_risk + cyclicality_risk + execution_risk) / 3

  Step 2: Base Risk Multiplier
    base_multiplier = 1 - (avg_risk * 0.3)
    — Caps the maximum per-company discount at 30%
    — avg_risk=1.0 → base_multiplier=0.70 (30% discount)
    — avg_risk=0.0 → base_multiplier=1.00 (no discount)

  Step 3: Efficiency Modifier
    eff_modifier = 1 + ((eff_score - 1) / 4) * 0.1
    — Higher efficiency slightly reduces the risk penalty
    — eff_score=1 → modifier=1.00 (no bonus)
    — eff_score=5 → modifier=1.10 (10% bonus, less penalty)

  Step 4: Per-company Risk Multiplier
    risk_multiplier = base_multiplier * eff_modifier

  PART 2 — Global risk discount (from UI sidebar slider):

  Step 5: Global Discount Factor
    global_discount = 1 - (clamp(risk_discount_pct, 0, 30) / 100)
    — risk_discount_pct=0  → global_discount=1.00 (no additional discount)
    — risk_discount_pct=10 → global_discount=0.90 (10% additional discount)
    — risk_discount_pct=30 → global_discount=0.70 (30% additional discount)

  Step 6: Final Adjusted Growth %
    adjusted_growth_pct = growth_forecast_pct * risk_multiplier * global_discount

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORKED EXAMPLES (at default risk_discount_pct=10):

  NVIDIA (NVDA):
    avg_risk        = (0.8 + 0.3 + 0.3) / 3        = 0.467
    base_multiplier = 1 - (0.467 * 0.3)             = 0.860
    eff_modifier    = 1 + ((5-1)/4) * 0.1           = 1.10
    risk_multiplier = 0.860 * 1.10                  = 0.946
    global_discount = 1 - (10/100)                  = 0.90
    adjusted_growth = 45.0 * 0.946 * 0.90           = 38.31%

  Fluor (FLR):
    avg_risk        = (0.5 + 0.6 + 0.8) / 3         = 0.633
    base_multiplier = 1 - (0.633 * 0.3)             = 0.810
    eff_modifier    = 1 + ((1-1)/4) * 0.1           = 1.00
    risk_multiplier = 0.810 * 1.00                  = 0.810
    global_discount = 1 - (10/100)                  = 0.90
    adjusted_growth = 15.0 * 0.810 * 0.90           = 10.94%

  At risk_discount_pct=0 (no global discount, per-company risk only):
    NVIDIA: 45.0 * 0.946 * 1.00 = 42.57%
    Fluor:  15.0 * 0.810 * 1.00 = 12.15%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT TO DO:
1. Loop through every record.
2. Get all input values using .get() with safe defaults.
3. Clamp risk sub-scores to 0.0–1.0.
4. Clamp risk_discount_pct to 0–30.
5. Apply the 6-step formula above.
6. Round risk_multiplier to 4 decimal places.
7. Round adjusted_growth_pct to 4 decimal places.
8. Write both back into the record.
9. Return the updated list.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INPUT:  list[dict]  — records from Growth Forecast Agent
        risk_discount_pct: float — from the UI sidebar slider (default 10.0)
OUTPUT: list[dict]  — same records, risk_multiplier and
                      adjusted_growth_pct filled in

DO NOT:
- Modify growth_forecast_pct — only write into adjusted_growth_pct.
- Apply Power Efficiency Weighting here — that belongs to Ranking Agent.
- Change any other field in the record.
- Crash if values are missing — always use .get() with defaults.
- Apply risk_discount_pct more than once — it is applied here only,
  the Ranking Agent does not apply it again.

CURRENT UI STATUS:
The Streamlit sliders currently show hardcoded mock data from
frontend/data.py — moving the slider does not yet affect the ranking.
This is expected while agents are still placeholders. Once the UI owner
wires in the real pipeline, they must call:
    records = adjust_risk(records, risk_discount_pct=risk_discount)
"""

def run(records: list[dict], risk_discount_pct: float = 10.0) -> list[dict]:
    # TODO: implement this agent
    # 1. Loop through records
    # 2. Get risk sub-scores, eff_score, growth_forecast_pct
    # 3. Clamp sub-scores to 0-1, clamp risk_discount_pct to 0-30
    # 4. Apply 6-step formula
    # 5. Write risk_multiplier and adjusted_growth_pct into record
    # 6. Return updated records
    return records


def _clamp(value, lo=0.0, hi=1.0) -> float:
    """Clamp a value between lo and hi, safely handling non-numeric input."""
    try:
        return max(lo, min(hi, float(value)))
    except (ValueError, TypeError):
        return lo