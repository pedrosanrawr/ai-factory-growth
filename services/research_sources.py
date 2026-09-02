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
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol
from urllib.parse import urlencode

from dotenv import load_dotenv

# --- Config -----------------------------------------------------------------

USER_AGENT_ENV_VAR = "RESEARCH_SOURCES_USER_AGENT"
REQUEST_TIMEOUT_SECONDS = 10
# Keep automated access below the SEC's published 10 requests/second limit.
MIN_REQUEST_INTERVAL_SECONDS = 0.12
_request_lock = threading.Lock()
_last_request_at = 0.0

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
        "company": "",  # SEC filer name when the provider can identify it
        "cik": "",  # SEC Central Index Key when available
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


def _open_sec_request(request: urllib.request.Request, timeout: int):
    """Open a SEC request while keeping the shared process below 10 req/sec."""
    global _last_request_at
    with _request_lock:
        wait_seconds = MIN_REQUEST_INTERVAL_SECONDS - (time.monotonic() - _last_request_at)
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        response = urllib.request.urlopen(request, timeout=timeout)
        _last_request_at = time.monotonic()
        return response


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
    load_dotenv()
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
        payload = self._request(f'"{company}"')
        return _normalize_edgar_response(payload)

    def search(self, query: str, start_date: str | None = None) -> list[dict]:
        """Search EDGAR filings using documented Boolean keyword syntax."""
        query = _validate_company(query)
        return _normalize_edgar_response(self._request(query, start_date=start_date))

    def _request(self, query: str, start_date: str | None = None) -> dict:
        params = {
            "q": query,
            "forms": self.forms,
            "size": self.max_results,
        }
        if start_date:
            params["startdt"] = start_date
        url = f"{self.BASE_URL}?{urlencode(params)}"
        request = urllib.request.Request(url, headers={"User-Agent": self.user_agent})

        try:
            with _open_sec_request(request, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raise ResearchSourceError(
                f"EDGAR returned HTTP {exc.code} for query={query!r}"
            ) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ResearchSourceError(
                f"Could not reach EDGAR for query={query!r}: {exc}"
            ) from exc

        try:
            return json.loads(raw)
        except (ValueError, TypeError) as exc:
            raise ResearchSourceError(
                f"EDGAR returned a non-JSON response for query={query!r}"
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
    Builds the filing index page, which is stable even when the full-text
    search result points at an exhibit filename that is no longer available:
    https://www.sec.gov/Archives/edgar/data/{cik}/{accession-no-dashes}/{accession}-index.htm
    """
    if not hit_id or ":" not in hit_id:
        return ""
    accession_dashed, _ = hit_id.split(":", 1)
    accession_nodash = accession_dashed.replace("-", "")
    cik_segment = accession_nodash[:10].lstrip("0") or "0"
    return f"https://www.sec.gov/Archives/edgar/data/{cik_segment}/{accession_nodash}/{accession_dashed}-index.htm"


def _cik_from_hit_id(hit_id: str) -> str:
    """Return a zero-padded CIK from an EDGAR full-text hit identifier."""
    accession = str(hit_id or "").split(":", 1)[0]
    digits = accession.split("-", 1)[0]
    return digits.zfill(10) if digits.isdigit() and len(digits) <= 10 else ""


def _source_cik(source: dict, hit_id: str) -> str:
    """Prefer EDGAR's filer CIK over the accession prefix.

    An accession can be filed by an agent, so its prefix is not always the
    reporting company. Full-text hits expose the actual filer in ``ciks``.
    """
    ciks = source.get("ciks") if isinstance(source, dict) else None
    if isinstance(ciks, list) and ciks:
        value = str(ciks[0]).strip()
        if value.isdigit() and len(value) <= 10:
            return value.zfill(10)
    return _cik_from_hit_id(hit_id)


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
        document["cik"] = _source_cik(source, hit_id)
        document["company"] = entity_name or _first_display_name(source.get("display_names"))
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
        cached_time = datetime.fromisoformat(cached_at)
        if cached_time.tzinfo is None:
            return None
        age_seconds = (datetime.now(timezone.utc) - cached_time).total_seconds()
    except (TypeError, ValueError):
        return None
    if age_seconds < 0 or age_seconds > CACHE_TTL_SECONDS:
        return None

    documents = cached.get("documents")
    return documents if isinstance(documents, list) else None


def _write_cache(company: str, documents: list[dict]) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = _cache_path(company)
        payload = {
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "documents": documents,
        }
        path.write_text(json.dumps(payload, indent=2))
    except (OSError, TypeError, ValueError):
        # Caching is optional; an unavailable cache must not hide fetched data.
        return


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


# --- SEC-only AI Factory discovery and financial facts -----------------------

AI_FACTORY_DISCOVERY_QUERIES = {
    "Compute/Server": '(GPU OR accelerator OR "AI server") AND "data center"',
    "Networking": '(networking OR ethernet OR optical) AND "data center"',
    "Power Infrastructure": '(switchgear OR generator OR power) AND "data center"',
    "Cooling Systems": '("liquid cooling" OR thermal OR HVAC) AND "data center"',
    "Engineering & Construction": '(construction OR engineering) AND "data center"',
}


def fetch_sec_listing(cik: str, user_agent: str | None = None) -> dict:
    """Return current ticker/exchange metadata for an SEC reporting company."""
    cik = str(cik).strip().zfill(10)
    if not cik.isdigit() or len(cik) != 10:
        raise ValueError("cik must contain up to 10 digits")
    agent = _resolve_user_agent(user_agent)
    request = urllib.request.Request(
        f"https://data.sec.gov/submissions/CIK{cik}.json",
        headers={"User-Agent": agent},
    )
    try:
        with _open_sec_request(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read())
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise ResearchSourceError(f"Could not retrieve SEC listing metadata for CIK {cik}") from exc
    if not isinstance(payload, dict):
        raise ResearchSourceError(f"Invalid SEC listing metadata for CIK {cik}")
    tickers = payload.get("tickers", [])
    exchanges = payload.get("exchanges", [])
    return {
        "tickers": [str(value) for value in tickers if str(value).strip()] if isinstance(tickers, list) else [],
        "exchanges": [str(value) for value in exchanges if str(value).strip()] if isinstance(exchanges, list) else [],
    }


def discover_ai_factory_companies(
    max_results_per_role: int = 50,
    max_companies: int = 20,
    listing_lookup=fetch_sec_listing,
) -> list[dict]:
    """Discover SEC-reporting companies from AI Factory filing keywords.

    This is intentionally a candidate universe, not a claim that every hit has
    direct revenue exposure. The research and review stages must validate that
    exposure before an analysis is treated as verified.
    """
    source = EdgarFullTextSearchSource(max_results=max_results_per_role)
    candidates: dict[str, dict] = {}
    recent_start = (datetime.now(timezone.utc) - timedelta(days=365 * 3)).date().isoformat()
    for role, query in AI_FACTORY_DISCOVERY_QUERIES.items():
        try:
            documents = source.search(query, start_date=recent_start)
        except ResearchSourceError:
            continue
        for document in documents:
            cik = str(document.get("cik", ""))
            company = str(document.get("company", "")).strip()
            if not cik or not company:
                continue
            candidate = candidates.setdefault(
                cik,
                {"company": company, "cik": cik, "role": role, "discovery_documents": []},
            )
            candidate["discovery_documents"].append(document)
    listed_candidates = []
    for candidate in candidates.values():
        try:
            listing = listing_lookup(candidate["cik"])
        except (ResearchSourceError, ValueError):
            continue
        if not listing.get("tickers") or not listing.get("exchanges"):
            continue
        candidate["ticker"] = listing["tickers"][0]
        candidate["exchange"] = listing["exchanges"][0]
        listed_candidates.append(candidate)
        if len(listed_candidates) >= max(1, max_companies):
            break
    return listed_candidates


def _latest_annual_value(facts: dict, tags: tuple[str, ...]) -> tuple[float, str]:
    """Return the most recently filed annual USD fact for the first available tag."""
    for tag in tags:
        concept = facts.get(tag, {}) if isinstance(facts, dict) else {}
        units = concept.get("units", {}) if isinstance(concept, dict) else {}
        rows = units.get("USD", []) if isinstance(units, dict) else []
        annual = [
            row for row in rows
            if isinstance(row, dict) and row.get("form") in {"10-K", "20-F", "40-F"}
            and row.get("fy") and row.get("val") is not None
        ]
        if annual:
            latest = max(annual, key=lambda row: (str(row.get("fy", "")), str(row.get("filed", ""))))
            try:
                return float(latest["val"]), str(latest.get("filed", ""))
            except (TypeError, ValueError):
                continue
    return 0.0, ""


def fetch_company_facts(cik: str, user_agent: str | None = None) -> dict:
    """Retrieve annual revenue and operating income from SEC Company Facts."""
    cik = str(cik).strip().zfill(10)
    if not cik.isdigit() or len(cik) != 10:
        raise ValueError("cik must contain up to 10 digits")
    agent = _resolve_user_agent(user_agent)
    request = urllib.request.Request(
        f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
        headers={"User-Agent": agent},
    )
    try:
        with _open_sec_request(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read())
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise ResearchSourceError(f"Could not retrieve SEC company facts for CIK {cik}") from exc

    facts = payload.get("facts", {}) if isinstance(payload, dict) else {}
    gaap = facts.get("us-gaap", {}) if isinstance(facts, dict) else {}
    operating_income, operating_filed = _latest_annual_value(gaap, ("OperatingIncomeLoss",))
    revenue, revenue_filed = _latest_annual_value(
        gaap,
        ("RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet", "Revenues"),
    )
    margin_pct = (operating_income / revenue * 100) if revenue else 0.0
    retrieved_at = datetime.now(timezone.utc).isoformat()
    return {
        "operating_margin_pct": margin_pct,
        "publication_date": max(operating_filed, revenue_filed),
        "retrieved_at": retrieved_at,
        "url": f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
        "title": f"SEC Company Facts: CIK {cik}",
        "source_type": "other",
        "supporting_text": "SEC XBRL annual operating income and revenue facts.",
    }
