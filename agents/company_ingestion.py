"""
Agent 2: Company Ingestion Agent
Owner: Valdez

GOAL:
Load the 20 Companies CSV and convert each row into a structured
company record matching our shared schema. This is the FIRST agent
in the pipeline — all other agents depend on its output.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CSV FILE LOCATION:
  data/companies.csv

CSV COLUMNS → SCHEMA FIELDS (exact mapping):
  "Company Name + Ticker"   → record["company"]               str
  "Primary AI Factory Role" → record["role"]                  str
  "Short Description"       → record["short_description"]     str
  "Operating Margin %"      → record["operating_margin_pct"]  float
  "Revenue Exposure %"      → record["revenue_exposure_pct"]  float  *
  "Moat Notes"              → record["moat_notes"]            str
  "Growth Catalysts"        → record["growth_catalysts"]      str
  "Risk Notes"              → record["risk_notes"]            str
  "Source Links"            → record["source_links"]          str
  "Moat Score"              → record["moat_score"]            int
  "Growth Forecast %"       → record["growth_forecast_pct"]   float
  "Concentration Risk"      → record["concentration_risk"]    float
  "Cyclicality Risk"        → record["cyclicality_risk"]      float
  "Execution Risk"          → record["execution_risk"]        float
  "Efficiency Score"        → record["eff_score"]             int

  * "Revenue Exposure %" contains text like "~89.70% Direct (...)"
    Use _parse_pct() helper below to extract just the number.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT TO DO:
1. Import pandas and re.
2. Import empty_record from schema.
3. Read the CSV: df = pd.read_csv(csv_path)
4. Check required columns exist — raise ValueError if missing.
5. Loop: for _, row in df.iterrows():
6. Create blank record: record = empty_record()
7. Map each CSV column to the correct schema field.
8. Skip rows where "Company Name + Ticker" is blank or "nan".
9. Append valid records to a list.
10. Return the list.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORKED EXAMPLES:

  NVIDIA row in CSV:
    "Company Name + Ticker"   = "NVIDIA Corporation (NVDA)"
    "Primary AI Factory Role" = "Compute/Server"
    "Operating Margin %"      = 60.38
    "Revenue Exposure %"      = "~89.70% Direct (...)"  → parse → 89.70
    "Moat Score"              = 5
    "Growth Forecast %"       = 45.0
    "Efficiency Score"        = 5

  Output record (partial):
    record["company"]              = "NVIDIA Corporation (NVDA)"
    record["role"]                 = "Compute/Server"
    record["operating_margin_pct"] = 60.38
    record["revenue_exposure_pct"] = 89.70
    record["moat_score"]           = 5
    record["growth_forecast_pct"]  = 45.0
    record["eff_score"]            = 5

  Blank row handling:
    "Company Name + Ticker" = "" or "nan" → skip this row entirely

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INPUT:  csv_path: str = "data/companies.csv"
OUTPUT: list[dict]  — one record per valid CSV row

DO NOT:
- Hard-code any company data — always read from the CSV.
- Crash if a numeric field has a typo — use try/except, default to 0.0.
- Return records with "Company Name + Ticker" blank or "nan".
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
    """
    Extract the first number from a string like '~89.70% Direct...'.
    Falls back to direct float conversion for plain numbers like '60.38'.
    """
    try:
        return float(str(value).replace("%", "").strip())
    except (ValueError, TypeError):
        match = re.search(r'[\d.]+', str(value))
        return float(match.group()) if match else 0.0