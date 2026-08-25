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


def _parse_pct(value) -> float:
    """
    Extract the first valid float from a string like '~89.70% Direct...' or '-2.2'.
    Falls back to direct float conversion or regex matching.
    """
    if pd.isna(value):
        return 0.0
    try:
        return float(str(value).replace("%", "").strip())
    except (ValueError, TypeError):
        # Match positive or negative floats/ints
        match = re.search(r"[-+]?\d*\.?\d+", str(value))
        return float(match.group()) if match else 0.0


def _to_float(value, default: float = 0.0) -> float:
    """Safe float parser with default fallback."""
    try:
        return float(value) if not pd.isna(value) else default
    except (ValueError, TypeError):
        return default


def _to_int(value, default: int = 0) -> int:
    """Safe int parser with default fallback."""
    try:
        return int(float(value)) if not pd.isna(value) else default
    except (ValueError, TypeError):
        return default


def _to_str(value, default: str = "") -> str:
    """Safe string parser that cleans NaN/empty entries."""
    if pd.isna(value):
        return default
    val_str = str(value).strip()
    return "" if val_str.lower() == "nan" else val_str


def run(csv_path: str = "data/companies.csv") -> list[dict]:
    """
    Reads the company CSV, validates required columns, maps fields to schema,
    and returns a list of standardized company record dictionaries.
    """
    df = pd.read_csv(csv_path)

    # 1. Validate required columns exist
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in CSV: {missing_cols}")

    records = []

    # 2. Iterate and map to schema
    for _, row in df.iterrows():
        company_raw = row.get("Company Name + Ticker")
        company = _to_str(company_raw)

        # Skip rows where company is blank or empty
        if not company:
            continue

        record = empty_record()

        # String fields
        record["company"] = company
        record["role"] = _to_str(row.get("Primary AI Factory Role"))
        record["short_description"] = _to_str(row.get("Short Description"))
        record["moat_notes"] = _to_str(row.get("Moat Notes"))
        record["growth_catalysts"] = _to_str(row.get("Growth Catalysts"))
        record["risk_notes"] = _to_str(row.get("Risk Notes"))
        record["source_links"] = _to_str(row.get("Source Links"))

        # Numeric / Percentage fields
        record["operating_margin_pct"] = _to_float(row.get("Operating Margin %"))
        record["revenue_exposure_pct"] = _parse_pct(row.get("Revenue Exposure %"))
        record["moat_score"] = _to_int(row.get("Moat Score"))
        record["growth_forecast_pct"] = _to_float(row.get("Growth Forecast %"))
        record["concentration_risk"] = _to_float(row.get("Concentration Risk"))
        record["cyclicality_risk"] = _to_float(row.get("Cyclicality Risk"))
        record["execution_risk"] = _to_float(row.get("Execution Risk"))
        record["eff_score"] = _to_int(row.get("Efficiency Score"))

        records.append(record)

    return records
