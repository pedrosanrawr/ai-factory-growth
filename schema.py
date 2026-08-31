"""Shared data schema for the AI Factory Growth project."""


def empty_record() -> dict:
    """Return a blank company record used by every agent file."""
    return {
        # company_ingestion.py
        "company": "",
        "role": "",
        "short_description": "",
        "revenue_exposure_pct": 0.0,
        "operating_margin_pct": 0.0,
        "moat_notes": "",
        "growth_catalysts": "",
        "risk_notes": "",
        "source_links": "",
        "eff_score": 1,

        # evidence: list of citation dictionaries managed by evidence_store.py
        "evidence": [],
        # ISO 8601 date/time for the research used by the analysis
        "research_as_of": "",
        # One of: unavailable, fallback, needs_review, verified
        "analysis_status": "unavailable",
        # 0.0-1.0 confidence supplied by an evidence-backed analysis
        "analysis_confidence": None,

        # market_mapping.py
        "segment_weight": 0.0,

        # moat_analysis.py
        "moat_score": 0,

        # margin_analysis.py
        "margin_score": 0,

        # growth_forecast.py
        "growth_forecast_pct": 0.0,
        
        # risk_adjustment.py
        "concentration_risk": 0.0,
        "cyclicality_risk": 0.0,
        "execution_risk": 0.0,
        "risk_multiplier": 1.0,
        "adjusted_growth_pct": 0.0,

        # ranking.py
        "tafgs_score": 0.0,
        "rank": 0,

        # report.py
        "primary_risk": "",
        "status": "",
    }


SEGMENT_WEIGHTS = {
    "Compute/Server": 0.40,
    "Networking": 0.20,
    "Power Infrastructure": 0.15,
    "Cooling Systems": 0.15,
    "Engineering & Construction": 0.10,
}


MARGIN_SCORE_BANDS = [
    (40, 5),
    (30, 4),
    (20, 3),
    (10, 2),
    (0, 1),
]
