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

def _clamp(value, lo=0.0, hi=1.0) -> float:
    """Clamp a value between lo and hi, safely handling non-numeric input."""
    try:
        return max(lo, min(hi, float(value)))
    except (ValueError, TypeError):
        return lo


def run(records: list[dict], risk_discount_pct: float = 10.0) -> list[dict]:
    """Apply deterministic risk adjustments to each record's growth forecast."""
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
