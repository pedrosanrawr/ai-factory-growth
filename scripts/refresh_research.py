"""Stage and approve a reviewable refresh of company research evidence."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from services import research_sources
from services.evidence_store import EvidenceStore, EvidenceValidationError, make_evidence_item, record_analysis_status


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _evidence_source_type(document: dict) -> str:
    source_type = str(document.get("source_type", "")).strip()
    if source_type != "sec_filing":
        supported = {"press_release", "earnings_call", "analyst_report", "news_article", "company_website", "other"}
        return source_type if source_type in supported else "other"
    title = str(document.get("title", ""))
    return next((form for form in ("10-K", "10-Q", "8-K") if form in title), "other")


def _document_to_evidence_kwargs(company: str, document: dict, retrieved_date: str) -> dict:
    """Map a normalized source document into the validated evidence format."""
    return {
        "url": str(document.get("url", "")).strip(),
        "title": str(document.get("title", "")).strip(),
        "retrieved_date": retrieved_date,
        "published_date": str(document.get("publication_date", "")).strip(),
        "excerpt": str(document.get("supporting_text", "")).strip(),
        "claim": f"Candidate source retrieved for {company} AI Factory research.",
        "source_type": _evidence_source_type(document),
        "status": "needs_review",
    }


def _evidence_key(item: dict) -> tuple[str, str]:
    return str(item.get("url", "")).strip().lower(), " ".join(str(item.get("claim", "")).strip().lower().split())


def build_change_report(companies: list[str], store: EvidenceStore) -> dict:
    """Collect candidate evidence without mutating the CSV or evidence store."""
    generated_at = _utc_now()
    retrieved_date = generated_at.split("T", 1)[0]
    results = []
    for company in companies:
        existing = store.get(company)
        known = {_evidence_key(item) for item in existing}
        candidates = []
        try:
            # Staging skips the local cache so a dry run has no hidden writes.
            documents = research_sources.fetch_company_research(company, use_cache=False)
        except (research_sources.ResearchSourceError, TypeError, ValueError):
            documents = []
        for document in documents:
            try:
                item = make_evidence_item(**_document_to_evidence_kwargs(company, document, retrieved_date))
            except EvidenceValidationError:
                continue
            if _evidence_key(item) not in known:
                known.add(_evidence_key(item))
                candidates.append(item)
        combined = [*existing, *candidates]
        results.append({
            "company": company,
            "analysis_status": "needs_review" if candidates else ("no_change" if existing else "unavailable"),
            "existing_evidence_count": len(existing),
            "new_evidence_count": len(candidates),
            "candidate_evidence": candidates,
            "resulting_analysis_status": record_analysis_status(combined),
        })
    return {
        "generated_at": generated_at,
        "research_as_of": retrieved_date,
        "companies": results,
        "summary": {
            "companies_checked": len(results),
            "companies_with_new_evidence": sum(item["new_evidence_count"] > 0 for item in results),
            "new_evidence_count": sum(item["new_evidence_count"] for item in results),
        },
    }


def write_report(report: dict, path: str | Path) -> None:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def _backup(path: Path, backup_dir: Path) -> str | None:
    if not path.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    suffix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"{path.name}.{suffix}.bak"
    shutil.copy2(path, backup_path)
    return str(backup_path)


def apply_approved_write(report: dict, *, input_csv: str | Path, evidence_store_path: str | Path, backup_dir: str | Path) -> dict:
    """Persist staged evidence after creating backups of every changed file."""
    csv_path, store_path, backups = Path(input_csv), Path(evidence_store_path), Path(backup_dir)
    csv_backup = _backup(csv_path, backups)
    evidence_store_backup = _backup(store_path, backups)
    store = EvidenceStore(path=str(store_path))
    approved = {
        str(item.get("company", "")): item.get("candidate_evidence", [])
        for item in report.get("companies", [])
        if item.get("candidate_evidence")
    }
    with csv_path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
        fieldnames = list(rows[0].keys()) if rows else []
    if "Source Links" not in fieldnames:
        raise ValueError("Input CSV must contain a Source Links column")
    for row in rows:
        candidates = approved.get(str(row.get("Company Name + Ticker", "")), [])
        if not candidates:
            continue
        merged = store.put(str(row["Company Name + Ticker"]), candidates)
        urls = [str(item["url"]).strip() for item in merged if item.get("url")]
        row["Source Links"] = "|".join(dict.fromkeys(urls))
    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return {"csv_backup": csv_backup, "evidence_store_backup": evidence_store_backup, "updated_companies": len(approved)}


def _companies_from_csv(path: str | Path) -> list[str]:
    with Path(path).open("r", encoding="utf-8", newline="") as file:
        return [str(row.get("Company Name + Ticker", "")).strip() for row in csv.DictReader(file) if str(row.get("Company Name + Ticker", "")).strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", default="data/companies.csv")
    parser.add_argument("--evidence-store", default="evidence_store.json")
    parser.add_argument("--output-report")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approve-write", action="store_true")
    parser.add_argument("--from-report")
    parser.add_argument("--backup-dir", default="backups")
    args = parser.parse_args(argv)
    if args.approve_write:
        if not args.from_report:
            parser.error("--approve-write requires --from-report")
        report = json.loads(Path(args.from_report).read_text(encoding="utf-8"))
        apply_approved_write(report, input_csv=args.input_csv, evidence_store_path=args.evidence_store, backup_dir=args.backup_dir)
        return 0
    report = build_change_report(_companies_from_csv(args.input_csv), EvidenceStore(args.evidence_store))
    if not args.dry_run:
        output = args.output_report or Path("data/refresh_reports") / f"research_refresh_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
        write_report(report, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
