"""
prediction.py — Model loading, inference, interpretation & recommendations.

Loads the pre-trained XGBoost / Random Forest models from the `models/`
directory, encodes customer inputs exactly as done during training,
runs single-customer inference, and produces SHAP-based factor analysis
plus rule-based business recommendations.

No training happens here — models are loaded with caching so the file is
read from disk exactly once per app session.
"""

import os
from typing import Optional

import joblib
import numpy as np
import shap
import streamlit as st

# ── Paths ────────────────────────────────────────────────────────────────

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODEL_DIR = os.path.join(_PROJECT_ROOT, "models")

MODEL_ALIASES = {
    "xgboost": "XGBoost",
    "random_forest": "Random Forest",
}

MODEL_FILES = {
    "xgboost": "xgboost_model.pkl",
    "random_forest": "random_forest_model.pkl",
}

MODEL_METADATA = {
    "xgboost": {
        "label": "XGBoost",
        "accuracy": 76.1,
        "auc": 0.8133,
        "note": "Highest accuracy on the held-out test set.",
    },
    "random_forest": {
        "label": "Random Forest",
        "accuracy": 76.0,
        "auc": 0.8163,
        "note": "Strongest AUC-ROC among the trained models.",
    },
}

# Best-performing model as default predictor (per model comparison).
DEFAULT_MODEL = "xgboost"

# ── Feature schema ────────────────────────────────────────────────────────
# Order must match the training DataFrame exactly (dataset column order
# after dropping `customerID` and the `Churn` target).

FEATURE_NAMES = [
    "gender", "SeniorCitizen", "Partner", "Dependents", "tenure",
    "PhoneService", "MultipleLines", "InternetService", "OnlineSecurity",
    "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV",
    "StreamingMovies", "Contract", "PaperlessBilling", "PaymentMethod",
    "MonthlyCharges", "TotalCharges",
]

# LabelEncoder-style mappings derived from the training pipeline
# (scikit-learn LabelEncoder sorts unique values alphabetically).
ENCODINGS = {
    "gender": {"Female": 0, "Male": 1},
    "SeniorCitizen": {"No": 0, "Yes": 1},
    "Partner": {"No": 0, "Yes": 1},
    "Dependents": {"No": 0, "Yes": 1},
    "PhoneService": {"No": 0, "Yes": 1},
    "MultipleLines": {"No": 0, "No phone service": 1, "Yes": 2},
    "InternetService": {"DSL": 0, "Fiber optic": 1, "No": 2},
    "OnlineSecurity": {"No": 0, "No internet service": 1, "Yes": 2},
    "OnlineBackup": {"No": 0, "No internet service": 1, "Yes": 2},
    "DeviceProtection": {"No": 0, "No internet service": 1, "Yes": 2},
    "TechSupport": {"No": 0, "No internet service": 1, "Yes": 2},
    "StreamingTV": {"No": 0, "No internet service": 1, "Yes": 2},
    "StreamingMovies": {"No": 0, "No internet service": 1, "Yes": 2},
    "Contract": {"Month-to-month": 0, "One year": 1, "Two year": 2},
    "PaperlessBilling": {"No": 0, "Yes": 1},
    "PaymentMethod": {
        "Bank transfer (automatic)": 0,
        "Credit card (automatic)": 1,
        "Electronic check": 2,
        "Mailed check": 3,
    },
}

REVERSE_ENCODINGS = {
    name: {v: k for k, v in mapping.items()}
    for name, mapping in ENCODINGS.items()
}

FEATURE_LABELS = {
    "gender": "Gender",
    "SeniorCitizen": "Senior Citizen",
    "Partner": "Partner",
    "Dependents": "Dependents",
    "tenure": "Tenure",
    "PhoneService": "Phone Service",
    "MultipleLines": "Multiple Lines",
    "InternetService": "Internet Service",
    "OnlineSecurity": "Online Security",
    "OnlineBackup": "Online Backup",
    "DeviceProtection": "Device Protection",
    "TechSupport": "Tech Support",
    "StreamingTV": "Streaming TV",
    "StreamingMovies": "Streaming Movies",
    "Contract": "Contract",
    "PaperlessBilling": "Paperless Billing",
    "PaymentMethod": "Payment Method",
    "MonthlyCharges": "Monthly Charges",
    "TotalCharges": "Total Charges",
}

NUMERIC_FEATURES = {"tenure", "MonthlyCharges", "TotalCharges"}

# ── Risk bands ────────────────────────────────────────────────────────────

RISK_LEVELS = {
    "Low Risk": ("#8FA28A", 0, 40),
    "Medium Risk": ("#C8A96B", 40, 70),
    "High Risk": ("#E0635A", 70, 100),
}

RISK_RECOMMENDATIONS = {
    "High Risk": [
        ("🎁", "Offer a retention discount",
         "Provide a targeted discount on the current plan to reduce churn pressure."),
        ("📅", "Recommend a yearly contract",
         "Lock in loyalty with a 12-month plan to increase retention likelihood."),
        ("📞", "Assign customer support follow-up",
         "Schedule proactive outreach to resolve pain points and build rapport."),
    ],
    "Medium Risk": [
        ("⭐", "Offer loyalty rewards",
         "Reward continued loyalty with perks or points to strengthen the relationship."),
        ("🛠️", "Review service quality",
         "Audit service reliability and address any recent issues or complaints."),
    ],
    "Low Risk": [
        ("🤝", "Maintain engagement",
         "Keep the customer engaged with proactive check-ins and relevant updates."),
        ("🚀", "Promote premium plans",
         "Upsell upgraded plans or add-ons now that the relationship is stable."),
    ],
}


# ── Model loading (cached once per session) ───────────────────────────────


def _model_path(alias: str) -> str:
    """Resolve the model file path, preferring the project-root models dir."""
    root_path = os.path.join(_MODEL_DIR, MODEL_FILES[alias])
    if os.path.exists(root_path):
        return root_path
    return os.path.join(os.getcwd(), "models", MODEL_FILES[alias])


@st.cache_resource(show_spinner="Loading trained model...")
def load_model(alias: str) -> Optional[object]:
    """Load and cache a trained model. Returns None if unavailable."""
    path = _model_path(alias)
    if not os.path.exists(path):
        return None
    try:
        return joblib.load(path)
    except Exception:
        return None


@st.cache_resource
def get_available_models() -> list:
    """Return aliases of models that exist on disk."""
    return [a for a in MODEL_ALIASES if os.path.exists(_model_path(a))]


def resolve_best_model() -> Optional[str]:
    """Return the default (best-performing) model alias, or the first
    available model if the default is missing."""
    available = get_available_models()
    if not available:
        return None
    if DEFAULT_MODEL in available:
        return DEFAULT_MODEL
    return available[0]


def model_info(alias: str) -> dict:
    """Return metadata for a model alias, falling back to empty metadata."""
    return MODEL_METADATA.get(alias, {
        "label": MODEL_ALIASES.get(alias, alias),
        "accuracy": None,
        "auc": None,
        "note": "",
    })


# ── SHAP explainer (cached once per model) ────────────────────────────────


@st.cache_resource(show_spinner=False)
def get_explainer(alias: str) -> Optional[object]:
    """Return a cached SHAP TreeExplainer for the given model."""
    model = load_model(alias)
    if model is None:
        return None
    try:
        return shap.TreeExplainer(model)
    except Exception:
        return None


# ── Encoding & validation ─────────────────────────────────────────────────


def encode_features(inputs: dict) -> np.ndarray:
    """Encode the form inputs into the numeric feature vector used by the
    models, preserving the exact training-time column order."""
    row = []
    for feat in FEATURE_NAMES:
        if feat in ENCODINGS:
            row.append(ENCODINGS[feat][inputs[feat]])
        else:
            row.append(float(inputs[feat]))
    return np.asarray(row, dtype=float)


def validate_inputs(inputs: dict) -> list:
    """Return a list of professional validation messages (empty if valid)."""
    errors = []
    tenure = inputs["tenure"]
    monthly = inputs["MonthlyCharges"]
    total = inputs["TotalCharges"]

    if tenure is None or tenure < 0 or tenure > 72:
        errors.append("Tenure must be between 0 and 72 months.")
    if monthly is None or monthly <= 0:
        errors.append("Monthly charges must be greater than zero.")
    elif monthly > 400:
        errors.append("Monthly charges look unusually high. Please check the value.")
    if total is None or total < 0:
        errors.append("Total charges cannot be negative.")
    elif total > 12000:
        errors.append("Total charges look unusually high. Please check the value.")
    return errors


# ── Inference ─────────────────────────────────────────────────────────────


def risk_level(prob_pct: float) -> tuple:
    """Map a churn probability (0-100) to (risk_label, color)."""
    if prob_pct < 40:
        return "Low Risk", RISK_LEVELS["Low Risk"][0]
    if prob_pct < 70:
        return "Medium Risk", RISK_LEVELS["Medium Risk"][0]
    return "High Risk", RISK_LEVELS["High Risk"][0]


def predict(model, features: np.ndarray) -> dict:
    """Run inference and return prediction details."""
    proba = float(model.predict_proba(features.reshape(1, -1))[0, 1])
    prob_pct = proba * 100.0
    label = "Likely to Churn" if proba >= 0.5 else "Likely to Stay"
    risk_label, risk_color = risk_level(prob_pct)
    return {
        "probability_pct": prob_pct,
        "label": label,
        "risk_label": risk_label,
        "risk_color": risk_color,
    }


# ── Feature interpretation ────────────────────────────────────────────────


def display_value(feat: str, value) -> str:
    """Human-readable rendering of a feature value."""
    rev = REVERSE_ENCODINGS.get(feat)
    if rev is not None:
        return rev.get(value, str(value))
    if feat == "tenure":
        return f"{value} months"
    if feat in ("MonthlyCharges", "TotalCharges"):
        return f"${value:,.2f}"
    return str(value)


def top_factors(alias: str, features: np.ndarray, inputs: dict) -> list:
    """Return the most influential features for this prediction.

    Uses SHAP values when available; otherwise falls back to the model's
    built-in feature importances.
    """
    factors = []
    explainer = get_explainer(alias)
    if explainer is not None:
        try:
            values = explainer.shap_values(features.reshape(1, -1))[0]
            for i, feat in enumerate(FEATURE_NAMES):
                factors.append({
                    "feature": FEATURE_LABELS[feat],
                    "value": display_value(feat, inputs[feat]),
                    "contribution": float(values[i]),
                    "source": "shap",
                })
            factors.sort(key=lambda f: abs(f["contribution"]), reverse=True)
            return factors[:5]
        except Exception:
            pass

    model = load_model(alias)
    if model is not None:
        importances = model.feature_importances_
        for i, feat in enumerate(FEATURE_NAMES):
            factors.append({
                "feature": FEATURE_LABELS[feat],
                "value": display_value(feat, inputs[feat]),
                "contribution": float(importances[i]),
                "source": "importance",
            })
        factors.sort(key=lambda f: f["contribution"], reverse=True)
        return factors[:5]
    return factors


# ── Recommendations ───────────────────────────────────────────────────────


def generate_recommendations(risk_label: str) -> list:
    """Return business recommendations for the given risk level."""
    return RISK_RECOMMENDATIONS.get(
        risk_label, RISK_RECOMMENDATIONS["Low Risk"]
    )
