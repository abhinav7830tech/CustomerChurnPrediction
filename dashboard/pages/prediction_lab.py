"""
AI Prediction Lab — Customer Churn Analytics Platform

Sprint 5: Premium enterprise UI for single-customer churn prediction.
Runs inference only via the pre-trained XGBoost / Random Forest models.

Presentation layer only — all prediction, SHAP, and recommendation
logic lives in `prediction.py` and is unchanged here.
"""

import os
import sys

import streamlit as st

try:
    import prediction
except ModuleNotFoundError:
    _dashboard_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _dashboard_dir not in sys.path:
        sys.path.insert(0, _dashboard_dir)
    import prediction

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="AI Prediction Lab",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Presentation-only constants (backend values are never altered) ────────────

RISK_PILL_COLORS = {
    "Low Risk": "#8FA28A",
    "Medium Risk": "#C8A96B",
    "High Risk": "#D97C7C",
}

VERDICT_COLORS = {
    "Likely to Stay": "#8FA28A",
    "Likely to Churn": "#D97C7C",
}

PRIORITY_LABELS = {
    "Low Risk": "LOW",
    "Medium Risk": "MEDIUM",
    "High Risk": "HIGH",
}

REC_EXTRA = {
    "Offer a retention discount": ("Reduce churn probability", "Medium"),
    "Recommend a yearly contract": ("Strengthen long-term loyalty", "No extra cost"),
    "Assign customer support follow-up": ("Resolve pain points early", "Low"),
    "Offer loyalty rewards": ("Reduce churn probability", "Low"),
    "Review service quality": ("Improve customer satisfaction", "Low"),
    "Maintain engagement": ("Sustain customer satisfaction", "Low"),
    "Promote premium plans": ("Grow revenue per customer", "Low"),
}

SUMMARY_GROUPS = [
    ("Personal", "👤", ["gender", "SeniorCitizen", "Partner", "Dependents"]),
    ("Account", "📇", ["tenure", "Contract", "PaperlessBilling", "PaymentMethod"]),
    (
        "Services", "📡",
        [
            "PhoneService", "MultipleLines", "InternetService",
            "OnlineSecurity", "OnlineBackup", "DeviceProtection",
            "TechSupport", "StreamingTV", "StreamingMovies",
        ],
    ),
    ("Billing", "💳", ["MonthlyCharges", "TotalCharges"]),
]


def _confidence(pct: float) -> tuple:
    """Presentation-only confidence label derived from the model output."""
    if pct >= 70 or pct <= 30:
        return "High", "#8FA28A"
    if pct >= 55 or pct <= 45:
        return "Medium", "#C8A96B"
    return "Low", "#D97C7C"


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM CSS
# ═══════════════════════════════════════════════════════════════════════════════


def _inject_css() -> None:
    """Premium page styles consistent with the analytics dashboard theme."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

    .stApp { background: #0F3040; }

    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 2.5rem;
        max-width: 1680px;
    }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }

    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #C8A96B, #8FA28A, #C8A96B);
        z-index: 999;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .back-link {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        color: #D6D8D8;
        text-decoration: none;
        font-size: 0.85rem;
        font-weight: 500;
        padding: 0.4rem 0;
        margin-bottom: 0.75rem;
    }

    .back-link:hover { color: #8FA28A; }

    /* ── Page header ── */
    .page-header { margin-bottom: 2.25rem; }

    .page-kicker {
        font-size: 0.72rem;
        font-weight: 700;
        color: #C8A96B;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        margin-bottom: 0.6rem;
    }

    .page-title {
        font-size: 2.8rem;
        font-weight: 800;
        color: #F4F2EE;
        margin-bottom: 0.85rem;
        letter-spacing: -0.025em;
        line-height: 1.15;
    }

    .page-subtitle {
        font-size: 1.05rem;
        color: #D6D8D8;
        font-weight: 400;
        line-height: 1.65;
        max-width: 760px;
        margin-bottom: 1.25rem;
    }

    .page-rule {
        width: 88px;
        height: 4px;
        border-radius: 2px;
        background: linear-gradient(90deg, #C8A96B, rgba(200,169,107,0.1));
    }

    /* ── Shared card ── */
    .card {
        background: linear-gradient(180deg, #234556 0%, #1f3d4d 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 1.75rem;
        margin-bottom: 1.25rem;
        animation: fadeIn 0.5s ease both;
        box-shadow: 0 2px 10px rgba(0,0,0,0.18);
    }

    .card-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: #C8A96B;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.4rem;
        display: flex;
        align-items: center;
    }

    .card-sub {
        font-size: 0.78rem;
        color: #D6D8D8;
        opacity: 0.75;
        margin-bottom: 1.25rem;
    }

    /* ── Tooltip ── */
    .tip {
        position: relative;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background: #163949;
        border: 1px solid rgba(255,255,255,0.16);
        color: #C8A96B;
        font-size: 0.58rem;
        font-weight: 700;
        cursor: help;
        margin-left: 0.45rem;
        vertical-align: middle;
        flex-shrink: 0;
    }
    .tip-text {
        position: absolute;
        bottom: 165%;
        left: 50%;
        transform: translateX(-50%);
        width: 230px;
        background: #0F3040;
        border: 1px solid rgba(255,255,255,0.12);
        color: #D6D8D8;
        font-size: 0.72rem;
        font-weight: 400;
        line-height: 1.5;
        letter-spacing: 0;
        text-transform: none;
        padding: 0.65rem 0.75rem;
        border-radius: 10px;
        box-shadow: 0 10px 28px rgba(0,0,0,0.45);
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.2s ease, visibility 0.2s ease;
        z-index: 60;
        pointer-events: none;
    }
    .tip:hover .tip-text { opacity: 1; visibility: visible; }

    /* ── Form section headers ── */
    .form-section {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        font-size: 0.78rem;
        font-weight: 700;
        color: #F4F2EE;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        border-bottom: 1px solid rgba(200,169,107,0.18);
        padding-bottom: 0.6rem;
        margin: 1.9rem 0 1.1rem 0;
    }
    .form-section .form-icon { font-size: 1rem; color: #C8A96B; }
    .form-section:first-of-type { margin-top: 0.4rem; }

    /* ── Widget styling (dark theme) ── */
    .stSelectbox label p,
    .stNumberInput label p,
    .stSlider label p,
    .stRadio label p,
    .stForm label p {
        color: #F4F2EE !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
    }

    .stSelectbox div[data-baseweb="select"] > div,
    .stNumberInput div[data-baseweb="input"] {
        background: #163949 !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important;
        color: #F4F2EE !important;
    }

    .stSelectbox div[data-baseweb="select"] > div:hover,
    .stNumberInput div[data-baseweb="input"]:hover {
        border-color: rgba(200,169,107,0.5) !important;
    }

    .stSelectbox div[data-baseweb="select"] span,
    .stSelectbox div[data-baseweb="select"] svg {
        color: #F4F2EE !important;
    }

    .stSelectbox [role="option"] {
        background: #163949 !important;
        color: #F4F2EE !important;
    }
    .stSelectbox [role="option"]:hover,
    .stSelectbox [role="option"][aria-selected="true"] {
        background: #8FA28A !important;
        color: #0F3040 !important;
    }

    .stNumberInput div[data-baseweb="input"] input {
        color: #F4F2EE !important;
    }

    .stNumberInput div[data-baseweb="input"] [data-testid="stNumberInputStepDown"],
    .stNumberInput div[data-baseweb="input"] [data-testid="stNumberInputStepUp"] {
        color: #C8A96B !important;
        background: transparent !important;
        border: none !important;
    }

    .stRadio [role="radiogroup"] { gap: 0.4rem; }
    .stRadio label[data-baseweb="radio"] span:first-child,
    .stRadio [data-testid="stRadio"] span[data-baseweb="radio"] {
        border-color: rgba(200,169,107,0.6) !important;
    }
    .stRadio label[data-baseweb="radio"] input:checked ~ span,
    .stRadio [data-testid="stRadio"] input:checked ~ span {
        background-color: #C8A96B !important;
        border-color: #C8A96B !important;
    }
    .stRadio label[data-baseweb="radio"] p,
    .stRadio [data-testid="stRadio"] p {
        color: #D6D8D8 !important;
        font-size: 0.82rem !important;
    }

    .stSlider div[role="slider"] {
        background-color: #C8A96B !important;
        border-color: #C8A96B !important;
        box-shadow: none !important;
    }
    .stSlider div[role="slider"]:hover {
        box-shadow: 0 0 0 8px rgba(200,169,107,0.18) !important;
    }
    .stSlider [data-testid="stSliderThumbValue"],
    .stSlider [data-testid="stSliderValue"] {
        color: #F4F2EE !important;
        background: #163949 !important;
        border-radius: 8px !important;
    }

    /* ── Predict button ── */
    .stButton button,
    button[kind="primary"],
    [data-testid="stFormSubmitButton"] button {
        width: 100% !important;
        min-height: 50px !important;
        border-radius: 14px !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.01em;
        color: #0F3040 !important;
        background: linear-gradient(135deg, #C8A96B 0%, #b09055 100%) !important;
        border: none !important;
        box-shadow: 0 6px 18px rgba(200,169,107,0.22) !important;
        transition: all 0.25s ease !important;
    }
    .stButton button:hover,
    button[kind="primary"]:hover,
    [data-testid="stFormSubmitButton"] button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 30px rgba(200,169,107,0.38) !important;
        background: linear-gradient(135deg, #d4b678 0%, #C8A96B 100%) !important;
        color: #0F3040 !important;
    }
    .stButton button:active,
    button[kind="primary"]:active,
    [data-testid="stFormSubmitButton"] button:active {
        transform: translateY(0) !important;
        box-shadow: 0 4px 12px rgba(200,169,107,0.25) !important;
    }

    /* ── Waiting card ── */
    .waiting-card {
        text-align: center;
        padding: 3.25rem 1.75rem;
        background: linear-gradient(180deg, #234556 0%, #1f3d4d 100%);
        border: 1px dashed rgba(200,169,107,0.35);
        border-radius: 18px;
        margin-bottom: 1.25rem;
        animation: fadeIn 0.5s ease both;
    }
    .waiting-icon { font-size: 2.4rem; color: #C8A96B; margin-bottom: 0.85rem; }
    .waiting-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #F4F2EE;
        margin-bottom: 0.55rem;
    }
    .waiting-text {
        font-size: 0.82rem;
        color: #D6D8D8;
        opacity: 0.75;
        line-height: 1.6;
        max-width: 340px;
        margin: 0 auto;
    }

    /* ── Result card ── */
    .verdict-label {
        font-size: 0.72rem;
        font-weight: 700;
        color: #C8A96B;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.55rem;
    }
    .verdict {
        font-size: 2.15rem;
        font-weight: 800;
        letter-spacing: -0.01em;
        margin-bottom: 1.35rem;
    }

    .prob-label {
        font-size: 0.66rem;
        font-weight: 600;
        color: #D6D8D8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.4rem;
        display: flex;
        align-items: center;
    }
    .prob-row { display: flex; align-items: baseline; gap: 0.55rem; margin-bottom: 0.7rem; }
    .prob-value { font-size: 2.4rem; font-weight: 800; color: #F4F2EE; letter-spacing: -0.01em; }
    .prob-caption { font-size: 0.72rem; color: #D6D8D8; opacity: 0.7; }

    .prob-bar {
        height: 14px;
        background: #163949;
        border-radius: 100px;
        overflow: hidden;
        margin-bottom: 1.35rem;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.35);
    }
    .prob-fill {
        height: 100%;
        border-radius: 100px;
        transition: width 0.9s cubic-bezier(0.16, 1, 0.3, 1);
        box-shadow: 0 0 12px rgba(255,255,255,0.12);
    }

    .risk-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1.4rem;
    }
    .risk-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.55rem;
        padding: 0.55rem 1.25rem;
        border-radius: 100px;
        font-size: 0.85rem;
        font-weight: 800;
        letter-spacing: 0.04em;
        color: #0F3040;
        box-shadow: 0 4px 14px rgba(0,0,0,0.25);
    }
    .risk-pill .pill-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #0F3040;
        opacity: 0.55;
    }

    .conf-block {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        background: #163949;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 0.8rem 1.1rem;
    }
    .conf-label {
        font-size: 0.72rem;
        font-weight: 600;
        color: #D6D8D8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .conf-value {
        font-size: 1rem;
        font-weight: 800;
        display: flex;
        align-items: center;
        gap: 0.45rem;
    }
    .conf-value::before {
        content: '';
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background: currentColor;
    }

    /* ── Model information card ── */
    .mi-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.9rem 1.25rem;
    }
    .mi-item {
        background: #163949;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 0.8rem 1rem;
    }
    .mi-label {
        font-size: 0.64rem;
        font-weight: 600;
        color: #C8A96B;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.3rem;
        display: flex;
        align-items: center;
    }
    .mi-value { font-size: 1rem; font-weight: 700; color: #F4F2EE; }

    /* ── Top factors ── */
    .factors-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.1rem 2rem;
    }
    .factor-row {
        background: #163949;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 0.9rem 1.1rem;
    }
    .factor-head {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 0.75rem;
        margin-bottom: 0.6rem;
    }
    .factor-name { font-size: 0.88rem; font-weight: 700; color: #F4F2EE; }
    .factor-value {
        font-size: 0.76rem;
        color: #D6D8D8;
        opacity: 0.8;
        margin-top: 0.15rem;
    }
    .factor-impact {
        font-size: 0.78rem;
        font-weight: 700;
        white-space: nowrap;
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
    }
    .factor-arrow { font-size: 0.85rem; }
    .factor-bar {
        height: 7px;
        background: rgba(255,255,255,0.06);
        border-radius: 100px;
        overflow: hidden;
    }
    .factor-fill {
        height: 100%;
        border-radius: 100px;
        transition: width 0.7s ease;
    }
    .factor-source {
        font-size: 0.72rem;
        color: #D6D8D8;
        opacity: 0.6;
        margin-top: 1.1rem;
        font-style: italic;
    }

    /* ── Recommendations ── */
    .rec-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1rem;
    }
    .rec-card {
        background: #163949;
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px;
        padding: 1.15rem 1.25rem;
        transition: transform 0.25s ease, border-color 0.25s ease;
    }
    .rec-card:hover {
        transform: translateY(-3px);
        border-color: rgba(200,169,107,0.4);
    }
    .rec-head { display: flex; align-items: flex-start; gap: 0.85rem; margin-bottom: 0.7rem; }
    .rec-icon {
        font-size: 1.35rem;
        flex-shrink: 0;
        background: #234556;
        border: 1px solid rgba(200,169,107,0.25);
        border-radius: 12px;
        width: 46px;
        height: 46px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .rec-kicker {
        font-size: 0.62rem;
        font-weight: 700;
        color: #C8A96B;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.3rem;
    }
    .rec-title { font-size: 0.92rem; font-weight: 700; color: #F4F2EE; line-height: 1.35; }
    .rec-meta { display: flex; flex-direction: column; gap: 0.45rem; }
    .rec-meta-item {
        display: flex;
        justify-content: space-between;
        gap: 0.75rem;
        font-size: 0.74rem;
        border-top: 1px dashed rgba(255,255,255,0.07);
        padding-top: 0.45rem;
    }
    .rec-meta-label { color: #D6D8D8; opacity: 0.7; }
    .rec-meta-value { color: #F4F2EE; font-weight: 600; text-align: right; }

    /* ── Customer summary ── */
    .summary-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1.1rem;
    }
    .summary-card {
        background: #163949;
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px;
        padding: 1.15rem 1.2rem;
    }
    .summary-card-title {
        display: flex;
        align-items: center;
        gap: 0.55rem;
        font-size: 0.78rem;
        font-weight: 700;
        color: #F4F2EE;
        margin-bottom: 0.9rem;
        padding-bottom: 0.6rem;
        border-bottom: 1px solid rgba(200,169,107,0.18);
    }
    .summary-card-title .summary-icon { font-size: 0.95rem; color: #C8A96B; }
    .summary-pairs { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem 0.9rem; }
    .summary-item { min-width: 0; }
    .summary-label {
        font-size: 0.62rem;
        font-weight: 600;
        color: #C8A96B;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin-bottom: 0.2rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .summary-value {
        font-size: 0.84rem;
        color: #F4F2EE;
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* ── Validation & error cards ── */
    .validation-card {
        background: #234556;
        border: 1px solid rgba(217, 124, 124, 0.45);
        border-radius: 14px;
        padding: 1.15rem 1.3rem;
        margin-bottom: 1.25rem;
        animation: fadeIn 0.4s ease both;
    }
    .validation-title {
        font-size: 0.86rem;
        font-weight: 700;
        color: #D97C7C;
        margin-bottom: 0.55rem;
    }
    .validation-item {
        font-size: 0.8rem;
        color: #F4F2EE;
        padding: 0.25rem 0;
        padding-left: 1rem;
        position: relative;
    }
    .validation-item::before {
        content: '•';
        position: absolute;
        left: 0.2rem;
        color: #D97C7C;
    }

    .error-card {
        text-align: center;
        padding: 3rem 1.75rem;
        background: #234556;
        border: 1px solid rgba(217, 124, 124, 0.4);
        border-radius: 18px;
        margin-top: 1rem;
        animation: fadeIn 0.5s ease both;
    }
    .error-icon { font-size: 2.4rem; margin-bottom: 0.85rem; }
    .error-title { font-size: 1.2rem; font-weight: 700; color: #F4F2EE; margin-bottom: 0.55rem; }
    .error-text {
        font-size: 0.82rem;
        color: #D6D8D8;
        line-height: 1.6;
        max-width: 540px;
        margin: 0 auto;
    }

    /* ── Responsive ── */
    @media (max-width: 1200px) {
        .summary-grid { grid-template-columns: repeat(2, 1fr); }
        .factors-grid { grid-template-columns: 1fr; }
    }
    @media (max-width: 768px) {
        .page-title { font-size: 1.7rem; }
        .page-subtitle { font-size: 0.92rem; }
        .verdict { font-size: 1.6rem; }
        .summary-grid { grid-template-columns: 1fr; }
        .summary-pairs { grid-template-columns: 1fr 1fr; }
        .rec-grid { grid-template-columns: 1fr; }
        .block-container { padding-left: 1rem; padding-right: 1rem; }
    }
    @media (min-width: 1600px) {
        .page-title { font-size: 3.1rem; }
    }
    </style>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════


def _header() -> None:
    """Hero header with kicker, large title, subtitle, and accent rule."""
    st.markdown(
        '<a class="back-link" href="/" target="_self">'
        "← Back to Dashboard</a>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="page-header">'
        '<div class="page-kicker">◆ AI Prediction Lab</div>'
        '<div class="page-title">AI Customer Churn Prediction</div>'
        '<div class="page-subtitle">'
        "Predict customer churn using the trained machine learning model "
        "and explain the prediction using model insights."
        "</div>"
        '<div class="page-rule"></div>'
        "</div>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# LEFT PANEL — CUSTOMER INFORMATION FORM
# ═══════════════════════════════════════════════════════════════════════════════


def _section(icon: str, title: str) -> None:
    st.markdown(
        f'<div class="form-section">'
        f'<span class="form-icon">{icon}</span>{title}'
        f"</div>",
        unsafe_allow_html=True,
    )


def _form_panel() -> None:
    """Customer information form. Writes results to session state."""
    available = prediction.get_available_models()
    best = prediction.resolve_best_model()

    with st.form("prediction_form"):
        st.markdown(
            '<div class="card-title">Customer Information</div>'
            '<div class="card-sub">Enter the customer profile to run a churn prediction</div>',
            unsafe_allow_html=True,
        )

        model_choice = best
        if len(available) > 1:
            options = {alias: prediction.MODEL_ALIASES[alias] for alias in available}
            model_choice = st.selectbox(
                "Prediction Model",
                options=list(options.keys()),
                format_func=lambda a: f"{options[a]}"
                + (" (best)" if a == best else ""),
                index=list(options.keys()).index(best),
            )

        _section("👤", "Personal Information")
        c1, c2 = st.columns(2)
        with c1:
            gender = st.selectbox("Gender", ["Male", "Female"])
        with c2:
            senior = st.radio("Senior Citizen", ["No", "Yes"], horizontal=True)
        c1, c2 = st.columns(2)
        with c1:
            partner = st.radio("Partner", ["No", "Yes"], horizontal=True)
        with c2:
            dependents = st.radio("Dependents", ["No", "Yes"], horizontal=True)

        _section("📇", "Account Information")
        tenure = st.slider(
            "Tenure (months)", min_value=0, max_value=72, value=36, step=1
        )
        c1, c2 = st.columns(2)
        with c1:
            contract = st.selectbox(
                "Contract",
                ["Month-to-month", "One year", "Two year"],
            )
        with c2:
            paperless = st.radio("Paperless Billing", ["No", "Yes"], horizontal=True)
        payment_method = st.selectbox(
            "Payment Method",
            [
                "Electronic check",
                "Mailed check",
                "Bank transfer (automatic)",
                "Credit card (automatic)",
            ],
        )

        _section("📡", "Services")
        c1, c2 = st.columns(2)
        with c1:
            phone_service = st.radio("Phone Service", ["No", "Yes"], horizontal=True)
        with c2:
            multiple_lines = st.selectbox(
                "Multiple Lines", ["No", "No phone service", "Yes"]
            )
        internet_service = st.selectbox(
            "Internet Service", ["DSL", "Fiber optic", "No"]
        )
        c1, c2 = st.columns(2)
        with c1:
            online_security = st.selectbox(
                "Online Security", ["No", "No internet service", "Yes"]
            )
        with c2:
            online_backup = st.selectbox(
                "Online Backup", ["No", "No internet service", "Yes"]
            )
        c1, c2 = st.columns(2)
        with c1:
            device_protection = st.selectbox(
                "Device Protection", ["No", "No internet service", "Yes"]
            )
        with c2:
            tech_support = st.selectbox(
                "Tech Support", ["No", "No internet service", "Yes"]
            )
        c1, c2 = st.columns(2)
        with c1:
            streaming_tv = st.selectbox(
                "Streaming TV", ["No", "No internet service", "Yes"]
            )
        with c2:
            streaming_movies = st.selectbox(
                "Streaming Movies", ["No", "No internet service", "Yes"]
            )

        _section("💳", "Billing")
        c1, c2 = st.columns(2)
        with c1:
            monthly_charges = st.number_input(
                "Monthly Charges ($)", min_value=0.0, max_value=400.0,
                value=70.0, step=5.0,
            )
        with c2:
            total_charges = st.number_input(
                "Total Charges ($)", min_value=0.0, max_value=12000.0,
                value=2520.0, step=50.0,
            )

        submitted = st.form_submit_button(
            "🔮 Predict Customer Churn", use_container_width=True
        )

    if not submitted:
        return

    inputs = {
        "gender": gender,
        "SeniorCitizen": senior,
        "Partner": partner,
        "Dependents": dependents,
        "tenure": int(tenure),
        "PhoneService": phone_service,
        "MultipleLines": multiple_lines,
        "InternetService": internet_service,
        "OnlineSecurity": online_security,
        "OnlineBackup": online_backup,
        "DeviceProtection": device_protection,
        "TechSupport": tech_support,
        "StreamingTV": streaming_tv,
        "StreamingMovies": streaming_movies,
        "Contract": contract,
        "PaperlessBilling": paperless,
        "PaymentMethod": payment_method,
        "MonthlyCharges": float(monthly_charges),
        "TotalCharges": float(total_charges),
    }

    errors = prediction.validate_inputs(inputs)
    if errors:
        st.session_state["prediction"] = None
        st.session_state["validation_errors"] = errors
        st.session_state["customer_inputs"] = inputs
        return

    model = prediction.load_model(model_choice)
    if model is None:
        st.session_state["prediction"] = None
        st.session_state["validation_errors"] = [
            "The selected model could not be loaded. Please try another model."
        ]
        st.session_state["customer_inputs"] = inputs
        return

    features = prediction.encode_features(inputs)
    result = prediction.predict(model, features)
    result["factors"] = prediction.top_factors(model_choice, features, inputs)
    result["model_alias"] = model_choice
    result["model_label"] = prediction.model_info(model_choice)["label"]
    result["model_accuracy"] = prediction.model_info(model_choice)["accuracy"]
    result["recommendations"] = prediction.generate_recommendations(
        result["risk_label"]
    )

    st.session_state["prediction"] = result
    st.session_state["customer_inputs"] = inputs
    st.session_state["validation_errors"] = None


# ═══════════════════════════════════════════════════════════════════════════════
# RIGHT PANEL — PREDICTION + MODEL INFO
# ═══════════════════════════════════════════════════════════════════════════════


def _waiting_card() -> None:
    st.markdown(
        '<div class="waiting-card">'
        '<div class="waiting-icon">🔮</div>'
        '<div class="waiting-title">Waiting for prediction...</div>'
        '<div class="waiting-text">'
        "Fill in the customer details on the left and click "
        "<b>Predict Customer Churn</b> to see the result."
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def _result_card(result: dict) -> None:
    prob = result["probability_pct"]
    risk = result["risk_label"]
    label = result["label"]

    verdict_color = VERDICT_COLORS.get(label, "#F4F2EE")
    risk_color = RISK_PILL_COLORS.get(risk, "#C8A96B")
    conf_label, conf_color = _confidence(prob)

    st.markdown(
        f'<div class="card" style="animation-delay:0.05s">'
        f'<div class="verdict-label">Prediction</div>'
        f'<div class="verdict" style="color:{verdict_color}">{label}</div>'
        f'<div class="prob-label">Churn Probability '
        f'<span class="tip">ⓘ'
        f'<span class="tip-text">Model output probability — the estimated '
        f"likelihood that this customer will churn.</span>"
        f"</span></div>"
        f'<div class="prob-row">'
        f'<div class="prob-value">{prob:.1f}%</div>'
        f'<div class="prob-caption">of 100</div>'
        f"</div>"
        f'<div class="prob-bar">'
        f'<div class="prob-fill" style="width:{min(prob, 100):.1f}%;background:{risk_color}"></div>'
        f"</div>"
        f'<div class="risk-row">'
        f'<span class="risk-pill" style="background:{risk_color}">'
        f'<span class="pill-dot"></span>{risk}</span>'
        f'<span class="tip">ⓘ'
        f'<span class="tip-text">Risk bands: Low 0–40% · Medium 40–70% · '
        f"High 70–100%.</span>"
        f"</span></div>"
        f'<div class="conf-block">'
        f'<div class="conf-label">Confidence Level</div>'
        f'<div class="conf-value" style="color:{conf_color}">{conf_label}</div>'
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _model_info_card(alias) -> None:
    info = prediction.model_info(alias)
    n_features = len(prediction.FEATURE_NAMES)

    st.markdown(
        f'<div class="card" style="animation-delay:0.12s">'
        f'<div class="card-title">Model Information '
        f'<span class="tip">ⓘ'
        f'<span class="tip-text">Trained classifier used for this prediction. '
        f"Loaded once per session — no retraining occurs.</span>"
        f"</span></div>"
        f'<div class="card-sub">Deployed model metadata</div>'
        f'<div class="mi-grid">'
        f'<div class="mi-item"><div class="mi-label">Model</div>'
        f'<div class="mi-value">{info["label"]}</div></div>'
        f'<div class="mi-item"><div class="mi-label">Accuracy</div>'
        f'<div class="mi-value">{info["accuracy"]:.1f}%</div></div>'
        f'<div class="mi-item"><div class="mi-label">Features Used</div>'
        f'<div class="mi-value">{n_features}</div></div>'
        f'<div class="mi-item"><div class="mi-label">Dataset</div>'
        f'<div class="mi-value">IBM Telco Churn</div></div>'
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# FULL-WIDTH SECTIONS — FACTORS, RECOMMENDATIONS, SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════


def _factors_card(result: dict) -> None:
    factors = result.get("factors") or []
    if not factors:
        return

    source = factors[0]["source"]
    rows = []
    for f in factors:
        contrib = f["contribution"]
        if source == "shap":
            magnitude = abs(contrib)
            scale = max(magnitude for g in factors) or 1.0
            width = magnitude / scale * 100
            if contrib >= 0:
                impact_color = "#D97C7C"
                arrow = "⬆"
                impact_text = "Increases Churn"
            else:
                impact_color = "#8FA28A"
                arrow = "⬇"
                impact_text = "Reduces Churn"
        else:
            scale = max(g["contribution"] for g in factors) or 1.0
            width = contrib / scale * 100
            impact_color = "#C8A96B"
            arrow = "◆"
            impact_text = f"{contrib / scale * 100:.0f}% Model Weight"

        rows.append(
            f'<div class="factor-row">'
            f'<div class="factor-head">'
            f'<div><div class="factor-name">{f["feature"]}</div>'
            f'<div class="factor-value">{f["value"]}</div></div>'
            f'<div class="factor-impact" style="color:{impact_color}">'
            f'<span class="factor-arrow">{arrow}</span>{impact_text}</div>'
            f"</div>"
            f'<div class="factor-bar">'
            f'<div class="factor-fill" style="width:{width:.1f}%;background:{impact_color}"></div>'
            f"</div>"
            f"</div>"
        )

    source_text = (
        "Contributions from SHAP (Shapley values) — magnitude reflects "
        "influence on this prediction."
        if source == "shap"
        else "Ranked by the model's built-in feature importances."
    )
    st.markdown(
        f'<div class="card" style="animation-delay:0.1s">'
        f'<div class="card-title">Top Contributing Factors '
        f'<span class="tip">ⓘ'
        f'<span class="tip-text">SHAP (Shapley) values quantify how much each '
        f"feature pushed this prediction toward churn or retention.</span>"
        f"</span></div>"
        f'<div class="card-sub">How each feature influenced this prediction</div>'
        f'<div class="factors-grid">{"".join(rows)}</div>'
        f'<div class="factor-source">{source_text}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def _recommendations_card(result: dict) -> None:
    recs = result.get("recommendations") or []
    if not recs:
        return

    priority = PRIORITY_LABELS.get(result["risk_label"], "MEDIUM")
    cards = []
    for icon, title, text in recs:
        impact, cost = REC_EXTRA.get(title, ("Improve retention", "Low"))
        cards.append(
            f'<div class="rec-card">'
            f'<div class="rec-head">'
            f'<div class="rec-icon">{icon}</div>'
            f'<div>'
            f'<div class="rec-kicker">Priority · {priority}</div>'
            f'<div class="rec-title">{title}</div>'
            f"</div>"
            f"</div>"
            f'<div class="rec-meta">'
            f'<div class="rec-meta-item">'
            f'<span class="rec-meta-label">Expected Impact</span>'
            f'<span class="rec-meta-value">{impact}</span>'
            f"</div>"
            f'<div class="rec-meta-item">'
            f'<span class="rec-meta-label">Estimated Cost</span>'
            f'<span class="rec-meta-value">{cost}</span>'
            f"</div>"
            f"</div>"
            f"</div>"
        )

    st.markdown(
        f'<div class="card" style="animation-delay:0.15s">'
        f'<div class="card-title">Recommended Actions</div>'
        f'<div class="card-sub">Suggested next steps for the retention team · '
        f'{result["risk_label"]}</div>'
        f'<div class="rec-grid">{"".join(cards)}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def _summary_card() -> None:
    inputs = st.session_state.get("customer_inputs")
    if not inputs:
        return

    cards = []
    for title, icon, features in SUMMARY_GROUPS:
        pairs = "".join(
            f'<div class="summary-item">'
            f'<div class="summary-label">{prediction.FEATURE_LABELS[f]}</div>'
            f'<div class="summary-value">{prediction.display_value(f, inputs[f])}</div>'
            f"</div>"
            for f in features
        )
        cards.append(
            f'<div class="summary-card">'
            f'<div class="summary-card-title">'
            f'<span class="summary-icon">{icon}</span>{title}</div>'
            f'<div class="summary-pairs">{pairs}</div>'
            f"</div>"
        )

    st.markdown(
        f'<div class="card" style="animation-delay:0.2s">'
        f'<div class="card-title">Customer Summary</div>'
        f'<div class="card-sub">Complete profile used for this prediction</div>'
        f'<div class="summary-grid">{"".join(cards)}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def _validation_card() -> None:
    errors = st.session_state.get("validation_errors")
    if not errors:
        return
    items = "".join(
        f'<div class="validation-item">{e}</div>' for e in errors
    )
    st.markdown(
        '<div class="validation-card">'
        '<div class="validation-title">⚠ Please Review the Form</div>'
        f"{items}"
        "</div>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════


def main() -> None:
    """Render the AI Prediction Lab page."""
    _inject_css()

    if "prediction_lab_inited" not in st.session_state:
        st.session_state["prediction_lab_inited"] = True
        st.session_state.pop("prediction", None)
        st.session_state.pop("customer_inputs", None)
        st.session_state.pop("validation_errors", None)

    available = prediction.get_available_models()
    if not available:
        _header()
        st.markdown(
            '<div class="error-card">'
            '<div class="error-icon">⚠️</div>'
            '<div class="error-title">Model Not Found</div>'
            '<div class="error-text">'
            "No trained model was found in the <b>models/</b> directory. "
            "Please ensure at least one of "
            "<b>xgboost_model.pkl</b> or <b>random_forest_model.pkl</b> is present, "
            "then reload this page."
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    _header()

    best = prediction.resolve_best_model()
    left, right = st.columns([0.6, 0.4], gap="large")
    with left:
        _form_panel()
        _validation_card()
    with right:
        result = st.session_state.get("prediction")
        if result is None:
            _waiting_card()
        else:
            _result_card(result)
        _model_info_card(
            result["model_alias"] if result else best
        )

    result = st.session_state.get("prediction")
    if result is not None:
        _factors_card(result)
        _recommendations_card(result)
    if st.session_state.get("customer_inputs"):
        _summary_card()


if __name__ == "__main__":
    main()
