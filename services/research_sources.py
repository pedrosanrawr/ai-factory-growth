"""FLORES work file: external research-source adapters.

Follow the TODOs below in order. Do not add a provider key or dependency
without team approval.

Goal: replace manual research-only inputs with a provider-neutral, testable source layer.

1. Propose supported sources and fields in the PR description before adding a provider dependency or key.
2. Create `services/research_sources.py` with a provider interface that returns normalized research documents, URLs, publication dates, and retrieval timestamps.
3. Implement one source adapter at a time; use an HTTP timeout, user agent, input validation, and clear errors.
4. Cache raw normalized results locally only if the storage location and retention behavior are documented.
5. Never overwrite existing CSV facts automatically; return candidate evidence for review.
6. Test normalization, network failure, invalid provider payloads, and a fixture-based successful response without live network calls.

External research-source adapters (implementation)

Provider-neutral research source layer. Replaces manual-only research
inputs with a testable adapter that fetches CANDIDATE evidence for a
human researcher to review, it never writes that evidence into
schema.py records or the CSV automatically.

Source used for v1: SEC EDGAR full-text search API (efts.sec.gov).
Chosen because:
  - No API key or signup required.
  - Zero new pip dependencies (stdlib urllib + json only), which keeps
    this out of the "new dependency / key needs team approval" gate
    described in the module TODO for v1.
  - Its filings are the most directly useful source for the project's
    moat/risk research (e.g. an 8-K disclosing a hyperscaler contract).

Known v1 limitation: EDGAR full-text search is a keyword search across
ALL filings, not a "get this company's own filings" lookup. Searching
a company's name returns filings that MENTION that name in quotes,
which is usually the company's own filing but can occasionally surface
a different filer's document that mentions them (e.g. a customer or
competitor). A v2 improvement would resolve the company name to a CIK
first (via the free, static company_tickers.json file) and scope the
search to filings BY that CIK specifically. Flagging this here so it's
visible in review, not just buried in a comment.

IMPORTANT BEFORE THIS RUNS AGAINST REAL TRAFFIC:
SEC's fair-access policy requires a real, working contact email in the
User-Agent header. Set it via the RESEARCH_SOURCES_USER_AGENT
environment variable, e.g.:
    export RESEARCH_SOURCES_USER_AGENT="AI Factory Growth Project you@example.com"
If it isn't set (and no explicit user_agent is passed in code), this
module raises ResearchSourceError immediately rather than silently
sending a fake/placeholder value that could get the calling IP
rate-limited or blocked. This check happens at EdgarFullTextSearchSource
construction time, deliberately outside fetch_company_research()'s
graceful-degradation path, since a missing env var is a setup mistake,
not a transient external-service outage, and should fail loudly.

Verified against the live EDGAR API via manual Postman request on
[9/1/2026]: endpoint reachable, response shape (hits.hits, _id, _source
fields) matches what this module expects. That check also surfaced
a bug in _first_display_name's regex, since real display_names values
look like "NVIDIA CORP  (NVDA)  (CIK 0001045810)" rather than the
digits-only trailing parenthetical the regex assumed; fixed below.

NOT YET RUN END-TO-END: fetch_company_research() itself has not been
called against live traffic, only verified via mocked responses (see
tests/test_research_sources.py) and the manual Postman check above.
Run one real fetch_company_research() call locally before merging to
confirm the full path (env var resolution, caching, normalization)
works together against a live response, not just the pieces in
isolation.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol
from urllib.parse import urlencode

# --- Config -----------------------------------------------------------------

USER_AGENT_ENV_VAR = "RESEARCH_SOURCES_USER_AGENT"
REQUEST_TIMEOUT_SECONDS = 10

# Local cache: one JSON file per company, under the repo's .cache/ dir.
# Retention: 24 hours. Documented here per the TODO file's caching rule.
# Rationale for 24h: this project's research doesn't need to be fresher
# than daily, and it keeps repeated runs during a work session under
# EDGAR's 10 req/sec limit without needing a smarter rate limiter yet.
CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache" / "research_sources"
CACHE_TTL_SECONDS = 24 * 60 * 60


# --- Normalized shape ---------------------------------------------------------


def empty_research_document() -> dict:
    """
    Shape every provider adapter must return, one dict per candidate
    document. Mirrors schema.py's empty_record() pattern: plain dict,
    not a class, so it stays easy to json.dumps() and cache.
    """
    return {
        "title": "",
        "url": "",
        "source_type": "",  # e.g. "sec_filing"
        "publication_date": "",  # ISO date string, YYYY-MM-DD
        "retrieved_at": "",  # ISO timestamp: when THIS module fetched it
        "supporting_text": "",  # short excerpt/description; may be empty
    }


class ResearchSource(Protocol):
    """Interface every source adapter must implement (TODO step 2)."""

    def fetch(self, company: str) -> list[dict]:
        """Return normalized candidate research documents for one company."""
        ...


class ResearchSourceError(Exception):
    """Raised when a provider adapter cannot return results (TODO step 3)."""


def _resolve_user_agent(explicit: str | None = None) -> str:
    """
    Resolve the User-Agent header: an explicit override wins, otherwise
    read RESEARCH_SOURCES_USER_AGENT from the environment.

    Raises ResearchSourceError if neither is available. This is called
    from EdgarFullTextSearchSource.__init__(), outside of
    fetch_company_research()'s try/except, so a missing env var fails
    loudly at construction time instead of being silently swallowed
    into an empty result list, a missing config value is a setup bug,
    not a transient outage.
    """
    if explicit:
        return explicit
    env_value = os.environ.get(USER_AGENT_ENV_VAR)
    if env_value:
        return env_value
    raise ResearchSourceError(
        f"{USER_AGENT_ENV_VAR} is not set. SEC EDGAR requires a real "
        "contact email in the User-Agent header. Set it with, e.g.:\n"
        f'  export {USER_AGENT_ENV_VAR}="AI Factory Growth Project you@example.com"'
    )


# --- Validation ---------------------------------------------------------------


def _validate_company(company: str) -> str:
    if not isinstance(company, str):
        raise TypeError(f"company must be a string, got {type(company).__name__}")
    company = company.strip()
    if not company:
        raise ValueError("company must not be empty")
    if len(company) > 200:
        raise ValueError("company name is unexpectedly long, possible bad input")
    return company


# --- SEC EDGAR adapter ---------------------------------------------------------


class EdgarFullTextSearchSource:
    """
    Adapter for the SEC EDGAR full-text search API (efts.sec.gov).

    No API key required. Requires a descriptive User-Agent header with
    a real contact email, per SEC's fair access policy, read from the
    RESEARCH_SOURCES_USER_AGENT environment variable by default.

    Raises ResearchSourceError at construction time if no user_agent
    is passed AND the environment variable isn't set.
    """

    BASE_URL = "https://efts.sec.gov/LATEST/search-index"
    SOURCE_TYPE = "sec_filing"

    def __init__(
        self,
        forms: str = "8-K,10-K,10-Q",
        max_results: int = 10,
        timeout: int = REQUEST_TIMEOUT_SECONDS,
        user_agent: str | None = None,
    ):
        self.forms = forms
        self.max_results = max_results
        self.timeout = timeout
        self.user_agent = _resolve_user_agent(user_agent)

    def fetch(self, company: str) -> list[dict]:
        company = _validate_company(company)
        payload = self._request(company)
        return _normalize_edgar_response(payload)

    def _request(self, company: str) -> dict:
        params = {
            "q": f'"{company}"',
            "forms": self.forms,
            "size": self.max_results,
        }
        url = f"{self.BASE_URL}?{urlencode(params)}"
        request = urllib.request.Request(url, headers={"User-Agent": self.user_agent})

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raise ResearchSourceError(
                f"EDGAR returned HTTP {exc.code} for company={company!r}"
            ) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ResearchSourceError(
                f"Could not reach EDGAR for company={company!r}: {exc}"
            ) from exc

        try:
            return json.loads(raw)
        except (ValueError, TypeError) as exc:
            raise ResearchSourceError(
                f"EDGAR returned a non-JSON response for company={company!r}"
            ) from exc


def _first_display_name(display_names) -> str:
    """Some EDGAR response variants use display_names like:
    'NVIDIA CORP  (NVDA)  (CIK 0001045810)' or 'NVIDIA CORP (0001045810)'."""
    if isinstance(display_names, list) and display_names:
        return str(display_names[0]).split("(")[0].strip()
    return ""


def _first_form_type(source: dict) -> str:
    form_type = source.get("form_type")
    if form_type:
        return form_type
    root_forms = source.get("root_forms")
    if isinstance(root_forms, list) and root_forms:
        return root_forms[0]
    return ""


def _build_filing_url(hit_id: str) -> str:
    """
    hit_id looks like "0001234567-24-001234:filing-main.htm".
    The first 10 digits of the accession number are the filer's CIK
    (usually the company itself; occasionally a filing agent).
    Builds: https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{filename}
    """
    if not hit_id or ":" not in hit_id:
        return ""
    accession_dashed, filename = hit_id.split(":", 1)
    accession_nodash = accession_dashed.replace("-", "")
    cik_segment = accession_nodash[:10].lstrip("0") or "0"
    return f"https://www.sec.gov/Archives/edgar/data/{cik_segment}/{accession_dashed}/{filename}"


def _normalize_edgar_response(payload: dict) -> list[dict]:
    """
    Turn a raw EDGAR full-text search JSON response into a list of
    normalized research documents (TODO step 3). Tolerant of missing
    optional fields, since this is a third-party response shape we
    don't control, but raises ResearchSourceError if the response is
    missing the structure we depend on entirely (TODO step 6: invalid
    provider payloads).
    """
    if not isinstance(payload, dict):
        raise ResearchSourceError("EDGAR response was not a JSON object")

    hits = payload.get("hits", {})
    hit_list = hits.get("hits") if isinstance(hits, dict) else None
    if not isinstance(hit_list, list):
        raise ResearchSourceError("EDGAR response was missing the expected hits list")

    retrieved_at = datetime.now(timezone.utc).isoformat()
    documents = []

    for hit in hit_list:
        if not isinstance(hit, dict):
            continue  # skip malformed individual hits rather than failing the whole batch

        source = hit.get("_source", {})
        if not isinstance(source, dict):
            source = {}
        hit_id = hit.get("_id", "")

        entity_name = source.get("entity_name") or _first_display_name(
            source.get("display_names")
        )
        form_type = _first_form_type(source)

        document = empty_research_document()
        document["title"] = (
            f"{entity_name or 'Unknown filer'} - {form_type or 'SEC filing'}".strip(
                " -"
            )
        )
        document["url"] = _build_filing_url(hit_id)
        document["source_type"] = EdgarFullTextSearchSource.SOURCE_TYPE
        document["publication_date"] = source.get("file_date", "")
        document["retrieved_at"] = retrieved_at
        document["supporting_text"] = source.get("file_description", "")
        documents.append(document)

    return documents


# --- Local cache (TODO step 4: documented location + retention) ---------------


def _cache_path(company: str) -> Path:
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", company.strip().lower())
    return CACHE_DIR / f"{safe_name}.json"


def _read_cache(company: str) -> list[dict] | None:
    path = _cache_path(company)
    if not path.exists():
        return None
    try:
        cached = json.loads(path.read_text())
    except (ValueError, OSError):
        return None

    cached_at = cached.get("cached_at") if isinstance(cached, dict) else None
    if not cached_at:
        return None
    try:
        age_seconds = (
            datetime.now(timezone.utc) - datetime.fromisoformat(cached_at)
        ).total_seconds()
    except ValueError:
        return None
    if age_seconds > CACHE_TTL_SECONDS:
        return None

    return cached.get("documents")


def _write_cache(company: str, documents: list[dict]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_path(company)
    payload = {
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "documents": documents,
    }
    path.write_text(json.dumps(payload, indent=2))


# --- Public entry point ---------------------------------------------------------


def fetch_company_research(company: str, use_cache: bool = True) -> list[dict]:
    """
    Return normalized candidate research documents for one company.

    Never overwrites CSV facts (TODO step 4/5): this function only
    returns data, it does not import schema.py or touch any CSV.

    Safe by default: if the provider fails (network error, bad
    payload), this returns an empty list rather than raising, so one
    company's fetch failure can't crash a batch run. Callers that want
    to distinguish "no results" from "provider errored" can call
    EdgarFullTextSearchSource().fetch(company) directly and catch
    ResearchSourceError themselves.
    """
    company = _validate_company(company)

    if use_cache:
        cached = _read_cache(company)
        if cached is not None:
            return cached

    source = EdgarFullTextSearchSource()
    try:
        documents = source.fetch(company)
    except ResearchSourceError:
        return []

    if use_cache:
        _write_cache(company, documents)

    return documents
