"""DE JESUS work file: evidence-grounded risk inputs.

Steps:
1. Keep the existing risk multiplier and global discount formulas unchanged.
2. Use structured Gemini output only for concentration, cyclicality, and
   execution sub-scores, rationale, confidence, and evidence IDs.
3. Validate and clamp every sub-score to 0--1 before applying this formula.
4. Retain the current CSV risk inputs when evidence or LLM output is invalid.
5. Record whether the result is verified, needs review, or a fallback.
6. Add tests for bounds, invalid citations, provider failure, and formula
   regression.

Do not let model output calculate risk_multiplier, adjusted growth, rank, or
TAFGS. The deterministic risk formula remains the final authority.
"""

from __future__ import annotations

import datetime as _dt
import logging
from typing import Any

from services.llm_client import ask_llm_json, is_llm_configured

logger = logging.getLogger(__name__)

# (temporary default)
DEFAULT_CONFIDENCE_THRESHOLD = 0.75


RISK_SUBSCORE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "concentration_risk": {"type": "number", "minimum": 0, "maximum": 1},
        "cyclicality_risk": {"type": "number", "minimum": 0, "maximum": 1},
        "execution_risk": {"type": "number", "minimum": 0, "maximum": 1},
        "rationale": {"type": "string", "minLength": 1},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "evidence_ids": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "concentration_risk",
        "cyclicality_risk",
        "execution_risk",
        "rationale",
        "confidence",
        "evidence_ids",
    ],
    "additionalProperties": False,
}

SYSTEM_PROMPT = (
    "You are a risk analyst for an AI-infrastructure investment research "
    "tool. Given a company's profile and a list of already-verified "
    "evidence citations, estimate three risk sub-scores on a 0.0-1.0 "
    "scale: concentration_risk (customer/revenue concentration), "
    "cyclicality_risk (exposure to capex or demand cycles), and "
    "execution_risk (delivery, integration, or operational execution "
    "risk). Base every score only on the supplied evidence. Cite the "
    "evidence IDs you actually relied on in evidence_ids -- never invent "
    "an ID that is not in the supplied list. If the evidence is "
    "insufficient to fully support a score, still provide your best "
    "estimate but report a low confidence value."
)


def _clamp(value, lo=0.0, hi=1.0) -> float:
    """Clamp a value between lo and hi, safely handling non-numeric input."""
    try:
        return max(lo, min(hi, float(value)))
    except (ValueError, TypeError):
        return lo


def _build_user_prompt(record: dict) -> str:
    """Assemble the evidence-grounded prompt for a single company record."""
    evidence = record.get("evidence") or []
    evidence_lines = (
        "\n".join(
            f"- id={_evidence_identifier(item)}: "
            f"{item.get('claim', item.get('excerpt', item.get('snippet', '')))}"
            for item in evidence
            if isinstance(item, dict) and _evidence_identifier(item)
        )
        or "(no evidence available)"
    )

    return (
        f"Company: {record.get('company', '')}\n"
        f"Role: {record.get('role', '')}\n"
        f"Description: {record.get('short_description', '')}\n"
        f"Growth catalysts: {record.get('growth_catalysts', '')}\n"
        f"Existing risk notes: {record.get('risk_notes', '')}\n\n"
        f"Evidence (only cite these IDs):\n{evidence_lines}"
    )


def _evidence_identifier(item: dict) -> str:
    """Use the approved evidence URL, with legacy ``id`` as a fallback."""
    return str(item.get("url") or item.get("id") or "").strip()


def _valid_evidence_ids(record: dict, evidence_ids: Any) -> bool:
    """True only if evidence_ids is non-empty and every ID is known to this record.

    An empty list, a non-list, or any ID not present in record["evidence"]
    counts as invalid -- fall back to Deterministic CSV values rather than trusting the model output.
    """
    if not isinstance(evidence_ids, list) or not evidence_ids:
        return False

    known_ids = {
        _evidence_identifier(item)
        for item in (record.get("evidence") or [])
        if isinstance(item, dict) and _evidence_identifier(item)
    }
    return all(isinstance(eid, str) and eid in known_ids for eid in evidence_ids)


def enrich_risk_inputs(
    records: list[dict],
    *,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> list[dict]:
    """Populate risk sub-scores from evidence-grounded Gemini output where possible.

    For each record:
      - If no Gemini API key is configured locally, leave the existing
        concentration_risk / cyclicality_risk / execution_risk values (from
        the CSV) untouched and set analysis_status = "unavailable".
      - If Gemini is configured but the call fails (timeout, provider error,
        malformed response) or cites evidence IDs that don't exist in this
        record's evidence list, leave the CSV values untouched and set
        analysis_status = "fallback".
      - If Gemini succeeds with verifiable citations, overwrite the three
        risk sub-scores with the (clamped) model output, set
        analysis_confidence and research_as_of, and set analysis_status to
        "verified" or "needs_review" depending on confidence_threshold.

    This function never computes risk_multiplier, adjusted_growth_pct,
    rank, or TAFGS -- that remains the sole responsibility of run(), which
    is unchanged below and simply consumes whatever risk sub-scores end up
    on the record, however they got there.
    """
    configured = is_llm_configured()

    for record in records:
        if record.get("_combined_llm_attempted"):
            continue
        if not configured or not any(
            _evidence_identifier(item)
            for item in (record.get("evidence") or [])
            if isinstance(item, dict)
        ):
            record["analysis_status"] = "unavailable"
            record["analysis_confidence"] = None
            continue

        try:
            result = ask_llm_json(
                SYSTEM_PROMPT,
                _build_user_prompt(record),
                schema=RISK_SUBSCORE_SCHEMA,
            )
        except Exception:
            logger.exception(
                "Unexpected error calling Gemini for %s",
                record.get("company"),
            )
            record["analysis_status"] = "fallback"
            record["analysis_confidence"] = None
            continue

        if not result.ok:
            logger.warning(
                "Gemini risk analysis failed for %s: [%s] %s",
                record.get("company"),
                result.error_type,
                result.error,
            )
            record["analysis_status"] = "fallback"
            record["analysis_confidence"] = None
            continue

        data = result.data or {}
        evidence_ids = data.get("evidence_ids", [])

        if not _valid_evidence_ids(record, evidence_ids):
            logger.warning(
                "Gemini cited unverifiable evidence for %s: %r",
                record.get("company"),
                evidence_ids,
            )
            record["analysis_status"] = "fallback"
            record["analysis_confidence"] = None
            continue

        confidence = _clamp(data.get("confidence", 0.0))

        record["concentration_risk"] = _clamp(data.get("concentration_risk", 0.0))
        record["cyclicality_risk"] = _clamp(data.get("cyclicality_risk", 0.0))
        record["execution_risk"] = _clamp(data.get("execution_risk", 0.0))
        record["analysis_confidence"] = confidence
        record["research_as_of"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
        record["analysis_status"] = (
            "verified" if confidence >= confidence_threshold else "needs_review"
        )

    return records


def run(records: list[dict], risk_discount_pct: float = 10.0) -> list[dict]:
    """Apply deterministic risk adjustments to each record's growth forecast. """
    try:
        global_pct = float(risk_discount_pct)
    except (ValueError, TypeError):
        global_pct = 10.0
    global_pct = max(0.0, min(30.0, global_pct))
    global_discount = 1 - (global_pct / 100)

    for record in records:
        growth_forecast_pct = record.get("growth_forecast_pct", 0.0) or 0.0
        try:
            growth_forecast_pct = float(growth_forecast_pct)
        except (ValueError, TypeError):
            growth_forecast_pct = 0.0

        concentration_risk = _clamp(record.get("concentration_risk", 0.0))
        cyclicality_risk = _clamp(record.get("cyclicality_risk", 0.0))
        execution_risk = _clamp(record.get("execution_risk", 0.0))

        try:
            eff_score = float(record.get("eff_score", 1))
        except (ValueError, TypeError):
            eff_score = 1.0
        eff_score = max(1.0, min(5.0, eff_score))

        avg_risk = (concentration_risk + cyclicality_risk + execution_risk) / 3
        base_multiplier = 1 - (avg_risk * 0.3)
        eff_modifier = 1 + ((eff_score - 1) / 4) * 0.1
        risk_multiplier = base_multiplier * eff_modifier
        adjusted_growth_pct = growth_forecast_pct * risk_multiplier * global_discount

        record["risk_multiplier"] = round(risk_multiplier, 4)
        record["adjusted_growth_pct"] = round(adjusted_growth_pct, 4)

    return records

