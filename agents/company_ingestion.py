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
