"""
AI Prediction Lab — Customer Churn Analytics Platform

Sprint 5: Premium enterprise UI for single-customer churn prediction.
Runs inference only via the pre-trained XGBoost / Random Forest models.

Presentation layer only — all prediction, SHAP, and recommendation
logic lives in `prediction.py` and is unchanged here.
"""

import theme

import hashlib
import os
import sys
import time

import streamlit as st

try:
    import prediction
except ModuleNotFoundError:
    _dashboard_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _dashboard_dir not in sys.path:
        sys.path.insert(0, _dashboard_dir)
    import prediction

try:
    import report
except ModuleNotFoundError:
    _dashboard_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _dashboard_dir not in sys.path:
        sys.path.insert(0, _dashboard_dir)
    import report

try:
    import pptx_report
except ModuleNotFoundError:
    _dashboard_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _dashboard_dir not in sys.path:
        sys.path.insert(0, _dashboard_dir)
    import pptx_report

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
    """Inject the shared design-system styles."""
    theme.inject_css()

def _header() -> None:
    """Hero header with kicker, large title, subtitle, and accent rule."""
    theme.page_header(
        title="AI Customer Churn Prediction",
        kicker="◆ AI Prediction Lab",
        subtitle=(
            "Predict customer churn using the trained machine learning model "
            "and explain the prediction using model insights."
        ),
        rule=True,
        back_link=True,
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
            "🔮 Predict Customer Churn", width="stretch"
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

    with st.status("Running churn prediction…", expanded=True) as status:
        status.update(label="Loading the trained model…", state="running")
        model = prediction.load_model(model_choice)
        time.sleep(0.1)
        if model is None:
            status.update(label="Model load failed", state="error")
            st.session_state["prediction"] = None
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

        status.update(label="Explaining the model decision…")
        result["factors"] = prediction.top_factors(model_choice, features, inputs)
        result["model_alias"] = model_choice
        result["model_label"] = prediction.model_info(model_choice)["label"]
        result["model_accuracy"] = prediction.model_info(model_choice)["accuracy"]
        result["recommendations"] = prediction.generate_recommendations(
            result["risk_label"]
        )

        status.update(label="Prediction ready", state="complete", expanded=False)

    st.session_state["prediction"] = result
    st.session_state["customer_inputs"] = inputs
    st.session_state["validation_errors"] = None
    st.toast("Prediction complete", icon="✅")


# ═══════════════════════════════════════════════════════════════════════════════
# RIGHT PANEL — PREDICTION + MODEL INFO
# ═══════════════════════════════════════════════════════════════════════════════


def _waiting_card() -> None:
    st.markdown(
        '<div class="waiting-card">'
        '<div class="waiting-icon">🔮</div>'
        '<div class="waiting-title">Waiting for a prediction</div>'
        '<div class="waiting-text">'
        "Complete the customer profile on the left and click "
        "<b>Predict Customer Churn</b> to reveal the model's verdict."
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="card" style="animation-delay:0.12s">'
        '<div class="card-title">How it works</div>'
        '<div class="card-sub">Three quick steps to an executive verdict</div>'
        '<div class="summary-grid" style="grid-template-columns:repeat(3,1fr)">'
        '<div class="summary-card"><div class="summary-card-title">'
        '<span class="summary-icon">1️⃣</span>Fill profile</div>'
        '<div class="summary-pairs"><div class="summary-item">'
        '<div class="summary-label">Personal, account, services, and billing</div></div></div></div>'
        '<div class="summary-card"><div class="summary-card-title">'
        '<span class="summary-icon">2️⃣</span>Run prediction</div>'
        '<div class="summary-pairs"><div class="summary-item">'
        '<div class="summary-label">The deployed model scores the account</div></div></div></div>'
        '<div class="summary-card"><div class="summary-card-title">'
        '<span class="summary-icon">3️⃣</span>Review & export</div>'
        '<div class="summary-pairs"><div class="summary-item">'
        '<div class="summary-label">Inspect factors, then export PDF or PPTX</div></div></div></div>'
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
# EXPORT TO PDF
# ═══════════════════════════════════════════════════════════════════════════════


def _export_signature(result: dict, inputs: dict) -> str:
    """Stable signature for caching generated export bytes per prediction."""
    flat = (
        str(result.get("label")),
        f"{result.get('probability_pct', 0.0):.4f}",
        str(result.get("risk_label")),
        str(result.get("model_alias")),
        str(sorted((inputs or {}).items())),
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


def _export_pdf(result: dict, inputs: dict) -> None:
    """Premium executive PDF / PPTX downloads built entirely in memory."""
    st.markdown(
        '<div class="card" style="animation-delay:0.25s">'
        '<div class="card-title">📄 Export</div>'
        '<div class="card-sub">Download a premium executive report (PDF) or '
        "presentation-ready deck (PPTX) for this prediction - cover page, "
        "executive summary, prediction overview, customer details, risk "
        "assessment, KPI summary, and recommendations."
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    signature = _export_signature(result, inputs)
    conf_label, _conf_color = _confidence(result.get("probability_pct", 0.0))
    analysis = {"confidence": conf_label}

    pdf_bytes = _cached_export(
        "lab_pdf", signature,
        lambda: report.build_report(result, inputs, analysis),
    )
    if pdf_bytes:
        clicked = theme.download_button(
            "📥 Download Executive Report (PDF)",
            data=pdf_bytes,
            file_name="customer_churn_executive_report.pdf",
            mime="application/pdf",
            key="prediction_lab_pdf_download",
        )
        if clicked:
            st.toast("Executive report (PDF) download started", icon="📥")
    else:
        st.markdown(
            '<div class="error-text">PDF generation is unavailable right '
            "now.</div>",
            unsafe_allow_html=True,
        )

    pptx_bytes = _cached_export(
        "lab_pptx", signature,
        lambda: pptx_report.build_presentation(result, inputs, analysis),
    )
    if pptx_bytes:
        clicked = theme.download_button(
            "📊 Download Presentation (.pptx)",
            data=pptx_bytes,
            file_name="customer_churn_executive_report.pptx",
            mime="application/vnd.openxmlformats-officedocument."
                 "presentationml.presentation",
            key="prediction_lab_pptx_download",
        )
        if clicked:
            st.toast("Presentation (PPTX) download started", icon="📊")
    else:
        st.markdown(
            '<div class="error-text">PPTX generation is unavailable right '
            "now.</div>",
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
    if result is not None and st.session_state.get("customer_inputs"):
        _export_pdf(result, st.session_state["customer_inputs"])


if __name__ == "__main__":
    main()
