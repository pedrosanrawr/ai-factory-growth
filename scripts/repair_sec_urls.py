"""Repair legacy SEC archive URLs that use dashed accession directories."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SEC_ARCHIVE_URL = re.compile(
    r"(https://www\.sec\.gov/Archives/edgar/data/\d+/)(\d{10})-?(\d{2})-?(\d{6})/[^?#/]+"
)


def repair_url(url: str) -> str:
    """Use a stable SEC filing index page for legacy archive URLs."""
    def replacement(match: re.Match) -> str:
        accession = f"{match.group(2)}-{match.group(3)}-{match.group(4)}"
        return f"{match.group(1)}{match.group(2)}{match.group(3)}{match.group(4)}/{accession}-index.htm"

    return SEC_ARCHIVE_URL.sub(replacement, str(url))


def _repair_value(value: Any) -> tuple[Any, int]:
    if isinstance(value, str):
        repaired = repair_url(value)
        return repaired, int(repaired != value)
    if isinstance(value, list):
        repaired_items, changes = [], 0
        for item in value:
            repaired, count = _repair_value(item)
            repaired_items.append(repaired)
            changes += count
        return repaired_items, changes
    if isinstance(value, dict):
        repaired_items, changes = {}, 0
        for key, item in value.items():
            repaired, count = _repair_value(item)
            repaired_items[key] = repaired
            changes += count
        return repaired_items, changes
    return value, 0


def _backup(path: Path, backup_root: Path) -> None:
    backup_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup_root / path.name)


def repair_json_file(path: Path, *, apply: bool, backup_root: Path) -> int:
    payload = json.loads(path.read_text(encoding="utf-8"))
    repaired, changes = _repair_value(payload)
    if changes and apply:
        _backup(path, backup_root)
        path.write_text(json.dumps(repaired, indent=2, sort_keys=True), encoding="utf-8")
    return changes


def repair_csv_file(path: Path, *, apply: bool, backup_root: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        fieldnames = reader.fieldnames
    if not fieldnames or "Source Links" not in fieldnames:
        return 0
    changes = 0
    for row in rows:
        repaired = repair_url(row.get("Source Links", ""))
        if repaired != row.get("Source Links", ""):
            row["Source Links"] = repaired
            changes += 1
    if changes and apply:
        _backup(path, backup_root)
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    return changes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write repairs after backing up affected files.")
    parser.add_argument("--evidence-store", default="evidence_store.json")
    parser.add_argument("--cache-dir", default=".cache/research_sources")
    parser.add_argument("--companies-csv", default="data/companies.csv")
    parser.add_argument("--backup-dir", default=None)
    args = parser.parse_args(argv)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = Path(args.backup_dir or f"backups/sec_url_repair_{stamp}")
    files = [Path(args.evidence_store), Path(args.companies_csv)]
    cache_dir = Path(args.cache_dir)
    files.extend(cache_dir.glob("*.json") if cache_dir.exists() else [])
    total = 0
    for path in files:
        if not path.exists():
            continue
        if path.suffix.lower() == ".csv":
            total += repair_csv_file(path, apply=args.apply, backup_root=backup_root)
        else:
            total += repair_json_file(path, apply=args.apply, backup_root=backup_root)
    action = "Repaired" if args.apply else "Would repair"
    print(f"{action} {total} legacy SEC URL(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
