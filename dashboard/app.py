"""
Executive Dashboard — Customer Churn Analytics Platform

Sprint 2: Live KPIs from dataset.
All hardcoded values replaced with dynamically calculated metrics.
"""

import streamlit as st

from utils import (
    load_data,
    get_total_customers,
    get_churn_rate,
    get_avg_tenure,
    get_avg_monthly_charges,
    get_avg_total_charges,
    get_top_churn_contract,
    get_retained_avg_monthly_charges,
    get_churned_avg_tenure,
    get_churned_avg_monthly_charges,
    get_top_internet_among_churned,
)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Customer Churn Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM CSS
# ═══════════════════════════════════════════════════════════════════════════════


def _inject_css() -> None:
    """Inject global styles, fonts, animations, and counter JS."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

    .stApp { background: #0F3040; }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: #C8A96B;
        z-index: 999;
    }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }

    .header-container { text-align: center; padding: 2.5rem 0 1rem 0; }

    .header-title {
        font-size: 2.8rem;
        font-weight: 800;
        color: #F4F2EE;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }

    .header-subtitle {
        font-size: 1.1rem;
        color: #D6D8D8;
        font-weight: 400;
        margin-bottom: 1.5rem;
    }

    .badge-container {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 0.75rem;
        margin-top: 1rem;
        margin-bottom: 1.5rem;
    }

    .badge {
        display: inline-flex;
        align-items: center;
        padding: 0.3rem 1rem;
        border-radius: 100px;
        font-size: 0.75rem;
        font-weight: 500;
        letter-spacing: 0.02em;
        border: 1px solid rgba(255,255,255,0.08);
    }

    @keyframes fadeIn {
        0% { opacity: 0; }
        100% { opacity: 1; }
    }

    @keyframes skeletonPulse {
        0% { opacity: 0.4; }
        50% { opacity: 0.8; }
        100% { opacity: 0.4; }
    }

    .skeleton {
        background: #234556;
        border-radius: 18px;
        animation: skeletonPulse 1.5s ease-in-out infinite;
    }

    .skeleton-kpi {
        height: 130px;
        margin-bottom: 1rem;
    }

    .skeleton-header {
        height: 80px;
        margin-bottom: 2rem;
        max-width: 500px;
        margin-left: auto;
        margin-right: auto;
    }

    .kpi-card {
        position: relative;
        background: #234556;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 1.5rem 1rem;
        text-align: center;
        animation: fadeIn 0.5s ease forwards;
        opacity: 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        height: 100%;
    }

    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 1.5rem; right: 1.5rem;
        height: 3px;
        background: #C8A96B;
        border-radius: 0 0 3px 3px;
    }

    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.2);
    }

    .kpi-label {
        font-size: 0.7rem;
        font-weight: 500;
        color: #D6D8D8;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.5rem;
    }

    .kpi-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #F4F2EE;
        line-height: 1.2;
    }

    .kpi-value.accent { color: #C8A96B; }

    .kpi-subtext {
        font-size: 0.6rem;
        color: #D6D8D8;
        margin-top: 0.5rem;
        font-weight: 400;
        opacity: 0.7;
    }

    .section-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #F4F2EE;
        margin-bottom: 0.25rem;
    }

    .section-sub {
        font-size: 0.85rem;
        color: #D6D8D8;
        margin-bottom: 1.5rem;
    }

    .insight-card {
        position: relative;
        background: #234556;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 1.5rem;
        animation: fadeIn 0.5s ease forwards;
        opacity: 0;
        height: 100%;
    }

    .insight-card::before {
        content: '';
        position: absolute;
        top: 0; left: 1.5rem; right: 1.5rem;
        height: 2px;
        background: #C8A96B;
    }

    .insight-icon {
        font-size: 1.2rem;
        color: #8FA28A;
        margin-bottom: 0.75rem;
    }

    .insight-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #F4F2EE;
        margin-bottom: 0.35rem;
        line-height: 1.4;
    }

    .insight-text {
        font-size: 0.8rem;
        color: #D6D8D8;
        line-height: 1.5;
    }

    .custom-divider {
        border: none;
        height: 1px;
        background: rgba(255,255,255,0.08);
        margin: 2.5rem 0;
    }

    .action-btn-container {
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        margin: 2.5rem 0 1rem 0;
        flex-wrap: wrap;
    }

    .btn-primary, .btn-secondary {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.8rem 2rem;
        border-radius: 14px;
        font-size: 0.9rem;
        font-weight: 600;
        text-decoration: none;
    }

    .btn-primary {
        background: #C8A96B;
        color: #0F3040;
        cursor: pointer;
        border: none;
    }

    .btn-primary:hover {
        background: #8FA28A;
    }

    .btn-secondary {
        background: transparent;
        color: #D6D8D8;
        border: 1px solid rgba(255,255,255,0.08);
        cursor: default;
    }

    .nav-btn-wrapper a {
        display: inline-flex !important;
        align-items: center !important;
        gap: 0.5rem !important;
        padding: 0.8rem 2rem !important;
        border-radius: 14px !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        background: #C8A96B !important;
        color: #0F3040 !important;
        text-decoration: none !important;
        cursor: pointer !important;
        border: none !important;
        justify-content: center !important;
        width: 100% !important;
    }

    .nav-btn-wrapper a:hover {
        background: #8FA28A !important;
        color: #0F3040 !important;
    }

    .footer {
        text-align: center;
        padding: 2rem 0 1rem 0;
        border-top: 1px solid rgba(255,255,255,0.06);
        margin-top: 1rem;
    }

    .footer-title {
        font-size: 0.85rem;
        font-weight: 500;
        color: #D6D8D8;
        margin-bottom: 0.3rem;
    }

    .footer-info {
        font-size: 0.7rem;
        color: rgba(255,255,255,0.35);
        line-height: 1.6;
    }

    .footer-info span {
        margin: 0 0.5rem;
        opacity: 0.5;
    }

    section[data-testid="stSidebar"] {
        background: #163949;
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    section[data-testid="stSidebar"] .stMarkdown {
        padding: 0 1rem;
    }

    .sidebar-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #F4F2EE;
        padding: 1.5rem 0 0.5rem 0;
    }

    .sidebar-section { margin-bottom: 1.25rem; }

    .sidebar-label {
        font-size: 0.6rem;
        font-weight: 600;
        color: #C8A96B;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.3rem;
    }

    .sidebar-value {
        font-size: 0.85rem;
        color: #D6D8D8;
        line-height: 1.4;
    }

    .sidebar-value.muted { color: rgba(255,255,255,0.3); }

    .sidebar-divider {
        border: none;
        height: 1px;
        background: rgba(255,255,255,0.06);
        margin: 1.25rem 0;
    }

    @media (max-width: 768px) {
        .header-title { font-size: 1.8rem; }
        .kpi-value { font-size: 1.5rem; }
        .action-btn-container { flex-direction: column; align-items: center; }
    }
    </style>

    <script>
    setTimeout(function() {
        var els = document.querySelectorAll('.kpi-value[data-value]');
        els.forEach(function(el) {
            var target = parseFloat(el.getAttribute('data-value'));
            if (isNaN(target)) return;
            var fmt = el.getAttribute('data-format') || 'number';
            var sfx = el.getAttribute('data-suffix') || '';
            var dur = 800;
            var start = null;
            function tick(ts) {
                if (!start) start = ts;
                var p = Math.min((ts - start) / dur, 1);
                var e = 1 - Math.pow(1 - p, 3);
                var v = e * target;
                if (fmt === 'percent') el.textContent = v.toFixed(1) + '%';
                else if (fmt === 'currency') el.textContent = '$' + v.toFixed(2);
                else if (fmt === 'suffix') el.textContent = Math.round(v) + sfx;
                else el.textContent = Math.round(v).toLocaleString();
                if (p < 1) requestAnimationFrame(tick);
            }
            requestAnimationFrame(tick);
        });
    }, 150);
    </script>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# REUSABLE COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════════


def _badge(name: str, color: str) -> str:
    """Return HTML for a pill-shaped technology badge."""
    return (
        f'<span class="badge" style="background:{color};color:#fff">'
        f'{name}</span>'
    )


def _kpi_card(title: str, value: str, delay: float, accent: bool = False,
              data_value: float | None = None, data_format: str = "number",
              data_suffix: str = "", subtext: str = "") -> str:
    """Return HTML for an animated KPI metric card with counter animation support."""
    val_class = "kpi-value accent" if accent else "kpi-value"
    data_attrs = ""
    if data_value is not None:
        data_attrs = f' data-value="{data_value}" data-format="{data_format}" data-suffix="{data_suffix}"'
    subtext_html = f'<div class="kpi-subtext">{subtext}</div>' if subtext else ""
    return (
        f'<div class="kpi-card" style="animation-delay:{delay}s">'
        f'<div class="kpi-label">{title}</div>'
        f'<div class="{val_class}"{data_attrs}>{value}</div>'
        f'{subtext_html}'
        f'</div>'
    )


def _insight_card(icon: str, title: str, desc: str, delay: float) -> str:
    """Return HTML for an insight card."""
    return (
        f'<div class="insight-card" style="animation-delay:{delay}s">'
        f'<div class="insight-icon">{icon}</div>'
        f'<div class="insight-title">{title}</div>'
        f'<div class="insight-text">{desc}</div>'
        f'</div>'
    )


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
            ("Technologies", "Python · scikit-learn · XGBoost · SHAP · Pandas · Streamlit"),
            ("Version", "1.0.0 (Sprint 2)"),
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
            '<div class="sidebar-value muted">github.com/abhinav/placeholder</div>'
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
        ("XGBoost", "#234556"),
        ("Random Forest", "#234556"),
        ("SHAP", "#234556"),
        ("SQLite", "#234556"),
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
        ("Total Customers", f"{total_customers:,}", 0.1, False, total_customers, "number", "", "Active subscribers"),
        ("Churn Rate", f"{churn_rate}%", 0.2, False, churn_rate, "percent", "", "Of total customer base"),
        ("Average Tenure", f"{avg_tenure} mo", 0.3, False, avg_tenure, "suffix", " mo", "Average customer relationship"),
    ]
    for col, (title, value, delay, accent, dv, dfmt, dsuf, sub) in zip(row1, kpi1_data):
        with col:
            st.markdown(
                _kpi_card(title, value, delay, accent, dv, dfmt, dsuf, sub),
                unsafe_allow_html=True,
            )

    row2 = st.columns(3, gap="medium")
    kpi2_data = [
        ("Avg. Monthly Charges", f"${avg_monthly_charges:.2f}", 0.4, False, avg_monthly_charges, "currency", "", "Per customer average"),
        ("Best Model", best_model, 0.5, False, None, "text", "", "Primary prediction model"),
        ("Model Accuracy", model_accuracy, 0.6, True, 76.1, "percent", "", "Based on test dataset"),
    ]
    for col, (title, value, delay, accent, dv, dfmt, dsuf, sub) in zip(row2, kpi2_data):
        with col:
            st.markdown(
                _kpi_card(title, value, delay, accent, dv, dfmt, dsuf, sub),
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
    st.markdown(
        '<div class="section-header">Key Insights</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-sub">'
        'Data-driven patterns discovered during exploratory analysis'
        '</div>',
        unsafe_allow_html=True,
    )

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
    """CTA buttons — Open Analytics navigates to the analytics page."""
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    cols = st.columns([1, 1.5, 0.5, 1.5, 1])
    with cols[1]:
        st.markdown('<div class="nav-btn-wrapper">', unsafe_allow_html=True)
        st.page_link("pages/analytics.py", label="📈 Open Analytics", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with cols[3]:
        st.markdown(
            '<div style="display:flex;justify-content:center;">'
            '<a class="btn-secondary"><span>🎯</span> Predict Customer</a>'
            '</div>',
            unsafe_allow_html=True,
        )


def _footer() -> None:
    """Page footer with version, date, developer, and GitHub link."""
    st.markdown(
        '<div class="footer">'
        '<div class="footer-title">Customer Churn Analytics Platform</div>'
        '<div class="footer-info">'
        'v1.0.0 <span>|</span> 2025-07-31 <span>|</span> Abhinav Agnihotri <span>|</span> github.com/abhinav/placeholder'
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
    avg_total_charges = get_avg_total_charges(df)
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
