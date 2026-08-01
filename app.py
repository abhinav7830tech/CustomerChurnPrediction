"""
Customer Churn Analytics Platform — Production Entry Point.

Multipage Streamlit application built on the `st.navigation` / `st.Page`
API. The sidebar exposes all six tools; every page is reused from
`dashboard/pages/` (and the Home UI from `dashboard/app.py`) — nothing is
duplicated here.

Author: Abhinav Agnihotri
Version: 2.0.0 (Production)
"""

import streamlit as st

_PAGES = {
    "home": st.Page(
        "dashboard/app.py",
        title="Home",
        icon="🏠",
        url_path="home",
        default=True,
    ),
    "analytics": st.Page(
        "dashboard/pages/analytics.py",
        title="Analytics",
        icon="📊",
        url_path="analytics",
    ),
    "prediction_lab": st.Page(
        "dashboard/pages/prediction_lab.py",
        title="Prediction Lab",
        icon="🧪",
        url_path="prediction_lab",
    ),
    "explainable_ai": st.Page(
        "dashboard/pages/Explainable_AI.py",
        title="Explainable AI",
        icon="🧠",
        url_path="explainable_ai",
    ),
    "business_recommendation": st.Page(
        "dashboard/pages/💼_Business_Recommendation_Engine.py",
        title="Business Recommendation Engine",
        icon="💼",
        url_path="business_recommendation",
    ),
    "executive_dashboard": st.Page(
        "dashboard/pages/executive_dashboard.py",
        title="Executive Dashboard",
        icon="📈",
        url_path="executive_dashboard",
    ),
}

st.session_state["_app_pages"] = _PAGES

st.navigation(list(_PAGES.values()), position="sidebar").run()
