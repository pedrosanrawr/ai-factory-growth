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

"""


def fetch_company_research(company: str) -> list[dict]:
    """Return normalized candidate research documents for one company."""
    # TODO(1): Choose an approved source provider and document its fields.
    # TODO(2): Fetch research with a timeout and safe error handling.
    # TODO(3): Normalize title, URL, source type, publication date, retrieval
    #          date, and supporting text into a consistent dictionary shape.
    # TODO(4): Return candidate evidence only; never overwrite CSV facts here.
    # TODO(5): Add fixture-based tests without calling the live provider.
    pass
