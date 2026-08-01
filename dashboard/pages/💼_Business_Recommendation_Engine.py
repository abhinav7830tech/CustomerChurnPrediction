"""
Business Recommendation Engine — Customer Churn Analytics Platform

Sprint 5: Rule-based business recommendations for every churn prediction.
Turns the model output into an 11-section executive action brief:
  01 Executive Summary       07 Recommended Campaign
  02 Retention Strategy      08 Action Timeline
  03 Action Cards            09 Business Scorecard
  04 Business Impact         10 Manager Notes
  05 Cost vs Benefit         11 Export to PDF
  06 Customer Segmentation

Presentation layer only — all prediction, SHAP, and recommendation logic
lives in `prediction.py` and is unchanged here. Financial metrics are
modeled estimates derived from the prediction and customer profile.
"""

import theme

import os
import re
import sys
from datetime import datetime

import plotly.graph_objects as go
import streamlit as st
from fpdf import FPDF
from fpdf.enums import XPos, YPos

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
    page_title="Business Recommendation Engine",
    page_icon="💼",
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

PRIORITY_ICONS = {
    "Critical": "🚨",
    "High": "🔴",
    "Medium": "🟡",
    "Standard": "🟢",
}

SEGMENT_META = {
    "Critical": ("🚨", "#D97C7C", "Very high churn probability, often with a short tenure."),
    "At Risk": ("⚠️", "#E0635A", "High churn probability — needs a proactive retention plan."),
    "VIP": ("💎", "#C8A96B", "Long tenure with high spend — protect and reward the relationship."),
    "Premium": ("⭐", "#8FA28A", "Above-average tenure or spend with headroom to grow."),
    "Standard": ("🤝", "#D6D8D8", "A stable relationship that benefits from gentle engagement."),
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

ACTION_REASONS = {
    "Offer a retention discount":
        "the model flags this customer as price-sensitive — a targeted discount "
        "directly lowers churn pressure",
    "Recommend a yearly contract":
        "contract type is one of the strongest drivers for this profile — a yearly "
        "term anchors loyalty",
    "Assign customer support follow-up":
        "support and service gaps stand out in the model's decision — proactive "
        "outreach resolves them early",
    "Offer loyalty rewards":
        "the analysis shows a relationship worth rewarding — perks strengthen the "
        "existing bond",
    "Review service quality":
        "service-level signals shape this prediction — an audit surfaces and fixes "
        "the root cause",
    "Maintain engagement":
        "the profile is stable — consistent check-ins sustain satisfaction and "
        "pre-empt drift",
    "Promote premium plans":
        "the customer profile carries clear headroom — an upsell deepens value "
        "while risk is low",
}

CAMPAIGNS = {
    "Critical": {
        "name": "Save-The-Customer Campaign",
        "channel": "Direct call + email",
        "message": "High-urgency personal outreach with a retention offer.",
        "incentive": "Retention discount + yearly contract",
    },
    "At Risk": {
        "name": "Re-engagement Campaign",
        "channel": "Email + SMS",
        "message": "Win-back messaging with a time-bound incentive.",
        "incentive": "Loyalty credit",
    },
    "VIP": {
        "name": "Loyalty & Upsell Campaign",
        "channel": "Account manager call",
        "message": "Reward tenure and introduce premium add-ons.",
        "incentive": "Exclusive perks",
    },
    "Premium": {
        "name": "Relationship Deepening Campaign",
        "channel": "Personalized email",
        "message": "Highlight value and invite to the premium tier.",
        "incentive": "Priority support",
    },
    "Standard": {
        "name": "Engagement & Upsell Campaign",
        "channel": "Newsletter + app",
        "message": "Nurture the relationship and cross-sell bundles.",
        "incentive": "Bundle offer",
    },
}

TIMELINE = [
    ("Today", "Day 0", "Log the customer into the CRM and flag the retention risk"),
    ("Contact", "Day 1-2", "Reach out via the campaign channel with the personalized message"),
    ("Offer", "Day 3-7", "Present the retention offer / plan change and capture acceptance"),
    ("Follow-up", "Week 2", "Confirm adoption and resolve any remaining objections"),
    ("Monitor", "Month 1", "Review usage, billing behaviour and satisfaction signals"),
    ("Success Evaluation", "Month 3", "Re-score churn risk and measure the campaign outcome"),
]

# Cost intensity of the modeled retention program per risk level.
COST_FACTOR = {
    "High Risk": 0.20,
    "Medium Risk": 0.10,
    "Low Risk": 0.05,
}


def _confidence(pct: float) -> tuple:
    """Presentation-only confidence label derived from the model output."""
    if pct >= 70 or pct <= 30:
        return "High", "#8FA28A"
    if pct >= 55 or pct <= 45:
        return "Medium", "#C8A96B"
    return "Low", "#D97C7C"


def _priority(risk_label: str) -> str:
    """Map the model risk band to an executive priority level."""
    if risk_label == "High Risk":
        return "Critical"
    if risk_label == "Medium Risk":
        return "High"
    return "Standard"


def _segment(prob: float, tenure: int, monthly: float) -> str:
    """Customer segment derived from risk, tenure, and monthly spend."""
    if prob >= 85 or (prob >= 70 and tenure < 12):
        return "Critical"
    if prob >= 70:
        return "At Risk"
    if tenure >= 60 and monthly >= 90:
        return "VIP"
    if tenure >= 48 or monthly >= 85:
        return "Premium"
    return "Standard"


def _gauge_color(value: float, invert: bool = False) -> str:
    """Band a 0-100 score into the palette (red/gold/sage)."""
    if invert:
        if value >= 70:
            return "#D97C7C"
        if value >= 40:
            return "#C8A96B"
        return "#8FA28A"
    if value >= 70:
        return "#8FA28A"
    if value >= 40:
        return "#C8A96B"
    return "#D97C7C"


def _analyze(result: dict, inputs: dict) -> dict:
    """Compute all business metrics and rule matches for a prediction."""
    prob = result["probability_pct"]
    risk = result["risk_label"]
    tenure = inputs["tenure"]
    monthly = inputs["MonthlyCharges"]
    contract = inputs["Contract"]
    internet = inputs["InternetService"]
    payment = inputs["PaymentMethod"]
    senior = inputs["SeniorCitizen"]
    partner = inputs["Partner"]
    dependents = inputs["Dependents"]
    tech_support = inputs["TechSupport"]
    online_security = inputs["OnlineSecurity"]

    p = prob / 100.0
    revenue_at_risk = 12.0 * monthly * p
    clv_estimate = 24.0 * monthly * (1.0 - p)
    retention_cost = monthly * COST_FACTOR.get(risk, 0.05) * 6.0
    potential_savings = revenue_at_risk * 0.65
    net_benefit = potential_savings - retention_cost
    roi_pct = (net_benefit / retention_cost * 100.0) if retention_cost > 0 else 0.0

    priority = _priority(risk)
    segment = _segment(prob, tenure, monthly)

    rules = []
    candidates = [
        (
            prob >= 70, "🚨", "Immediate Retention Intervention",
            "IF churn probability is ≥ 70% THEN escalate to the retention desk today",
            "Protects the highest-risk revenue immediately", "Medium",
        ),
        (
            prob >= 70 and tenure < 12, "🆘", "Early-Tenure Rescue",
            "IF churn probability is ≥ 70% AND tenure is under 12 months THEN "
            "prioritise an early-tenure rescue",
            "Targets the highest-churn window in the relationship", "Medium",
        ),
        (
            contract == "Month-to-month" and prob >= 40, "📅", "Contract Lock-In",
            "IF the contract is month-to-month THEN propose a yearly contract to "
            "anchor loyalty",
            "Converts a high-risk plan into a committed term", "No extra cost",
        ),
        (
            payment in ("Electronic check", "Mailed check"), "💳", "Payment Automation",
            "IF payment method is not automatic THEN move the customer to auto-pay",
            "Reduces friction-driven churn", "Low",
        ),
        (
            internet == "Fiber optic" and prob >= 40, "📡", "Fiber Experience Review",
            "IF internet is fiber optic AND risk is ≥ 40% THEN audit service quality "
            "and price",
            "Resolves the strongest service-level churn signal", "Low",
        ),
        (
            monthly >= 80, "💲", "Price-Value Alignment",
            "IF monthly charges are ≥ $80 THEN review the plan against usage to "
            "rebalance value",
            "Reduces price sensitivity on high-spend accounts", "Low",
        ),
        (
            internet != "No" and tech_support != "Yes", "🛠️", "Tech Support Enablement",
            "IF the customer has internet AND no tech support THEN enable support "
            "access",
            "Removes a top support gap", "Low",
        ),
        (
            internet != "No" and online_security != "Yes", "🔐", "Security Add-On Offer",
            "IF the customer has internet AND no online security THEN offer the "
            "security add-on",
            "Closes a protective gap and adds value", "Low",
        ),
        (
            senior == "Yes" and prob >= 50, "👴", "Senior-Care Touchpoint",
            "IF the customer is a senior AND risk is ≥ 50% THEN schedule a personal "
            "check-in",
            "Addresses the senior churn pattern personally", "Low",
        ),
        (
            tenure >= 24 and prob < 40, "⭐", "Loyalty Rewards",
            "IF tenure is ≥ 24 months AND risk is low THEN reward the loyalty",
            "Deepens an already-stable relationship", "Low",
        ),
        (
            internet == "No", "📦", "Bundle Introduction",
            "IF the customer has no internet service THEN explore a bundle upsell",
            "Creates stickiness through a bundled package", "Low",
        ),
        (
            partner == "Yes" or dependents == "Yes", "🏠", "Household Account Review",
            "IF household signals are present THEN review the full household account",
            "Protects the whole household relationship", "Low",
        ),
    ]
    for fires, icon, title, condition, impact, cost in candidates:
        if fires:
            rules.append({
                "icon": icon,
                "title": title,
                "condition": condition,
                "impact": impact,
                "cost": cost,
            })

    factors = result.get("factors") or []
    drivers = [f for f in factors if f["contribution"] > 0]
    top_driver = drivers[0] if drivers else (factors[0] if factors else None)

    actions = []
    for icon, title, text in result.get("recommendations", []):
        impact, cost = REC_EXTRA.get(title, ("Improve retention", "Low"))
        reason = ACTION_REASONS.get(title)
        if reason is None and top_driver:
            reason = (
                f"targets the strongest churn driver — "
                f"{top_driver['feature']} ({top_driver['value']})"
            )
        if reason is None:
            reason = "addresses the main risk signals identified by the model"
        actions.append({
            "icon": icon,
            "title": title,
            "reason": reason,
            "impact": impact,
            "cost": cost,
            "priority": priority,
            "confidence": _confidence(prob)[0],
        })

    loyalty = tenure / 72.0 * 100.0
    revenue_score = min(monthly / 120.0 * 100.0, 100.0)
    if internet == "No":
        upsell = 10.0
    else:
        missing = int(tech_support != "Yes") + int(online_security != "Yes") \
            + int(inputs["OnlineBackup"] != "Yes") + int(inputs["DeviceProtection"] != "Yes")
        upsell = 20.0 + missing * 20.0
    scorecard = [
        ("Churn Risk", prob, _gauge_color(prob, invert=True)),
        ("Loyalty", loyalty, _gauge_color(loyalty)),
        ("Revenue", revenue_score, _gauge_color(revenue_score)),
        ("Upsell", upsell, _gauge_color(upsell)),
        ("Retention Health", 100.0 - prob, _gauge_color(100.0 - prob)),
    ]

    campaign = CAMPAIGNS.get(segment, CAMPAIGNS["Standard"])

    conf_label, _ = _confidence(prob)
    return {
        "prob": prob,
        "risk": risk,
        "priority": priority,
        "segment": segment,
        "segment_icon": SEGMENT_META[segment][0],
        "segment_color": SEGMENT_META[segment][1],
        "revenue_at_risk": revenue_at_risk,
        "clv_estimate": clv_estimate,
        "retention_cost": retention_cost,
        "potential_savings": potential_savings,
        "net_benefit": net_benefit,
        "roi_pct": roi_pct,
        "confidence": conf_label,
        "rules": rules,
        "actions": actions,
        "top_driver": top_driver,
        "scorecard": scorecard,
        "campaign": campaign,
        "timeline": TIMELINE,
    }


def _manager_notes(result: dict, inputs: dict, a: dict) -> str:
    """One-paragraph, executive-ready summary of the action brief."""
    parts = [
        f"This customer carries a {a['prob']:.0f}% churn probability "
        f"({a['risk']}), exposing an estimated ${a['revenue_at_risk']:,.0f} in "
        f"annual revenue at risk. The profile falls into the {a['segment']} "
        f"segment and warrants a {a['priority']} response."
    ]
    if a["top_driver"] is not None:
        parts.append(
            f"The model identifies {a['top_driver']['feature']} "
            f"({a['top_driver']['value']}) as the strongest churn driver for "
            f"this customer."
        )
    parts.append(
        f"With a retention investment of ${a['retention_cost']:,.0f}, the modeled "
        f"benefit is ${a['potential_savings']:,.0f}, for an estimated ROI of "
        f"{a['roi_pct']:.0f}%. Recommended next step: {a['campaign']['name']}."
    )
    return " ".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM CSS
# ═══════════════════════════════════════════════════════════════════════════════


def _inject_css() -> None:
    """Inject the shared design-system styles."""
    theme.inject_css()

def _header() -> None:
    """Hero header with kicker, large title, subtitle, and accent rule."""
    theme.page_header(
        title="Turn Every Prediction Into a Retention Plan",
        kicker="◆ Business Recommendation Engine",
        subtitle=(
            "Rule-based, executive-ready business recommendations built from the "
            "churn prediction — strategy, actions, financial impact, campaign, and "
            "timeline in one action brief."
        ),
        rule=True,
        back_link=True,
    )


def _section_head(num: str, icon: str, title: str, sub: str) -> None:
    """Numbered section header used across the 11-part action brief."""
    st.markdown(theme.section_head(num, icon, title, sub), unsafe_allow_html=True)


def _metric_tile(label: str, value: str, sub: str = "", accent: bool = False) -> str:
    """HTML for an Analytics-style KPI metric tile."""
    val_class = "kpi-value accent" if accent else "kpi-value"
    subtext_html = f'<div class="kpi-subtext">{sub}</div>' if sub else ""
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="{val_class}">{value}</div>'
        f"{subtext_html}"
        f"</div>"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOMER PROFILE FORM (writes to the shared session state)
# ═══════════════════════════════════════════════════════════════════════════════


def _form_panel() -> None:
    """Customer profile form. Uses the exact same pipeline as the
    AI Prediction Lab and writes to the same session-state keys."""
    available = prediction.get_available_models()
    best = prediction.resolve_best_model()

    with st.form("business_form"):
        st.markdown(
            '<div class="card-title">Customer Profile</div>'
            '<div class="card-sub">Run a prediction, then generate the '
            "business action brief below</div>",
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
            "💼 Build Business Recommendation", width="stretch"
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

    model = prediction.load_model(model_choice)
    if model is None:
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
# SECTION 01 — EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════


def _executive_summary(result: dict, a: dict) -> None:
    info = prediction.model_info(result["model_alias"])
    risk_color = RISK_PILL_COLORS.get(a["risk"], "#C8A96B")
    seg_color = a["segment_color"]

    tiles = [
        ("Churn Probability", f'{a["prob"]:.1f}%',
         "Model output", False),
        ("Risk Level",
         f'<span class="risk-pill" style="background:{risk_color}">'
         f'<span class="pill-dot"></span>{a["risk"]}</span>',
         "", False),
        ("Priority", f'{PRIORITY_ICONS[a["priority"]]} {a["priority"]}',
         "Executive response level", False),
        ("Segment", f'{a["segment_icon"]} {a["segment"]}',
         f'<span style="color:{seg_color}">●</span> Behavioral classification', False),
        ("Revenue at Risk",
         f'<span class="kpi-risk">${a["revenue_at_risk"]:,.0f}</span>',
         "Modeled estimate · 12-mo horizon", True),
        ("CLV Estimate", f"${a['clv_estimate']:,.0f}",
         "Modeled estimate · 24-mo horizon", False),
        ("Model", info["label"],
         f"Accuracy {info['accuracy']:.1f}%", False),
    ]

    rows_html = []
    for label, value, sub, accent in tiles:
        val_class = "kpi-value accent" if accent else "kpi-value"
        subtext_html = f'<div class="kpi-subtext">{sub}</div>' if sub else ""
        rows_html.append(
            f'<div class="kpi-card">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="{val_class}">{value}</div>'
            f"{subtext_html}"
            f"</div>"
        )

    with st.container(border=True):
        st.markdown(
            f'<div class="es-grid">{"".join(rows_html)}</div>',
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 02 — RULE-BASED RETENTION STRATEGY
# ═══════════════════════════════════════════════════════════════════════════════


def _retention_strategy(a: dict) -> None:
    rules = a["rules"]
    if not rules:
        st.markdown(
            '<div class="note-text">No business rules fired for this profile — '
            "the customer sits in a low-risk, stable state. Standard engagement "
            "actions are recommended below.</div>",
            unsafe_allow_html=True,
        )
        return

    cards = []
    for rule in rules:
        cards.append(
            f'<div class="rule-card">'
            f'<div class="rule-head">'
            f'<div class="rule-icon">{rule["icon"]}</div>'
            f'<div>'
            f'<div class="rule-kicker">Priority · {a["priority"]}</div>'
            f'<div class="rule-title">{rule["title"]}</div>'
            f"</div></div>"
            f'<div class="rule-condition">{rule["condition"]}</div>'
            f'<div class="rule-meta">'
            f'<div class="rule-meta-item">'
            f'<span class="rule-meta-label">Expected Impact</span>'
            f'<span class="rule-meta-value">{rule["impact"]}</span></div>'
            f'<div class="rule-meta-item">'
            f'<span class="rule-meta-label">Estimated Cost</span>'
            f'<span class="rule-meta-value">{rule["cost"]}</span></div>'
            f"</div></div>"
        )

    with st.container(border=True):
        st.markdown(
            f'<div class="rule-grid">{"".join(cards)}</div>',
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 03 — ACTION CARDS
# ═══════════════════════════════════════════════════════════════════════════════


def _action_cards(a: dict) -> None:
    actions = a["actions"]
    if not actions:
        return

    cards = []
    for action in actions:
        cards.append(
            f'<div class="rec-card">'
            f'<div class="rec-head">'
            f'<div class="rec-icon">{action["icon"]}</div>'
            f'<div>'
            f'<div class="rec-kicker">Priority · {action["priority"]}'
            f" · Confidence · {action['confidence']}</div>"
            f'<div class="rec-title">{action["title"]}</div>'
            f"</div></div>"
            f'<div class="rec-reason">Business reason: {action["reason"]}.</div>'
            f'<div class="rec-meta">'
            f'<div class="rec-meta-item">'
            f'<span class="rec-meta-label">Expected Impact</span>'
            f'<span class="rec-meta-value">{action["impact"]}</span></div>'
            f'<div class="rec-meta-item">'
            f'<span class="rec-meta-label">Estimated Cost</span>'
            f'<span class="rec-meta-value">{action["cost"]}</span></div>'
            f"</div></div>"
        )

    with st.container(border=True):
        st.markdown(f'<div class="rec-grid">{"".join(cards)}</div>',
                    unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 04 — ESTIMATED BUSINESS IMPACT
# ═══════════════════════════════════════════════════════════════════════════════


def _business_impact(a: dict) -> None:
    metrics = [
        ("Revenue at Risk", f'<span class="kpi-risk">${a["revenue_at_risk"]:,.0f}</span>',
         "Modeled estimate · 12-mo horizon"),
        ("CLV Estimate", f"${a['clv_estimate']:,.0f}",
         "Modeled estimate · 24-mo horizon"),
        ("Retention Cost", f"${a['retention_cost']:,.0f}",
         "Modeled program cost · 6-mo horizon"),
        ("Potential Savings", f'<span class="kpi-safe">${a["potential_savings"]:,.0f}</span>',
         "Modeled benefit · 65% success"),
        ("Net Expected Value", f"${a['net_benefit']:,.0f}",
         "Benefit minus investment"),
        ("ROI", f"{a['roi_pct']:.0f}%",
         "Net value over investment"),
    ]

    row1 = st.columns(3, gap="medium")
    for col, (label, value, sub) in zip(row1, metrics[:3]):
        with col:
            st.markdown(_metric_tile(label, value, sub), unsafe_allow_html=True)

    row2 = st.columns(3, gap="medium")
    for col, (label, value, sub) in zip(row2, metrics[3:]):
        with col:
            st.markdown(_metric_tile(label, value, sub, accent=(label == "ROI")),
                        unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 05 — COST VS BENEFIT + ROI
# ═══════════════════════════════════════════════════════════════════════════════


def _cost_benefit(a: dict) -> None:
    with st.container(border=True):
        st.markdown(
            f'<div class="cb-grid">'
            f'<div class="cb-card">'
            f'<div class="cb-label">Estimated Investment</div>'
            f'<div class="cb-value">${a["retention_cost"]:,.0f}</div>'
            f"</div>"
            f'<div class="cb-card">'
            f'<div class="cb-label">Modeled Benefit</div>'
            f'<div class="cb-value" style="color:#8FA28A">'
            f"${a['potential_savings']:,.0f}</div>"
            f"</div>"
            f'<div class="cb-card">'
            f'<div class="cb-label">Net Expected Value</div>'
            f'<div class="cb-value">${a["net_benefit"]:,.0f}</div>'
            f"</div>"
            f"</div>"
            f'<div class="roi-row">'
            f'<div class="roi-label">Estimated Return on Investment</div>'
            f'<div class="roi-value">'
            f'{a["roi_pct"]:.0f}%'
            f'<span class="tip">ⓘ'
            f'<span class="tip-text">ROI = (modeled benefit − investment) ÷ '
            f"investment. A modeled estimate, not a guarantee.</span>"
            f"</span></div>"
            f"</div>"
            f'<div class="note-text">'
            f"All financial figures are <b>modeled estimates</b> derived from "
            f"the churn probability and customer profile — not from CRM or LTV "
            f"data. Benefit assumes a 65% retention success rate."
            f"</div>",
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 06 — CUSTOMER SEGMENTATION
# ═══════════════════════════════════════════════════════════════════════════════


def _segmentation(a: dict) -> None:
    cards = []
    for name, (icon, color, desc) in SEGMENT_META.items():
        current = name == a["segment"]
        tag = (
            f'<span class="seg-tag" style="background:{color}">This customer</span>'
            if current else ""
        )
        border = (
            f"border:1.5px solid {color};background:#234556;"
            if current
            else "opacity:0.78;"
        )
        cards.append(
            f'<div class="seg-card{" current" if current else ""}" '
            f'style="{border}">'
            f'<div class="seg-icon">{icon}</div>'
            f'<div class="seg-name">{name}</div>'
            f"{tag}"
            f'<div class="seg-desc">{desc}</div>'
            f"</div>"
        )

    with st.container(border=True):
        st.markdown(f'<div class="seg-grid">{"".join(cards)}</div>',
                    unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 07 — RECOMMENDED CAMPAIGN
# ═══════════════════════════════════════════════════════════════════════════════


def _campaign(a: dict) -> None:
    campaign = a["campaign"]
    with st.container(border=True):
        st.markdown(
            f'<div class="campaign-card">'
            f'<div class="camp-item">'
            f'<div class="camp-label">Campaign</div>'
            f'<div class="camp-value">{a["segment_icon"]} {campaign["name"]}</div>'
            f"</div>"
            f'<div class="camp-item">'
            f'<div class="camp-label">Channel</div>'
            f'<div class="camp-value">{campaign["channel"]}</div>'
            f"</div>"
            f'<div class="camp-item">'
            f'<div class="camp-label">Message</div>'
            f'<div class="camp-value">{campaign["message"]}</div>'
            f"</div>"
            f'<div class="camp-item">'
            f'<div class="camp-label">Incentive</div>'
            f'<div class="camp-value">{campaign["incentive"]}</div>'
            f"</div>"
            f"</div>"
            f'<div class="note-text">The campaign is matched to the customer '
            f"segment and risk level above.</div>",
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 08 — ACTION TIMELINE
# ═══════════════════════════════════════════════════════════════════════════════


def _timeline(a: dict) -> None:
    steps = []
    for i, (phase, timing, action) in enumerate(a["timeline"], start=1):
        steps.append(
            f'<div class="tl-step">'
            f'<div class="tl-num">{i}</div>'
            f'<div class="tl-body" style="flex:1">'
            f'<div class="tl-head">'
            f'<span class="tl-phase">{phase}</span>'
            f'<span class="tl-time">{timing}</span>'
            f"</div>"
            f'<div class="tl-action">{action}</div>'
            f"</div>"
            f"</div>"
        )

    with st.container(border=True):
        st.markdown(
            f'<div class="timeline">{"".join(steps)}</div>'
            f'<div class="note-text">Suggested execution cadence once the '
            f"campaign is approved — adjust to internal workflows.</div>",
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 09 — BUSINESS SCORECARD
# ═══════════════════════════════════════════════════════════════════════════════


def _scorecard_gauge(label: str, value: float, color: str) -> go.Figure:
    """Plotly gauge for a single 0-100 business score."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": "", "font": {"color": "#F4F2EE", "size": 26}},
        title={"text": label, "font": {"color": "#C8A96B", "size": 12}},
        gauge={
            "shape": "angular",
            "axis": {
                "range": [0, 100],
                "tickcolor": "#D6D8D8",
                "tickfont": {"color": "#D6D8D8", "size": 9},
            },
            "bar": {"color": color, "thickness": 0.3},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40], "color": "rgba(217,124,124,0.18)"},
                {"range": [40, 70], "color": "rgba(200,169,107,0.22)"},
                {"range": [70, 100], "color": "rgba(143,162,138,0.26)"},
            ],
        },
    ))
    fig.update_layout(
        height=225,
        margin=dict(t=45, b=10, l=15, r=15),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif"},
    )
    return fig


def _scorecard(a: dict) -> None:
    cols = st.columns(5, gap="medium")
    for col, (label, value, color) in zip(cols, a["scorecard"]):
        with col:
            with st.container(border=True):
                st.plotly_chart(
                    _scorecard_gauge(label, value, color),
                    width="stretch",
                )
    st.markdown(
        '<div class="note-text">'
        "Scores are 0–100 derived from the customer profile and prediction: "
        "<b>Churn Risk</b> is the model probability, <b>Loyalty</b> tenure, "
        "<b>Revenue</b> monthly spend, <b>Upsell</b> the share of premium "
        "add-ons not yet held, and <b>Retention Health</b> the inverse of "
        "churn risk.</div>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 10 — MANAGER NOTES
# ═══════════════════════════════════════════════════════════════════════════════


def _manager_notes_section(result: dict, inputs: dict, a: dict) -> None:
    paragraph = _manager_notes(result, inputs, a)
    with st.container(border=True):
        st.markdown(
            '<div class="notes-box">'
            f"<p>{paragraph}</p>"
            "</div>",
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 11 — EXPORT TO PDF
# ═══════════════════════════════════════════════════════════════════════════════


def _ascii(text) -> str:
    """Strip non-Latin-1 characters for fpdf2's core fonts."""
    return re.sub(r"[^\x00-\x7F]", "", str(text))


def _build_pdf(result: dict, inputs: dict, a: dict) -> bytes:
    """Build a clean multi-page PDF action brief with fpdf2."""
    info = prediction.model_info(result["model_alias"])

    class Report(FPDF):
        def footer(self):
            self.set_y(-14)
            self.set_font("Helvetica", "", 7)
            self.set_text_color(150, 150, 150)
            self.cell(0, 5,
                      "Customer Churn Analytics Platform  -  Page "
                      f"{self.page_no()}",
                      align="C")

    pdf = Report(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(14, 15, 14)
    pdf.add_page()

    pdf.set_fill_color(15, 48, 64)
    pdf.rect(0, 0, 210, 30, "F")
    pdf.set_fill_color(200, 169, 107)
    pdf.rect(0, 30, 210, 2.2, "F")
    pdf.set_text_color(244, 242, 238)
    pdf.set_xy(14, 7)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 7, "Business Recommendation Report - Customer Churn")
    pdf.set_xy(14, 16)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(214, 216, 216)
    pdf.cell(0, 5, "Executive action brief generated by the Customer Churn Analytics Platform")
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

    section("1. Executive Summary")
    kv("Prediction", result["label"])
    kv("Churn probability", f"{a['prob']:.1f}%")
    kv("Risk level", a["risk"])
    kv("Priority", a["priority"])
    kv("Segment", a["segment"])
    kv("Revenue at risk (12-mo)", f"${a['revenue_at_risk']:,.0f}")
    kv("CLV estimate (24-mo)", f"${a['clv_estimate']:,.0f}")
    kv("Model", info["label"])

    section("2. Customer Profile")
    for feat in prediction.FEATURE_NAMES:
        kv(prediction.FEATURE_LABELS[feat],
           prediction.display_value(feat, inputs[feat]))

    section("3. Retention Strategy (fired rules)")
    for rule in a["rules"]:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 5, f"- {_ascii(rule['title'])}",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.multi_cell(0, 4.5, _ascii(rule["condition"]))
        pdf.ln(1)

    section("4. Recommended Actions")
    for action in a["actions"]:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 5, f"- {_ascii(action['title'])}",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.multi_cell(0, 4.5,
                       _ascii(f"Business reason: {action['reason']}. "
                              f"Impact: {action['impact']}. "
                              f"Cost: {action['cost']}."))
        pdf.ln(1)

    section("5. Cost vs Benefit")
    kv("Retention investment", f"${a['retention_cost']:,.0f}")
    kv("Modeled benefit", f"${a['potential_savings']:,.0f}")
    kv("Net expected value", f"${a['net_benefit']:,.0f}")
    kv("Estimated ROI", f"{a['roi_pct']:.0f}%")

    section("6. Campaign & Timeline")
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, f"Campaign: {_ascii(a['campaign']['name'])}",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.multi_cell(0, 4.5,
                   _ascii(f"Channel: {a['campaign']['channel']} | "
                          f"Message: {a['campaign']['message']} | "
                          f"Incentive: {a['campaign']['incentive']}"))
    pdf.ln(1)
    for phase, timing, action in a["timeline"]:
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.cell(0, 5, f"{_ascii(phase)} ({_ascii(timing)})",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.multi_cell(0, 4.5, _ascii(action))

    section("7. Business Scorecard")
    for label, value, _ in a["scorecard"]:
        kv(label, f"{value:.0f} / 100")

    section("8. Manager Notes")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(30, 40, 45)
    pdf.multi_cell(0, 5, _ascii(_manager_notes(result, inputs, a)))

    section("9. Methodology & Estimates")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(60, 70, 75)
    pdf.multi_cell(
        0, 4.5,
        _ascii(
            f"Prediction from the deployed {info['label']} classifier "
            f"({len(prediction.FEATURE_NAMES)} features, trained on the IBM "
            f"Telco Customer Churn dataset). Retention strategies are matched "
            f"to the customer by a rule engine over risk tier, tenure, "
            f"contract, monthly charges, internet service, payment method, "
            f"support features, and household signals. Financial figures are "
            f"modeled estimates derived from the prediction and customer "
            f"profile — not from CRM or LTV data. Benefit assumes a 65% "
            f"retention success rate."
        ),
    )

    return bytes(pdf.output())


def _export_pdf(result: dict, inputs: dict, a: dict) -> None:
    with st.container(border=True):
        st.markdown(
            '<div class="export-desc">'
            "Generates a clean, self-contained PDF with the executive summary, "
            "customer profile, retention strategy, recommended actions, "
            "cost-benefit analysis, campaign, timeline, scorecard, and manager "
            "notes — ready to share with stakeholders or attach to a CRM case."
            "</div>",
            unsafe_allow_html=True,
        )
        try:
            pdf_bytes = _build_pdf(result, inputs, a)
        except Exception:
            pdf_bytes = None

        if pdf_bytes:
            theme.download_button(
                "📥 Download Business Report (PDF)",
                data=pdf_bytes,
                file_name="business_recommendation_report.pdf",
                mime="application/pdf",
                key="business_pdf_download",
            )
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
    """Render the Business Recommendation Engine page."""
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

    st.markdown(
        '<div class="meta-hint">An <b>11-section</b> executive action brief '
        "generated from the latest churn prediction. Financial figures are "
        "modeled estimates.</div>",
        unsafe_allow_html=True,
    )

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
            '<div class="entry-icon">💼</div>'
            '<div class="entry-title">No prediction yet</div>'
            '<div class="entry-text">'
            "Run a prediction using the customer profile above (or from the AI "
            "Prediction Lab) and this page will build an executive retention "
            "plan — from rule-based strategy to financial impact and a "
            "shareable PDF report."
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="waiting-card">'
            '<div class="waiting-icon">💼</div>'
            '<div class="waiting-title">Waiting for a prediction...</div>'
            '<div class="waiting-text">'
            "Fill in the customer details above and click <b>Build Business "
            "Recommendation</b> to generate the action brief."
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    a = _analyze(result, inputs)

    # 01 · Executive Summary
    _section_head("01", "🎯", "Executive Summary",
                  "The business picture at a glance")
    _executive_summary(result, a)

    # 02 · Rule-based Retention Strategy
    _section_head("02", "🧭", "Retention Strategy",
                  "Business rules matched to this customer's profile")
    _retention_strategy(a)

    # 03 · Action Cards
    _section_head("03", "⚡", "Action Cards",
                  "Concrete next steps with the business reason behind each")
    _action_cards(a)

    # 04 · Estimated Business Impact
    _section_head("04", "📈", "Estimated Business Impact",
                  "Modeled financial KPIs for this customer")
    _business_impact(a)

    # 05 · Cost vs Benefit + ROI
    _section_head("05", "⚖️", "Cost vs Benefit",
                  "Investment, benefit, and return for the recommended plan")
    _cost_benefit(a)

    # 06 · Customer Segmentation
    _section_head("06", "🗂️", "Customer Segmentation",
                  "Where this customer sits in the value-risk taxonomy")
    _segmentation(a)

    # 07 · Recommended Campaign
    _section_head("07", "📣", "Recommended Campaign",
                  "The campaign matched to this customer's segment")
    _campaign(a)

    # 08 · Action Timeline
    _section_head("08", "⏱️", "Action Timeline",
                  "Execution cadence from today to success evaluation")
    _timeline(a)

    # 09 · Business Scorecard
    _section_head("09", "📊", "Business Scorecard",
                  "Five business scores derived from the profile and prediction")
    _scorecard(a)

    # 10 · Manager Notes
    _section_head("10", "📝", "Manager Notes",
                  "Auto-generated executive summary for the account owner")
    _manager_notes_section(result, inputs, a)

    # 11 · Export to PDF
    _section_head("11", "📄", "Export to PDF",
                  "Download this action brief as a shareable report")
    _export_pdf(result, inputs, a)


if __name__ == "__main__":
    main()
