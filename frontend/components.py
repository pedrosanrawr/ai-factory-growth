import base64
import csv
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
            f'{render_company_profile(row, index)}</div>'
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
    "needs_review": "Needs Review",
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
        source_type = escape(str(item.get("source_type", "other")))
        retrieved_date = escape(str(item.get("retrieved_date", "")))
        item_status = str(item.get("status", "needs_review")).strip() or "needs_review"
        status_class = RESEARCH_STATUS_CLASSES.get(item_status, "status-unavailable")
        status_label = RESEARCH_STATUS_LABELS.get(item_status, "Research Unavailable")

        parsed = urlparse(url)
        link_html = title
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            safe_url = escape(url, quote=True)
            link_html = f'<a class="evidence-link" href="{safe_url}" target="_blank" rel="noopener noreferrer">{title}</a>'

        items.append(
            '<li class="evidence-item">'
            f'<span class="evidence-item-title">{link_html}</span>'
            '<span class="evidence-item-meta">'
            f'<span class="evidence-source-type">{source_type}</span>'
            f'<span class="evidence-retrieved">Retrieved {retrieved_date}</span>'
            f'<span class="research-status-badge evidence-status {status_class}">'
            '<span class="status-dot"></span>'
            f"{escape(status_label)}</span>"
            "</span></li>"
        )

    return f'<ul class="evidence-list">{"".join(items)}</ul>'


def _source_links_html(source_links: str) -> str:
    """Turn pipe-separated safe URLs from the CSV into source links."""
    links = []
    for index, value in enumerate(str(source_links or "").split("|"), start=1):
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


def render_company_profile(row: dict, rank: int) -> str:
    """Render one detail view from the Report Agent's existing profile fields."""
    company = escape(str(row.get("company", "Company")))
    role = escape(str(row.get("role", "Unclassified")))
    description = escape(str(row.get("short_description", "No description provided.")))
    moat_notes = escape(str(row.get("moat_notes", "No moat narrative provided.")))
    catalysts = escape(str(row.get("growth_catalysts", "No growth catalysts provided.")))
    risks = escape(str(row.get("risk_notes", "No risk notes provided.")))
    revenue_exposure = float(row.get("revenue_exposure_pct", 0.0) or 0.0)
    segment_weight = float(row.get("segment_weight", 0.0) or 0.0)
    tafgs = row.get("tafgs", 0.0)
    analysis_status = row.get("analysis_status", "unavailable")
    analysis_confidence = row.get("analysis_confidence")
    research_as_of = escape(str(row.get("research_as_of", "")).strip() or "Not yet researched")
    evidence = row.get("evidence") or []

    return (
        '<div class="company-profile">'
        '<div class="profile-heading">'
        f'<span class="profile-rank">#{rank}</span><div><div class="profile-company">{company}</div>'
        f'<div class="profile-role">{role}</div></div>'
        f'<div class="profile-heading-status">{research_status_badge(analysis_status, analysis_confidence)}'
        f'<span class="research-as-of">As of {research_as_of}</span></div>'
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
        '<div class="profile-detail sources-detail"><span>Research Sources</span>'
        f'<div class="source-links">{_source_links_html(row.get("source_links", ""))}</div></div>'
        '<div class="profile-detail evidence-detail"><span>Evidence &amp; Refresh Status</span>'
        f'{_evidence_items_html(evidence)}</div>'
        '</div></div>'
    )
