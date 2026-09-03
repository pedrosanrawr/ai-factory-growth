"""Run cached Gemini analysis offline and publish a local dashboard snapshot."""

from __future__ import annotations

import argparse

from agents.company_ingestion import run as ingest_companies
from agents.research_analysis import run as analyze_research
from services.llm_client import is_llm_configured
from services.research_snapshot import load_snapshot, snapshot_entry, write_snapshot


def _select_batch(records: list[dict], batch_size: int, batch_number: int) -> list[dict]:
    """Return one 1-indexed batch while preserving the ranked CSV ordering."""
    if batch_size < 1:
        raise ValueError("--batch-size must be at least 1")
    if batch_number < 1:
        raise ValueError("--batch-number must be at least 1")
    start = (batch_number - 1) * batch_size
    return records[start:start + batch_size]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", default="data/companies.csv")
    parser.add_argument("--output", default="data/research_snapshots/latest.json")
    parser.add_argument("--batch-size", type=int, default=5, help="Companies to analyze per run (default: 5).")
    parser.add_argument("--batch-number", type=int, default=1, help="1-indexed company batch to analyze (default: 1).")
    args = parser.parse_args(argv)

    if not is_llm_configured():
        print("Gemini is not configured; the existing research snapshot was left unchanged.")
        return 0

    records = ingest_companies(args.input_csv)
    try:
        batch = _select_batch(records, args.batch_size, args.batch_number)
    except ValueError as error:
        parser.error(str(error))
    analyzed = analyze_research(batch)
    snapshots = load_snapshot(args.output)
    updated = 0
    failures = []
    for record in analyzed:
        if record.get("_combined_llm_analysis"):
            snapshots[str(record.get("company", ""))] = snapshot_entry(record)
            updated += 1
        elif record.get("_combined_llm_error"):
            failures.append(str(record["_combined_llm_error"]))
    write_snapshot(snapshots, args.output)
    print(f"Published {updated} cached Gemini analysis snapshot(s) from batch {args.batch_number} ({len(batch)} company record(s)).")
    if failures:
        print(f"Gemini could not analyze {len(failures)} company record(s): {failures[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
