"""
Home page — Customer Churn Analytics Platform (Executive Dashboard).

Live KPIs from the dataset, key churn insights, and one-click navigation
into the Analytics and AI Prediction Lab pages. Runs as the `home` page of
the production entry point (`app.py`, which uses st.navigation).

Version: 2.0.0 (Production)
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import theme

import streamlit as st

from utils import (
    load_data,
    get_total_customers,
    get_churn_rate,
    get_avg_tenure,
    get_avg_monthly_charges,
    get_top_churn_contract,
    get_retained_avg_monthly_charges,
    get_churned_avg_tenure,
    get_churned_avg_monthly_charges,
    get_top_internet_among_churned,
)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

_APP_VERSION = "2.0.0"

st.set_page_config(
    page_title="Customer Churn Analytics Platform",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM CSS
# ═══════════════════════════════════════════════════════════════════════════════


def _inject_css() -> None:
    """Inject the shared design-system styles and counter animation JS."""
    theme.inject_css()
    theme.inject_kpi_counter()


def _badge(name: str, color: str) -> str:
    """Return HTML for a pill-shaped technology badge."""
    return theme.metric_badge(name, color)


def _kpi_card(title: str, value: str, delay: float, accent: bool = False,
              data_value: float | None = None, data_format: str = "number",
              data_suffix: str = "", subtext: str = "",
              icon: str = "", tone: str = "") -> str:
    """KPI metric card — delegates to the shared design system."""
    return theme.kpi_card(
        title, value, subtext=subtext, accent=accent, delay=delay,
        data_value=data_value, data_format=data_format, data_suffix=data_suffix,
        icon=icon, tone=tone,
    )


def _insight_card(icon: str, title: str, desc: str, delay: float) -> str:
    """Insight card — delegates to the shared design system."""
    return theme.info_card(icon, title, desc, delay)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTIONS
# ═══════════════════════════════════════════════════════════════════════════════


def _sidebar(total_customers: int) -> None:
    """Collapsible sidebar with project metadata."""
    with st.sidebar:
        st.markdown('<div class="sidebar-title">Project Info</div>', unsafe_allow_html=True)
        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

        fields = [
            ("Developer", "Abhinav Agnihotri"),
            ("Technologies", "Python · Streamlit · XGBoost · Random Forest · SHAP · Plotly"),
            ("Version", f"{_APP_VERSION} (Production)"),
            ("Dataset", f"IBM Telco Customer Churn · {total_customers:,} records"),
        ]
        for label, value in fields:
            st.markdown(
                f'<div class="sidebar-section">'
                f'<div class="sidebar-label">{label}</div>'
                f'<div class="sidebar-value">{value}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
        st.markdown(
            '<div class="sidebar-section">'
            '<div class="sidebar-label">GitHub</div>'
            '<div class="sidebar-value muted">'
            '<a href="https://github.com/abhinav7830tech/CustomerChurnPrediction" '
            'target="_blank" rel="noopener noreferrer">'
            'github.com/abhinav7830tech/CustomerChurnPrediction'
            '</a>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )


def _header() -> None:
    """Hero header with title, subtitle, and technology badges."""
    st.markdown('<div class="header-container">', unsafe_allow_html=True)

    st.markdown(
        '<div class="header-title">Customer Churn Analytics Platform</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="header-subtitle">'
        'AI-Powered Customer Retention Dashboard'
        '</div>',
        unsafe_allow_html=True,
    )

    badges = [
        ("Python", "#234556"),
        ("Streamlit", "#234556"),
        ("XGBoost", "#234556"),
        ("Random Forest", "#234556"),
        ("SHAP", "#234556"),
        ("Plotly", "#234556"),
        ("Pandas", "#234556"),
    ]
    badges_html = '<div class="badge-container">' + "".join(
        _badge(name, color) for name, color in badges
    ) + "</div>"
    st.markdown(badges_html, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def _kpi_section(
    total_customers: int,
    churn_rate: float,
    avg_tenure: float,
    avg_monthly_charges: float,
    best_model: str,
    model_accuracy: str,
) -> None:
    """Six animated KPI metric cards in two rows of three."""
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    row1 = st.columns(3, gap="medium")
    kpi1_data = [
        ("Total Customers", f"{total_customers:,}", 0.1, False, total_customers, "number", "", "Active subscribers", "👥", "customers"),
        ("Churn Rate", f"{churn_rate}%", 0.2, False, churn_rate, "percent", "", "Of total customer base", "📉", "churn"),
        ("Average Tenure", f"{avg_tenure} mo", 0.3, False, avg_tenure, "suffix", " mo", "Average customer relationship", "⏳", "retention"),
    ]
    for col, (title, value, delay, accent, dv, dfmt, dsuf, sub, icon, tone) in zip(row1, kpi1_data):
        with col:
            st.markdown(
                _kpi_card(title, value, delay, accent, dv, dfmt, dsuf, sub, icon, tone),
                unsafe_allow_html=True,
            )

    row2 = st.columns(3, gap="medium")
    kpi2_data = [
        ("Avg. Monthly Charges", f"${avg_monthly_charges:.2f}", 0.4, False, avg_monthly_charges, "currency", "", "Per customer average", "💰", "revenue"),
        ("Best Model", best_model, 0.5, False, None, "text", "", "Primary prediction model", "🧠", "health"),
        ("Model Accuracy", model_accuracy, 0.6, True, 76.1, "percent", "", "Based on test dataset", "🎯", "accuracy"),
    ]
    for col, (title, value, delay, accent, dv, dfmt, dsuf, sub, icon, tone) in zip(row2, kpi2_data):
        with col:
            st.markdown(
                _kpi_card(title, value, delay, accent, dv, dfmt, dsuf, sub, icon, tone),
                unsafe_allow_html=True,
            )


def _insights_section(
    top_contract: str,
    top_contract_pct: float,
    churned_tenure: float,
    churned_charges: float,
    retained_charges: float,
    top_internet: str,
) -> None:
    """Four insight cards highlighting key churn patterns."""
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    theme.section_header("Key Insights", sub="Data-driven patterns discovered during exploratory analysis")

    cols = st.columns(4, gap="medium")
    insights = [
        ("◆", "Month-to-Month Contracts",
         f"{top_contract} contracts have the highest churn rate at {top_contract_pct}%.", 0.1),
        ("◆", "Low Tenure Customers",
         f"Churned customers have an average tenure of only {churned_tenure} months.", 0.2),
        ("◆", "Higher Monthly Charges",
         f"Churned customers pay ${churned_charges:.2f}/mo vs ${retained_charges:.2f}/mo for retained.", 0.3),
        ("◆", "Fiber Optic Users",
         f"{top_internet} is the most common internet service among churned customers.", 0.4),
    ]
    for col, (icon, title, desc, delay) in zip(cols, insights):
        with col:
            st.markdown(
                _insight_card(icon, title, desc, delay),
                unsafe_allow_html=True,
            )


def _action_buttons() -> None:
    """CTA buttons — navigate to the Analytics and Prediction Lab pages."""
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    cols = st.columns([1, 1.5, 0.5, 1.5, 1])
    pages = st.session_state.get("_app_pages", {})
    analytics_page = pages.get("analytics")
    lab_page = pages.get("prediction_lab")
    with cols[1]:
        if analytics_page is not None:
            st.page_link(analytics_page, label="📈 Open Analytics", width="stretch")
        else:
            st.switch_page("pages/analytics.py")
    with cols[3]:
        if lab_page is not None:
            st.page_link(lab_page, label="🎯 Predict Customer", width="stretch")
        else:
            st.switch_page("pages/prediction_lab.py")


def _footer() -> None:
    """Page footer with version, date, developer, and GitHub link."""
    today = datetime.now().strftime("%Y-%m-%d")
    st.markdown(
        '<div class="footer">'
        '<div class="footer-title">Customer Churn Analytics Platform</div>'
        '<div class="footer-info">'
        f'v{_APP_VERSION} <span>|</span> {today} <span>|</span> Abhinav Agnihotri <span>|</span> '
        '<a href="https://github.com/abhinav7830tech/CustomerChurnPrediction" '
        'target="_blank" rel="noopener noreferrer">'
        'github.com/abhinav7830tech/CustomerChurnPrediction'
        '</a>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════


def main() -> None:
    """Assemble and render the Executive Dashboard."""
    _inject_css()

    placeholder = st.empty()
    with placeholder.container():
        st.markdown(
            '<div style="text-align:center;padding:4rem 0 2rem 0">'
            '<div class="skeleton skeleton-header"></div>'
            '</div>',
            unsafe_allow_html=True,
        )
        for _ in range(2):
            cols = st.columns(3, gap="medium")
            for col in cols:
                with col:
                    st.markdown(
                        '<div class="skeleton skeleton-kpi"></div>',
                        unsafe_allow_html=True,
                    )

    df = load_data()

    placeholder.empty()

    # -- Compute KPI values --
    total_customers = get_total_customers(df)
    churn_rate = get_churn_rate(df)
    avg_tenure = get_avg_tenure(df)
    avg_monthly_charges = get_avg_monthly_charges(df)
    top_contract, top_contract_pct = get_top_churn_contract(df)
    churned_tenure = get_churned_avg_tenure(df)
    churned_charges = get_churned_avg_monthly_charges(df)
    retained_charges = get_retained_avg_monthly_charges(df)
    top_internet = get_top_internet_among_churned(df)

    _sidebar(total_customers)
    _header()
    _kpi_section(
        total_customers=total_customers,
        churn_rate=churn_rate,
        avg_tenure=avg_tenure,
        avg_monthly_charges=avg_monthly_charges,
        best_model="XGBoost",
        model_accuracy="76.1%",
    )
    _insights_section(
        top_contract=top_contract,
        top_contract_pct=top_contract_pct,
        churned_tenure=churned_tenure,
        churned_charges=churned_charges,
        retained_charges=retained_charges,
        top_internet=top_internet,
    )
    _action_buttons()
    _footer()


if __name__ == "__main__":
    main()
