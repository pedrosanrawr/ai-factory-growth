"""IGOT work file: evidence and citation storage.

Follow the TODOs below in order. Keep legacy ``source_links`` compatible.

Goal: make every generated research claim traceable to stored evidence.

1. Propose new shared fields before editing `schema.py`; use additive fields such as `evidence`, `research_as_of`, and `analysis_status` rather than renaming current fields.
2. Define an evidence item with at least URL, source title, retrieved date, published date when known, excerpt/claim support, and source type.
3. Implement an evidence-store service that validates URLs, de-duplicates entries, and preserves records by company identifier.
4. Define an explicit status for `verified`, `needs_review`, and `unavailable`; do not label unverified model output as verified.
5. Keep legacy `source_links` readable during the migration.
6. Add contract tests for schema defaults, duplicate evidence, invalid URL rejection, and legacy-row compatibility.

"""

def store_evidence(company: str, evidence: list[dict]) -> list[dict]:
    """Validate, de-duplicate, and store evidence for one company."""
    # TODO(1): Agree additive schema fields with the team before editing schema.py.
    # TODO(2): Define required evidence fields: URL, title, dates, source type,
    #          excerpt, and supported claim.
    # TODO(3): Validate URLs and reject incomplete evidence safely.
    # TODO(4): Store entries by company and de-duplicate matching evidence.
    # TODO(5): Add verified, needs_review, and unavailable status handling.
    # TODO(6): Test schema defaults, invalid URLs, duplicates, and CSV migration.
    pass
