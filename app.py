"""
Executive Dashboard — Customer Churn Analytics Platform

Sprint 1: Landing page only.
No ML inference, no analytics, no database — purely UI.

Author: Abhinav Agnihotri
Version: 1.0.0
"""

import sys
from pathlib import Path

import streamlit as st

try:
    sys.path.insert(0, str(Path(__file__).resolve().parent / "dashboard"))
    import theme  # shared design system (theme.css + components)
    _HAS_THEME = True
except Exception:
    _HAS_THEME = False

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
    """Inject the shared design-system styles plus landing-only extras."""
    extra = """
    .kpi-card { animation: fadeIn 0.5s ease both; }

    @media (max-width: 768px) {
        .header-title { font-size: 1.8rem; }
        .kpi-value { font-size: 1.3rem; }
    }
    """
    if _HAS_THEME:
        theme.inject_css(extra)
        return
    st.markdown(
        "<style>"
        ".stApp{background:#0F3040;}"
        ".block-container{max-width:1200px;padding-top:2rem;padding-bottom:2rem;}"
        ".header-container{text-align:center;padding:2rem 0 .5rem 0;}"
        ".header-title{font-size:2.2rem;font-weight:800;color:#F4F2EE;margin-bottom:.5rem;}"
        ".header-subtitle{font-size:1.1rem;color:#D6D8D8;margin-bottom:1.5rem;}"
        ".badge-container{display:flex;justify-content:center;flex-wrap:wrap;gap:.75rem;margin:1rem 0 1.5rem 0;}"
        ".badge{display:inline-flex;align-items:center;padding:.3rem 1rem;border-radius:100px;font-size:.75rem;color:#F4F2EE;border:1px solid rgba(255,255,255,.12);}"
        ".kpi-card,.insight-card{background:linear-gradient(180deg,#234556,#1f3d4d);border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:1.4rem 1rem;text-align:center;}"
        ".kpi-value{font-size:1.8rem;font-weight:700;color:#F4F2EE;}"
        ".kpi-value.accent{color:#C8A96B;}"
        ".kpi-label{font-size:.7rem;color:#D6D8D8;text-transform:uppercase;letter-spacing:.06em;margin-bottom:.35rem;}"
        ".insight-icon{font-size:1.5rem;margin-bottom:.6rem;}"
        ".insight-title{font-size:.88rem;font-weight:700;color:#F4F2EE;margin-bottom:.35rem;}"
        ".insight-text{font-size:.76rem;color:#D6D8D8;line-height:1.6;}"
        ".section-header{font-size:1.15rem;font-weight:700;color:#F4F2EE;margin-bottom:.15rem;}"
        ".section-sub{font-size:.8rem;color:#D6D8D8;margin-bottom:1rem;}"
        ".custom-divider{border:none;height:1px;background:rgba(255,255,255,.08);margin:1.5rem 0;}"
        ".action-btn-container{display:flex;justify-content:center;gap:1.5rem;margin:2.5rem 0 1rem 0;flex-wrap:wrap;}"
        ".btn-primary,.btn-secondary{display:inline-flex;align-items:center;gap:.5rem;padding:.8rem 2rem;border-radius:12px;font-size:.9rem;font-weight:600;text-decoration:none;}"
        ".btn-primary{background:linear-gradient(135deg,#C8A96B,#b09055);color:#0F3040;}"
        ".btn-secondary{background:transparent;color:#D6D8D8;border:1px solid rgba(255,255,255,.08);}"
        ".footer{text-align:center;padding:2.5rem 0 1rem 0;border-top:1px solid rgba(255,255,255,.08);}"
        ".footer-title{font-size:1rem;font-weight:600;color:#F4F2EE;margin-bottom:.25rem;}"
        ".footer-sub{font-size:.8rem;color:#D6D8D8;opacity:.7;}"
        ".sidebar-title{font-size:1.1rem;font-weight:700;color:#F4F2EE;padding:1.5rem 0 .5rem 0;}"
        ".sidebar-label{font-size:.6rem;font-weight:600;color:#C8A96B;text-transform:uppercase;letter-spacing:.08em;margin-bottom:.3rem;}"
        ".sidebar-value{font-size:.85rem;color:#D6D8D8;line-height:1.4;}"
        ".sidebar-value.muted{color:rgba(255,255,255,.3);}"
        ".sidebar-divider{border:none;height:1px;background:rgba(255,255,255,.08);margin:1.25rem 0;}"
        "</style>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# REUSABLE COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════════


def _badge(name: str, color: str) -> str:
    """Return HTML for a pill-shaped technology badge."""
    if _HAS_THEME:
        return theme.metric_badge(name, color)
    return (
        f'<span class="badge" style="background:{color};color:#fff">'
        f'{name}</span>'
    )


def _kpi_card(title: str, value: str, delay: float, accent: bool = False) -> str:
    """Return HTML for an animated KPI metric card."""
    if _HAS_THEME:
        return theme.kpi_card(title, value, accent=accent, delay=delay)
    val_class = "kpi-value accent" if accent else "kpi-value"
    return (
        f'<div class="kpi-card" style="animation-delay:{delay}s">'
        f'<div class="kpi-label">{title}</div>'
        f'<div class="{val_class}">{value}</div>'
        f'</div>'
    )


def _insight_card(icon: str, title: str, desc: str, delay: float) -> str:
    """Return HTML for an insight card."""
    if _HAS_THEME:
        return theme.info_card(icon, title, desc, delay)
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
    if _HAS_THEME:
        theme.section_header(
            "🔍 Key Insights",
            sub="Data-driven patterns discovered during exploratory analysis",
        )
    else:
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
