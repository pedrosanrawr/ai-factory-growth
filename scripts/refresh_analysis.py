"""Run cached Gemini analysis offline and publish a local dashboard snapshot."""

from __future__ import annotations

import argparse

from agents.company_ingestion import run as ingest_companies
from agents.research_analysis import run as analyze_research
from services.llm_client import is_llm_configured
from services.research_snapshot import load_snapshot, snapshot_entry, write_snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", default="data/companies.csv")
    parser.add_argument("--output", default="data/research_snapshots/latest.json")
    args = parser.parse_args(argv)

    if not is_llm_configured():
        print("Gemini is not configured; the existing research snapshot was left unchanged.")
        return 0

    records = ingest_companies(args.input_csv)
    analyzed = analyze_research(records)
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
    print(f"Published {updated} cached Gemini analysis snapshot(s).")
    if failures:
        print(f"Gemini could not analyze {len(failures)} company record(s): {failures[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
