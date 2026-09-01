"""Contract tests for evidence_store.py.

Covers: schema defaults, duplicate evidence, invalid URL rejection, and
legacy source_links compatibility, per the work-file TODOs.
"""
import pytest

from schema import empty_record
from services.evidence_store import (
    EvidenceStore,
    EvidenceValidationError,
    make_evidence_item,
    migrate_legacy_record,
    migrate_legacy_source_links,
    new_company_record,
    record_analysis_status,
    store_evidence,
)


VALID_ITEM_KWARGS = dict(
    url="https://www.sec.gov/company/10k",
    title="Company 10-K FY2025",
    retrieved_date="2026-08-01",
    claim="Revenue grew 12% year over year.",
    source_type="10-K",
    excerpt="Revenue increased 12% to $1.2B.",
    published_date="2026-02-15",
)


# --------------------------------------------------------------------------
# 1. Schema defaults
# --------------------------------------------------------------------------

def test_schema_defaults_are_untouched():
    record = empty_record()
    assert record["evidence"] == []
    assert record["research_as_of"] == ""
    assert record["analysis_status"] == "unavailable"
    assert record["analysis_confidence"] is None
    # legacy field still present and untouched
    assert record["source_links"] == ""


def test_new_company_record_only_sets_company():
    record = new_company_record("Acme Corp")
    baseline = empty_record()
    baseline["company"] = "Acme Corp"
    assert record == baseline


# --------------------------------------------------------------------------
# 2 & 3. Evidence item shape + URL validation
# --------------------------------------------------------------------------

def test_make_evidence_item_success():
    item = make_evidence_item(**VALID_ITEM_KWARGS)
    assert item["url"] == VALID_ITEM_KWARGS["url"]
    assert item["title"] == VALID_ITEM_KWARGS["title"]
    assert item["retrieved_date"] == VALID_ITEM_KWARGS["retrieved_date"]
    assert item["published_date"] == VALID_ITEM_KWARGS["published_date"]
    assert item["excerpt"] == VALID_ITEM_KWARGS["excerpt"]
    assert item["claim"] == VALID_ITEM_KWARGS["claim"]
    assert item["source_type"] == "10-K"
    # default status must never be "verified" unless explicitly requested
    assert item["status"] == "needs_review"


@pytest.mark.parametrize("bad_url", ["", "not-a-url", "ftp://example.com/x", "www.example.com"])
def test_invalid_url_rejection(bad_url):
    kwargs = dict(VALID_ITEM_KWARGS)
    kwargs["url"] = bad_url
    with pytest.raises(EvidenceValidationError):
        make_evidence_item(**kwargs)


def test_missing_required_field_rejection():
    kwargs = dict(VALID_ITEM_KWARGS)
    del kwargs["title"]
    with pytest.raises(EvidenceValidationError):
        make_evidence_item(**kwargs)


def test_unknown_source_type_rejection():
    kwargs = dict(VALID_ITEM_KWARGS)
    kwargs["source_type"] = "tweet"
    with pytest.raises(EvidenceValidationError):
        make_evidence_item(**kwargs)


def test_store_evidence_rejects_bad_url_end_to_end():
    store = EvidenceStore(path=":memory:")
    bad = dict(VALID_ITEM_KWARGS)
    bad["url"] = "not-a-url"
    with pytest.raises(EvidenceValidationError):
        store_evidence("Acme Corp", [bad], store=store)
    # nothing should have been written
    assert store.get("Acme Corp") == []


def test_store_evidence_never_auto_verifies():
    store = EvidenceStore(path=":memory:")
    result = store_evidence("Acme Corp", [VALID_ITEM_KWARGS], store=store)
    assert result[0]["status"] == "needs_review"


# --------------------------------------------------------------------------
# 4. Duplicate evidence handling, preserved by company identifier
# --------------------------------------------------------------------------

def test_duplicate_evidence_is_deduped():
    store = EvidenceStore(path=":memory:")
    store_evidence("Acme Corp", [VALID_ITEM_KWARGS], store=store)
    result = store_evidence("Acme Corp", [VALID_ITEM_KWARGS], store=store)
    assert len(result) == 1


def test_evidence_isolated_per_company():
    store = EvidenceStore(path=":memory:")
    store_evidence("Acme Corp", [VALID_ITEM_KWARGS], store=store)
    other_kwargs = dict(VALID_ITEM_KWARGS)
    other_kwargs["url"] = "https://www.sec.gov/other/10k"
    store_evidence("Other Inc", [other_kwargs], store=store)

    assert len(store.get("Acme Corp")) == 1
    assert len(store.get("Other Inc")) == 1
    assert store.get("Acme Corp")[0]["url"] != store.get("Other Inc")[0]["url"]


def test_different_claim_same_url_is_not_a_duplicate():
    store = EvidenceStore(path=":memory:")
    store_evidence("Acme Corp", [VALID_ITEM_KWARGS], store=store)
    second_kwargs = dict(VALID_ITEM_KWARGS)
    second_kwargs["claim"] = "Operating margin expanded to 24%."
    result = store_evidence("Acme Corp", [second_kwargs], store=store)
    assert len(result) == 2


# --------------------------------------------------------------------------
# 5 & 6. Legacy source_links compatibility
# --------------------------------------------------------------------------

def test_migrate_legacy_source_links_basic():
    legacy = "https://example.com/a, https://example.com/b|https://example.com/c"
    items = migrate_legacy_source_links(legacy, retrieved_date="2026-08-01")
    assert len(items) == 3
    urls = {item["url"] for item in items}
    assert urls == {
        "https://example.com/a",
        "https://example.com/b",
        "https://example.com/c",
    }
    # legacy data has no confirmed claim, so it must never be "verified"
    assert all(item["status"] == "needs_review" for item in items)


def test_migrate_legacy_source_links_skips_garbage_without_raising():
    legacy = "https://example.com/a, not-a-url, "
    items = migrate_legacy_source_links(legacy, retrieved_date="2026-08-01")
    assert len(items) == 1
    assert items[0]["url"] == "https://example.com/a"


def test_migrate_legacy_source_links_empty():
    assert migrate_legacy_source_links("", "2026-08-01") == []
    assert migrate_legacy_source_links("   ", "2026-08-01") == []


def test_legacy_row_compatibility_full_record():
    legacy_record = empty_record()
    legacy_record["company"] = "Legacy Co"
    legacy_record["source_links"] = "https://example.com/legacy1, https://example.com/legacy2"
    # legacy row predates the evidence field entirely
    legacy_record["evidence"] = []

    migrated = migrate_legacy_record(legacy_record, retrieved_date="2026-08-01")

    # source_links stays intact and readable
    assert migrated["source_links"] == legacy_record["source_links"]
    assert len(migrated["evidence"]) == 2
    assert migrated["analysis_status"] == "needs_review"
    # original record object must not be mutated in place
    assert legacy_record["evidence"] == []


def test_legacy_row_with_no_source_links_stays_unavailable():
    legacy_record = empty_record()
    legacy_record["company"] = "Empty Co"
    migrated = migrate_legacy_record(legacy_record, retrieved_date="2026-08-01")
    assert migrated["evidence"] == []
    assert migrated["analysis_status"] == "unavailable"


def test_record_analysis_status_requires_actual_verified_item():
    unverified = [make_evidence_item(**VALID_ITEM_KWARGS)]
    assert record_analysis_status(unverified) == "needs_review"

    verified_kwargs = dict(VALID_ITEM_KWARGS)
    verified_kwargs["status"] = "verified"
    verified = [make_evidence_item(**verified_kwargs)]
    assert record_analysis_status(verified) == "verified"

    assert record_analysis_status([]) == "unavailable"