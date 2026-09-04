"""One evidence-grounded Gemini analysis per company for the free-tier queue.

This consolidates only the provider call. The moat, growth, risk, margin,
cross-validation, and ranking stages remain separate workflow responsibilities.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Callable
from typing import Any

from services.evidence_store import record_analysis_status
from services.llm_client import ask_llm_json, is_llm_configured


CACHE_TTL_SECONDS = 24 * 60 * 60
MIN_REQUEST_INTERVAL_SECONDS = 3.5
MAX_EVIDENCE_PER_ANALYSIS = 8
MAX_RATIONALE_CHARACTERS = 600
MAX_CITED_EVIDENCE = 3
_request_lock = threading.Lock()
_last_request_at = 0.0

RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "moat_score": {"type": "integer", "minimum": 0, "maximum": 5},
        "moat_rationale": {"type": "string", "minLength": 1, "maxLength": MAX_RATIONALE_CHARACTERS},
        "growth_forecast_pct": {"type": "number", "minimum": -100, "maximum": 500},
        "growth_rationale": {"type": "string", "minLength": 1, "maxLength": MAX_RATIONALE_CHARACTERS},
        "concentration_risk": {"type": "number", "minimum": 0, "maximum": 1},
        "cyclicality_risk": {"type": "number", "minimum": 0, "maximum": 1},
        "execution_risk": {"type": "number", "minimum": 0, "maximum": 1},
        "risk_rationale": {"type": "string", "minLength": 1, "maxLength": MAX_RATIONALE_CHARACTERS},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "evidence_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": MAX_CITED_EVIDENCE},
    },
    "required": [
        "moat_score", "moat_rationale", "growth_forecast_pct", "growth_rationale",
        "concentration_risk", "cyclicality_risk", "execution_risk", "risk_rationale",
        "confidence", "evidence_ids",
    ],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You are an equity-research analyst for AI Factory infrastructure.
Using only the supplied evidence, return one JSON assessment of the company's
competitive moat, three-year AI-driven revenue CAGR, and concentration,
cyclicality, and execution risks. Cite only supplied evidence URLs. Do not
calculate a final ranking or TAFGS score. Keep each rationale under 100 words
and cite at most three URLs."""


def _cache_path() -> Path:
    return Path(os.getenv("LLM_ANALYSIS_CACHE_PATH", ".cache/llm_analysis.json"))


def _cache_key(record: dict) -> str:
    evidence = record.get("evidence", [])
    fingerprint = {
        "company": record.get("company", ""),
        "cik": record.get("cik", ""),
        "evidence": [
            {
                "url": item.get("url", ""),
                "claim": item.get("claim", ""),
                "published_date": item.get("published_date", ""),
            }
            for item in evidence if isinstance(item, dict)
        ],
    }
    return hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest()


def _read_cache(key: str) -> dict | None:
    path = _cache_path()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        item = payload.get(key, {}) if isinstance(payload, dict) else {}
        created_at = datetime.fromisoformat(item.get("created_at", ""))
        analysis = item.get("analysis")
        if created_at.tzinfo and (datetime.now(timezone.utc) - created_at).total_seconds() <= CACHE_TTL_SECONDS and isinstance(analysis, dict):
            return analysis
    except (OSError, ValueError, TypeError):
        pass
    return None


def _write_cache(key: str, analysis: dict) -> None:
    path = _cache_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        if not isinstance(data, dict):
            data = {}
        data[key] = {"created_at": datetime.now(timezone.utc).isoformat(), "analysis": analysis}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    except (OSError, TypeError, ValueError):
        pass


def _known_evidence_ids(record: dict) -> set[str]:
    return {
        str(item.get("url", "")).strip()
        for item in record.get("evidence", [])
        if isinstance(item, dict) and item.get("url")
    }


def _prompt(record: dict) -> str:
    evidence_items = sorted(
        (
            item for item in record.get("evidence", [])
            if isinstance(item, dict) and item.get("url")
        ),
        key=lambda item: str(item.get("published_date", "")),
        reverse=True,
    )[:MAX_EVIDENCE_PER_ANALYSIS]
    evidence = "\n".join(
        f"- {item.get('url', '')}: {item.get('claim') or item.get('excerpt', '')}"
        for item in evidence_items
    )
    return (
        f"Company: {record.get('company', '')}\nRole: {record.get('role', '')}\n"
        f"Description: {record.get('short_description', '')}\n"
        f"Growth catalysts: {record.get('growth_catalysts', '')}\n"
        f"Existing risks: {record.get('risk_notes', '')}\n\nEvidence URLs (cite only these):\n{evidence}"
    )


def _wait_for_request_slot() -> None:
    global _last_request_at
    with _request_lock:
        remaining = MIN_REQUEST_INTERVAL_SECONDS - (time.monotonic() - _last_request_at)
        if remaining > 0:
            time.sleep(remaining)
        _last_request_at = time.monotonic()


def _retry_delay_seconds(error: str | None) -> float | None:
    """Read Gemini's explicit 429 retry delay without relying on SDK internals."""
    match = re.search(r"retry in\s+([0-9.]+)s", str(error or ""), re.IGNORECASE)
    return float(match.group(1)) + 0.5 if match else None


def _apply(record: dict, analysis: dict) -> bool:
    evidence_ids = analysis.get("evidence_ids", [])
    if not isinstance(evidence_ids, list) or not evidence_ids or not all(
        isinstance(value, str) and value in _known_evidence_ids(record) for value in evidence_ids
    ):
        return False
    record.update(
        {
            "moat_score": int(analysis["moat_score"]),
            "moat_rationale": analysis["moat_rationale"].strip(),
            "moat_evidence_ids": list(evidence_ids),
            "growth_forecast_pct": round(float(analysis["growth_forecast_pct"]), 4),
            "growth_rationale": analysis["growth_rationale"].strip(),
            "growth_evidence_ids": list(evidence_ids),
            "concentration_risk": float(analysis["concentration_risk"]),
            "cyclicality_risk": float(analysis["cyclicality_risk"]),
            "execution_risk": float(analysis["execution_risk"]),
            "risk_rationale": analysis["risk_rationale"].strip(),
            "risk_evidence_ids": list(evidence_ids),
            "analysis_confidence": round(float(analysis["confidence"]), 4),
            "analysis_status": record_analysis_status(record.get("evidence", [])),
            "research_as_of": datetime.now(timezone.utc).isoformat(),
            "_combined_llm_analysis": True,
        }
    )
    return True


def run(
    records: list[dict],
    *,
    progress_callback: Callable[[str], None] | None = None,
) -> list[dict]:
    """Populate all LLM-derived fields with one cached, throttled call/company."""
    if not is_llm_configured():
        return records
    eligible_records = [record for record in records if _known_evidence_ids(record)]
    total = len(eligible_records)
    for index, record in enumerate(eligible_records, start=1):
        company = str(record.get("company") or f"company {index}")
        if progress_callback:
            progress_callback(f"Gemini analysis {index}/{total}: {company}")
        # Specialist agents must not make their former separate Gemini calls,
        # even when this combined request falls back due to quota or bad output.
        record["_combined_llm_attempted"] = True
        key = _cache_key(record)
        cached = _read_cache(key)
        if cached and _apply(record, cached):
            if progress_callback:
                progress_callback(f"Gemini analysis {index}/{total}: {company} (cached)")
            continue
        _wait_for_request_slot()
        result = ask_llm_json(SYSTEM_PROMPT, _prompt(record), schema=RESPONSE_SCHEMA, max_tokens=2048)
        retry_delay = _retry_delay_seconds(result.error) if not result.ok else None
        if retry_delay is not None:
            if progress_callback:
                progress_callback(
                    f"Gemini analysis {index}/{total}: rate limited; waiting "
                    f"{retry_delay:.0f}s before retrying {company}."
                )
            time.sleep(retry_delay)
            _wait_for_request_slot()
            result = ask_llm_json(
                SYSTEM_PROMPT, _prompt(record), schema=RESPONSE_SCHEMA, max_tokens=2048
            )
        if result.ok and result.data and _apply(record, result.data):
            _write_cache(key, result.data)
        elif not result.ok:
            record["analysis_status"] = "fallback"
            record["_combined_llm_error"] = result.error or "Gemini analysis failed."
        else:
            record["_combined_llm_error"] = (
                "Gemini returned citations that did not match the supplied evidence."
            )
    return records
