"""
Agent 8: Report Agent
Owner: Dones

GOAL:
Transform the Top 20 ranked company records into display-ready
profile dicts that the Streamlit UI can render directly.
Also generate the Agent Summary text shown at the bottom of the app.

This agent does NOT compute anything new — it only assembles and
formats what the earlier agents already produced.

VARIABLES YOU WILL READ FROM THE RECORD:
- record["rank"]                  →  int
- record["company"]               →  str
- record["role"]                  →  str
- record["moat_score"]            →  int (0–5)
- record["operating_margin_pct"]  →  float
- record["adjusted_growth_pct"]   →  float
- record["eff_score"]             →  int (1–5)
- record["margin_score"]          →  int (1–5)
- record["tafgs_score"]           →  float
- record["status"]                →  str ("Profitable"/"Unprofitable")
- record["concentration_risk"]    →  float (0–1)
- record["cyclicality_risk"]      →  float (0–1)
- record["execution_risk"]        →  float (0–1)
- record["moat_notes"]            →  str (for expandable profile)
- record["growth_catalysts"]      →  str (for expandable profile)
- record["risk_notes"]            →  str (for expandable profile)

VARIABLES YOU WILL FILL PER RECORD:
- record["primary_risk"]  →  str — the label of the HIGHEST risk sub-score
  Logic:
    risk_scores = {
        "Concentration": record["concentration_risk"],
        "Cyclicality":   record["cyclicality_risk"],
        "Execution":     record["execution_risk"],
    }
    primary_risk = max(risk_scores, key=risk_scores.get)

WHAT TO DO:
1. Loop through every record in the Top 20 list.
2. Determine primary_risk using the logic above.
3. Write it into record["primary_risk"].
4. Build a display-ready dict for the UI (see OUTPUT FORMAT below).
5. Append to a profiles list.
6. After the loop, build the agent_summary string.
7. Return (profiles, agent_summary) as a tuple.

OUTPUT FORMAT — each profile dict should have these keys
(these are the exact keys the frontend/components.py expects):
  {
    "company":       record["company"],
    "role":          record["role"],
    "moat":          record["moat_score"],
    "margin_pct":    record["operating_margin_pct"],
    "growth_pct":    record["adjusted_growth_pct"],
    "eff_score":     record["eff_score"],
    "primary_risk":  primary_risk,
    "status":        record["status"],
    "margin_score":  record["margin_score"],
    "tafgs":         record["tafgs_score"],
    # narrative fields for expandable profile view
    "moat_notes":       record["moat_notes"],
    "growth_catalysts": record["growth_catalysts"],
    "risk_notes":       record["risk_notes"],
  }

AGENT SUMMARY STRING FORMAT:
  f"Risk Discount of {risk_discount_pct:.0f}% and
    Power Efficiency Weight of {power_efficiency_weight:.1f}x applied."

  Example output:
  "Risk Discount of 10% and Power Efficiency Weight of 1.2x applied."

INPUT:  list[dict]  — Top 20 ranked records from Ranking Agent
        risk_discount_pct: float — from sidebar (default 10.0)
        power_efficiency_weight: float — from sidebar (default 1.2)
OUTPUT: tuple[list[dict], str]
        — (list of display-ready profile dicts, agent summary string)

DO NOT:
- Recalculate TAFGS, moat, margin, or growth.
- Change the ranking or order of records — preserve the order from
  the Ranking Agent.
- Crash if a risk sub-score is missing — use .get() with default 0.0.
"""

def run(records: list[dict],
        risk_discount_pct: float = 10.0,
        power_efficiency_weight: float = 1.2) -> tuple[list[dict], str]:
    # TODO: implement this agent
    # 1. Loop, determine primary_risk, build profile dict
    # 2. Build agent_summary string
    # 3. Return (profiles, agent_summary)
    return [], ""