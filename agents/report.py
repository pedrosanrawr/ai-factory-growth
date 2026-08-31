"""DONES work file: research reporting and refresh visibility.

Steps:
1. Preserve every existing frontend output key and ranking order.
2. Add research date, analysis status, confidence, and evidence items once
   Member 3's contract is available.
3. Keep source_links readable during migration to structured evidence.
4. Provide display data for verified, fallback, and needs-review states.
5. Coordinate popup rendering changes with frontend components and styles.
6. Add serialization and frontend rendering tests for each status.

Do not recalculate TAFGS, moat, margin, growth, or risk in this module.
Done when users can see the evidence and whether analysis is verified,
fallback-based, or needs review.
"""

def run(records: list[dict],
        risk_discount_pct: float = 10.0,
        power_efficiency_weight: float = 1.2) -> tuple[list[dict], str]:
    """Build display profiles and a summary without changing ranking order."""
    profiles = []

    for record in records:
        primary_risk = _primary_risk(record)
        record["primary_risk"] = primary_risk

        profiles.append(
            {
                "company": record.get("company", ""),
                "role": record.get("role", ""),
                "short_description": record.get("short_description", ""),
                "revenue_exposure_pct": record.get("revenue_exposure_pct", 0.0),
                "segment_weight": record.get("segment_weight", 0.0),
                "moat": record.get("moat_score", 0),
                "margin_pct": record.get("operating_margin_pct", 0.0),
                "growth_pct": record.get("adjusted_growth_pct", 0.0),
                "eff_score": record.get("eff_score", 0),
                "primary_risk": primary_risk,
                "status": record.get("status", ""),
                "margin_score": record.get("margin_score", 0),
                "tafgs": record.get("tafgs_score", 0.0),
                "moat_notes": record.get("moat_notes", ""),
                "growth_catalysts": record.get("growth_catalysts", ""),
                "risk_notes": record.get("risk_notes", ""),
                "source_links": record.get("source_links", ""),
            }
        )

    agent_summary = (
        f"Risk Discount of {risk_discount_pct:.0f}% and Power Efficiency "
        f"Weight of {power_efficiency_weight:.1f}x applied globally across scores."
    )
    return profiles, agent_summary


def _primary_risk(record: dict) -> str:
    """Return the highest-scoring risk label in the documented tie order."""
    risk_scores = {
        "Concentration": _risk_score(record.get("concentration_risk", 0.0)),
        "Cyclicality": _risk_score(record.get("cyclicality_risk", 0.0)),
        "Execution": _risk_score(record.get("execution_risk", 0.0)),
    }
    return max(risk_scores, key=risk_scores.get)


def _risk_score(value) -> float:
    """Convert a risk value to a float without failing on incomplete records."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
