"""DON work file: evidence-grounded three-year growth analysis.

Steps:
1. Keep ``run(records)`` and the existing ``[-100, 500]`` range guard.
2. Supply company context, growth catalysts, dated evidence, and CSV forecast
   to the structured Gemini helper.
3. Request forecast, concise rationale, confidence, and evidence reference IDs.
4. Validate the response, then clamp the numeric forecast using this module.
5. On missing evidence or a failed/invalid LLM response, retain the CSV value
   and record a fallback status.
6. Add tests for valid, malformed, out-of-range, missing-evidence, and
   fallback cases.

Do not rank records or alter the risk-adjustment or TAFGS formulas.
Done when the forecast is citation-backed, range-safe, and CSV compatible.
"""

import math
from datetime import datetime, timezone
from typing import Any

from services.llm_client import ask_llm_json, is_llm_configured
from services.evidence_store import record_analysis_status

FORECAST_MIN = -100.0
FORECAST_MAX = 500.0

_SYSTEM_PROMPT = """\
You are a senior equity research analyst specializing in AI infrastructure.
Given a company's profile and growth catalysts, estimate its 3-year
AI-driven revenue CAGR (compound annual growth rate) as a percentage.

Rules:
- Base your estimate only on the provided context and evidence.
- The forecast must be between -100.0 and 500.0.
- Provide a concise rationale (1-2 sentences).
- Assign a confidence score between 0.0 and 1.0.
- List the source URLs or titles you relied on as evidence_ids.
- Return ONLY valid JSON matching the supplied schema.
"""

GROWTH_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "forecast_pct": {"type": "number", "minimum": -100, "maximum": 500},
        "rationale": {"type": "string", "minLength": 1},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "evidence_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1},
    },
    "required": ["forecast_pct", "rationale", "confidence", "evidence_ids"],
    "additionalProperties": False,
}

_USER_PROMPT_TEMPLATE = """\
Company: {company}
AI Factory Role: {role}
Description: {description}
Growth Catalysts: {catalysts}
CSV growth forecast (for reference): {csv_forecast}%
Available evidence (only cite these URLs):
{evidence}

Provide an evidence-grounded 3-year AI-driven CAGR estimate.

Return ONLY a valid JSON object with these fields:
- forecast_pct: number (the 3-year CAGR percentage, between -100 and 500)
- rationale: string (1-2 sentence justification)
- confidence: number (0.0 to 1.0)
- evidence_ids: non-empty array of URLs copied exactly from the evidence above
"""


def _to_float(value: Any, default: float = 0.0) -> float:
    """Safe float parser that also rejects inf/nan."""
    try:
        parsed = float(value) if value is not None else default
        return parsed if math.isfinite(parsed) else default
    except (ValueError, TypeError):
        return default


def _clamp(value: float, lo: float, hi: float) -> float:
    """Clamp a value between lo and hi."""
    return max(lo, min(hi, value))


def _validate_response(data: dict[str, Any]) -> tuple[float, str, float, list[str]] | None:
    """Validate LLM JSON response. Returns (forecast, rationale, confidence, evidence_ids) or None."""
    if not isinstance(data, dict):
        return None

    forecast = _to_float(data.get("forecast_pct"), None)
    if forecast is None:
        return None

    rationale = data.get("rationale", "")
    if not isinstance(rationale, str) or not rationale.strip():
        rationale = "No rationale provided."

    confidence = _clamp(_to_float(data.get("confidence"), 0.0), 0.0, 1.0)
    evidence_ids = data.get("evidence_ids", [])
    if not isinstance(evidence_ids, list):
        evidence_ids = []

    return (forecast, rationale, confidence, evidence_ids)


def _validate_evidence_ids(evidence_ids: list[str], evidence: list[dict]) -> list[str] | None:
    """Accept only non-empty citations that match stored evidence URLs."""
    if not isinstance(evidence_ids, list) or not evidence_ids:
        return None

    known_urls = {
        str(item.get("url", "")).strip().lower()
        for item in evidence
        if isinstance(item, dict) and item.get("url")
    }
    validated = []
    for evidence_id in evidence_ids:
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            return None
        normalized = evidence_id.strip()
        if normalized.lower() not in known_urls:
            return None
        validated.append(normalized)
    return validated


def _fallback(record: dict, csv_growth: float, now_iso: str) -> None:
    """Set record to fallback state with CSV value."""
    record["growth_forecast_pct"] = round(csv_growth, 4)
    record["analysis_status"] = "fallback"
    record["analysis_confidence"] = None
    record["research_as_of"] = now_iso


def run(records: list[dict]) -> list[dict]:
    """Validate growth forecast and optionally enrich with LLM analysis."""
    llm_available = is_llm_configured()
    now_iso = datetime.now(timezone.utc).isoformat()

    for record in records:
        csv_growth = _clamp(_to_float(record.get("growth_forecast_pct", 0.0), 0.0),
                            FORECAST_MIN, FORECAST_MAX)

        if record.get("_combined_llm_attempted"):
            record["growth_forecast_pct"] = round(csv_growth, 4)
            continue

        evidence = record.get("evidence")
        if not llm_available or not isinstance(evidence, list) or not evidence:
            _fallback(record, csv_growth, now_iso)
            continue

        evidence_text = "\n".join(
            f"- {item.get('url', '')}: {item.get('claim', item.get('excerpt', ''))}"
            for item in evidence
            if isinstance(item, dict) and item.get("url")
        )
        if not evidence_text:
            _fallback(record, csv_growth, now_iso)
            continue

        user_prompt = _USER_PROMPT_TEMPLATE.format(
            company=record.get("company", "Unknown"),
            role=record.get("role", "Unknown"),
            description=record.get("short_description", ""),
            catalysts=record.get("growth_catalysts", ""),
            csv_forecast=record.get("growth_forecast_pct", 0.0),
            evidence=evidence_text,
        )

        try:
            result = ask_llm_json(
                system_prompt=_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                schema=GROWTH_RESPONSE_SCHEMA,
                temperature=0.2,
                max_tokens=800,
            )
        except Exception:
            _fallback(record, csv_growth, now_iso)
            continue

        if not result.ok:
            _fallback(record, csv_growth, now_iso)
            continue

        validated = _validate_response(result.data or {})
        if validated is None:
            _fallback(record, csv_growth, now_iso)
            continue

        llm_forecast, rationale, confidence, evidence_ids = validated
        validated_ids = _validate_evidence_ids(evidence_ids, evidence)
        if validated_ids is None:
            _fallback(record, csv_growth, now_iso)
            continue
        llm_forecast = _clamp(llm_forecast, FORECAST_MIN, FORECAST_MAX)

        record["growth_forecast_pct"] = round(llm_forecast, 4)
        record["analysis_confidence"] = round(confidence, 4)
        record["research_as_of"] = now_iso
        record["growth_rationale"] = rationale
        record["growth_evidence_ids"] = validated_ids
        record["analysis_status"] = record_analysis_status(evidence)

    return records
