"""Attach external, reviewable research evidence to discovered companies."""

from __future__ import annotations

from datetime import datetime, timezone

from services.evidence_store import (
    EvidenceValidationError,
    record_analysis_status,
    research_document_to_evidence,
    store_evidence,
)
from services.research_sources import (
    ResearchSourceError,
    fetch_company_facts,
    fetch_company_research,
)


def _claim(record: dict) -> str:
    return (
        f"External source retrieved for {record.get('company', 'the company')} "
        f"for AI Factory role and growth research."
    )


def enrich_records(records: list[dict]) -> list[dict]:
    """Fetch and persist candidate evidence without auto-verifying any claim.

    Provider failures degrade one record at a time. A company remains eligible
    for CSV-free ranking, but its analysis status communicates that evidence is
    unavailable or needs human review.
    """
    now_iso = datetime.now(timezone.utc).isoformat()

    for record in records:
        documents: list[dict] = list(record.get("discovery_documents", []))
        try:
            facts = fetch_company_facts(record.get("cik", ""))
            if facts.get("operating_margin_pct") is not None:
                record["operating_margin_pct"] = facts["operating_margin_pct"]
            documents.append(facts)
        except (ResearchSourceError, ValueError):
            pass

        try:
            documents.extend(fetch_company_research(record.get("company", "")))
        except (ResearchSourceError, TypeError, ValueError):
            pass

        evidence = []
        for document in documents:
            try:
                evidence.append(research_document_to_evidence(document, claim=_claim(record)))
            except EvidenceValidationError:
                continue
        if evidence:
            try:
                record["evidence"] = store_evidence(record.get("company", ""), evidence)
            except EvidenceValidationError:
                record["evidence"] = evidence
        record["research_as_of"] = now_iso
        record["analysis_status"] = record_analysis_status(record.get("evidence", []))
    return records
