import re
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from schema import empty_record
from services.evidence_store import EvidenceStore, migrate_legacy_record, record_analysis_status
from services.research_snapshot import apply_snapshot, load_snapshot

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

DEFAULT_COMPANY_CSV = Path(__file__).resolve().parents[1] / "data" / "companies.csv"


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


def _run_csv_fixture(csv_path: str, evidence_store: EvidenceStore | None = None) -> list[dict]:
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
    snapshots = load_snapshot()
    csv_snapshot_date = datetime.fromtimestamp(
        Path(csv_path).stat().st_mtime, timezone.utc
    ).date().isoformat()
    evidence_store = evidence_store or EvidenceStore(
        path=os.environ.get("EVIDENCE_STORE_PATH", "evidence_store.json")
    )

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

        # Evidence is joined from the approved local store only. This keeps
        # dashboard ingestion fast and avoids any live research request.
        evidence = evidence_store.get(company)
        if evidence:
            record["evidence"] = evidence
            record["analysis_status"] = record_analysis_status(evidence)
            record["research_as_of"] = max(
                (str(item.get("retrieved_date", "")) for item in evidence),
                default="",
            )
        else:
            # Existing CSV source links are usable as unverified evidence for
            # offline analysis without fetching anything during dashboard load.
            record = migrate_legacy_record(record, csv_snapshot_date)

        apply_snapshot(record, snapshots)

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


def run(
    csv_path: str | Path | None = None,
    *,
    evidence_store: EvidenceStore | None = None,
) -> list[dict]:
    """Load the predefined company universe from the curated CSV file.

    The CSV is the single ingestion input, so dashboard runs are immediate and
    repeatable. Company-universe changes are made by updating the CSV.
    """
    return _run_csv_fixture(str(csv_path or DEFAULT_COMPANY_CSV), evidence_store)
