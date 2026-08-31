"""
Agent 8: Report Agent
Owner: Dones

GOAL:
Transform the Top 20 ranked records into display-ready profile dicts
that the Streamlit UI renders directly. Also generate the Agent Summary
text shown at the bottom of the app.

This agent does NOT compute anything new — it only assembles and
formats what the earlier agents already produced.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
- record["status"]                →  str ("Profitable" / "Unprofitable")
- record["concentration_risk"]    →  float (0–1)
- record["cyclicality_risk"]      →  float (0–1)
- record["execution_risk"]        →  float (0–1)
- record["moat_notes"]            →  str
- record["growth_catalysts"]      →  str
- record["risk_notes"]            →  str

VARIABLES YOU WILL FILL PER RECORD:
- record["primary_risk"]  →  str — label of the HIGHEST risk sub-score

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRIMARY RISK LOGIC:
  Pick whichever of the 3 sub-scores is highest:
    risk_scores = {
        "Concentration": record.get("concentration_risk", 0.0),
        "Cyclicality":   record.get("cyclicality_risk",   0.0),
        "Execution":     record.get("execution_risk",     0.0),
    }
    primary_risk = max(risk_scores, key=risk_scores.get)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT TO DO:
1. Loop through every record in the Top 20 list.
2. Determine primary_risk using the logic above.
3. Write it into record["primary_risk"].
4. Build a display-ready profile dict (see OUTPUT FORMAT below).
5. Append to profiles list.
6. After the loop, build the agent_summary string.
7. Return (profiles, agent_summary) as a tuple.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT — exact keys expected by frontend/components.py:
  {
    "company":          record["company"],
    "role":             record["role"],
    "moat":             record["moat_score"],
    "margin_pct":       record["operating_margin_pct"],
    "growth_pct":       record["adjusted_growth_pct"],
    "eff_score":        record["eff_score"],
    "primary_risk":     primary_risk,
    "status":           record["status"],
    "margin_score":     record["margin_score"],
    "tafgs":            record["tafgs_score"],
    "moat_notes":       record["moat_notes"],
    "growth_catalysts": record["growth_catalysts"],
    "risk_notes":       record["risk_notes"],
  }

AGENT SUMMARY STRING FORMAT:
  f"Risk Discount of {risk_discount_pct:.0f}% and Power Efficiency
    Weight of {power_efficiency_weight:.1f}x applied globally across scores."

  Example at defaults (risk=10%, weight=1.2x):
    "Risk Discount of 10% and Power Efficiency Weight of 1.2x applied
     globally across scores."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORKED EXAMPLES:

  NVIDIA (NVDA) — concentration_risk=0.8, cyclicality=0.3, execution=0.3:
    risk_scores  = {"Concentration": 0.8, "Cyclicality": 0.3, "Execution": 0.3}
    primary_risk = "Concentration"  (highest value)

  Fluor (FLR) — concentration_risk=0.5, cyclicality=0.6, execution=0.8:
    risk_scores  = {"Concentration": 0.5, "Cyclicality": 0.6, "Execution": 0.8}
    primary_risk = "Execution"  (highest value)

  GE Vernova (GEV) — concentration_risk=0.5, cyclicality=0.7, execution=0.5:
    risk_scores  = {"Concentration": 0.5, "Cyclicality": 0.7, "Execution": 0.5}
    primary_risk = "Cyclicality"  (highest value)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INPUT:  list[dict]  — Top 20 ranked records from Ranking Agent
        risk_discount_pct: float — from sidebar (default 10.0)
        power_efficiency_weight: float — from sidebar (default 1.2)
OUTPUT: tuple[list[dict], str]
        — (list of display-ready profile dicts, agent summary string)

DO NOT:
- Recalculate TAFGS, moat, margin, or growth.
- Change the order of records — preserve ranking from Ranking Agent.
- Crash if a risk sub-score is missing — use .get() with default 0.0.
"""


def run(records: list[dict],
        risk_discount_pct: float = 10.0,
        power_efficiency_weight: float = 1.2) -> tuple[list[dict], str]:
    """Build display profiles and a summary without changing ranking order."""
    profiles = []

    for record in records:
        primary_risk = _primary_risk(record)
        record["primary_risk"] = primary_risk

        profiles.append(
            {
                "company": record.get("company", ""),
                "role": record.get("role", ""),
                "short_description": record.get("short_description", ""),
                "revenue_exposure_pct": record.get("revenue_exposure_pct", 0.0),
                "segment_weight": record.get("segment_weight", 0.0),
                "moat": record.get("moat_score", 0),
                "margin_pct": record.get("operating_margin_pct", 0.0),
                "growth_pct": record.get("adjusted_growth_pct", 0.0),
                "eff_score": record.get("eff_score", 0),
                "primary_risk": primary_risk,
                "status": record.get("status", ""),
                "margin_score": record.get("margin_score", 0),
                "tafgs": record.get("tafgs_score", 0.0),
                "moat_notes": record.get("moat_notes", ""),
                "growth_catalysts": record.get("growth_catalysts", ""),
                "risk_notes": record.get("risk_notes", ""),
                "source_links": record.get("source_links", ""),
            }
        )

    agent_summary = (
        f"Risk Discount of {risk_discount_pct:.0f}% and Power Efficiency "
        f"Weight of {power_efficiency_weight:.1f}x applied globally across scores."
    )
    return profiles, agent_summary


def _primary_risk(record: dict) -> str:
    """Return the highest-scoring risk label in the documented tie order."""
    risk_scores = {
        "Concentration": _risk_score(record.get("concentration_risk", 0.0)),
        "Cyclicality": _risk_score(record.get("cyclicality_risk", 0.0)),
        "Execution": _risk_score(record.get("execution_risk", 0.0)),
    }
    return max(risk_scores, key=risk_scores.get)


def _risk_score(value) -> float:
    """Convert a risk value to a float without failing on incomplete records."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
