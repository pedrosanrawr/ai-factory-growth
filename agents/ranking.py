"""
Agent 7: Ranking Agent
Owner: Flores

GOAL:
Compute the final TAFGS score for each company using the agreed
formula, then sort all companies by the selected ranking priority
and assign final ranks (1 = best).

VARIABLES YOU WILL READ FROM THE RECORD:
- record["moat_score"]          →  int (0–5), from Moat Analysis Agent
- record["margin_score"]        →  int (1–5), from Margin Analysis Agent
- record["adjusted_growth_pct"] →  float, from Risk Adjustment Agent
                                   ⚠️ USE THIS, NOT growth_forecast_pct
- record["eff_score"]           →  int (1–5), from CSV (via Company Ingestion)
- record["status"]              →  str ("Profitable"/"Unprofitable"),
                                   needed for "Profitability First" sort

VARIABLES YOU WILL FILL:
- record["tafgs_score"]  →  float (the final computed score)
- record["rank"]         →  int (1 = highest tafgs_score)

TAFGS FORMULA (from the project brief):
  TAFGS = Moat Score × Operating Margin Score × Forecast AI-Driven Growth

  In code:
    tafgs_score = moat_score * margin_score * (adjusted_growth_pct / 100)

  NOTE: adjusted_growth_pct is divided by 100 to convert from % to decimal.
  Example: NVIDIA → 5 * 5 * (42.57 / 100) = 5 * 5 * 0.4257 = 10.64

  ⚠️ DO NOT include Efficiency Score or risk_discount in this formula.
  The TAFGS formula is exactly Moat × Margin × Growth — nothing else.

STATUS FIELD:
  Before sorting, fill the status field for each record:
    record["status"] = "Profitable" if record["operating_margin_pct"] > 0
                       else "Unprofitable"

SORTING OPTIONS (based on ranking_priority parameter):
  "Profitability First"  →  sort by (status=="Profitable" DESC, tafgs_score DESC)
  "Growth % (Highest)"  →  sort by adjusted_growth_pct DESC
  "TAFGS Score"         →  sort by tafgs_score DESC (default)

WHAT TO DO:
1. Loop through every record, compute tafgs_score and fill status.
2. Sort the full list based on ranking_priority.
3. Take the top 20 records: top_20 = sorted_records[:20]
4. Assign ranks: for i, record in enumerate(top_20): record["rank"] = i + 1
5. Return top_20 (NOT the full list — only the Top 20).

INPUT:  list[dict]  — records from Risk Adjustment Agent
        ranking_priority: str — from the sidebar radio button
OUTPUT: list[dict]  — Top 20 records only, tafgs_score and rank filled in

WORKED EXAMPLES:

  NVIDIA:
    moat=5, margin_score=5, adjusted_growth=42.57%
    tafgs = 5 * 5 * 0.4257 = 10.64

  Arista:
    moat=4, margin_score=5, adjusted_growth≈27.72%
    tafgs = 4 * 5 * 0.2772 = 5.54

  Fluor:
    moat=3, margin_score=1, adjusted_growth≈12.15%
    tafgs = 3 * 1 * 0.1215 = 0.36

DO NOT:
- Return more than 20 records.
- Include Efficiency Score in the TAFGS computation.
- Use growth_forecast_pct (raw) — always use adjusted_growth_pct.
- Apply any sidebar discount here — the formula is clean.

CONTROLLER CONTRACT (takes precedence over the earlier placeholder example):
The UI passes its 1.0-2.0 Power Efficiency Weighting slider value as
  power_efficiency_weight. Calculate:
    base_tafgs = moat_score * margin_score * (adjusted_growth_pct / 100)
    efficiency_factor = 1 + ((clamp(eff_score, 1, 5) - 1) / 4) *
                        (clamp(power_efficiency_weight, 1.0, 2.0) - 1)
    tafgs_score = base_tafgs * efficiency_factor
This rewards higher efficiency without applying the risk discount twice.
"""

def run(records: list[dict],
        ranking_priority: str = "TAFGS Score",
        power_efficiency_weight: float = 1.2) -> list[dict]:
    # TODO: implement this agent
    # 1. Loop, compute tafgs_score, fill status
    # 2. Sort by ranking_priority
    # 3. Slice top 20, assign ranks
    # 4. Return top 20
    return records
