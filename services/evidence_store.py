"""IGOT work file: evidence and citation storage.

Follow the TODOs below in order. Keep legacy ``source_links`` compatible.

Goal: make every generated research claim traceable to stored evidence.

1. Use only the evidence-related field names added to `schema.py` by the
   project owner. Do not add, rename, or modify fields in `schema.py`.

    "evidence": [],
    "research_as_of": "",
    "analysis_status": "unavailable",
    "analysis_confidence": None,
    
2. Define an evidence item with at least URL, source title, retrieved date, published date when known, excerpt/claim support, and source type.
3. Implement an evidence-store service that validates URLs, de-duplicates entries, and preserves records by company identifier.
4. Define an explicit status for `verified`, `needs_review`, and `unavailable`; do not label unverified model output as verified.
5. Keep legacy `source_links` readable during the migration.
6. Add contract tests for schema defaults, duplicate evidence, invalid URL rejection, and legacy-row compatibility.

"""

from __future__ import annotations
 
import json
import os
import re
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse
from services.helpers.evidence_store_helpers import _is_valid_url, _is_valid_iso_date
 
from schema import empty_record

EVIDENCE_STATUSES = {"verified", "needs_review", "unavailable"}
RECORD_ANALYSIS_STATUSES = {"unavailable", "fallback", "needs_review", "verified"}
 
SOURCE_TYPES = {
    "10-K", "10-Q", "8-K", "press_release", "earnings_call",
    "analyst_report", "news_article", "company_website", "other",
}
 
REQUIRED_EVIDENCE_FIELDS = ("url", "title", "retrieved_date", "claim", "source_type")

class EvidenceValidationError(ValueError):
    """Raised when an evidence dict is missing required data or malformed."""

def make_evidence_item(
    *,
    url: str = "",
    title: str = "",
    retrieved_date: str = "",
    claim: str = "",
    source_type: str = "",
    excerpt: str = "",
    published_date: Optional[str] = None,
    status: str = "needs_review",
) -> dict:
    """Build and validate a single evidence item.
 
    Raises EvidenceValidationError if the item is incomplete or malformed.
    `status` defaults to "needs_review" -- callers must explicitly pass
    status="verified" after actually confirming the source; this function
    never upgrades a status on its own.
    """
    missing = []
    if not url or not str(url).strip():
        missing.append("url")
    if not title or not str(title).strip():
        missing.append("title")
    if not retrieved_date or not str(retrieved_date).strip():
        missing.append("retrieved_date")
    if not claim or not str(claim).strip():
        missing.append("claim")
    if not source_type or not str(source_type).strip():
        missing.append("source_type")
    if missing:
        raise EvidenceValidationError(
            f"Evidence item missing required field(s): {', '.join(missing)}"
        )
 
    if not _is_valid_url(url):
        raise EvidenceValidationError(f"Evidence item has invalid URL: {url!r}")
 
    if not _is_valid_iso_date(retrieved_date):
        raise EvidenceValidationError(
            f"Evidence item has invalid retrieved_date: {retrieved_date!r}"
        )
 
    if published_date not in (None, "") and not _is_valid_iso_date(published_date):
        raise EvidenceValidationError(
            f"Evidence item has invalid published_date: {published_date!r}"
        )
 
    if source_type not in SOURCE_TYPES:
        raise EvidenceValidationError(
            f"Evidence item has unknown source_type: {source_type!r}. "
            f"Expected one of {sorted(SOURCE_TYPES)}"
        )
 
    if status not in EVIDENCE_STATUSES:
        raise EvidenceValidationError(
            f"Evidence item has invalid status: {status!r}. "
            f"Expected one of {sorted(EVIDENCE_STATUSES)}"
        )
 
    return {
        "url": url.strip(),
        "title": str(title).strip(),
        "retrieved_date": retrieved_date.strip(),
        "published_date": (published_date or "").strip() if published_date else "",
        "excerpt": str(excerpt).strip(),
        "claim": str(claim).strip(),
        "source_type": source_type,
        "status": status,
    }
 
 
def _dedup_key(item: dict) -> tuple:
    """Two evidence items are treated as duplicates when they cite the
    same URL in support of the same claim (case/whitespace-insensitive).
    """
    return (
        item["url"].strip().lower(),
        " ".join(item["claim"].strip().lower().split()),
    )

class EvidenceStore:
    """Persists evidence lists keyed by company identifier.
 
    Backed by a JSON file so records survive process restarts. Pass
    path=":memory:" for a pure in-memory store (used by tests).
    """
 
    def __init__(self, path: str = "evidence_store.json"):
        self.path = path
        self._data: dict[str, list[dict]] = {}
        if path != ":memory:" and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict) and all(
                    isinstance(items, list) for items in loaded.values()
                ):
                    self._data = loaded
            except (OSError, json.JSONDecodeError):
                # A corrupt optional local store must not stop the application.
                self._data = {}
 
    def _persist(self) -> None:
        if self.path == ":memory:":
            return
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, sort_keys=True)
 
    def get(self, company: str) -> list[dict]:
        """Return the stored evidence list for a company (empty if none)."""
        return list(self._data.get(company, []))
 
    def put(self, company: str, evidence: list[dict]) -> list[dict]:
        """Merge new (already-validated) evidence items into a company's
        record, skipping duplicates, and persist the result."""
        if not company or not str(company).strip():
            raise EvidenceValidationError("company identifier is required")
 
        existing = self._data.get(company, [])
        seen = {_dedup_key(e) for e in existing}
        merged = list(existing)
        for item in evidence:
            key = _dedup_key(item)
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
 
        self._data[company] = merged
        self._persist()
        return list(merged)
 
 
# Module-level default store, shared unless a caller supplies their own.
_default_store = EvidenceStore(
    path=os.environ.get("EVIDENCE_STORE_PATH", "evidence_store.json")
)

def store_evidence(
    company: str,
    evidence: list[dict],
    store: Optional[EvidenceStore] = None,
) -> list[dict]:
    """Validate, de-duplicate, and store evidence for one company.
 
    ``evidence`` is a list of raw evidence dicts (e.g. url/title/claim/etc,
    as assembled by a research step). Each item is validated and
    normalized via `make_evidence_item` before being merged into the
    store. Any incomplete or malformed item raises
    `EvidenceValidationError` -- bad evidence is rejected loudly rather
    than silently written into the store or silently dropped.
 
    Returns the full, de-duplicated evidence list now on file for
    `company` (existing entries + newly added ones).
    """
    if not company or not str(company).strip():
        raise EvidenceValidationError("company identifier is required")
    if not isinstance(evidence, list):
        raise EvidenceValidationError("evidence must be a list of dicts")
 
    store = store or _default_store
 
    validated = []
    for raw in evidence:
        if not isinstance(raw, dict):
            raise EvidenceValidationError(f"Evidence item must be a dict, got {type(raw)!r}")
        validated.append(make_evidence_item(**raw))
 
    return store.put(company, validated)


def research_document_to_evidence(
    document: dict,
    *,
    claim: str,
    status: str = "needs_review",
) -> dict:
    """Convert one normalized research document into the evidence contract.

    Research adapters return provider-neutral ``publication_date`` and
    ``retrieved_at`` fields. The evidence contract uses ``published_date`` and
    ``retrieved_date`` and requires a human/agent claim, so the conversion is
    explicit rather than silently marking a document as verified evidence.
    """
    if not isinstance(document, dict):
        raise EvidenceValidationError("research document must be a dictionary")

    source_type = str(document.get("source_type", "")).strip()
    if source_type == "sec_filing":
        title = str(document.get("title", ""))
        source_type = next(
            (form for form in ("10-K", "10-Q", "8-K") if form in title),
            "other",
        )

    retrieved_at = str(document.get("retrieved_at", "")).strip()
    return make_evidence_item(
        url=str(document.get("url", "")),
        title=str(document.get("title", "")),
        retrieved_date=retrieved_at,
        published_date=str(document.get("publication_date", "")),
        excerpt=str(document.get("supporting_text", "")),
        claim=claim,
        source_type=source_type or "other",
        status=status,
    )
 
 
def new_company_record(company: str) -> dict:
    """Convenience wrapper around schema.empty_record() that also fills in
    the company identifier. Does not touch any schema.py field."""
    record = empty_record()
    record["company"] = company
    return record
 
 
def record_analysis_status(evidence: list[dict]) -> str:
    """Derive a company-level `analysis_status` (schema.py field) from a
    list of already-validated evidence items.
 
      - no evidence at all --> "unavailable"
      - evidence exists, none verified --> "needs_review"
      - at least one item is "verified" --> "verified"
 
    Never returns "verified" unless at least one underlying item is
    actually marked verified -- this is what prevents unverified model
    output from being labeled verified at the record level.
    """
    if not evidence:
        return "unavailable"
    if any(item.get("status") == "verified" for item in evidence):
        return "verified"
    return "needs_review"

_LEGACY_SPLIT_RE = re.compile(r"[,;|\n]+")
 
 
def migrate_legacy_source_links(
    source_links: str,
    retrieved_date: str,
) -> list[dict]:
    """Convert a legacy `source_links` string (schema.py field, still
    written by older agent code) into evidence items.
 
    Legacy rows only ever stored a raw string of one or more URLs (often
    comma/pipe/newline separated) with no title, claim, or verification
    info. Each URL becomes an evidence item with status "needs_review"
    (never "verified" -- we have no supporting claim/excerpt to confirm)
    so it stays visible and traceable without overstating confidence.
    Blank/whitespace-only `source_links` yields an empty list.
    """
    if not source_links or not str(source_links).strip():
        return []
 
    urls = [u.strip() for u in _LEGACY_SPLIT_RE.split(source_links) if u.strip()]
 
    items = []
    for url in urls:
        if not _is_valid_url(url):
            continue
        domain = urlparse(url).netloc
        items.append(
            make_evidence_item(
                url=url,
                title=f"Legacy source ({domain})",
                retrieved_date=retrieved_date,
                claim="Migrated from legacy source_links field; claim not recorded.",
                source_type="other",
                status="needs_review",
            )
        )
    return items
 
 
def migrate_legacy_record(record: dict, retrieved_date: str) -> dict:
    """Return a copy of a legacy-style record (schema.py fields) with its
    `source_links` string folded into the new `evidence` list, leaving
    `source_links` itself untouched and still readable.
    """
    updated = dict(record)
    legacy_items = migrate_legacy_source_links(
        record.get("source_links", ""), retrieved_date
    )
    existing_evidence = record.get("evidence") or []
    seen = {_dedup_key(e) for e in existing_evidence}
    merged = list(existing_evidence)
    for item in legacy_items:
        key = _dedup_key(item)
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    updated["evidence"] = merged
    if not updated.get("analysis_status") or updated.get("analysis_status") == "unavailable":
        updated["analysis_status"] = record_analysis_status(merged)
    return updated
