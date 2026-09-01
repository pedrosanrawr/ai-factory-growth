"""
tests/test_research_sources.py

Tests for services/research_sources.py. Every test that would otherwise
hit the network mocks urllib.request.urlopen instead, per the TODO
file's rule: "fixture-based successful response without live network
calls."

Run from the project root with:
    python -m unittest tests.test_research_sources -v
"""

import json
import os
import sys
import unittest
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

# Put the repo root on sys.path so `from services.research_sources import ...`
# works regardless of how this file is invoked.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services import research_sources
from services.research_sources import (
    EdgarFullTextSearchSource,
    ResearchSourceError,
    _build_filing_url,
    _normalize_edgar_response,
    _read_cache,
    _validate_company,
    _write_cache,
    empty_research_document,
    fetch_company_research,
)

# ---------------------------------------------------------------------------
# Fixture: a realistic EDGAR full-text search response, one complete hit
# and one hit missing several optional fields (to test tolerance).
# ---------------------------------------------------------------------------

SAMPLE_EDGAR_RESPONSE = {
    "query": {"from": 0, "size": 10, "q": '"NVIDIA"'},
    "hits": {
        "total": {"value": 2, "relation": "eq"},
        "hits": [
            {
                "_id": "0001045810-24-000123:nvda-8k.htm",
                "_source": {
                    "file_date": "2024-05-22",
                    "period_of_report": "2024-05-22",
                    "form_type": "8-K",
                    "entity_name": "NVIDIA CORP",
                    "file_num": "001-23985",
                    "film_num": "",
                    "file_description": "Material agreement disclosure",
                },
            },
            {
                # Missing entity_name, file_description, and uses
                # display_names instead, to check the fallback path.
                "_id": "0001045810-24-000200:nvda-10q.htm",
                "_source": {
                    "file_date": "2024-08-15",
                    "form_type": "10-Q",
                    "display_names": ["NVIDIA CORP  (NVDA)  (CIK 0001045810)"],
                },
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# _validate_company
# ---------------------------------------------------------------------------


class TestValidateCompany(unittest.TestCase):
    def test_accepts_and_strips_valid_string(self):
        self.assertEqual(_validate_company("  Nvidia  "), "Nvidia")

    def test_rejects_empty_string(self):
        with self.assertRaises(ValueError):
            _validate_company("   ")

    def test_rejects_non_string(self):
        with self.assertRaises(TypeError):
            _validate_company(12345)

    def test_rejects_unreasonably_long_input(self):
        with self.assertRaises(ValueError):
            _validate_company("x" * 500)


# ---------------------------------------------------------------------------
# _normalize_edgar_response
# ---------------------------------------------------------------------------


class TestNormalizeEdgarResponse(unittest.TestCase):
    def test_normalizes_a_complete_hit(self):
        docs = _normalize_edgar_response(SAMPLE_EDGAR_RESPONSE)
        self.assertEqual(len(docs), 2)

        first = docs[0]
        self.assertEqual(first["title"], "NVIDIA CORP - 8-K")
        self.assertEqual(first["source_type"], "sec_filing")
        self.assertEqual(first["publication_date"], "2024-05-22")
        self.assertEqual(first["supporting_text"], "Material agreement disclosure")
        self.assertTrue(
            first["url"].startswith("https://www.sec.gov/Archives/edgar/data/")
        )
        self.assertTrue(first["retrieved_at"])  # non-empty ISO timestamp

    def test_falls_back_to_display_names_when_entity_name_missing(self):
        docs = _normalize_edgar_response(SAMPLE_EDGAR_RESPONSE)
        second = docs[1]
        self.assertEqual(second["title"], "NVIDIA CORP - 10-Q")

    def test_missing_optional_fields_default_to_empty_string_not_crash(self):
        docs = _normalize_edgar_response(SAMPLE_EDGAR_RESPONSE)
        second = docs[1]
        self.assertEqual(second["supporting_text"], "")

    def test_every_document_has_the_full_normalized_shape(self):
        docs = _normalize_edgar_response(SAMPLE_EDGAR_RESPONSE)
        for doc in docs:
            self.assertEqual(set(doc.keys()), set(empty_research_document().keys()))

    def test_raises_on_missing_hits_key(self):
        with self.assertRaises(ResearchSourceError):
            _normalize_edgar_response({"query": {}})

    def test_raises_on_hits_not_a_list(self):
        with self.assertRaises(ResearchSourceError):
            _normalize_edgar_response({"hits": {"hits": "not-a-list"}})

    def test_raises_on_payload_not_a_dict(self):
        with self.assertRaises(ResearchSourceError):
            _normalize_edgar_response(["unexpected", "list"])

    def test_skips_malformed_individual_hits_without_failing_the_batch(self):
        payload = {
            "hits": {
                "hits": [
                    "not-a-dict",
                    SAMPLE_EDGAR_RESPONSE["hits"]["hits"][0],
                ]
            }
        }
        docs = _normalize_edgar_response(payload)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["title"], "NVIDIA CORP - 8-K")


# ---------------------------------------------------------------------------
# _build_filing_url
# ---------------------------------------------------------------------------


class TestBuildFilingUrl(unittest.TestCase):
    def test_builds_expected_url(self):
        url = _build_filing_url("0001045810-24-000123:nvda-8k.htm")
        self.assertEqual(
            url,
            "https://www.sec.gov/Archives/edgar/data/1045810/0001045810-24-000123/nvda-8k.htm",
        )

    def test_returns_empty_string_for_malformed_id(self):
        self.assertEqual(_build_filing_url("no-colon-here"), "")
        self.assertEqual(_build_filing_url(""), "")


# ---------------------------------------------------------------------------
# User-Agent resolution (RESEARCH_SOURCES_USER_AGENT env var)
# ---------------------------------------------------------------------------


class TestUserAgentResolution(unittest.TestCase):
    def test_explicit_user_agent_overrides_env_var(self):
        with patch.dict(
            os.environ, {"RESEARCH_SOURCES_USER_AGENT": "From Env you@example.com"}
        ):
            source = EdgarFullTextSearchSource(
                user_agent="Explicit Value you@example.com"
            )
        self.assertEqual(source.user_agent, "Explicit Value you@example.com")

    def test_falls_back_to_env_var_when_no_explicit_value(self):
        with patch.dict(
            os.environ, {"RESEARCH_SOURCES_USER_AGENT": "From Env you@example.com"}
        ):
            source = EdgarFullTextSearchSource()
        self.assertEqual(source.user_agent, "From Env you@example.com")

    def test_raises_clear_error_when_neither_is_set(self):
        with (
            patch.dict(os.environ, {}, clear=True),
            self.assertRaises(ResearchSourceError) as ctx,
        ):
            EdgarFullTextSearchSource()
        self.assertIn("RESEARCH_SOURCES_USER_AGENT", str(ctx.exception))

    def test_missing_env_var_fails_loudly_not_silently_via_fetch_company_research(
        self,
    ):
        # This is the important behavioral guarantee: a missing/misconfigured
        # env var must NOT be swallowed into an empty result list the way a
        # transient network failure is, that would hide a setup mistake.
        with (
            patch.dict(os.environ, {}, clear=True),
            self.assertRaises(ResearchSourceError),
        ):
            fetch_company_research("NVIDIA", use_cache=False)


# ---------------------------------------------------------------------------
# EdgarFullTextSearchSource.fetch (network mocked)
# ---------------------------------------------------------------------------


def _mock_urlopen_returning(payload: dict):
    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.read.return_value = json.dumps(payload).encode("utf-8")
    return mock_response


class TestEdgarFetchMocked(unittest.TestCase):
    def setUp(self):
        # These tests construct EdgarFullTextSearchSource() with no
        # explicit user_agent, so RESEARCH_SOURCES_USER_AGENT needs to
        # be set for the duration of the test, or construction itself
        # would raise before the mocked network call ever happens.
        self._env_patcher = patch.dict(
            os.environ, {"RESEARCH_SOURCES_USER_AGENT": "Test Agent test@example.com"}
        )
        self._env_patcher.start()

    def tearDown(self):
        self._env_patcher.stop()

    @patch("services.research_sources.urllib.request.urlopen")
    def test_fetch_returns_normalized_documents_on_success(self, mock_urlopen):
        mock_urlopen.return_value = _mock_urlopen_returning(SAMPLE_EDGAR_RESPONSE)
        source = EdgarFullTextSearchSource()

        docs = source.fetch("NVIDIA")

        self.assertEqual(len(docs), 2)
        mock_urlopen.assert_called_once()

    @patch("services.research_sources.urllib.request.urlopen")
    def test_fetch_sends_user_agent_header(self, mock_urlopen):
        mock_urlopen.return_value = _mock_urlopen_returning(SAMPLE_EDGAR_RESPONSE)
        source = EdgarFullTextSearchSource(user_agent="Test Agent test@example.com")

        source.fetch("NVIDIA")

        sent_request = mock_urlopen.call_args[0][0]
        self.assertEqual(
            sent_request.get_header("User-agent"), "Test Agent test@example.com"
        )

    @patch("services.research_sources.urllib.request.urlopen")
    def test_fetch_raises_on_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://efts.sec.gov/LATEST/search-index", 403, "Forbidden", None, None
        )
        source = EdgarFullTextSearchSource()

        with self.assertRaises(ResearchSourceError):
            source.fetch("NVIDIA")

    @patch("services.research_sources.urllib.request.urlopen")
    def test_fetch_raises_on_connection_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("connection refused")
        source = EdgarFullTextSearchSource()

        with self.assertRaises(ResearchSourceError):
            source.fetch("NVIDIA")

    @patch("services.research_sources.urllib.request.urlopen")
    def test_fetch_raises_on_timeout(self, mock_urlopen):
        mock_urlopen.side_effect = TimeoutError("timed out")
        source = EdgarFullTextSearchSource()

        with self.assertRaises(ResearchSourceError):
            source.fetch("NVIDIA")

    @patch("services.research_sources.urllib.request.urlopen")
    def test_fetch_raises_on_non_json_response(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.read.return_value = b"<html>not json</html>"
        mock_urlopen.return_value = mock_response
        source = EdgarFullTextSearchSource()

        with self.assertRaises(ResearchSourceError):
            source.fetch("NVIDIA")

    @patch("services.research_sources.urllib.request.urlopen")
    def test_fetch_rejects_bad_company_before_any_network_call(self, mock_urlopen):
        source = EdgarFullTextSearchSource()

        with self.assertRaises(ValueError):
            source.fetch("")

        mock_urlopen.assert_not_called()


# ---------------------------------------------------------------------------
# fetch_company_research (public entry point; cache disabled per-test
# via use_cache=False unless a test is specifically about caching)
# ---------------------------------------------------------------------------


class TestFetchCompanyResearch(unittest.TestCase):
    def setUp(self):
        self._env_patcher = patch.dict(
            os.environ, {"RESEARCH_SOURCES_USER_AGENT": "Test Agent test@example.com"}
        )
        self._env_patcher.start()

    def tearDown(self):
        self._env_patcher.stop()

    @patch("services.research_sources.urllib.request.urlopen")
    def test_returns_normalized_documents_on_success(self, mock_urlopen):
        mock_urlopen.return_value = _mock_urlopen_returning(SAMPLE_EDGAR_RESPONSE)

        docs = fetch_company_research("NVIDIA", use_cache=False)

        self.assertEqual(len(docs), 2)

    @patch("services.research_sources.urllib.request.urlopen")
    def test_returns_empty_list_instead_of_raising_on_provider_failure(
        self, mock_urlopen
    ):
        mock_urlopen.side_effect = urllib.error.URLError("connection refused")

        docs = fetch_company_research("NVIDIA", use_cache=False)

        self.assertEqual(docs, [])

    def test_rejects_bad_company_input(self):
        with self.assertRaises(ValueError):
            fetch_company_research("", use_cache=False)


# ---------------------------------------------------------------------------
# Local cache
# ---------------------------------------------------------------------------


class TestCache(unittest.TestCase):
    def setUp(self):
        # Point the cache at a throwaway directory so tests never touch
        # the real .cache/ folder, and so they can't interfere with
        # each other or with a real run of the app.
        import tempfile

        self._tmpdir = tempfile.TemporaryDirectory()
        self._patcher = patch.object(
            research_sources, "CACHE_DIR", Path(self._tmpdir.name)
        )
        self._patcher.start()

        self._env_patcher = patch.dict(
            os.environ, {"RESEARCH_SOURCES_USER_AGENT": "Test Agent test@example.com"}
        )
        self._env_patcher.start()

    def tearDown(self):
        self._patcher.stop()
        self._tmpdir.cleanup()
        self._env_patcher.stop()

    def test_write_then_read_round_trip(self):
        docs = [dict(empty_research_document(), title="Cached Doc")]
        _write_cache("Nvidia", docs)

        result = _read_cache("Nvidia")

        self.assertEqual(result, docs)

    def test_read_returns_none_when_nothing_cached(self):
        self.assertIsNone(_read_cache("Never Cached Co"))

    def test_read_returns_none_when_cache_entry_expired(self):
        docs = [dict(empty_research_document(), title="Stale Doc")]
        _write_cache("Old Co", docs)

        # Manually age the cache file past the 24h TTL.
        stale_time = datetime.now(timezone.utc) - timedelta(hours=25)
        path = research_sources._cache_path("Old Co")
        payload = json.loads(path.read_text())
        payload["cached_at"] = stale_time.isoformat()
        path.write_text(json.dumps(payload))

        self.assertIsNone(_read_cache("Old Co"))

    @patch("services.research_sources.urllib.request.urlopen")
    def test_fetch_company_research_uses_cache_on_second_call(self, mock_urlopen):
        mock_urlopen.return_value = _mock_urlopen_returning(SAMPLE_EDGAR_RESPONSE)

        first = fetch_company_research("NVIDIA", use_cache=True)
        second = fetch_company_research("NVIDIA", use_cache=True)

        self.assertEqual(first, second)
        mock_urlopen.assert_called_once()  # second call served from cache, no network hit


if __name__ == "__main__":
    unittest.main()
