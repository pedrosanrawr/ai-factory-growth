"""Contract tests for evidence_store.py.

Covers: schema defaults, duplicate evidence, invalid URL rejection, and
legacy source_links compatibility, per the work-file TODOs.

picks these up directly.
"""
import unittest
import tempfile
from pathlib import Path

from schema import empty_record
from services.evidence_store import (
    EvidenceStore,
    EvidenceValidationError,
    make_evidence_item,
    migrate_legacy_record,
    migrate_legacy_source_links,
    new_company_record,
    record_analysis_status,
    research_document_to_evidence,
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


class SchemaDefaultsTests(unittest.TestCase):
    """1. Schema defaults."""

    def test_schema_defaults_are_untouched(self):
        record = empty_record()
        self.assertEqual(record["evidence"], [])
        self.assertEqual(record["research_as_of"], "")
        self.assertEqual(record["analysis_status"], "unavailable")
        self.assertIsNone(record["analysis_confidence"])
        # legacy field still present and untouched
        self.assertEqual(record["source_links"], "")

    def test_new_company_record_only_sets_company(self):
        record = new_company_record("Acme Corp")
        baseline = empty_record()
        baseline["company"] = "Acme Corp"
        self.assertEqual(record, baseline)


class EvidenceItemValidationTests(unittest.TestCase):
    """2 & 3. Evidence item shape + URL validation."""

    def test_make_evidence_item_success(self):
        item = make_evidence_item(**VALID_ITEM_KWARGS)
        self.assertEqual(item["url"], VALID_ITEM_KWARGS["url"])
        self.assertEqual(item["title"], VALID_ITEM_KWARGS["title"])
        self.assertEqual(item["retrieved_date"], VALID_ITEM_KWARGS["retrieved_date"])
        self.assertEqual(item["published_date"], VALID_ITEM_KWARGS["published_date"])
        self.assertEqual(item["excerpt"], VALID_ITEM_KWARGS["excerpt"])
        self.assertEqual(item["claim"], VALID_ITEM_KWARGS["claim"])
        self.assertEqual(item["source_type"], "10-K")
        # default status must never be "verified" unless explicitly requested
        self.assertEqual(item["status"], "needs_review")

    def test_invalid_url_rejection(self):
        for bad_url in ["", "not-a-url", "ftp://example.com/x", "www.example.com"]:
            with self.subTest(bad_url=bad_url):
                kwargs = dict(VALID_ITEM_KWARGS)
                kwargs["url"] = bad_url
                with self.assertRaises(EvidenceValidationError):
                    make_evidence_item(**kwargs)

    def test_missing_required_field_rejection(self):
        kwargs = dict(VALID_ITEM_KWARGS)
        del kwargs["title"]
        with self.assertRaises(EvidenceValidationError):
            make_evidence_item(**kwargs)

    def test_unknown_source_type_rejection(self):
        kwargs = dict(VALID_ITEM_KWARGS)
        kwargs["source_type"] = "tweet"
        with self.assertRaises(EvidenceValidationError):
            make_evidence_item(**kwargs)

    def test_store_evidence_rejects_bad_url_end_to_end(self):
        store = EvidenceStore(path=":memory:")
        bad = dict(VALID_ITEM_KWARGS)
        bad["url"] = "not-a-url"
        with self.assertRaises(EvidenceValidationError):
            store_evidence("Acme Corp", [bad], store=store)
        # nothing should have been written
        self.assertEqual(store.get("Acme Corp"), [])

    def test_store_evidence_never_auto_verifies(self):
        store = EvidenceStore(path=":memory:")
        result = store_evidence("Acme Corp", [VALID_ITEM_KWARGS], store=store)
        self.assertEqual(result[0]["status"], "needs_review")


class DuplicateEvidenceTests(unittest.TestCase):
    """4. Duplicate evidence handling, preserved by company identifier."""

    def test_duplicate_evidence_is_deduped(self):
        store = EvidenceStore(path=":memory:")
        store_evidence("Acme Corp", [VALID_ITEM_KWARGS], store=store)
        result = store_evidence("Acme Corp", [VALID_ITEM_KWARGS], store=store)
        self.assertEqual(len(result), 1)

    def test_evidence_isolated_per_company(self):
        store = EvidenceStore(path=":memory:")
        store_evidence("Acme Corp", [VALID_ITEM_KWARGS], store=store)
        other_kwargs = dict(VALID_ITEM_KWARGS)
        other_kwargs["url"] = "https://www.sec.gov/other/10k"
        store_evidence("Other Inc", [other_kwargs], store=store)

        self.assertEqual(len(store.get("Acme Corp")), 1)
        self.assertEqual(len(store.get("Other Inc")), 1)
        self.assertNotEqual(
            store.get("Acme Corp")[0]["url"], store.get("Other Inc")[0]["url"]
        )

    def test_different_claim_same_url_is_not_a_duplicate(self):
        store = EvidenceStore(path=":memory:")
        store_evidence("Acme Corp", [VALID_ITEM_KWARGS], store=store)
        second_kwargs = dict(VALID_ITEM_KWARGS)
        second_kwargs["claim"] = "Operating margin expanded to 24%."
        result = store_evidence("Acme Corp", [second_kwargs], store=store)
        self.assertEqual(len(result), 2)


class LegacyCompatibilityTests(unittest.TestCase):
    """5 & 6. Legacy source_links compatibility."""

    def test_migrate_legacy_source_links_basic(self):
        legacy = "https://example.com/a, https://example.com/b|https://example.com/c"
        items = migrate_legacy_source_links(legacy, retrieved_date="2026-08-01")
        self.assertEqual(len(items), 3)
        urls = {item["url"] for item in items}
        self.assertEqual(
            urls,
            {
                "https://example.com/a",
                "https://example.com/b",
                "https://example.com/c",
            },
        )
        # legacy data has no confirmed claim, so it must never be "verified"
        self.assertTrue(all(item["status"] == "needs_review" for item in items))

    def test_migrate_legacy_source_links_skips_garbage_without_raising(self):
        legacy = "https://example.com/a, not-a-url, "
        items = migrate_legacy_source_links(legacy, retrieved_date="2026-08-01")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://example.com/a")

    def test_migrate_legacy_source_links_empty(self):
        self.assertEqual(migrate_legacy_source_links("", "2026-08-01"), [])
        self.assertEqual(migrate_legacy_source_links("   ", "2026-08-01"), [])

    def test_legacy_row_compatibility_full_record(self):
        legacy_record = empty_record()
        legacy_record["company"] = "Legacy Co"
        legacy_record["source_links"] = (
            "https://example.com/legacy1, https://example.com/legacy2"
        )
        # legacy row predates the evidence field entirely
        legacy_record["evidence"] = []

        migrated = migrate_legacy_record(legacy_record, retrieved_date="2026-08-01")

        # source_links stays intact and readable
        self.assertEqual(migrated["source_links"], legacy_record["source_links"])
        self.assertEqual(len(migrated["evidence"]), 2)
        self.assertEqual(migrated["analysis_status"], "needs_review")
        # original record object must not be mutated in place
        self.assertEqual(legacy_record["evidence"], [])

    def test_legacy_row_with_no_source_links_stays_unavailable(self):
        legacy_record = empty_record()
        legacy_record["company"] = "Empty Co"
        migrated = migrate_legacy_record(legacy_record, retrieved_date="2026-08-01")
        self.assertEqual(migrated["evidence"], [])
        self.assertEqual(migrated["analysis_status"], "unavailable")

    def test_record_analysis_status_requires_actual_verified_item(self):
        unverified = [make_evidence_item(**VALID_ITEM_KWARGS)]
        self.assertEqual(record_analysis_status(unverified), "needs_review")

        verified_kwargs = dict(VALID_ITEM_KWARGS)
        verified_kwargs["status"] = "verified"
        verified = [make_evidence_item(**verified_kwargs)]
        self.assertEqual(record_analysis_status(verified), "verified")

        self.assertEqual(record_analysis_status([]), "unavailable")


class ResearchDocumentCompatibilityTests(unittest.TestCase):
    def test_converts_research_source_document_to_evidence_contract(self):
        document = {
            "title": "NVIDIA CORP - 10-K",
            "url": "https://www.sec.gov/Archives/example.htm",
            "source_type": "sec_filing",
            "publication_date": "2026-02-15",
            "retrieved_at": "2026-09-02T08:00:00+00:00",
            "supporting_text": "Annual filing.",
        }

        item = research_document_to_evidence(
            document,
            claim="The company reported annual results.",
        )

        self.assertEqual(item["source_type"], "10-K")
        self.assertEqual(item["published_date"], "2026-02-15")
        self.assertEqual(item["retrieved_date"], "2026-09-02T08:00:00+00:00")
        self.assertEqual(item["status"], "needs_review")

    def test_corrupt_persisted_store_loads_as_empty(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "evidence.json"
            path.write_text("not valid json", encoding="utf-8")
            store = EvidenceStore(path=str(path))

        self.assertEqual(store.get("Acme Corp"), [])


if __name__ == "__main__":
    unittest.main()
