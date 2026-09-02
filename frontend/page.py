import streamlit as st
import base64

from frontend.components import (
    render_capital_stack_overview,
    load_logo_html,
    render_ingestion_table,
    render_ranking_table,
)
from frontend.styles import APP_CSS
from schema import SEGMENT_WEIGHTS
from services.investor_report import build_investor_report_pdf
from workflow import run_workflow


ROLE_OPTIONS = list(SEGMENT_WEIGHTS)


def render_app() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)

    logo_img = load_logo_html()
    risk_discount = st.session_state.get("risk_discount", 10)
    power_weight = st.session_state.get("power_weight", 1.2)
    ranking_priority = st.session_state.get("ranking_priority", "Profitability First")
    role_filter = st.session_state.get("role_filter", ROLE_OPTIONS[:])

    try:
        with st.spinner("Loading curated AI Factory rankings..."):
            ingestion_rows, ranked_rows, agent_summary = run_pipeline(
                risk_discount=risk_discount,
                power_weight=power_weight,
                ranking_priority=ranking_priority,
                role_filter=role_filter,
            )
    except (FileNotFoundError, ValueError) as error:
        st.error(f"Unable to load the company analysis pipeline: {error}")
        return

    pdf_data = build_investor_report_pdf(
        ranked_rows,
        ranking_priority=ranking_priority,
        agent_summary=agent_summary,
    )
    pdf_base64 = base64.b64encode(pdf_data).decode("utf-8")

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
                    href="data:application/pdf;base64,{pdf_base64}"
                    download="ai_factory_growth_investor_report.pdf"
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
                    <span>Export PDF</span>
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
        st.markdown("<div style='height: 0px;'></div>", unsafe_allow_html=True)
        power_weight = render_power_slider()
    with control_right:
        ranking_priority = render_priority_radio()

    role_filter = render_role_filter_card()

    st.markdown(
        render_capital_stack_overview(ranked_rows, SEGMENT_WEIGHTS),
        unsafe_allow_html=True,
    )
    st.markdown(render_ingestion_table(ingestion_rows), unsafe_allow_html=True)
    st.markdown(
        render_ranking_table(ranked_rows, ranking_priority, agent_summary),
        unsafe_allow_html=True,
    )



def render_risk_slider() -> int:
    current_value = st.session_state.get("risk_discount", 10)
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="control-card-marker slider-control">
                <div class="range-label">
                    <span>Risk Adjustment Agent Discount</span>
                    <span class="range-value">{current_value}%</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return st.slider(
            "Risk Adjustment Agent Discount",
            min_value=0,
            max_value=30,
            value=10,
            step=5,
            label_visibility="collapsed",
            key="risk_discount",
        )


def render_power_slider() -> float:
    current_value = st.session_state.get("power_weight", 1.2)
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="control-card-marker slider-control">
                <div class="range-label">
                    <span>Power Efficiency Weighting</span>
                    <span class="range-value">{current_value:.2f}x</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return st.slider(
            "Power Efficiency Weighting",
            min_value=1.0,
            max_value=2.0,
            value=1.2,
            step=0.1,
            label_visibility="collapsed",
            key="power_weight",
        )


def render_priority_radio() -> str:
    with st.container(border=True):
        st.markdown(
            """
            <div class="control-card-marker radio-control">
                <div class="section-card-title">Ranking Agent Priority</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        value = st.radio(
            "Ranking Agent Priority",
            options=["Profitability First", "Growth % (Highest)", "TAFGS Score"],
            index=0,
            label_visibility="collapsed",
            key="ranking_priority",
        )
        st.markdown("<div class='radio-spacer'></div>", unsafe_allow_html=True)
        return value


def render_role_filter_card() -> list[str]:
    with st.container(border=True):
        st.markdown(
            """
            <div class="section-card-title role-filter-title">Filter by AI Factory Role</div>
            """,
            unsafe_allow_html=True,
        )
        return st.pills(
            "Filter by AI Factory Role",
            options=ROLE_OPTIONS,
            selection_mode="multi",
            default=ROLE_OPTIONS[:5],
            label_visibility="collapsed",
            key="role_filter",
        )


def run_pipeline(
    risk_discount: float,
    power_weight: float,
    ranking_priority: str,
    role_filter: list[str],
) -> tuple[list[dict], list[dict], str]:
    """Run the LangGraph workflow used by the dashboard."""
    state = run_workflow(
        risk_discount=risk_discount,
        power_weight=power_weight,
        ranking_priority=ranking_priority,
        role_filter=role_filter,
    )
    return state["ingestion_rows"], state["ranked_rows"], state["agent_summary"]
