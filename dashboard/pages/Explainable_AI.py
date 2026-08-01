"""
Explainable AI — Customer Churn Analytics Platform

Sprint 5: Premium explainable-AI dashboard. Turns any churn prediction into a
12-section, human-readable decision report:
  01 Prediction Summary     07 Risk Meter
  02 SHAP Waterfall         08 Prioritized Recommendations
  03 Top Drivers            09 Sortable Feature Importance Table
  04 Protective Factors     10 Confidence Level
  05 Business Explanation   11 Export to PDF
  06 What-if Analysis       12 Presentation Mode

Presentation layer only — all prediction, SHAP, and recommendation logic
lives in `prediction.py` and is unchanged here.
"""

import theme

import hashlib
import os
import re
import sys
import time
from datetime import datetime

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from scipy.special import expit

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
    page_title="Explainable AI",
    page_icon="🔬",
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

TIER_META = {
    "High Risk": ("Immediate", "🚨", "#D97C7C"),
    "Medium Risk": ("Near-term", "⏳", "#C8A96B"),
    "Low Risk": ("Long-term", "🌱", "#8FA28A"),
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

# Jargon-free one-line explanations per feature (presentation only).
WHY = {
    "Contract": {
        "pos": "Month-to-month contracts carry the highest churn risk in the industry.",
        "neg": "Longer-term contracts lock in loyalty and strongly reduce churn risk.",
    },
    "Tenure": {
        "pos": "A short tenure signals a customer still in the risky early phase.",
        "neg": "Long tenure reflects strong habit and dramatically lowers churn risk.",
    },
    "Internet Service": {
        "pos": "Fiber optic service correlates with elevated churn.",
        "neg": "No or DSL-only internet service reduces churn exposure.",
    },
    "Payment Method": {
        "pos": "Electronic check payment is one of the strongest churn indicators.",
        "neg": "Automatic payment methods signal commitment and reduce churn.",
    },
    "Monthly Charges": {
        "pos": "Higher monthly spend increases price sensitivity and churn pressure.",
        "neg": "A lower monthly bill reduces price pressure on the customer.",
    },
    "Total Charges": {
        "pos": "High cumulative spend can amplify dissatisfaction.",
        "neg": "Lower cumulative spend limits the financial stakes and churn exposure.",
    },
    "Online Security": {
        "pos": "Missing online security is a common churn-adjacent gap.",
        "neg": "Enrolled online security protects the account and reduces churn.",
    },
    "Tech Support": {
        "pos": "Lack of tech support correlates with more churn.",
        "neg": "Having tech support access resolves issues early and lowers churn.",
    },
    "Online Backup": {
        "pos": "Missing online backup adds to churn pressure.",
        "neg": "Online backup enrolment is protective against churn.",
    },
    "Device Protection": {
        "pos": "Missing device protection adds to churn pressure.",
        "neg": "Device protection enrolment is protective against churn.",
    },
    "Streaming TV": {
        "pos": "Streaming TV without other protections adds churn risk.",
        "neg": "No streaming add-on reduces churn exposure.",
    },
    "Streaming Movies": {
        "pos": "Streaming Movies without other protections adds churn risk.",
        "neg": "No streaming add-on reduces churn exposure.",
    },
    "Partner": {
        "pos": "Partner status nudges risk upward in this profile - unusual.",
        "neg": "Having a partner typically anchors the household and reduces churn.",
    },
    "Dependents": {
        "pos": "Households with dependents rarely churn - a surprising signal here.",
        "neg": "Dependents anchor the household and strongly reduce churn.",
    },
    "Senior Citizen": {
        "pos": "Senior-citizen status is associated with higher churn.",
        "neg": "The age profile mildly favors retention.",
    },
    "Phone Service": {
        "pos": "A phone line adds a small amount of churn surface.",
        "neg": "No phone service avoids an extra churn surface.",
    },
    "Multiple Lines": {
        "pos": "Multiple lines add modest churn pressure.",
        "neg": "A single or no phone line limits churn surface.",
    },
    "Paperless Billing": {
        "pos": "Paperless billing is linked to higher churn.",
        "neg": "Traditional paper billing reduces churn slightly.",
    },
    "Gender": {
        "pos": "Gender contributes only a minor upward tilt here.",
        "neg": "Gender contributes negligibly toward retention.",
    },
}


def _confidence(pct: float) -> tuple:
    """Presentation-only confidence label derived from the model output."""
    if pct >= 70 or pct <= 30:
        return "High", "#8FA28A"
    if pct >= 55 or pct <= 45:
        return "Medium", "#C8A96B"
    return "Low", "#D97C7C"


def _why_sentence(label: str, contribution: float) -> str:
    """Plain-language rationale for a factor's direction on this prediction."""
    d = WHY.get(label)
    if d is None:
        return (
            "This factor pushes toward churn in the current profile."
            if contribution > 0
            else "This factor pulls toward retention in the current profile."
        )
    return d["pos"] if contribution > 0 else d["neg"]


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM CSS
# ═══════════════════════════════════════════════════════════════════════════════


def _inject_css() -> None:
    """Inject the shared design-system styles."""
    theme.inject_css()

def _inject_presentation_css() -> None:
    """Section 12 — larger type, wider canvas, fewer distractions."""
    st.markdown("""
    <style>
    .block-container { max-width: 1900px; }
    .page-title { font-size: 3.9rem; }
    .page-subtitle { font-size: 1.3rem; max-width: 1000px; }
    .sec-title { font-size: 1.35rem; }
    .sec-sub { font-size: 0.95rem; }
    .verdict { font-size: 2.7rem; }
    .prob-value { font-size: 3.1rem; }
    .mi-value { font-size: 1.2rem; }
    .why-box { font-size: 1.25rem; line-height: 2; }
    .factor-name { font-size: 1.05rem; }
    .factor-why { font-size: 0.95rem; }
    .rec-title { font-size: 1.1rem; }
    .rec-text { font-size: 0.95rem; }
    .note-text { font-size: 0.95rem; }
    [data-testid="stVerticalBlockBorderWrapper"] { padding: 0.9rem 1.2rem; }
    </style>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════


def _header() -> None:
    """Hero header with kicker, large title, subtitle, and accent rule."""
    theme.page_header(
        title="Why Did the Model Decide That?",
        kicker="◆ Explainable AI",
        subtitle=(
            "A transparent, jargon-free breakdown of every churn prediction — "
            "from the SHAP math underneath to the business actions on top."
        ),
        rule=True,
        back_link=True,
    )


def _section_head(num: str, icon: str, title: str, sub: str) -> None:
    """Numbered section header used across the 12-part dashboard."""
    st.markdown(theme.section_head(num, icon, title, sub), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOMER PROFILE FORM (writes to the shared session state)
# ═══════════════════════════════════════════════════════════════════════════════


def _form_panel() -> None:
    """Customer profile form. Uses the exact same pipeline as the
    AI Prediction Lab and writes to the same session-state keys."""
    available = prediction.get_available_models()
    best = prediction.resolve_best_model()

    with st.form("xai_form"):
        st.markdown(
            '<div class="card-title">Customer Profile</div>'
            '<div class="card-sub">Run a prediction, then explore the '
            "explainable analysis below</div>",
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

        st.markdown(
            '<div class="card-title" style="margin-top:0.8rem">Personal & Account</div>',
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            gender = st.selectbox("Gender", ["Male", "Female"])
        with c2:
            senior = st.radio("Senior Citizen", ["No", "Yes"], horizontal=True)
        with c3:
            partner = st.radio("Partner", ["No", "Yes"], horizontal=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            dependents = st.radio("Dependents", ["No", "Yes"], horizontal=True)
        with c2:
            tenure = st.slider(
                "Tenure (months)", min_value=0, max_value=72, value=36, step=1
            )
        with c3:
            contract = st.selectbox(
                "Contract", ["Month-to-month", "One year", "Two year"]
            )
        c1, c2 = st.columns(2)
        with c1:
            paperless = st.radio("Paperless Billing", ["No", "Yes"], horizontal=True)
        with c2:
            payment_method = st.selectbox(
                "Payment Method",
                ["Electronic check", "Mailed check",
                 "Bank transfer (automatic)", "Credit card (automatic)"],
            )

        st.markdown(
            '<div class="card-title" style="margin-top:0.8rem">Services</div>',
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            phone_service = st.radio("Phone Service", ["No", "Yes"], horizontal=True)
        with c2:
            multiple_lines = st.selectbox(
                "Multiple Lines", ["No", "No phone service", "Yes"]
            )
        with c3:
            internet_service = st.selectbox(
                "Internet Service", ["DSL", "Fiber optic", "No"]
            )
        c1, c2, c3 = st.columns(3)
        with c1:
            online_security = st.selectbox(
                "Online Security", ["No", "No internet service", "Yes"]
            )
        with c2:
            online_backup = st.selectbox(
                "Online Backup", ["No", "No internet service", "Yes"]
            )
        with c3:
            device_protection = st.selectbox(
                "Device Protection", ["No", "No internet service", "Yes"]
            )
        c1, c2, c3 = st.columns(3)
        with c1:
            tech_support = st.selectbox(
                "Tech Support", ["No", "No internet service", "Yes"]
            )
        with c2:
            streaming_tv = st.selectbox(
                "Streaming TV", ["No", "No internet service", "Yes"]
            )
        with c3:
            streaming_movies = st.selectbox(
                "Streaming Movies", ["No", "No internet service", "Yes"]
            )

        st.markdown(
            '<div class="card-title" style="margin-top:0.8rem">Billing</div>',
            unsafe_allow_html=True,
        )
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
            "🔬 Analyze This Customer", width="stretch"
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
        st.session_state["validation_errors"] = errors
        st.session_state["customer_inputs"] = inputs
        return

    with st.status("Running explainability pipeline…", expanded=True) as status:
        status.update(label="Loading the trained model…", state="running")
        model = prediction.load_model(model_choice)
        time.sleep(0.1)
        if model is None:
            status.update(label="Model load failed", state="error")
            st.session_state["validation_errors"] = [
                "The selected model could not be loaded. Please try another model."
            ]
            st.session_state["customer_inputs"] = inputs
            return

        status.update(label="Encoding customer features…")
        features = prediction.encode_features(inputs)
        time.sleep(0.1)

        status.update(label="Scoring churn probability…")
        result = prediction.predict(model, features)
        time.sleep(0.1)

        status.update(label="Computing SHAP contributions…")
        result["factors"] = prediction.top_factors(model_choice, features, inputs)
        result["model_alias"] = model_choice
        result["model_label"] = prediction.model_info(model_choice)["label"]
        result["model_accuracy"] = prediction.model_info(model_choice)["accuracy"]
        result["recommendations"] = prediction.generate_recommendations(
            result["risk_label"]
        )

        status.update(label="Explanation ready", state="complete", expanded=False)

    st.session_state["prediction"] = result
    st.session_state["customer_inputs"] = inputs
    st.session_state["validation_errors"] = None
    st.toast("Explanation complete", icon="✅")


def _validation_card() -> None:
    errors = st.session_state.get("validation_errors")
    if not errors:
        return
    items = "".join(f'<div class="validation-item">{e}</div>' for e in errors)
    st.markdown(
        '<div class="validation-card">'
        '<div class="validation-title">⚠ Please Review the Form</div>'
        f"{items}"
        "</div>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 01 — PREDICTION SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════


def _hero(result: dict) -> None:
    prob = result["probability_pct"]
    risk = result["risk_label"]
    label = result["label"]
    verdict_color = VERDICT_COLORS.get(label, "#F4F2EE")
    risk_color = RISK_PILL_COLORS.get(risk, "#C8A96B")
    conf_label, conf_color = _confidence(prob)
    info = prediction.model_info(result["model_alias"])

    c1, c2, c3 = st.columns([1.15, 1.5, 1], gap="large")
    with c1:
        with st.container(border=True):
            st.markdown(
                f'<div class="verdict-label">Prediction</div>'
                f'<div class="verdict" style="color:{verdict_color}">{label}</div>'
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
                f"</div>",
                unsafe_allow_html=True,
            )
    with c2:
        with st.container(border=True):
            st.markdown(
                f'<div class="prob-label">Churn Probability '
                f'<span class="tip">ⓘ'
                f'<span class="tip-text">Model output probability — the estimated '
                f"likelihood this customer will churn.</span>"
                f"</span></div>"
                f'<div class="prob-row">'
                f'<div class="prob-value">{prob:.1f}%</div>'
                f'<div class="prob-caption">of 100</div>'
                f"</div>"
                f'<div class="prob-bar">'
                f'<div class="prob-fill" style="width:{min(prob, 100):.1f}%;'
                f'background:{risk_color}"></div>'
                f"</div>"
                f'<div class="note-text">'
                f"Decision threshold at <b>50%</b> — the model is "
                f"{abs(prob - 50):.1f} pts {('above' if prob >= 50 else 'below')} "
                f"the churn/stay decision line.</div>",
                unsafe_allow_html=True,
            )
    with c3:
        with st.container(border=True):
            st.markdown(
                f'<div class="card-title">Model</div>'
                f'<div class="mi-grid">'
                f'<div class="mi-item"><div class="mi-label">Classifier</div>'
                f'<div class="mi-value">{info["label"]}</div></div>'
                f'<div class="mi-item"><div class="mi-label">Accuracy</div>'
                f'<div class="mi-value">{info["accuracy"]:.1f}%</div></div>'
                f'<div class="mi-item"><div class="mi-label">AUC-ROC</div>'
                f'<div class="mi-value">{info["auc"]:.4f}</div></div>'
                f'<div class="mi-item"><div class="mi-label">Features</div>'
                f'<div class="mi-value">{len(prediction.FEATURE_NAMES)}</div></div>'
                f"</div>"
                f'<div class="note-text">Explanations use SHAP Shapley values '
                f"from the deployed model — no retraining occurs.</div>",
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════════════════
# SHAP HELPERS (reuse the cached explainer — never recompute logic)
# ═══════════════════════════════════════════════════════════════════════════════


def _shap_factors(alias: str, features: np.ndarray, inputs: dict):
    """All SHAP contributions for the prediction (or None if unavailable)."""
    base, raw = prediction.get_shap_values(alias, features)
    if raw is None:
        return None, None
    factors = []
    for i, feat in enumerate(prediction.FEATURE_NAMES):
        factors.append({
            "feature": prediction.FEATURE_LABELS[feat],
            "value": prediction.display_value(feat, inputs[feat]),
            "contribution": float(raw[i]),
            "key": feat,
        })
    factors.sort(key=lambda f: abs(f["contribution"]), reverse=True)
    return base, factors


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 02 — SHAP WATERFALL PLOT
# ═══════════════════════════════════════════════════════════════════════════════


def _waterfall_figure(base: float, values: np.ndarray, inputs: dict):
    """Actual SHAP waterfall — starts at the base rate, each factor shifts
    the model output until it lands on this customer's prediction."""
    vals = np.asarray([float(v) for v in values])
    labels = [prediction.FEATURE_LABELS[f] for f in prediction.FEATURE_NAMES]

    order = np.argsort(-np.abs(vals))
    vals_s = vals[order]
    labels_s = [labels[i] for i in order]
    disp_s = [
        prediction.display_value(prediction.FEATURE_NAMES[i],
                                 inputs[prediction.FEATURE_NAMES[i]])
        for i in order
    ]

    cum = base + np.concatenate([[0.0], np.cumsum(vals_s)[:-1]])
    final = float(base + vals.sum())
    y = np.arange(len(vals_s))[::-1]

    fig, ax = plt.subplots(figsize=(11, 7.5), facecolor="#0F3040")
    ax.set_facecolor("#0F3040")

    for yi, v, start, lab, disp in zip(y, vals_s, cum, labels_s, disp_s):
        color = "#D97C7C" if v >= 0 else "#8FA28A"
        ax.barh(yi, v, left=start, height=0.72, color=color, zorder=3)
        ax.annotate(
            f"{v:+.2f}", xy=(start + v, yi), va="center",
            ha="left" if v >= 0 else "right",
            color="#F4F2EE", fontsize=8.5, fontweight="bold",
            xytext=(3 if v >= 0 else -3, 0), textcoords="offset points",
        )

    ax.axvline(base, color="#C8A96B", linestyle="--", linewidth=1, alpha=0.85)
    ax.set_yticks(y)
    ax.set_yticklabels(
        [f"{lab}  ·  {disp}" for lab, disp in zip(labels_s, disp_s)],
        color="#D6D8D8", fontsize=8.5,
    )
    ax.set_xticks([base, final])
    ax.set_xticklabels([f"base {base:.2f}", f"{final:.2f}"],
                       color="#C8A96B", fontsize=8.5)
    ax.set_xlabel(
        "Model output (log-odds)  —  higher = more churn risk",
        color="#D6D8D8", fontsize=9,
    )
    ax.set_title(
        f"Churn probability after all factors: {expit(final) * 100:.1f}%   "
        f"(baseline {expit(base) * 100:.1f}%)",
        color="#F4F2EE", fontsize=10.5, pad=12,
    )
    ax.tick_params(axis="x", colors="#D6D8D8")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#234556")
    ax.grid(axis="x", color="#234556", alpha=0.6, linestyle=":")
    ax.set_xlim(min(base, cum.min()) - 0.4, max(final, cum.max()) + 0.4)

    fig.subplots_adjust(left=0.34, right=0.97, top=0.9, bottom=0.12)
    return fig


def _waterfall(alias: str, features: np.ndarray, inputs: dict) -> None:
    with st.container(border=True):
        base, values = prediction.get_shap_values(alias, features)
        if values is None:
            return
        st.pyplot(_waterfall_figure(base, values, inputs))
        st.markdown(
            '<div class="note-text">'
            "Red bars push the prediction <b>toward churn</b>; green bars pull it "
            "<b>toward retention</b>. The dashed gold line is the base churn rate "
            "of the training population; the model moves from that baseline to "
            "this customer's probability, one factor at a time."
            "</div>",
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTIONS 03 & 04 — TOP DRIVERS / PROTECTIVE FACTORS
# ═══════════════════════════════════════════════════════════════════════════════


def _factor_column(num, icon, title, sub, factors, positive: bool) -> None:
    if not factors:
        return
    accent = "#D97C7C" if positive else "#8FA28A"
    arrow = "⬆" if positive else "⬇"
    impact_text = "Increases Churn" if positive else "Reduces Churn"
    max_abs = max((abs(f["contribution"]) for f in factors), default=1.0)

    _section_head(num, icon, title, sub)
    rows = []
    for f in factors[:6]:
        width = abs(f["contribution"]) / max_abs * 100
        rows.append(
            f'<div class="factor-row">'
            f'<div class="factor-head">'
            f'<div><div class="factor-name">{f["feature"]}</div>'
            f'<div class="factor-value">{f["value"]}</div></div>'
            f'<div class="factor-impact" style="color:{accent}">'
            f'<span class="factor-arrow">{arrow}</span>{impact_text}</div>'
            f"</div>"
            f'<div class="factor-bar">'
            f'<div class="factor-fill" style="width:{width:.0f}%;'
            f'background:{accent}"></div></div>'
            f'<div class="factor-why">{_why_sentence(f["feature"], f["contribution"])}</div>'
            f"</div>"
        )
    with st.container(border=True):
        st.markdown("".join(rows), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 05 — PLAIN-LANGUAGE BUSINESS EXPLANATION
# ═══════════════════════════════════════════════════════════════════════════════


def _explanation(result: dict, factors: list) -> None:
    prob = result["probability_pct"]
    risk = result["risk_label"]
    drivers = [f for f in factors if f["contribution"] > 0]
    protectors = [f for f in factors if f["contribution"] < 0]

    top = drivers[0] if drivers else None
    second = drivers[1] if len(drivers) > 1 else None
    prot = protectors[0] if protectors else None
    prot2 = protectors[1] if len(protectors) > 1 else None

    s = [
        f"This customer is <b>{prob:.0f}% likely to churn</b> and sits in the "
        f"<b>{risk}</b> band.",
    ]
    if top:
        s.append(
            f"The single strongest signal is <b>{top['feature']} "
            f"({top['value']})</b> — "
            f"{_why_sentence(top['feature'], top['contribution']).lower()}"
        )
    if second:
        s.append(
            f"Secondary pressure comes from <b>{second['feature']} "
            f"({second['value']})</b>."
        )
    if prot:
        s.append(
            f"Pulling the other way, <b>{prot['feature']} ({prot['value']})</b> — "
            f"{_why_sentence(prot['feature'], prot['contribution']).lower()}"
        )
    if prot2:
        s.append(
            f"<b>{prot2['feature']} ({prot2['value']})</b> also helps retention."
        )
    s.append(
        "Across all 19 factors the model lands on its final decision. "
        "The waterfall below shows the same story visually: bars above the "
        "baseline push toward churn, bars below it toward retention."
    )

    _section_head("05", "🗣️", "Plain-Language Explanation",
                  "What this prediction means in business terms")
    with st.container(border=True):
        st.markdown(
            '<div class="why-box">'
            + "".join(f"<p>{p}</p>" for p in s)
            + "</div>",
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 06 — WHAT-IF ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════


def _what_if(result: dict, inputs: dict) -> None:
    alias = result["model_alias"]
    base_prob = result["probability_pct"]
    base_verdict = result["label"]
    base_color = VERDICT_COLORS.get(base_verdict, "#F4F2EE")

    _section_head("06", "🧪", "What-if Analysis",
                  "Simulate how changing one factor reshapes the prediction")

    feats = list(prediction.FEATURE_NAMES)
    chosen = st.selectbox(
        "Feature to simulate",
        feats,
        format_func=lambda f: prediction.FEATURE_LABELS[f],
        key="xai_whatif_feat",
    )
    label = prediction.FEATURE_LABELS[chosen]
    current = inputs[chosen]

    c1, c2 = st.columns([1.15, 1.5], gap="large")
    with c1:
        with st.container(border=True):
            st.markdown(
                f'<div class="whatif-feature">Current · {label}</div>'
                f'<div class="whatif-value">{prediction.display_value(chosen, current)}</div>'
                f'<div class="whatif-current">Baseline churn probability</div>'
                f'<div class="prob-row">'
                f'<div class="prob-value" style="font-size:1.9rem">{base_prob:.1f}%</div>'
                f'<div class="prob-caption">churn</div></div>'
                f'<div class="verdict" style="font-size:1.2rem;color:{base_color}">'
                f"{base_verdict}</div>",
                unsafe_allow_html=True,
            )
    with c2:
        with st.container(border=True):
            st.markdown(
                f'<div class="whatif-feature">Simulate a change</div>',
                unsafe_allow_html=True,
            )
            if chosen in prediction.ENCODINGS:
                options = list(prediction.ENCODINGS[chosen].keys())
                idx = options.index(current) if current in options else 0
                new_val = st.selectbox(
                    "New value", options, index=idx,
                    key="xai_whatif_val_cat",
                )
            else:
                bounds = {
                    "tenure": (0, 72, 1),
                    "MonthlyCharges": (0.0, 400.0, 5.0),
                    "TotalCharges": (0.0, 12000.0, 50.0),
                }
                lo, hi, step = bounds[chosen]
                new_val = st.slider(
                    "New value", lo, hi, float(current), step,
                    key="xai_whatif_val_num",
                )

            model = prediction.load_model(alias)
            sim_inputs = dict(inputs)
            sim_inputs[chosen] = new_val
            sim_features = prediction.encode_features(sim_inputs)
            sim = prediction.predict(model, sim_features)
            sim_prob = sim["probability_pct"]
            delta = sim_prob - base_prob

            if delta > 0:
                arrow = "➜"
                badge = f"▲ {delta:+.1f} pts"
                badge_color = "#D97C7C"
                delta_txt = "Risk increases"
            elif delta < 0:
                arrow = "➜"
                badge = f"▼ {delta:+.1f} pts"
                badge_color = "#8FA28A"
                delta_txt = "Risk decreases"
            else:
                arrow = "➜"
                badge = "— no change"
                badge_color = "#C8A96B"
                delta_txt = "No effect"

            sim_risk_color = RISK_PILL_COLORS.get(sim["risk_label"], "#C8A96B")
            st.markdown(
                f'<div class="delta-row">'
                f'<div class="delta-step">{base_prob:.1f}%</div>'
                f'<div class="delta-arrow">{arrow}</div>'
                f'<div class="delta-step" style="color:{sim_risk_color}">'
                f"{sim_prob:.1f}%</div>"
                f'<div class="delta-badge" style="background:{badge_color}">'
                f"{badge}</div>"
                f'<div class="delta-verdict" style="color:{sim_risk_color}">'
                f"{sim['label']} · {sim['risk_label']}</div>"
                f"</div>"
                f'<div class="whatif-note">'
                f"Only <b>{label}</b> changed — from "
                f"<b>{prediction.display_value(chosen, current)}</b> to "
                f"<b>{prediction.display_value(chosen, new_val)}</b> — "
                f"while all 18 other inputs were held constant. "
                f"<b>{delta_txt}</b>.</div>",
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 07 — RISK METER GAUGE
# ═══════════════════════════════════════════════════════════════════════════════


def _gauge_figure(prob: float, risk_color: str, risk_label: str):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=prob,
        number={"suffix": "%", "font": {"color": "#F4F2EE", "size": 46}},
        title={"text": "Churn Risk", "font": {"color": "#C8A96B", "size": 15}},
        gauge={
            "shape": "angular",
            "axis": {
                "range": [0, 100],
                "tickcolor": "#D6D8D8",
                "tickfont": {"color": "#D6D8D8", "size": 11},
            },
            "bar": {"color": risk_color, "thickness": 0.28},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40], "color": "rgba(143,162,138,0.30)"},
                {"range": [40, 70], "color": "rgba(200,169,107,0.30)"},
                {"range": [70, 100], "color": "rgba(217,124,124,0.30)"},
            ],
            "threshold": {
                "line": {"color": "#F4F2EE", "width": 3},
                "thickness": 0.85,
                "value": prob,
            },
        },
    ))
    fig.update_layout(
        height=300,
        margin=dict(t=60, b=10, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif"},
        annotations=[
            dict(
                text=risk_label,
                x=0.5, y=0.42, showarrow=False,
                font={"size": 15, "color": risk_color},
            )
        ],
    )
    return fig


def _risk_meter(prob: float, risk_color: str, risk_label: str) -> None:
    with st.container(border=True):
        st.plotly_chart(_gauge_figure(prob, risk_color, risk_label),
                        width="stretch")
        st.markdown(
            f'<div class="note-text">Risk bands: Low 0–40% · Medium 40–70% · '
            f"High 70–100%. This customer sits in <b>{risk_label}</b>.</div>",
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 08 — PRIORITIZED RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════════════════


def _recommendations(result: dict) -> None:
    recs = result.get("recommendations") or []
    if not recs:
        return

    tier, tier_icon, tier_color = TIER_META.get(
        result["risk_label"], ("Near-term", "⏳", "#C8A96B")
    )

    _section_head("08", "🛠️", "Prioritized Recommendations",
                  f"Suggested next steps · grouped by urgency for {result['risk_label']}")

    cards = []
    for icon, title, text in recs:
        impact, cost = REC_EXTRA.get(title, ("Improve retention", "Low"))
        cards.append(
            f'<div class="rec-card">'
            f'<div class="rec-head">'
            f'<div class="rec-icon">{icon}</div>'
            f'<div>'
            f'<div class="rec-kicker">Priority · {tier}</div>'
            f'<div class="rec-title">{title}</div>'
            f"</div></div>"
            f'<div class="rec-text">{text}</div>'
            f'<div class="rec-meta">'
            f'<div class="rec-meta-item">'
            f'<span class="rec-meta-label">Expected Impact</span>'
            f'<span class="rec-meta-value">{impact}</span></div>'
            f'<div class="rec-meta-item">'
            f'<span class="rec-meta-label">Estimated Cost</span>'
            f'<span class="rec-meta-value">{cost}</span></div>'
            f"</div></div>"
        )

    with st.container(border=True):
        st.markdown(
            f'<div class="tier-banner">'
            f'<span class="tier-badge" style="background:{tier_color}">{tier}</span>'
            f"{tier_icon} Recommended actions for this customer "
            f"({len(recs)} steps)</div>",
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="rec-grid">{"".join(cards)}</div>',
                    unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 09 — SORTABLE FEATURE IMPORTANCE TABLE
# ═══════════════════════════════════════════════════════════════════════════════


def _importance_table(factors: list) -> None:
    rows = [{
        "Feature": f["feature"],
        "Current Value": f["value"],
        "Contribution": f["contribution"],
        "Impact": abs(f["contribution"]),
        "Direction": ("Increases churn" if f["contribution"] >= 0
                      else "Reduces churn"),
    } for f in factors]
    df = pd.DataFrame(rows).sort_values("Impact", ascending=False).reset_index(drop=True)

    try:
        styled = df.style.set_properties(**{
            "background-color": "#163949",
            "color": "#F4F2EE",
            "border": "none",
            "font-family": "Inter, sans-serif",
            "font-size": "12px",
        })
        styled = styled.map(lambda v: (
            "color:#D97C7C;font-weight:600"
            if v == "Increases churn"
            else ("color:#8FA28A;font-weight:600" if v == "Reduces churn" else "")
        ))
        styled = styled.set_table_styles([{
            "selector": "th",
            "props": [
                ("background-color", "#234556"),
                ("color", "#C8A96B"),
                ("font-weight", "600"),
                ("font-size", "11px"),
                ("border", "none"),
                ("text-transform", "uppercase"),
            ],
        }])
        st.dataframe(
            styled,
            width="stretch",
            hide_index=True,
            column_config={
                "Contribution": st.column_config.NumberColumn(
                    "Contribution (SHAP)", format="%+.2f",
                ),
                "Impact": st.column_config.NumberColumn("Impact (abs)", format="%.2f"),
            },
        )
    except Exception:
        st.dataframe(df, width="stretch", hide_index=True)

    st.markdown(
        '<div class="note-text">'
        "All 19 features ranked by absolute SHAP contribution. Click any column "
        "header to re-sort. Positive contributions increase churn risk; "
        "negative contributions reduce it.</div>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 10 — CONFIDENCE LEVEL
# ═══════════════════════════════════════════════════════════════════════════════


def _confidence_card(result: dict) -> None:
    prob = result["probability_pct"]
    conf_label, conf_color = _confidence(prob)
    margin = abs(prob - 50)
    side = "churn" if prob >= 50 else "stay"

    with st.container(border=True):
        st.markdown(
            f'<div class="conf-block" style="margin-bottom:0.9rem">'
            f'<div class="conf-label">Confidence Level</div>'
            f'<div class="conf-value" style="color:{conf_color}">{conf_label}</div>'
            f"</div>"
            f'<div class="note-text">'
            f"The prediction sits <b>{margin:.1f} pts</b> away from the 50% "
            f"decision threshold, on the <b>{side}</b> side. Larger margins "
            f"mean more decisive (and more confident) model outputs. "
            f"Confidence here is a presentation-level summary of that margin."
            f"</div>",
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 11 — EXPORT TO PDF
# ═══════════════════════════════════════════════════════════════════════════════


def _ascii(text) -> str:
    """Strip non-Latin-1 characters for fpdf2's core fonts."""
    return re.sub(r"[^\x00-\x7F]", "", str(text))


def _build_pdf(result: dict, inputs: dict, all_factors=None) -> bytes:
    """Build a clean multi-page PDF report with fpdf2."""
    prob = result["probability_pct"]
    conf_label, _ = _confidence(prob)
    info = prediction.model_info(result["model_alias"])
    factors = all_factors if all_factors else result.get("factors", [])

    class Report(FPDF):
        def footer(self):
            self.set_y(-14)
            self.set_font("Helvetica", "", 7)
            self.set_text_color(150, 150, 150)
            self.cell(0, 5, f"Customer Churn Analytics Platform  -  Page {self.page_no()}",
                      align="C")

    pdf = Report(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(14, 15, 14)
    pdf.add_page()

    # Header band
    pdf.set_fill_color(15, 48, 64)
    pdf.rect(0, 0, 210, 30, "F")
    pdf.set_fill_color(200, 169, 107)
    pdf.rect(0, 30, 210, 2.2, "F")
    pdf.set_text_color(244, 242, 238)
    pdf.set_xy(14, 7)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 7, "Explainable AI Report - Customer Churn")
    pdf.set_xy(14, 16)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(214, 216, 216)
    pdf.cell(0, 5, "Model decision report generated by the Customer Churn Analytics Platform")
    pdf.set_xy(14, 22)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 5, datetime.now().strftime("Generated %Y-%m-%d at %H:%M"))

    def section(title):
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_fill_color(200, 169, 107)
        pdf.set_text_color(15, 48, 64)
        pdf.cell(0, 8, title, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(30, 40, 45)
        pdf.ln(2)

    def kv(label, value):
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(62, 6, _ascii(label), new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 6, _ascii(value), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    section("1. Prediction Summary")
    kv("Prediction", result["label"])
    kv("Churn probability", f"{prob:.1f}%")
    kv("Risk level", result["risk_label"])
    kv("Confidence level", conf_label)
    kv("Model", info["label"])
    kv("Model accuracy", f"{info['accuracy']:.1f}%")

    section("2. Customer Profile")
    for feat in prediction.FEATURE_NAMES:
        kv(prediction.FEATURE_LABELS[feat],
           prediction.display_value(feat, inputs[feat]))

    section("3. Top Contributing Factors")
    for f in (result.get("factors") or [])[:5]:
        sign = "increases churn" if f["contribution"] >= 0 else "reduces churn"
        kv(f"{f['feature']} ({f['value']})",
           f"{f['contribution']:+.2f}  -  {sign}")

    section("4. Recommended Actions")
    for icon, title, text in result.get("recommendations", []):
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 5, f"- {_ascii(title)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.multi_cell(0, 4.5, _ascii(text))
        pdf.ln(1)

    section("5. Feature Importance (all features)")
    for f in factors:
        sign = "increases churn" if f["contribution"] >= 0 else "reduces churn"
        kv(f"{f['feature']} ({f['value']})",
           f"{f['contribution']:+.2f}  -  {sign}")

    section("6. Methodology Note")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(60, 70, 75)
    pdf.multi_cell(
        0, 4.5,
        _ascii(
            f"Contributions are SHAP (Shapley) values computed from the deployed "
            f"{info['label']} classifier ({len(prediction.FEATURE_NAMES)} features, "
            f"trained on the IBM Telco Customer Churn dataset). Each value is the "
            f"log-odds shift that factor applied to the model's prediction, "
            f"starting from the population base rate. Recommendations are "
            f"rule-based actions matched to the customer's risk level."
        ),
    )

    return bytes(pdf.output())


def _export_signature(result: dict, inputs: dict, all_factors) -> str:
    """Stable signature for caching generated export bytes per prediction."""
    factors_str = "|".join(
        f"{f.get('feature')}:{f.get('contribution', 0.0):.4f}:{f.get('value', '')}"
        for f in (all_factors or [])
    )
    flat = (
        str(result.get("label")),
        f"{result.get('probability_pct', 0.0):.4f}",
        str(result.get("risk_label")),
        str(result.get("model_alias")),
        str(sorted((inputs or {}).items())),
        factors_str,
    )
    return hashlib.sha1("|".join(flat).encode("utf-8")).hexdigest()


def _cached_export(kind: str, signature: str, factory) -> bytes | None:
    """Return cached export bytes for this signature, or build and cache them."""
    key = f"_export_cache_{kind}"
    cached = st.session_state.get(key)
    if cached is not None and cached[0] == signature:
        return cached[1]
    try:
        data = factory()
    except Exception:
        return None
    st.session_state[key] = (signature, data)
    return data


def _export_pdf(result: dict, inputs: dict, all_factors) -> None:
    _section_head("11", "📄", "Export to PDF",
                  "Download this decision as a shareable report")

    with st.container(border=True):
        st.markdown(
            '<div class="export-desc">'
            "Generates a clean, self-contained PDF with the prediction summary, "
            "customer profile, top contributing factors, recommended actions, "
            "and the full 19-feature importance breakdown — ready to share with "
            "stakeholders or attach to a CRM case."
            "</div>",
            unsafe_allow_html=True,
        )

        signature = _export_signature(result, inputs, all_factors)
        pdf_bytes = _cached_export(
            "xai_pdf", signature,
            lambda: _build_pdf(result, inputs, all_factors),
        )
        if pdf_bytes:
            clicked = theme.download_button(
                "📥 Download PDF Report",
                data=pdf_bytes,
                file_name="explainable_ai_report.pdf",
                mime="application/pdf",
                key="xai_pdf_download",
            )
            if clicked:
                st.toast("PDF report download started", icon="📥")
        else:
            st.markdown(
                '<div class="error-text">PDF generation is unavailable right '
                "now.</div>",
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════


def main() -> None:
    """Render the Explainable AI dashboard."""
    _inject_css()
    _header()

    available = prediction.get_available_models()
    if not available:
        st.markdown(
            '<div class="error-card">'
            '<div class="error-icon">⚠️</div>'
            '<div class="error-title">Model Not Found</div>'
            '<div class="error-text">'
            "No trained model was found in the <b>models/</b> directory. "
            "Please ensure at least one of <b>xgboost_model.pkl</b> or "
            "<b>random_forest_model.pkl</b> is present, then reload this page."
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    # Section 12 — Presentation mode control (affects the whole page).
    present = st.toggle(
        "🎬 Presentation Mode",
        help="Hide input controls and enlarge the analysis for screen sharing.",
        key="xai_present",
    )
    if present:
        _inject_presentation_css()

    st.markdown(
        '<div class="meta-hint">A <b>12-section</b> explainable breakdown of '
        "the latest churn prediction.</div>",
        unsafe_allow_html=True,
    )

    # Render the profile form first (like the AI Prediction Lab) so its
    # session-state write is visible in the same script run.
    if not present:
        has_errors = bool(st.session_state.get("validation_errors"))
        result_before = st.session_state.get("prediction")
        with st.expander(
            "Customer Profile", expanded=(result_before is None or has_errors)
        ):
            _form_panel()
        _validation_card()

    result = st.session_state.get("prediction")
    inputs = st.session_state.get("customer_inputs")

    if result is None or inputs is None:
        st.markdown(
            '<div class="entry-card">'
            '<div class="entry-icon">🔬</div>'
            '<div class="entry-title">No prediction yet</div>'
            '<div class="entry-text">'
            "Run a prediction using the customer profile above (or from the AI "
            "Prediction Lab) and this page will break the model's decision down "
            "into 12 explainable sections — from the SHAP waterfall to PDF export."
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="waiting-card">'
            '<div class="waiting-icon">🔬</div>'
            '<div class="waiting-title">Waiting for a prediction...</div>'
            '<div class="waiting-text">'
            "Fill in the customer details above and click <b>Analyze This "
            "Customer</b> to generate the explainable analysis."
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    # ── Shared analysis inputs ──────────────────────────────────────────────
    features_vec = prediction.encode_features(inputs)
    alias = result["model_alias"]
    base, factors = _shap_factors(alias, features_vec, inputs)

    # 01 · Prediction Summary
    _section_head("01", "🎯", "Prediction Summary",
                  "The model's decision at a glance")
    _hero(result)

    # 02 · SHAP Waterfall
    _section_head("02", "📊", "SHAP Waterfall",
                  "How the model moved from the base rate to this customer")
    if base is not None:
        _waterfall(alias, features_vec, inputs)
    else:
        with st.container(border=True):
            st.markdown(
                '<div class="note-text">SHAP values are unavailable for this '
                "model, so the waterfall cannot be drawn. Top contributing "
                "factors below come from the model's built-in importances "
                "instead.</div>",
                unsafe_allow_html=True,
            )

    # 03 & 04 · Drivers / Protective factors
    drivers = [f for f in factors if f["contribution"] > 0] if factors else []
    protectors = [f for f in factors if f["contribution"] < 0] if factors else []
    c1, c2 = st.columns(2, gap="large")
    with c1:
        _factor_column("03", "🔥", "Top Drivers",
                       "What is pushing this customer toward churn",
                       drivers, positive=True)
    with c2:
        _factor_column("04", "🛡️", "Protective Factors",
                       "What is keeping this customer from churning",
                       protectors, positive=False)

    # 05 · Plain-language explanation
    if factors:
        _explanation(result, factors)

    # 06 · What-if analysis
    if not present:
        _what_if(result, inputs)

    # 07 · Risk Meter  |  10 · Confidence (paired layout)
    risk_color = RISK_PILL_COLORS.get(result["risk_label"], "#C8A96B")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        _section_head("07", "🎚️", "Risk Meter",
                      "Where this customer sits on the churn scale")
        _risk_meter(result["probability_pct"], risk_color, result["risk_label"])
    with c2:
        _section_head("10", "💯", "Confidence Level",
                      "How decisive the model is about this prediction")
        _confidence_card(result)

    # 08 · Prioritized recommendations
    _recommendations(result)

    # 09 · Sortable feature importance table
    _section_head("09", "📋", "Feature Importance",
                  "All 19 features — sortable, ranked by impact")
    with st.container(border=True):
        _importance_table(factors)

    # 11 · Export to PDF
    _export_pdf(result, inputs, factors)


if __name__ == "__main__":
    main()
