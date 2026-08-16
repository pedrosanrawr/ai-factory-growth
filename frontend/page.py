import streamlit as st
import base64

from frontend.components import (
    build_export_csv,
    load_logo_html,
    render_ingestion_table,
    render_ranking_table,
)
from frontend.data import COMPANIES, ROLE_OPTIONS
from frontend.styles import APP_CSS


def render_app() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)

    logo_img = load_logo_html()
    csv_data = build_export_csv(COMPANIES)
    csv_base64 = base64.b64encode(csv_data).decode("utf-8")

    st.markdown(
        f"""
        <div class="top-shell">
            <div class="top-shell-inner">
                <div class="brand-wrap">
                    <div class="brand-icon">{logo_img}</div>
                    <div>
                        <div class="brand-title">Agentic Control Panel</div>
                        <div class="brand-subtitle">NEXOVYRE</div>
                    </div>
                </div>
                <a
                    class="export-button"
                    href="data:text/csv;base64,{csv_base64}"
                    download="top_ai_factory_analysis_ui.csv"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                    >
                        <path
                            d="M0 0h24v24H0z"
                            fill="none"
                        />
                        <path
                            fill="currentColor"
                            d="M11.625 15.513q-.175-.063-.325-.213l-3.6-3.6q-.3-.3-.288-.7t.288-.7q.3-.3.713-.312t.712.287L11 12.15V5q0-.425.288-.712T12 4t.713.288T13 5v7.15l1.875-1.875q.3-.3.713-.288t.712.313q.275.3.288.7t-.288.7l-3.6 3.6q-.15.15-.325.213t-.375.062t-.375-.062M6 20q-.825 0-1.412-.587T4 18v-2q0-.425.288-.712T5 15t.713.288T6 16v2h12v-2q0-.425.288-.712T19 15t.713.288T20 16v2q0 .825-.587 1.413T18 20z"
                        />
                    </svg>
                    <span>Export Report</span>
                </a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="hero-title">Top AI Factory Analysis</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hero-subtitle">Agentic Evaluation Matrix for Compute Infrastructure</p>',
        unsafe_allow_html=True,
    )

    control_left, control_right = st.columns([3, 2])
    with control_left:
        risk_discount = render_risk_slider()
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        power_weight = render_power_slider()
    with control_right:
        ranking_priority = render_priority_radio()

    role_filter = st.multiselect(
        "Filter by AI Factory Role",
        options=ROLE_OPTIONS,
        default=ROLE_OPTIONS[:5],
        label_visibility="collapsed",
    )

    chip_html = "".join(f'<span class="chip">{role}</span>' for role in role_filter)
    st.markdown(
        f"""
        <div class="chip-box">
            <div class="chip-title">Filter by AI Factory Role</div>
            <div class="chip-row">{chip_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    filtered_rows = [row for row in COMPANIES if row["role"] in role_filter] if role_filter else COMPANIES[:]
    ranked_rows = rank_rows(filtered_rows, ranking_priority)

    st.markdown(render_ingestion_table(filtered_rows), unsafe_allow_html=True)
    st.markdown(
        render_ranking_table(ranked_rows, ranking_priority, risk_discount, power_weight),
        unsafe_allow_html=True,
    )


def render_risk_slider() -> int:
    current_value = st.session_state.get("risk_discount", 10)
    st.markdown(
        f"""
        <div class="section-card">
            <div class="range-label">
                <span>Risk Adjustment Agent Discount</span>
                <span class="range-value">{current_value}%</span>
            </div>
        """,
        unsafe_allow_html=True,
    )
    value = st.slider(
        "Risk Adjustment Agent Discount",
        min_value=0,
        max_value=30,
        value=10,
        step=5,
        label_visibility="collapsed",
        key="risk_discount",
    )
    st.markdown("</div>", unsafe_allow_html=True)
    return value


def render_power_slider() -> float:
    current_value = st.session_state.get("power_weight", 1.2)
    st.markdown(
        f"""
        <div class="section-card">
            <div class="range-label">
                <span>Power Efficiency Weighting</span>
                <span class="range-value">{current_value:.2f}x</span>
            </div>
        """,
        unsafe_allow_html=True,
    )
    value = st.slider(
        "Power Efficiency Weighting",
        min_value=1.0,
        max_value=2.0,
        value=1.2,
        step=0.1,
        label_visibility="collapsed",
        key="power_weight",
    )
    st.markdown("</div>", unsafe_allow_html=True)
    return value


def render_priority_radio() -> str:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-card-title">Ranking Agent Priority</div>
        """,
        unsafe_allow_html=True,
    )
    value = st.radio(
        "Ranking Agent Priority",
        options=["Profitability First", "Growth % (Highest)", "TAFGS Score"],
        index=0,
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)
    return value


def rank_rows(rows: list[dict], ranking_priority: str) -> list[dict]:
    if ranking_priority == "Profitability First":
        return sorted(
            rows,
            key=lambda row: (row["status"] == "Profitable", row["margin_score"], row["tafgs"]),
            reverse=True,
        )
    if ranking_priority == "Growth % (Highest)":
        return sorted(rows, key=lambda row: row["growth_pct"], reverse=True)
    return sorted(rows, key=lambda row: row["tafgs"], reverse=True)
