"""ESPINOSA work file: evidence-grounded moat analysis.

Steps:
1. Keep ``run(records)`` compatible with the existing workflow.
2. Use Member 1's structured Gemini helper and Member 3's evidence contract.
3. Request score (0--5), rationale, confidence, and evidence reference IDs.
4. Validate every returned field and evidence reference before saving it.
5. If evidence or the LLM is unavailable, keep the existing CSV moat score.
6. Add tests for valid output, invalid output, invalid citations, and fallback.

Do not change the TAFGS formula, rank records, or remove CSV compatibility.
Done when the analysis is explainable, evidence-linked, and remains compatible
with CSV-only ranking.
"""

from __future__ import annotations

import logging
from typing import Any

from services.llm_client import ask_llm_json, is_llm_configured, LLMResult
from services.evidence_store import record_analysis_status

logger = logging.getLogger(__name__)

# ── JSON Schema the LLM must conform to ──────────────────────────────────

MOAT_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "moat_score": {
            "type": "integer",
            "minimum": 0,
            "maximum": 5,
            "description": "Competitive moat strength from 0 (none) to 5 (dominant).",
        },
        "rationale": {
            "type": "string",
            "minLength": 1,
            "description": "Concise explanation of the moat assessment.",
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Confidence in the assessment from 0.0 to 1.0.",
        },
        "evidence_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of evidence URLs that support this analysis.",
        },
    },
    "required": ["moat_score", "rationale", "confidence", "evidence_ids"],
    "additionalProperties": False,
}

# ── Prompt templates ──────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    "You are a financial analyst specializing in competitive moat assessment "
    "for AI infrastructure companies. Evaluate the company's competitive "
    "advantages and barriers to entry. You MUST cite only the provided "
    "evidence URLs in your evidence_ids array. Do NOT invent or fabricate "
    "any URLs."
)


def _build_user_prompt(record: dict) -> str:
    """Assemble a per-company prompt with available context and evidence."""
    company = record.get("company", "Unknown")
    role = record.get("role", "Unknown")
    description = record.get("short_description", "N/A")
    moat_notes = record.get("moat_notes", "N/A")
    csv_score = record.get("moat_score", 0)

    evidence_list = record.get("evidence", [])
    if evidence_list:
        evidence_text = "\n".join(
            f"  - [{e.get('title', 'Untitled')}]({e.get('url', '')}): "
            f"{e.get('claim', 'No claim')}"
            for e in evidence_list
            if isinstance(e, dict)
        )
    else:
        evidence_text = "  No evidence available."

    return (
        f"Company: {company}\n"
        f"Role: {role}\n"
        f"Description: {description}\n"
        f"Moat Notes: {moat_notes}\n"
        f"Current CSV Moat Score: {csv_score}\n"
        f"\nAvailable Evidence:\n{evidence_text}\n"
        f"\nProvide a moat score (0-5), rationale, confidence (0.0-1.0), "
        f"and a list of evidence URLs from the evidence above that support "
        f"your analysis. Only reference URLs that appear in the evidence list."
    )


# ── Validation helpers ────────────────────────────────────────────────────

def _clamp_score(value: Any) -> int:
    """Safely clamp a moat score to 0-5."""
    try:
        score = int(value)
    except (ValueError, TypeError):
        return 0
    return max(0, min(5, score))


def _clamp_confidence(value: Any) -> float:
    """Safely clamp confidence to 0.0-1.0."""
    try:
        conf = float(value)
    except (ValueError, TypeError):
        return 0.0
    return max(0.0, min(1.0, conf))


def _validate_evidence_ids(
    evidence_ids: list,
    record_evidence: list[dict],
) -> list[str] | None:
    """Verify every evidence_id from the LLM matches a stored evidence URL.

    Returns the validated list if all IDs are valid, or None if any ID is
    invalid (which triggers a fallback to the CSV score).
    """
    if not isinstance(evidence_ids, list):
        return None

    known_urls = {
        e.get("url", "").strip().lower()
        for e in record_evidence
        if isinstance(e, dict) and e.get("url")
    }

    validated = []
    for eid in evidence_ids:
        if not isinstance(eid, str) or not eid.strip():
            return None
        if eid.strip().lower() not in known_urls:
            return None
        validated.append(eid.strip())

    return validated


# ── Fallback (original CSV-only path) ────────────────────────────────────

def _apply_csv_fallback(record: dict, *, set_fallback_status: bool = True) -> None:
    """Clamp the existing CSV moat_score and mark as fallback."""
    record["moat_score"] = _clamp_score(record.get("moat_score", 0))
    if set_fallback_status:
        record["analysis_status"] = "fallback"


# ── LLM-backed analysis for a single record ──────────────────────────────

def _analyze_single_record(record: dict) -> None:
    """Run LLM-backed moat analysis on one record, with CSV fallback."""
    company = record.get("company", "Unknown")

    # Build prompt and call LLM
    user_prompt = _build_user_prompt(record)

    result: LLMResult = ask_llm_json(
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        schema=MOAT_RESPONSE_SCHEMA,
        temperature=0.2,
        max_tokens=800,
    )

    # Handle LLM failure
    if not result.ok:
        logger.warning(
            "LLM analysis failed for %s: [%s] %s",
            company,
            result.error_type,
            result.error,
        )
        _apply_csv_fallback(record)
        return

    data = result.data

    # Validate score
    llm_score = _clamp_score(data.get("moat_score"))

    # Validate confidence
    llm_confidence = _clamp_confidence(data.get("confidence"))

    # Validate rationale
    rationale = data.get("rationale", "")
    if not isinstance(rationale, str) or not rationale.strip():
        logger.warning("LLM returned empty rationale for %s; falling back.", company)
        _apply_csv_fallback(record)
        return

    # Validate evidence references
    evidence_ids = data.get("evidence_ids", [])
    record_evidence = record.get("evidence", [])

    validated_ids = _validate_evidence_ids(evidence_ids, record_evidence)
    if validated_ids is None:
        logger.warning(
            "LLM returned invalid evidence citations for %s; falling back.",
            company,
        )
        _apply_csv_fallback(record)
        return

    # All validation passed — apply LLM results
    record["moat_score"] = llm_score
    record["analysis_confidence"] = llm_confidence
    record["moat_rationale"] = rationale.strip()
    record["moat_evidence_ids"] = validated_ids
    record["analysis_status"] = record_analysis_status(record_evidence)


# ── Public entry point ────────────────────────────────────────────────────

def run(records: list[dict]) -> list[dict]:
    """Validate and optionally enhance each record's moat_score.

    When Gemini is configured and evidence is available, requests an
    LLM-backed assessment with score, rationale, confidence, and
    evidence citations. Falls back to the original CSV moat_score
    (clamped 0-5) whenever the LLM is unavailable or returns invalid data.
    """
    llm_available = is_llm_configured()

    for record in records:
        if llm_available and record.get("evidence"):
            try:
                _analyze_single_record(record)
            except Exception:
                logger.exception(
                    "Unexpected error analyzing %s; falling back.",
                    record.get("company", "Unknown"),
                )
                _apply_csv_fallback(record)
        else:
            # No LLM or no evidence — preserve CSV score with clamping
            record["moat_score"] = _clamp_score(record.get("moat_score", 0))

    return records
