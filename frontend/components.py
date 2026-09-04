import base64
import csv
import re
from html import escape
from io import StringIO
from pathlib import Path
from urllib.parse import urlparse


def build_export_csv(rows: list[dict]) -> bytes:
    buffer = StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "Rank",
            "Company",
            "Role",
            "Segment Spend Weight",
            "Revenue Exposure %",
            "Moat",
            "Margin %",
            "Growth %",
            "Eff. Score",
            "Primary Risk",
            "Status",
            "Margin Score",
            "TAFGS",
        ],
    )
    writer.writeheader()
    for index, row in enumerate(rows, start=1):
        writer.writerow(
            {
                "Rank": index,
                "Company": row["company"],
                "Role": row["role"],
                "Segment Spend Weight": row.get("segment_weight", 0.0),
                "Revenue Exposure %": row.get("revenue_exposure_pct", 0.0),
                "Moat": row["moat"],
                "Margin %": row["margin_pct"],
                "Growth %": row["growth_pct"],
                "Eff. Score": row["eff_score"],
                "Primary Risk": row["primary_risk"],
                "Status": row["status"],
                "Margin Score": row["margin_score"],
                "TAFGS": row["tafgs"],
            }
        )
    return buffer.getvalue().encode("utf-8")


def load_logo_html(path: str = "assets/logo.png") -> str:
    logo_path = Path(path)
    if not logo_path.exists():
        return ""

    try:
        encoded = base64.b64encode(logo_path.read_bytes()).decode()
        return (
            f'<img src="data:image/png;base64,{encoded}" '
            'alt="Logo" style="width:44px;height:auto;" />'
        )
    except OSError:
        return ""


def render_system_information_modal() -> str:
    """Render the teacher-facing methodology dialog for the dashboard header."""
    return (
        '<div id="system-methodology" class="profile-modal methodology-modal" '
        'role="dialog" aria-modal="true" aria-labelledby="methodology-title">'
        '<a class="profile-modal-backdrop" href="#" aria-label="Close system methodology"></a>'
        '<div class="profile-modal-panel methodology-modal-panel" role="document">'
        '<div class="profile-modal-topbar">'
        '<div><span id="methodology-title" class="profile-modal-kicker">'
        'About This System</span>'
        '<span class="profile-modal-caption">Methodology, data flow, and quality controls</span></div>'
        '<a class="profile-modal-close" href="#" aria-label="Close system methodology" '
        'title="Close information">'
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6.7 5.3 12 12-1.4 1.4-12-12zM17.3 5.3l1.4 1.4-12 12-1.4-1.4z"/></svg></a>'
        '</div>'
        '<div class="profile-modal-body methodology-body">'
        '<section class="methodology-intro">'
        '<span class="methodology-eyebrow">AI FACTORY GROWTH IDENTIFICATION</span>'
        '<h2>How the ranking is produced</h2>'
        '<p>This decision-support system identifies and ranks public companies positioned to benefit from the global build-out of AI factories and hyperscale data centers over the next three years.</p>'
        '</section>'
        '<section class="methodology-section">'
        '<div class="methodology-section-heading"><span>01</span><div><h3>AI Factory coverage</h3><p>Companies are classified by where they monetize infrastructure spending.</p></div></div>'
        '<div class="methodology-chip-row">'
        '<span>Compute / Server</span><span>Networking</span><span>Power Infrastructure</span>'
        '<span>Cooling Systems</span><span>Engineering &amp; Construction</span></div></section>'
        '<section class="methodology-section">'
        '<div class="methodology-section-heading"><span>02</span><div><h3>Eight-agent LangGraph pipeline</h3><p>LangGraph coordinates a defined handoff from company inputs to an investor-ready report.</p></div></div>'
        '<ol class="methodology-pipeline">'
        '<li><strong>Company Ingestion</strong><small>Loads the curated public-company universe.</small></li>'
        '<li><strong>Market Mapping</strong><small>Assigns the AI Factory segment and spend weight.</small></li>'
        '<li><strong>Moat Analysis</strong><small>Assesses differentiation and ecosystem lock-in.</small></li>'
        '<li><strong>Margin Analysis</strong><small>Normalizes operating-margin strength.</small></li>'
        '<li><strong>Growth Forecast</strong><small>Estimates three-year AI-driven growth.</small></li>'
        '<li><strong>Risk Adjustment</strong><small>Accounts for concentration, cyclicality, and execution risk.</small></li>'
        '<li><strong>Ranking</strong><small>Calculates the Total AI Factory Growth Score.</small></li>'
        '<li><strong>Report</strong><small>Presents the ordered Top 20 and company profiles.</small></li>'
        '</ol></section>'
        '<section class="methodology-section methodology-quality">'
        '<div class="methodology-section-heading"><span>03</span><div><h3>Data, research, and validation</h3></div></div>'
        '<div class="methodology-quality-grid">'
        '<div><strong>Curated baseline</strong><p>The standard dashboard uses the approved CSV company universe for fast, repeatable scoring.</p></div>'
        '<div><strong>Optional deep research</strong><p>SEC evidence and Gemini can enrich analysis when a research refresh is requested. Evidence remains reviewable.</p></div>'
        '<div><strong>Cross-validation gate</strong><p>Before ranking, the workflow checks score ranges, risk values, evidence status, and citation references between agent handoffs.</p></div>'
        '</div></section>'
        '<div class="methodology-note"><strong>Important:</strong> This is an educational equity-research decision-support tool, not investment advice. Research marked for review requires human validation.</div>'
        '</div></div></div>'
    )


def moat_dots(score: int) -> str:
    return "".join(
        f'<span class="dot {"active" if i < score else ""}"></span>'
        for i in range(5)
    )


def mini_bar(value: float, max_value: float, fill_class: str) -> str:
    width = 0 if max_value == 0 else max(0.0, min(abs(value) / max_value * 100, 100))
    return (
        '<div class="mini-bar-wrap">'
        f'<div class="mini-bar"><div class="mini-fill {fill_class}" style="width:{width:.1f}%"></div></div>'
        f"<span>{value:.0f}%</span>"
        "</div>"
    )


def status_badge(status: str) -> str:
    status_class = "profitable" if status == "Profitable" else "unprofitable"
    return (
        f'<span class="status-badge {status_class}">'
        '<span class="status-dot"></span>'
        f"{status}</span>"
    )


def render_ingestion_table(rows: list[dict]) -> str:
    should_scroll = len(rows) > 8
    scroll_class = "table-scroll scroll-enabled" if should_scroll else "table-scroll"
    body = []
    for row in rows:
        margin_fill = "fill-red" if row["margin_pct"] < 0 else "fill-purple"
        body.append(
            "<tr>"
            f'<td class="company-cell">{row["company"]}</td>'
            f'<td class="role-cell">{row["role"]}</td>'
            f'<td class="small-center"><span class="dot-row">{moat_dots(row["moat"])}</span></td>'
            f'<td class="mini-center">{mini_bar(row["margin_pct"], 60, margin_fill)}</td>'
            f'<td class="mini-center">{mini_bar(row["growth_pct"], 60, "fill-green")}</td>'
            f'<td class="eff-score">{row["eff_score"]}</td>'
            f'<td class="risk-cell center-cell"><span class="risk-badge">{row["primary_risk"]}</span></td>'
            "</tr>"
        )

    return (
        '<div class="table-card">'
        '<div class="table-header">'
        '<div class="table-header-left"><span class="table-header-icon">◫</span>'
        "<span>Company Ingestion &amp; Metric Editing</span></div></div>"
        f'<div class="{scroll_class}">'
        '<table class="dashboard-table">'
        "<thead><tr>"
        "<th>Company</th><th>Role</th><th>Moat</th><th>Margin %</th><th>Growth %</th><th>Eff. Score</th><th>Primary Risk</th>"
        "</tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table></div></div>"
    )


def render_ranking_table(
    rows: list[dict],
    ranking_priority: str,
    agent_summary: str,
) -> str:
    should_scroll = len(rows) > 8
    scroll_class = "table-scroll scroll-enabled" if should_scroll else "table-scroll"
    body = []
    profile_modals = []
    for index, row in enumerate(rows, start=1):
        company = str(row.get("company", ""))
        body.append(
            "<tr>"
            f'<td class="rank-cell">{index}</td>'
            f'<td class="company-cell">{row["company"]}</td>'
            f'<td class="role-cell">{row["role"]}</td>'
            f'<td class="metric-moat">{row["moat"]}</td>'
            f'<td class="metric-margin">{row["margin_pct"]:.1f}%</td>'
            f'<td class="metric-growth">{row["growth_pct"]:.1f}%</td>'
            f'<td class="metric-eff">{row["eff_score"]}</td>'
            f'<td class="risk-cell center-cell">{row["primary_risk"]}</td>'
            f'<td class="status-cell center-cell">{status_badge(row["status"])}</td>'
            f'<td class="small-center">{row["margin_score"]}</td>'
            f'<td class="metric-tafgs">{row["tafgs"]}</td>'
            '<td class="profile-action-cell">'
            f'<a class="profile-view-link" href="#company-profile-{index - 1}" '
            f'aria-label="View research profile for {escape(company, quote=True)}" title="View research profile">'
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5c-5.2 0-9.4 4.3-10.5 7 1.1 2.7 5.3 7 10.5 7s9.4-4.3 10.5-7C21.4 9.3 17.2 5 12 5Zm0 11.5A4.5 4.5 0 1 1 12 7a4.5 4.5 0 0 1 0 9.5Zm0-2A2.5 2.5 0 1 0 12 9a2.5 2.5 0 0 0 0 5.5Z"/></svg>'
            '<span>View</span></a></td>'
            "</tr>"
        )
        profile_modals.append(
            f'<div id="company-profile-{index - 1}" class="profile-modal" role="dialog" aria-modal="true">'
            '<div class="profile-modal-backdrop" aria-hidden="true"></div>'
            '<div class="profile-modal-panel" role="document">'
            '<div class="profile-modal-topbar">'
            '<div><span class="profile-modal-kicker">Company Research Profile</span>'
            '<span class="profile-modal-caption">Analysis, metrics, and source evidence</span></div>'
            '<a class="profile-modal-close" href="#" aria-label="Close company research profile" title="Close profile">'
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6.7 5.3 12 12-1.4 1.4-12-12zM17.3 5.3l1.4 1.4-12 12-1.4-1.4z"/></svg></a>'
            '</div>'
            f'<div class="profile-modal-body">{render_company_profile(row, index)}</div></div>'
            "</div>"
        )

    return (
        '<div class="table-card">'
        '<div class="table-header">'
        '<div class="table-header-left"><span class="table-header-icon rank">⇄</span>'
        f"<span>Ranking Output: {ranking_priority}</span></div>"
        f'<span class="table-pill">{len(rows)} Factories Sorted</span>'
        "</div>"
        f'<div class="{scroll_class}">'
        '<table class="dashboard-table">'
        "<thead><tr>"
        "<th>Rank</th><th>Company</th><th>Role</th><th>Moat</th><th>Margin %</th><th>Growth %</th><th>Eff. Score</th><th>Primary Risk</th><th>Status</th><th>Margin</th><th>TAFGS</th><th>Profile</th>"
        "</tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table></div>"
        '<div class="summary-bar">'
        '<span class="summary-icon">🛡</span>'
        f"<span><strong>Agent Summary:</strong> {agent_summary}</span>"
        f"</div></div>{''.join(profile_modals)}"
    )


def render_capital_stack_overview(
    rows: list[dict], segment_weights: dict[str, float]
) -> str:
    """Render the existing segment weights without changing the TAFGS formula."""
    active_counts = {role: 0 for role in segment_weights}
    for row in rows:
        role = row.get("role", "")
        if role in active_counts:
            active_counts[role] += 1

    segments = []
    for role, weight in segment_weights.items():
        segments.append(
            '<div class="stack-segment">'
            f'<div class="stack-segment-head"><span>{escape(role)}</span>'
            f'<strong>{weight:.0%}</strong></div>'
            f'<div class="stack-track"><div class="stack-fill" style="width:{weight * 100:.0f}%"></div></div>'
            f'<div class="stack-segment-foot">{active_counts[role]} companies in current view</div>'
            "</div>"
        )

    return (
        '<div class="stack-card">'
        '<div class="stack-title-row"><div>'
        '<div class="section-card-title">AI Factory Capital Stack</div>'
        '<div class="stack-subtitle">Reference share of AI Factory infrastructure spend</div>'
        '</div><span class="stack-badge">Market Mapping Agent</span></div>'
        f'<div class="stack-grid">{"".join(segments)}</div>'
        '</div>'
    )


RESEARCH_STATUS_LABELS = {
    "verified": "Verified",
    "needs_review": "New Source",
    "fallback": "Fallback (Unverified)",
    "unavailable": "Research Unavailable",
}
RESEARCH_STATUS_CLASSES = {
    "verified": "status-verified",
    "needs_review": "status-needs-review",
    "fallback": "status-fallback",
    "unavailable": "status-unavailable",
}


def research_status_badge(analysis_status: str, analysis_confidence=None) -> str:
    """Render the research-refresh status badge shown on a company profile.

    Falls back to an understandable "Research Unavailable" label for any
    status this design doesn't explicitly recognize, so the popup never
    silently shows a blank or raw internal status string.
    """
    status_key = str(analysis_status or "").strip() or "unavailable"
    label = RESEARCH_STATUS_LABELS.get(status_key, "Research Unavailable")
    status_class = RESEARCH_STATUS_CLASSES.get(status_key, "status-unavailable")

    confidence_html = ""
    if status_key == "verified" and isinstance(analysis_confidence, (int, float)):
        confidence_html = f'<span class="research-status-confidence">{analysis_confidence:.0%} confidence</span>'

    return (
        f'<span class="research-status-badge {status_class}">'
        '<span class="status-dot"></span>'
        f"{escape(label)}</span>{confidence_html}"
    )


def _evidence_items_html(evidence: list[dict]) -> str:
    """Render candidate/confirmed evidence items from evidence_store.py.

    Each item already carries its own per-source status (verified /
    needs_review / unavailable), which may differ from the company-level
    analysis_status, e.g. a company can be "needs_review" overall while
    having one older "verified" item alongside new unverified ones.
    """
    if not evidence:
        return (
            '<span class="profile-empty">No evidence on file yet — this '
            "company is pending its next research review.</span>"
        )

    items = []
    for item in evidence:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url", "")).strip()
        title = escape(str(item.get("title", "Untitled source")))
        item_status = str(item.get("status", "needs_review")).strip() or "needs_review"
        status_class = RESEARCH_STATUS_CLASSES.get(item_status, "status-unavailable")
        status_label = RESEARCH_STATUS_LABELS.get(item_status, "Research Unavailable")

        parsed = urlparse(url)
        link_html = title
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            safe_url = escape(url, quote=True)
            link_html = f'<a class="evidence-pill" href="{safe_url}" target="_blank" rel="noopener noreferrer">{title}'
            link_html += f'<span class="evidence-pill-status {status_class}">{escape(status_label)}</span></a>'

        if link_html == title:
            link_html = (
                f'<span class="evidence-pill">{title}'
                f'<span class="evidence-pill-status {status_class}">{escape(status_label)}</span></span>'
            )

        items.append(
            f'<li class="evidence-item">{link_html}</li>'
        )

    return f'<ul class="evidence-list">{"".join(items)}</ul>'


def _source_links_html(source_links: str) -> str:
    """Turn pipe-separated safe URLs from the CSV into source links."""
    links = []
    normalized_links = re.sub(r"(?<!:)//(?=www\.)", "|https://", str(source_links or ""))
    for index, value in enumerate(normalized_links.split("|"), start=1):
        url = value.strip()
        parsed = urlparse(url)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            host = escape(parsed.netloc.removeprefix("www."))
            safe_url = escape(url, quote=True)
            links.append(
                f'<a class="source-link" href="{safe_url}" target="_blank" '
                f'rel="noopener noreferrer">Source {index} · {host}</a>'
            )
    return "".join(links) or '<span class="profile-empty">No source link provided.</span>'


def _display_narrative(analysis: object, baseline: object) -> str:
    """Keep citations in the evidence contract, not inside investor-facing prose."""
    narrative = str(analysis or baseline or "No analysis provided.")
    narrative = re.sub(
        r"\bAs cited in\s+https?://[^\s,]+\s+and\s+https?://[^\s,]+,\s*its\b",
        "Its",
        narrative,
        flags=re.IGNORECASE,
    )
    narrative = re.sub(r"\s*\(\s*(?:source:\s*)?https?://[^)]*\)", "", narrative, flags=re.IGNORECASE)
    narrative = re.sub(r"https?://[^\s,)]*", "", narrative)
    narrative = re.sub(r"\bAs cited in(?:\s+and)?\s*,?\s*", "", narrative, flags=re.IGNORECASE)
    narrative = re.sub(r"\.\s+its\b", ". Its", narrative)
    narrative = re.sub(r"\s+([,.;:])", r"\1", narrative)
    narrative = re.sub(r"\s{2,}", " ", narrative).strip()
    return escape(narrative)


def render_company_profile(row: dict, rank: int) -> str:
    """Render one detail view from the Report Agent's existing profile fields."""
    company = escape(str(row.get("company", "Company")))
    role = escape(str(row.get("role", "Unclassified")))
    description = escape(str(row.get("short_description", "No description provided.")))
    moat_notes = _display_narrative(row.get("moat_rationale"), row.get("moat_notes", "No moat narrative provided."))
    catalysts = _display_narrative(row.get("growth_rationale"), row.get("growth_catalysts", "No growth catalysts provided."))
    risks = _display_narrative(row.get("risk_rationale"), row.get("risk_notes", "No risk notes provided."))
    revenue_exposure = float(row.get("revenue_exposure_pct", 0.0) or 0.0)
    segment_weight = float(row.get("segment_weight", 0.0) or 0.0)
    tafgs = row.get("tafgs", 0.0)
    analysis_status = row.get("analysis_status", "unavailable")
    analysis_confidence = row.get("analysis_confidence")
    research_as_of = escape(
        str(row.get("research_as_of", "")).strip() or "Baseline data"
    )
    evidence = row.get("evidence") or []
    source_links = (
        '<div class="profile-detail sources-detail"><span>Source Links</span>'
        f'<div class="source-links">{_source_links_html(row.get("source_links", ""))}</div></div>'
    )
    llm_badge = (
        '<span class="llm-analysis-badge">&#10022; Gemini Enhanced</span>'
        if row.get("gemini_enhanced") or row.get("_cached_llm_analysis")
        else ""
    )
    profile_prefix = '<div class="company-profile">'
    if llm_badge:
        profile_prefix += (
            '<div class="profile-ai-enhanced-row">'
            f'<span class="profile-ai-enhanced-snapshot">Research snapshot: {research_as_of}</span>'
            f'{llm_badge}</div>'
        )

    return profile_prefix + (
        '<div class="profile-heading">'
        f'<span class="profile-rank">#{rank}</span><div><div class="profile-company">{company}</div>'
        f'<div class="profile-role">{role}</div></div>'
        f'<div class="profile-heading-status">{research_status_badge(analysis_status, analysis_confidence)}'
        '</div>'
        '</div>'
        f'<p class="profile-description">{description}</p>'
        '<div class="profile-metrics">'
        f'<div><span>Revenue Exposure</span><strong>{revenue_exposure:.1f}%</strong></div>'
        f'<div><span>Segment Weight</span><strong>{segment_weight:.0%}</strong></div>'
        f'<div><span>TAFGS</span><strong>{tafgs}</strong></div>'
        '</div>'
        '<div class="profile-detail-grid">'
        f'<div class="profile-detail moat-detail"><span>Moat &amp; Differentiation</span><p>{moat_notes}</p></div>'
        f'<div class="profile-detail growth-detail"><span>AI Growth Catalysts</span><p>{catalysts}</p></div>'
        f'<div class="profile-detail risk-detail"><span>Key Risks</span><p>{risks}</p></div>'
        f'{source_links}'
        '<div class="profile-detail evidence-detail"><span>Research Evidence</span>'
        f'{_evidence_items_html(evidence)}</div>'
        '</div></div>'
    )
