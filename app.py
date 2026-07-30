"""
Executive Dashboard — Customer Churn Analytics Platform

Sprint 1: Landing page only.
No ML inference, no analytics, no database — purely UI.

Author: Abhinav Agnihotri
Version: 1.0.0
"""

import streamlit as st

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
    """Inject global styles, fonts, and animations."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

    .stApp { background: #08080f; }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* ── Accent bar ── */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #3b82f6, #60a5fa, #3b82f6);
        z-index: 999;
    }

    /* ── Hide Streamlit chrome ── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }

    /* ── Header ── */
    .header-container { text-align: center; padding: 2rem 0 0.5rem 0; }

    .header-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #f8fafc 0%, #60a5fa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }

    .header-subtitle {
        font-size: 1.1rem;
        color: #64748b;
        font-weight: 400;
        margin-bottom: 1.5rem;
    }

    /* ── Badges ── */
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
        padding: 0.35rem 1rem;
        border-radius: 100px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.01em;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }

    /* ── Keyframes ── */
    @keyframes fadeSlideUp {
        0% { opacity: 0; transform: translateY(24px); }
        100% { opacity: 1; transform: translateY(0); }
    }

    /* ── KPI Cards ── */
    .kpi-card {
        background: linear-gradient(145deg, #14142a 0%, #1a1a35 100%);
        border: 1px solid rgba(59, 130, 246, 0.1);
        border-radius: 16px;
        padding: 1.5rem 1rem;
        text-align: center;
        animation: fadeSlideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        opacity: 0;
        transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
        height: 100%;
    }

    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(59, 130, 246, 0.12);
        border-color: rgba(59, 130, 246, 0.3);
    }

    .kpi-label {
        font-size: 0.75rem;
        font-weight: 500;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.5rem;
    }

    .kpi-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #f8fafc;
        line-height: 1.2;
    }

    .kpi-value.accent { color: #3b82f6; }

    /* ── Section headers ── */
    .section-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 0.25rem;
    }

    .section-sub {
        font-size: 0.85rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }

    /* ── Insight Cards ── */
    .insight-card {
        background: linear-gradient(145deg, #14142a 0%, #1a1a35 100%);
        border: 1px solid rgba(59, 130, 246, 0.08);
        border-radius: 14px;
        padding: 1.5rem;
        animation: fadeSlideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        opacity: 0;
        transition: transform 0.3s ease, border-color 0.3s ease;
        height: 100%;
    }

    .insight-card:hover {
        transform: translateY(-2px);
        border-color: rgba(59, 130, 246, 0.25);
    }

    .insight-icon { font-size: 1.8rem; margin-bottom: 0.75rem; }

    .insight-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 0.35rem;
        line-height: 1.4;
    }

    .insight-text {
        font-size: 0.8rem;
        color: #64748b;
        line-height: 1.5;
    }

    /* ── Dividers ── */
    .custom-divider {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.15), transparent);
        margin: 2.5rem 0;
    }

    /* ── Action buttons ── */
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
        border-radius: 10px;
        font-size: 0.95rem;
        font-weight: 600;
        cursor: default;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        text-decoration: none;
    }

    .btn-primary {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: #fff;
        box-shadow: 0 4px 14px rgba(59, 130, 246, 0.25);
    }

    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.35);
    }

    .btn-secondary {
        background: transparent;
        color: #94a3b8;
        border: 1px solid rgba(148, 163, 184, 0.2);
    }

    .btn-secondary:hover {
        border-color: rgba(59, 130, 246, 0.4);
        color: #f8fafc;
        transform: translateY(-2px);
    }

    /* ── Footer ── */
    .footer {
        text-align: center;
        padding: 2.5rem 0 1rem 0;
        border-top: 1px solid rgba(148, 163, 184, 0.08);
        margin-top: 1rem;
    }

    .footer-title {
        font-size: 1rem;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 0.25rem;
    }

    .footer-sub {
        font-size: 0.8rem;
        color: #475569;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: #0c0c1a;
        border-right: 1px solid rgba(59, 130, 246, 0.08);
    }

    section[data-testid="stSidebar"] .stMarkdown {
        padding: 0 1rem;
    }

    .sidebar-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #f8fafc;
        padding: 1.5rem 0 0.5rem 0;
    }

    .sidebar-section { margin-bottom: 1.25rem; }

    .sidebar-label {
        font-size: 0.65rem;
        font-weight: 600;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.3rem;
    }

    .sidebar-value {
        font-size: 0.9rem;
        color: #cbd5e1;
        line-height: 1.4;
    }

    .sidebar-value.muted { color: #475569; }

    .sidebar-divider {
        border: none;
        height: 1px;
        background: rgba(148, 163, 184, 0.08);
        margin: 1.25rem 0;
    }

    /* ── Responsive ── */
    @media (max-width: 768px) {
        .header-title { font-size: 1.8rem; }
        .kpi-value { font-size: 1.5rem; }
        .action-btn-container { flex-direction: column; align-items: center; }
    }
    </style>
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


def _kpi_card(title: str, value: str, delay: float, accent: bool = False) -> str:
    """Return HTML for an animated KPI metric card."""
    val_class = "kpi-value accent" if accent else "kpi-value"
    return (
        f'<div class="kpi-card" style="animation-delay:{delay}s">'
        f'<div class="kpi-label">{title}</div>'
        f'<div class="{val_class}">{value}</div>'
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


def _sidebar() -> None:
    """Collapsible sidebar with project metadata."""
    with st.sidebar:
        st.markdown('<div class="sidebar-title">ℹ️ Project Info</div>', unsafe_allow_html=True)
        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

        fields = [
            ("Developer", "Abhinav Agnihotri"),
            ("Technologies", "Python · scikit-learn · XGBoost · SHAP · Pandas · Streamlit"),
            ("Version", "1.0.0 (Sprint 1)"),
            ("Dataset", "IBM Telco Customer Churn · 7,043 records"),
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
        ("Python", "#3776AB"),
        ("XGBoost", "#289639"),
        ("Random Forest", "#FF6F00"),
        ("SHAP", "#7C3AED"),
        ("SQLite", "#003B57"),
        ("Pandas", "#130654"),
    ]
    badges_html = '<div class="badge-container">' + "".join(
        _badge(name, color) for name, color in badges
    ) + "</div>"
    st.markdown(badges_html, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def _kpi_section() -> None:
    """Six animated KPI metric cards in two rows of three."""
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    row1 = st.columns(3, gap="medium")
    for col, (title, value, delay, accent) in zip(
        row1,
        [
            ("Total Customers", "7,043", 0.1, False),
            ("Churn Rate", "26.5%", 0.2, False),
            ("Average Tenure", "32.4 mo", 0.3, False),
        ],
    ):
        with col:
            st.markdown(
                _kpi_card(title, value, delay, accent),
                unsafe_allow_html=True,
            )

    row2 = st.columns(3, gap="medium")
    for col, (title, value, delay, accent) in zip(
        row2,
        [
            ("Avg. Monthly Charges", "$64.80", 0.4, False),
            ("Best Model", "XGBoost", 0.5, False),
            ("Model Accuracy", "76.1%", 0.6, True),
        ],
    ):
        with col:
            st.markdown(
                _kpi_card(title, value, delay, accent),
                unsafe_allow_html=True,
            )


def _insights_section() -> None:
    """Four insight cards highlighting key churn patterns."""
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header">🔍 Key Insights</div>',
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
        ("📅", "Month-to-Month Contracts",
         "Customers on month-to-month plans show the highest churn rate across all contract types.", 0.1),
        ("⏳", "Low Tenure Customers",
         "New customers with short tenure are significantly more likely to churn.", 0.2),
        ("💰", "Higher Monthly Charges",
         "Customers paying higher monthly charges exhibit increased churn probability.", 0.3),
        ("🌐", "Fiber Optic Users",
         "Fiber optic internet service correlates with higher churn compared to DSL.", 0.4),
    ]
    for col, (icon, title, desc, delay) in zip(cols, insights):
        with col:
            st.markdown(
                _insight_card(icon, title, desc, delay),
                unsafe_allow_html=True,
            )


def _action_buttons() -> None:
    """Non-functional CTA buttons (placeholders for Sprint 2+)."""
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div class="action-btn-container">'
        '<a class="btn-primary"><span>📈</span> Open Analytics</a>'
        '<a class="btn-secondary"><span>🎯</span> Predict Customer</a>'
        '</div>',
        unsafe_allow_html=True,
    )


def _footer() -> None:
    """Page footer."""
    st.markdown(
        '<div class="footer">'
        '<div class="footer-title">Customer Churn Analytics Platform</div>'
        '<div class="footer-sub">Created for Internship Presentation</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════


def main() -> None:
    """Assemble and render the Executive Dashboard."""
    _inject_css()
    _sidebar()
    _header()
    _kpi_section()
    _insights_section()
    _action_buttons()
    _footer()


if __name__ == "__main__":
    main()
