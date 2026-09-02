"""Generate a deterministic investor-ready PDF from ranked company snapshots."""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from urllib.parse import urlparse
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# Print palette: strong enough for white paper and ordinary office printers.
NAVY = colors.HexColor("#10233D")
BLUE = colors.HexColor("#126A8A")
PANEL = colors.HexColor("#F2F6FA")
CYAN = colors.HexColor("#0A6F8F")
MUTED = colors.HexColor("#63758A")
INK = colors.HexColor("#1B2A3A")
WHITE = colors.white


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("InvestorTitle", parent=base["Title"], fontName="Helvetica-Bold", fontSize=23, leading=28, textColor=NAVY, spaceAfter=6),
        "subtitle": ParagraphStyle("InvestorSubtitle", parent=base["Normal"], fontSize=10, leading=14, textColor=MUTED, spaceAfter=18),
        "heading": ParagraphStyle("InvestorHeading", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=BLUE, spaceBefore=14, spaceAfter=7),
        "body": ParagraphStyle("InvestorBody", parent=base["BodyText"], fontSize=9.2, leading=13.5, textColor=INK, spaceAfter=7),
        "small": ParagraphStyle("InvestorSmall", parent=base["BodyText"], fontSize=7.5, leading=10, textColor=MUTED, spaceAfter=4),
        "table": ParagraphStyle("InvestorTable", parent=base["BodyText"], fontSize=7.4, leading=9, textColor=INK),
        "company": ParagraphStyle("InvestorCompany", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=NAVY, spaceBefore=5, spaceAfter=7),
    }


def _paragraph(value: object, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(str(value or "-")), style)


def _footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D7E0E9"))
    canvas.setLineWidth(0.5)
    canvas.line(0.55 * inch, 0.48 * inch, A4[0] - 0.55 * inch, 0.48 * inch)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(0.55 * inch, 0.35 * inch, "NEXOVYRE | AI Factory Growth Equity Research")
    canvas.drawRightString(A4[0] - 0.55 * inch, 0.35 * inch, f"Page {document.page}")
    canvas.restoreState()


def _source_hosts(value: object) -> str:
    """Return concise, readable source references instead of raw long URLs."""
    hosts: list[str] = []
    for source in str(value or "").split("|"):
        host = urlparse(source.strip()).netloc.removeprefix("www.")
        if host and host not in hosts:
            hosts.append(host)
    return "; ".join(hosts[:4]) or "No source link recorded"


def build_investor_report_pdf(
    rows: list[dict],
    *,
    ranking_priority: str,
    agent_summary: str,
) -> bytes:
    """Return a presentation-ready PDF without invoking any external services."""
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.6 * inch,
        title="AI Factory Growth Equity Research",
    )
    styles = _styles()
    story = [
        _paragraph("AI Factory Growth Equity Research", styles["title"]),
        _paragraph(
            f"Investor ranking report | Generated {datetime.now(timezone.utc):%d %b %Y} | Priority: {ranking_priority}",
            styles["subtitle"],
        ),
        _paragraph("Executive Summary", styles["heading"]),
        _paragraph(
            "This report ranks public companies with direct exposure to the AI Factory capital stack. "
            "Scores combine competitive moat, normalized operating margin, and AI-driven growth, with documented risk adjustments.",
            styles["body"],
        ),
        _paragraph(agent_summary, styles["small"]),
        _paragraph("Methodology", styles["heading"]),
        _paragraph(
            "TAFGS = Moat Score x Operating Margin Score x Risk-Adjusted AI-Driven Growth. "
            "The live ranking is deterministic; any research snapshot is prepared offline and cached before publication.",
            styles["body"],
        ),
        _paragraph("Top AI Factory Growth Ranking", styles["heading"]),
    ]
    header = ["Rank", "Company", "Role", "Moat", "Margin", "Growth", "TAFGS"]
    table_rows = [header]
    for row in rows:
        table_rows.append([
            str(row.get("rank", "")),
            _paragraph(row.get("company", ""), styles["table"]),
            _paragraph(row.get("role", ""), styles["table"]),
            str(row.get("moat", "")),
            f'{float(row.get("margin_pct", 0) or 0):.1f}%',
            f'{float(row.get("growth_pct", 0) or 0):.1f}%',
            f'{float(row.get("tafgs", 0) or 0):.3f}',
        ])
    ranking_table = Table(table_rows, colWidths=[0.38 * inch, 1.72 * inch, 1.12 * inch, 0.42 * inch, 0.6 * inch, 0.6 * inch, 0.55 * inch], repeatRows=1)
    ranking_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 1), (-1, -1), INK),
        ("BACKGROUND", (0, 1), (-1, -1), WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PANEL]),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C9D5E2")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([ranking_table, Spacer(1, 16), _paragraph("Company Profiles", styles["heading"])])

    for index, row in enumerate(rows):
        company = f'#{row.get("rank", index + 1)} {row.get("company", "")}'
        profile_metrics = Table(
            [[
                _paragraph("Role", styles["small"]),
                _paragraph("Moat", styles["small"]),
                _paragraph("Operating Margin", styles["small"]),
                _paragraph("AI Growth", styles["small"]),
                _paragraph("TAFGS", styles["small"]),
            ], [
                _paragraph(row.get("role", "-"), styles["table"]),
                _paragraph(row.get("moat", "-"), styles["table"]),
                _paragraph(f'{float(row.get("margin_pct", 0) or 0):.1f}%', styles["table"]),
                _paragraph(f'{float(row.get("growth_pct", 0) or 0):.1f}%', styles["table"]),
                _paragraph(f'{float(row.get("tafgs", 0) or 0):.3f}', styles["table"]),
            ]],
            colWidths=[1.55 * inch, 0.58 * inch, 1.15 * inch, 0.88 * inch, 0.65 * inch],
        )
        profile_metrics.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PANEL),
            ("BACKGROUND", (0, 1), (-1, -1), WHITE),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#C9D5E2")),
            ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D7E0E9")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.extend([
            _paragraph(company, styles["company"]),
            profile_metrics,
            _paragraph(f'Primary risk: {row.get("primary_risk", "-")}', styles["small"]),
            _paragraph("Investment Role", styles["heading"]),
            _paragraph(row.get("short_description", ""), styles["body"]),
            _paragraph("Moat & Differentiation", styles["heading"]),
            _paragraph(row.get("moat_notes", ""), styles["body"]),
            _paragraph("AI Growth Catalysts", styles["heading"]),
            _paragraph(row.get("growth_catalysts", ""), styles["body"]),
            _paragraph("Key Risks", styles["heading"]),
            _paragraph(row.get("risk_notes", ""), styles["body"]),
        ])
        story.extend([
            _paragraph("Referenced Sources", styles["heading"]),
            _paragraph(_source_hosts(row.get("source_links", "")), styles["small"]),
        ])
        if index < len(rows) - 1:
            story.append(Spacer(1, 14))

    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()
