"""
Agent 2: Company Ingestion Agent
Owner: Valdez

GOAL:
Load the 20 Companies CSV file and convert each row into a structured
company record that matches our shared schema. This is the FIRST agent
in the pipeline — all other agents depend on the output of this one,
so it must run before everything else.

CSV FILE LOCATION:
  data/companies.csv

CSV COLUMNS YOU WILL READ (these are the exact column names in the CSV):
  - "Company Name + Ticker"     → record["company"]
  - "Primary AI Factory Role"   → record["role"]
  - "Short Description"         → record["short_description"]
  - "Operating Margin %"        → record["operating_margin_pct"]   (float)
  - "Revenue Exposure %"        → record["revenue_exposure_pct"]   (float — see note below)
  - "Moat Notes"                → record["moat_notes"]
  - "Growth Catalysts"          → record["growth_catalysts"]
  - "Risk Notes"                → record["risk_notes"]
  - "Source Links"              → record["source_links"]
  - "Moat Score"                → record["moat_score"]             (int, 0–5)
  - "Growth Forecast %"         → record["growth_forecast_pct"]    (float)
  - "Concentration Risk"        → record["concentration_risk"]     (float, 0–1)
  - "Cyclicality Risk"          → record["cyclicality_risk"]       (float, 0–1)
  - "Execution Risk"            → record["execution_risk"]         (float, 0–1)
  - "Efficiency Score"          → record["eff_score"]              (int, 1–5)

IMPORTANT NOTE ON "Revenue Exposure %":
  This column contains text like "~89.70% Direct (...)" not a plain number.
  You need to extract just the first number from the string using a helper.
  Example: "~89.70% Direct..." → 89.70
  Use this helper:
    import re
    def parse_pct(value):
        match = re.search(r'[\d.]+', str(value))
        return float(match.group()) if match else 0.0

WHAT TO DO:
1. Import pandas and re.
2. Import empty_record from schema.
3. Read the CSV: df = pd.read_csv(csv_path)
4. Check that required columns exist — raise ValueError if any are missing.
5. Loop through each row with: for _, row in df.iterrows():
6. Create a blank record: record = empty_record()
7. Map each CSV column to the correct schema field (see list above).
8. Skip rows where "Company Name + Ticker" is blank or "nan".
9. Append valid records to a list.
10. Return the list.

INPUT:  csv_path: str = "data/companies.csv"
OUTPUT: list[dict]  — list of company records, one per CSV row

EXAMPLE OUTPUT (one record):
{
  "company":               "NVIDIA Corporation (NVDA)",
  "role":                  "Compute/Server",
  "short_description":     "Pioneered accelerated computing...",
  "operating_margin_pct":  60.38,
  "revenue_exposure_pct":  89.70,
  "moat_notes":            "Architectural Lock-In: CUDA...",
  "growth_catalysts":      "Backlog Growth: ~$1 trillion...",
  "risk_notes":            "Concentration: Two customers...",
  "source_links":          "https://...",
  "moat_score":            5,
  "growth_forecast_pct":   45.0,
  "concentration_risk":    0.8,
  "cyclicality_risk":      0.3,
  "execution_risk":        0.3,
  "eff_score":             5,
  # all other schema fields remain at their default values (0, 0.0, "")
}

DO NOT:
- Hard-code any company data — always read from the CSV.
- Return records with missing required fields.
- Crash if a numeric field has a typo — use try/except and default to 0.0.
"""

import re
import pandas as pd
from schema import empty_record

REQUIRED_COLUMNS = [
    "Company Name + Ticker",
    "Primary AI Factory Role",
    "Operating Margin %",
    "Moat Score",
    "Growth Forecast %",
    "Concentration Risk",
    "Cyclicality Risk",
    "Execution Risk",
    "Efficiency Score",
]

def run(csv_path: str = "data/companies.csv") -> list[dict]:
    # TODO: implement this agent
    # 1. Read CSV
    # 2. Validate required columns
    # 3. Loop rows, create empty_record(), map fields, append
    # 4. Return list
    return []


def _parse_pct(value) -> float:
    """Extract the first number from a string like '~89.70% Direct...'"""
    try:
        return float(str(value).replace("%", "").strip())
    except (ValueError, TypeError):
        match = re.search(r'[\d.]+', str(value))
        return float(match.group()) if match else 0.0