import base64
import csv
from io import StringIO
from pathlib import Path


def build_export_csv(rows: list[dict]) -> bytes:
    buffer = StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "Rank",
            "Company",
            "Role",
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
    body = []
    for row in rows:
        margin_fill = "fill-red" if row["margin_pct"] < 0 else "fill-purple"
        body.append(
            "<tr>"
            f'<td class="company-cell">{row["company"]}</td>'
            f'<td class="role-cell">{row["role"]}</td>'
            f'<td class="small-center"><span class="dot-row">{moat_dots(row["moat"])}</span></td>'
            f"<td>{mini_bar(row['margin_pct'], 60, margin_fill)}</td>"
            f"<td>{mini_bar(row['growth_pct'], 60, 'fill-green')}</td>"
            f'<td class="eff-score">{row["eff_score"]}</td>'
            f'<td class="risk-cell"><span class="risk-badge">{row["primary_risk"]}</span></td>'
            "</tr>"
        )
    return (
        '<div class="table-card">'
        '<div class="table-header">'
        '<div class="table-header-left"><span class="table-header-icon">◫</span>'
        "<span>Company Ingestion &amp; Metric Editing</span></div></div>"
        '<table class="dashboard-table">'
        "<thead><tr>"
        "<th>Company</th><th>Role</th><th>Moat</th><th>Margin %</th><th>Growth %</th><th>Eff. Score</th><th>Primary Risk</th>"
        "</tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table></div>"
    )


def render_ranking_table(
    rows: list[dict],
    ranking_priority: str,
    risk_discount: int,
    power_weight: float,
) -> str:
    body = []
    for index, row in enumerate(rows, start=1):
        body.append(
            "<tr>"
            f'<td class="rank-cell">{index}</td>'
            f'<td class="company-cell">{row["company"]}</td>'
            f'<td class="role-cell">{row["role"]}</td>'
            f'<td class="metric-moat">{row["moat"]}</td>'
            f'<td class="metric-margin">{row["margin_pct"]:.1f}%</td>'
            f'<td class="metric-growth">{row["growth_pct"]:.1f}%</td>'
            f'<td class="metric-eff">{row["eff_score"]}</td>'
            f'<td class="risk-cell">{row["primary_risk"]}</td>'
            f'<td class="status-cell">{status_badge(row["status"])}</td>'
            f'<td class="small-center">{row["margin_score"]}</td>'
            f'<td class="metric-tafgs">{row["tafgs"]}</td>'
            "</tr>"
        )
    return (
        '<div class="table-card">'
        '<div class="table-header">'
        '<div class="table-header-left"><span class="table-header-icon rank">⇄</span>'
        f"<span>Ranking Output: {ranking_priority}</span></div>"
        f'<span class="table-pill">{len(rows)} Factories Sorted</span>'
        "</div>"
        '<table class="dashboard-table">'
        "<thead><tr>"
        "<th>Rank</th><th>Company</th><th>Role</th><th>Moat</th><th>Margin %</th><th>Growth %</th><th>Eff. Score</th><th>Primary Risk</th><th>Status</th><th>Margin</th><th>TAFGS</th>"
        "</tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table>"
        '<div class="summary-bar">'
        '<span class="summary-icon">🛡</span>'
        f"<span><strong>Agent Summary:</strong> Risk Discount of {risk_discount}% and Power Efficiency Weight of {power_weight:.1f}x applied globally across scores.</span>"
        "</div></div>"
    )
