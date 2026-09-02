"""LangGraph workflow and cross-validation for the AI Factory pipeline.

The graph preserves the existing deterministic scoring order. Its validation
gate never recalculates TAFGS: it corrects malformed agent inputs and marks
unsupported LLM output as ``needs_review`` before ranking proceeds.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from agents.company_ingestion import run as ingest_companies
from agents.growth_forecast import run as forecast_growth
from agents.margin_analysis import run as analyze_margin
from agents.market_mapping import run as map_segments
from agents.moat_analysis import run as analyze_moat
from agents.ranking import run as rank_companies
from agents.research_analysis import run as analyze_research
from agents.report import run as generate_report
from agents.risk_adjustment import enrich_risk_inputs, run as adjust_risk
from services.research_enrichment import enrich_records
from schema import SEGMENT_WEIGHTS


class WorkflowState(TypedDict, total=False):
    """Data passed between workflow nodes."""

    records: list[dict]
    ranked_records: list[dict]
    ingestion_rows: list[dict]
    ranked_rows: list[dict]
    agent_summary: str
    validation_errors: list[str]
    risk_discount: float
    power_weight: float
    ranking_priority: str
    role_filter: list[str]
    run_deep_research: bool
    progress_callback: Callable[[str], None]


VALID_ANALYSIS_STATUSES = {"unavailable", "fallback", "needs_review", "verified"}


def _as_finite_float(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
        return parsed if math.isfinite(parsed) else default
    except (TypeError, ValueError):
        return default


def _clamp(value: Any, low: float, high: float, default: float = 0.0) -> float:
    return max(low, min(high, _as_finite_float(value, default)))


def _has_verified_evidence(record: dict) -> bool:
    evidence = record.get("evidence", [])
    return isinstance(evidence, list) and any(
        isinstance(item, dict)
        and item.get("url")
        and item.get("status") == "verified"
        for item in evidence
    )


def _citations_are_known(record: dict) -> bool:
    """Ensure any agent citation list refers only to this record's evidence."""
    evidence = record.get("evidence", [])
    if not isinstance(evidence, list):
        return False
    known = {
        str(item.get("url", "")).strip().lower()
        for item in evidence
        if isinstance(item, dict) and item.get("url")
    }
    for field in ("moat_evidence_ids", "growth_evidence_ids", "risk_evidence_ids"):
        citations = record.get(field)
        if citations is None:
            continue
        if not isinstance(citations, list) or not citations:
            return False
        if any(not isinstance(value, str) or value.strip().lower() not in known for value in citations):
            return False
    return True


def cross_validate_records(records: list[dict]) -> tuple[list[dict], list[str]]:
    """Validate agent handoffs and return reviewable errors without rerunning LLMs."""
    errors: list[str] = []

    for index, record in enumerate(records):
        company = str(record.get("company") or f"record {index + 1}")
        invalid = False

        moat_score = _clamp(record.get("moat_score"), 0, 5)
        if moat_score != record.get("moat_score"):
            errors.append(f"{company}: corrected invalid moat_score.")
            record["moat_score"] = int(moat_score)
            invalid = True

        growth = _clamp(record.get("growth_forecast_pct"), -100, 500)
        if growth != record.get("growth_forecast_pct"):
            errors.append(f"{company}: corrected invalid growth_forecast_pct.")
            record["growth_forecast_pct"] = round(growth, 4)
            invalid = True

        for field in ("concentration_risk", "cyclicality_risk", "execution_risk"):
            score = _clamp(record.get(field), 0, 1)
            if score != record.get(field):
                errors.append(f"{company}: corrected invalid {field}.")
                record[field] = score
                invalid = True

        status = record.get("analysis_status", "unavailable")
        if status not in VALID_ANALYSIS_STATUSES:
            errors.append(f"{company}: replaced unknown analysis_status.")
            record["analysis_status"] = "needs_review"
            invalid = True
            status = "needs_review"

        confidence = record.get("analysis_confidence")
        if confidence is not None:
            normalized_confidence = _clamp(confidence, 0, 1)
            if normalized_confidence != confidence:
                errors.append(f"{company}: corrected invalid analysis_confidence.")
                record["analysis_confidence"] = normalized_confidence
                invalid = True

        if status == "verified" and (
            not _has_verified_evidence(record) or not _citations_are_known(record)
        ):
            errors.append(f"{company}: verified analysis lacks valid verified evidence.")
            record["analysis_status"] = "needs_review"
            invalid = True

        if invalid and record.get("analysis_status") == "verified":
            record["analysis_status"] = "needs_review"

    return records, errors


def _ingest(_: WorkflowState) -> WorkflowState:
    return {"records": ingest_companies(), "validation_errors": []}


def _map_segments(state: WorkflowState) -> WorkflowState:
    return {"records": map_segments(state["records"])}


def _research(state: WorkflowState) -> WorkflowState:
    """Attach external evidence only for an operator-requested refresh."""
    if not state.get("run_deep_research", False):
        # The specialist agents recognize this marker and retain the reviewed
        # CSV inputs instead of issuing their former individual Gemini calls.
        for record in state["records"]:
            record["_combined_llm_attempted"] = True
        return {"records": state["records"]}
    return {"records": enrich_records(state["records"])}


def _analyze_research(state: WorkflowState) -> WorkflowState:
    """Use one throttled Gemini request per company before specialist handoffs."""
    if not state.get("run_deep_research", False):
        return {"records": state["records"]}
    return {
        "records": analyze_research(
            state["records"], progress_callback=state.get("progress_callback")
        )
    }


def _analyze_moat(state: WorkflowState) -> WorkflowState:
    return {"records": analyze_moat(state["records"])}


def _analyze_margin(state: WorkflowState) -> WorkflowState:
    return {"records": analyze_margin(state["records"])}


def _forecast_growth(state: WorkflowState) -> WorkflowState:
    return {"records": forecast_growth(state["records"])}


def _analyze_risk(state: WorkflowState) -> WorkflowState:
    records = enrich_risk_inputs(state["records"])
    return {"records": adjust_risk(records, risk_discount_pct=state["risk_discount"])}


def _cross_validate(state: WorkflowState) -> WorkflowState:
    records, errors = cross_validate_records(state["records"])
    return {"records": records, "validation_errors": errors}


def _filter_roles(state: WorkflowState) -> WorkflowState:
    role_filter = state.get("role_filter", [])
    if not role_filter:
        return {"records": state["records"]}
    return {"records": [record for record in state["records"] if record.get("role") in role_filter]}


def _rank(state: WorkflowState) -> WorkflowState:
    return {
        "ranked_records": rank_companies(
            state["records"],
            ranking_priority=state["ranking_priority"],
            power_efficiency_weight=state["power_weight"],
        )
    }


def _report(state: WorkflowState) -> WorkflowState:
    ingestion_rows, _ = generate_report(
        state["records"],
        risk_discount_pct=state["risk_discount"],
        power_efficiency_weight=state["power_weight"],
    )
    ranked_rows, agent_summary = generate_report(
        state["ranked_records"],
        risk_discount_pct=state["risk_discount"],
        power_efficiency_weight=state["power_weight"],
    )
    return {
        "ingestion_rows": ingestion_rows,
        "ranked_rows": ranked_rows,
        "agent_summary": agent_summary,
    }


def build_workflow():
    """Build the complete, bounded LangGraph analysis workflow."""
    graph = StateGraph(WorkflowState)
    nodes = {
        "ingest": _ingest,
        "map_segments": _map_segments,
        "research": _research,
        "analyze_research": _analyze_research,
        "analyze_moat": _analyze_moat,
        "analyze_margin": _analyze_margin,
        "forecast_growth": _forecast_growth,
        "analyze_risk": _analyze_risk,
        "cross_validate": _cross_validate,
        "filter_roles": _filter_roles,
        "rank": _rank,
        "report": _report,
    }
    for name, node in nodes.items():
        graph.add_node(name, node)

    order = tuple(nodes)
    graph.add_edge(START, order[0])
    for current, following in zip(order, order[1:]):
        graph.add_edge(current, following)
    graph.add_edge(order[-1], END)
    return graph.compile()


def run_workflow(
    *,
    risk_discount: float,
    power_weight: float,
    ranking_priority: str,
    role_filter: list[str],
    run_deep_research: bool = False,
    progress_callback: Callable[[str], None] | None = None,
) -> WorkflowState:
    """Invoke the graph with the dashboard controls and return its final state."""
    return build_workflow().invoke(
        {
            "risk_discount": risk_discount,
            "power_weight": power_weight,
            "ranking_priority": ranking_priority,
            "role_filter": role_filter,
            "run_deep_research": run_deep_research,
            "progress_callback": progress_callback,
        }
    )
