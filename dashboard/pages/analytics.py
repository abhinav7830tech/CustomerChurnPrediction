"""
Analytics Module — Customer Churn Analytics Platform
Sprint 3: Interactive BI dashboard with Plotly visualizations.
All metrics update in real time based on sidebar filters.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils import (
    load_data,
    get_total_customers,
    get_churn_rate,
    get_avg_tenure,
    get_avg_monthly_charges,
    get_avg_total_charges,
)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Customer Churn Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM CSS
# ═══════════════════════════════════════════════════════════════════════════════


def _inject_css() -> None:
    """Page-level styles consistent with the landing page dark theme."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

    .stApp { background: #08080f; }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }

    /* ── Accent bar ── */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #3b82f6, #60a5fa, #3b82f6);
        z-index: 999;
    }

    /* ── Page header ── */
    .page-header {
        margin-bottom: 1.5rem;
    }

    .page-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #f8fafc 0%, #60a5fa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.25rem;
        letter-spacing: -0.02em;
    }

    .page-subtitle {
        font-size: 1rem;
        color: #64748b;
        font-weight: 400;
    }

    /* ── KPI cards ── */
    .kpi-card {
        background: linear-gradient(145deg, #14142a 0%, #1a1a35 100%);
        border: 1px solid rgba(59, 130, 246, 0.1);
        border-radius: 16px;
        padding: 1.25rem 1rem;
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
        height: 100%;
    }

    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(59, 130, 246, 0.1);
        border-color: rgba(59, 130, 246, 0.25);
    }

    .kpi-label {
        font-size: 0.7rem;
        font-weight: 500;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.35rem;
    }

    .kpi-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #f8fafc;
        line-height: 1.2;
    }

    .kpi-value.accent { color: #3b82f6; }

    /* ── Section headers ── */
    .section-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 0.15rem;
    }

    .section-sub {
        font-size: 0.8rem;
        color: #475569;
        margin-bottom: 1rem;
    }

    .custom-divider {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.12), transparent);
        margin: 1.5rem 0;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: #0c0c1a;
        border-right: 1px solid rgba(59, 130, 246, 0.08);
    }

    section[data-testid="stSidebar"] .stMarkdown {
        padding: 0 0.5rem;
    }

    section[data-testid="stSidebar"] .stMultiSelect label,
    section[data-testid="stSidebar"] .stSelectbox label {
        color: #94a3b8 !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    section[data-testid="stSidebar"] .stMultiSelect div[data-baseweb="select"] > div {
        background: #14142a !important;
        border: 1px solid rgba(59, 130, 246, 0.15) !important;
        border-radius: 8px !important;
        color: #f8fafc !important;
    }

    section[data-testid="stSidebar"] .stMultiSelect span {
        color: #f8fafc !important;
    }

    /* ── Insight cards ── */
    .insight-card {
        background: linear-gradient(145deg, #14142a 0%, #1a1a35 100%);
        border: 1px solid rgba(59, 130, 246, 0.08);
        border-radius: 12px;
        padding: 1.25rem;
        transition: transform 0.3s ease, border-color 0.3s ease;
        height: 100%;
    }

    .insight-card:hover {
        transform: translateY(-2px);
        border-color: rgba(59, 130, 246, 0.2);
    }

    .insight-icon { font-size: 1.5rem; margin-bottom: 0.5rem; }

    .insight-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 0.25rem;
    }

    .insight-text {
        font-size: 0.75rem;
        color: #64748b;
        line-height: 1.5;
    }

    /* ── Dataframe ── */
    .stDataFrame {
        background: transparent;
    }

    .stDataFrame table {
        font-size: 0.8rem;
    }

    /* ── Back link ── */
    .back-link {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        color: #64748b;
        text-decoration: none;
        font-size: 0.85rem;
        font-weight: 500;
        padding: 0.4rem 0;
        transition: color 0.2s ease;
    }

    .back-link:hover {
        color: #60a5fa;
    }

    /* ── Download button ── */
    .stDownloadButton button {
        background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }

    .stDownloadButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3) !important;
    }

    /* ── Plotly chart containers ── */
    .chart-container {
        background: #14142a;
        border: 1px solid rgba(59, 130, 246, 0.08);
        border-radius: 14px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    @media (max-width: 768px) {
        .page-title { font-size: 1.5rem; }
        .kpi-value { font-size: 1.3rem; }
    }
    </style>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA PREP
# ═══════════════════════════════════════════════════════════════════════════════


@st.cache_data
def _prepare_encoded(df: pd.DataFrame) -> pd.DataFrame:
    """Produce a numeric-encoded copy for correlation heatmap."""
    enc = df.copy()
    mapping = {
        "gender": {"Male": 1, "Female": 0},
        "Partner": {"Yes": 1, "No": 0},
        "Dependents": {"Yes": 1, "No": 0},
        "PhoneService": {"Yes": 1, "No": 0},
        "PaperlessBilling": {"Yes": 1, "No": 0},
        "Churn": {"Yes": 1, "No": 0},
    }
    for col, m in mapping.items():
        enc[col] = enc[col].map(m)
    enc["Contract"] = enc["Contract"].map(
        {"Month-to-month": 0, "One year": 1, "Two year": 2}
    )
    enc["InternetService"] = enc["InternetService"].map(
        {"DSL": 0, "Fiber optic": 1, "No": 2}
    )
    enc["PaymentMethod"] = enc["PaymentMethod"].map({
        "Electronic check": 0, "Mailed check": 1,
        "Bank transfer (automatic)": 2, "Credit card (automatic)": 3,
    })
    return enc


# ═══════════════════════════════════════════════════════════════════════════════
# PLOTLY TEMPLATE
# ═══════════════════════════════════════════════════════════════════════════════


def _dark_template() -> go.layout.Template:
    """Corporate dark theme for all Plotly charts."""
    return go.layout.Template(
        layout=dict(
            font=dict(family="Inter, sans-serif", size=12, color="#cbd5e1"),
            title=dict(font=dict(size=14, color="#f8fafc"), x=0.5),
            paper_bgcolor="#14142a",
            plot_bgcolor="#08080f",
            margin=dict(l=40, r=20, t=40, b=40),
            xaxis=dict(
                gridcolor="#1e1e3a",
                zerolinecolor="#1e1e3a",
                tickfont=dict(size=10, color="#64748b"),
                title=dict(font=dict(size=11, color="#94a3b8")),
            ),
            yaxis=dict(
                gridcolor="#1e1e3a",
                zerolinecolor="#1e1e3a",
                tickfont=dict(size=10, color="#64748b"),
                title=dict(font=dict(size=11, color="#94a3b8")),
            ),
            legend=dict(
                font=dict(size=10, color="#cbd5e1"),
                bgcolor="rgba(0,0,0,0)",
                orientation="h",
                y=1.12,
            ),
            hoverlabel=dict(
                bgcolor="#1a1a35",
                font_color="#f8fafc",
                font_size=11,
            ),
            colorway=["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6",
                      "#ec4899", "#06b6d4", "#84cc16"],
        )
    )


TEMPLATE = _dark_template()

CHURN_COLORS = {"No": "#3b82f6", "Yes": "#ef4444"}

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR FILTERS
# ═══════════════════════════════════════════════════════════════════════════════


def _render_sidebar(df: pd.DataFrame) -> pd.DataFrame:
    """Build filter widgets in the sidebar and return the filtered DataFrame."""
    with st.sidebar:
        st.markdown(
            '<a class="back-link" href="/" target="_self">'
            "← Back to Dashboard</a>",
            unsafe_allow_html=True,
        )

        st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:1.1rem;font-weight:700;color:#f8fafc;'
            'margin-bottom:1rem;">Filters</div>',
            unsafe_allow_html=True,
        )

        gender = st.multiselect(
            "Gender", options=sorted(df["gender"].unique()),
            default=sorted(df["gender"].unique()),
        )
        senior = st.multiselect(
            "Senior Citizen",
            options=sorted(df["SeniorCitizen"].unique()),
            default=sorted(df["SeniorCitizen"].unique()),
            format_func=lambda x: "Yes" if x == 1 else "No",
        )
        partner = st.multiselect(
            "Partner", options=sorted(df["Partner"].unique()),
            default=sorted(df["Partner"].unique()),
        )
        dependents = st.multiselect(
            "Dependents", options=sorted(df["Dependents"].unique()),
            default=sorted(df["Dependents"].unique()),
        )
        internet = st.multiselect(
            "Internet Service",
            options=sorted(df["InternetService"].unique()),
            default=sorted(df["InternetService"].unique()),
        )
        contract = st.multiselect(
            "Contract", options=sorted(df["Contract"].unique()),
            default=sorted(df["Contract"].unique()),
        )
        payment = st.multiselect(
            "Payment Method",
            options=sorted(df["PaymentMethod"].unique()),
            default=sorted(df["PaymentMethod"].unique()),
        )

        st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:0.8rem;color:#475569;text-align:center;">'
            f"Filters applied in real time</div>",
            unsafe_allow_html=True,
        )

    mask = (
        df["gender"].isin(gender)
        & df["SeniorCitizen"].isin(senior)
        & df["Partner"].isin(partner)
        & df["Dependents"].isin(dependents)
        & df["InternetService"].isin(internet)
        & df["Contract"].isin(contract)
        & df["PaymentMethod"].isin(payment)
    )
    return df[mask].reset_index(drop=True)


# ═══════════════════════════════════════════════════════════════════════════════
# KPI ROW
# ═══════════════════════════════════════════════════════════════════════════════


def _kpi_row(filtered: pd.DataFrame) -> None:
    """Display six KPI cards that reflect the current filter state."""
    total = get_total_customers(filtered)
    churn_rate = get_churn_rate(filtered)
    avg_tenure = get_avg_tenure(filtered)
    avg_monthly = get_avg_monthly_charges(filtered)

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    row1 = st.columns(3, gap="medium")
    for col, (label, value, accent) in zip(
        row1,
        [
            ("Total Customers", f"{total:,}", False),
            ("Churn Rate", f"{churn_rate}%", False),
            ("Average Tenure", f"{avg_tenure} mo", False),
        ],
    ):
        with col:
            val_class = "kpi-value accent" if accent else "kpi-value"
            st.markdown(
                f'<div class="kpi-card">'
                f'<div class="kpi-label">{label}</div>'
                f'<div class="{val_class}">{value}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )

    row2 = st.columns(3, gap="medium")
    for col, (label, value, accent) in zip(
        row2,
        [
            ("Avg. Monthly Charges", f"${avg_monthly:.2f}", False),
            ("Total Charges", f"${get_avg_total_charges(filtered):.2f}", False),
            ("Churned Customers",
             f"{int((filtered['Churn'] == 'Yes').sum()):,}", True),
        ],
    ):
        with col:
            val_class = "kpi-value accent" if accent else "kpi-value"
            st.markdown(
                f'<div class="kpi-card">'
                f'<div class="kpi-label">{label}</div>'
                f'<div class="{val_class}">{value}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════════════════
# CHART BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════


def _churn_donut(df: pd.DataFrame) -> go.Figure:
    """Churn distribution as a donut chart."""
    counts = df["Churn"].value_counts().reset_index()
    counts.columns = ["Churn", "Count"]
    fig = px.pie(
        counts, names="Churn", values="Count", hole=0.55,
        color="Churn", color_discrete_map=CHURN_COLORS,
        title="Churn Distribution",
    )
    fig.update_traces(
        textinfo="label+percent",
        textfont_size=12,
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
    )
    fig.update_layout(template=TEMPLATE)
    return fig


def _contract_chart(df: pd.DataFrame) -> go.Figure:
    """Grouped bar: contract type vs churn."""
    ctab = (
        df.groupby(["Contract", "Churn"])
        .size()
        .reset_index(name="Count")
    )
    fig = px.bar(
        ctab, x="Contract", y="Count", color="Churn",
        barmode="group", color_discrete_map=CHURN_COLORS,
        title="Contract Type vs Churn",
    )
    fig.update_layout(template=TEMPLATE)
    return fig


def _internet_chart(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar: internet service vs churn."""
    itab = (
        df.groupby(["InternetService", "Churn"])
        .size()
        .reset_index(name="Count")
    )
    fig = px.bar(
        itab, y="InternetService", x="Count", color="Churn",
        orientation="h", barmode="group",
        color_discrete_map=CHURN_COLORS,
        title="Internet Service vs Churn",
    )
    fig.update_layout(template=TEMPLATE)
    return fig


def _payment_chart(df: pd.DataFrame) -> go.Figure:
    """Bar chart: payment method vs churn."""
    ptab = (
        df.groupby(["PaymentMethod", "Churn"])
        .size()
        .reset_index(name="Count")
    )
    fig = px.bar(
        ptab, x="PaymentMethod", y="Count", color="Churn",
        barmode="group", color_discrete_map=CHURN_COLORS,
        title="Payment Method vs Churn",
    )
    fig.update_layout(
        template=TEMPLATE,
        xaxis_tickangle=-30,
    )
    return fig


def _monthly_hist(df: pd.DataFrame) -> go.Figure:
    """Histogram of monthly charges split by churn."""
    fig = px.histogram(
        df, x="MonthlyCharges", color="Churn",
        color_discrete_map=CHURN_COLORS, nbins=30,
        title="Monthly Charges Distribution",
    )
    fig.update_layout(
        template=TEMPLATE,
        barmode="overlay",
        bargap=0.05,
    )
    fig.update_traces(opacity=0.75)
    return fig


def _tenure_hist(df: pd.DataFrame) -> go.Figure:
    """Histogram of tenure split by churn."""
    fig = px.histogram(
        df, x="tenure", color="Churn",
        color_discrete_map=CHURN_COLORS, nbins=30,
        title="Tenure Distribution",
    )
    fig.update_layout(
        template=TEMPLATE,
        barmode="overlay",
        bargap=0.05,
    )
    fig.update_traces(opacity=0.75)
    return fig


def _senior_chart(df: pd.DataFrame) -> go.Figure:
    """Bar chart: churn rate by senior citizen status."""
    sdf = df.copy()
    sdf["SeniorCitizen"] = sdf["SeniorCitizen"].map({0: "No", 1: "Yes"})
    stab = (
        sdf.groupby(["SeniorCitizen", "Churn"])
        .size()
        .reset_index(name="Count")
    )
    fig = px.bar(
        stab, x="SeniorCitizen", y="Count", color="Churn",
        barmode="group", color_discrete_map=CHURN_COLORS,
        title="Churn by Senior Citizen",
    )
    fig.update_layout(template=TEMPLATE)
    return fig


def _correlation_heatmap(encoded: pd.DataFrame) -> go.Figure:
    """Correlation heatmap of numeric / encoded features."""
    numeric_cols = [
        "tenure", "MonthlyCharges", "TotalCharges",
        "gender", "SeniorCitizen", "Partner", "Dependents",
        "PhoneService", "PaperlessBilling", "Contract",
        "InternetService", "PaymentMethod", "Churn",
    ]
    corr = encoded[numeric_cols].corr()

    fig = go.Figure(
        data=go.Heatmap(
            z=corr.values,
            x=corr.columns,
            y=corr.columns,
            colorscale="Blues",
            zmin=-1, zmax=1,
            text=np.round(corr.values, 2),
            texttemplate="%{text}",
            textfont=dict(size=8, color="#f8fafc"),
            hovertemplate=(
                "<b>%{x}</b> vs <b>%{y}</b><br>"
                "Correlation: %{z:.3f}<extra></extra>"
            ),
        ),
    )
    fig.update_layout(
        template=TEMPLATE,
        title="Feature Correlation Heatmap",
        height=500,
        xaxis=dict(tickangle=-45, tickfont_size=9),
        yaxis=dict(tickfont_size=9),
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# CHARTS SECTION
# ═══════════════════════════════════════════════════════════════════════════════


def _charts_section(filtered: pd.DataFrame, encoded_all: pd.DataFrame) -> None:
    """Render the 8-chart grid (4 rows x 2 columns)."""
    st.markdown(
        '<div class="section-header">📊 Visualizations</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-sub">'
        "Interactive charts — hover, zoom, and pan for deeper exploration"
        "</div>",
        unsafe_allow_html=True,
    )

    # Row 1: Churn donut + Contract chart
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.plotly_chart(_churn_donut(filtered), use_container_width=True)
    with c2:
        st.plotly_chart(_contract_chart(filtered), use_container_width=True)

    # Row 2: Internet service + Payment method
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.plotly_chart(_internet_chart(filtered), use_container_width=True)
    with c2:
        st.plotly_chart(_payment_chart(filtered), use_container_width=True)

    # Row 3: Monthly charges + Tenure histograms
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.plotly_chart(_monthly_hist(filtered), use_container_width=True)
    with c2:
        st.plotly_chart(_tenure_hist(filtered), use_container_width=True)

    # Row 4: Senior citizen + Correlation heatmap
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.plotly_chart(_senior_chart(filtered), use_container_width=True)
    with c2:
        # For the heatmap, use the filtered rows from the full encoded dataset
        idxs = set(filtered.index)
        enc_filtered = encoded_all[encoded_all.index.isin(idxs)].reset_index(
            drop=True
        )
        st.plotly_chart(
            _correlation_heatmap(enc_filtered), use_container_width=True
        )


# ═══════════════════════════════════════════════════════════════════════════════
# DATA TABLE
# ═══════════════════════════════════════════════════════════════════════════════


def _data_table(filtered: pd.DataFrame) -> None:
    """Interactive data table with sorting, search, and scrolling."""
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header">📋 Filtered Dataset</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="section-sub">{len(filtered):,} records shown</div>',
        unsafe_allow_html=True,
    )

    display = filtered.drop(columns=["customerID"], errors="ignore")
    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={col: st.column_config.TextColumn(col) for col in display.columns},
    )


# ═══════════════════════════════════════════════════════════════════════════════
# BUSINESS INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════════


def _insights_panel(filtered: pd.DataFrame) -> None:
    """Auto-generated business insights from the filtered data."""
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header">💡 Business Insights</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-sub">'
        "Automatically generated from the filtered dataset"
        "</div>",
        unsafe_allow_html=True,
    )

    churned = filtered[filtered["Churn"] == "Yes"]
    retained = filtered[filtered["Churn"] == "No"]

    # Compute insights
    total = len(filtered)
    churn_count = len(churned)
    churn_pct = round(churn_count / total * 100, 1) if total else 0

    top_contract = (
        churned.groupby("Contract").size().idxmax()
        if len(churned) else "N/A"
    )
    top_contract_pct = (
        round(
            churned.groupby("Contract").size().max() / churn_count * 100, 1
        )
        if churn_count else 0
    )

    top_payment = (
        churned.groupby("PaymentMethod").size().idxmax()
        if len(churned) else "N/A"
    )
    top_payment_pct = (
        round(
            churned.groupby("PaymentMethod").size().max() / churn_count * 100, 1
        )
        if churn_count else 0
    )

    avg_mc_churned = (
        round(churned["MonthlyCharges"].mean(), 2) if len(churned) else 0
    )
    avg_mc_retained = (
        round(retained["MonthlyCharges"].mean(), 2) if len(retained) else 0
    )

    avg_tenure_churned = (
        round(churned["tenure"].mean(), 1) if len(churned) else 0
    )
    avg_tenure_retained = (
        round(retained["tenure"].mean(), 1) if len(retained) else 0
    )

    top_internet = (
        churned["InternetService"].mode()[0]
        if len(churned) else "N/A"
    )

    cols = st.columns(4, gap="medium")
    insight_data = [
        (
            "📅",
            "Highest Churn Contract",
            f"{top_contract} — {top_contract_pct}% of churned customers.",
        ),
        (
            "💳",
            "Highest Churn Payment",
            f"{top_payment} — {top_payment_pct}% of churned customers.",
        ),
        (
            "💰",
            "Avg Monthly Charges",
            f"Churned: ${avg_mc_churned:.2f} | Retained: ${avg_mc_retained:.2f}",
        ),
        (
            "⏳",
            "Avg Tenure",
            f"Churned: {avg_tenure_churned} mo | Retained: {avg_tenure_retained} mo",
        ),
    ]
    for col, (icon, title, desc) in zip(cols, insight_data):
        with col:
            st.markdown(
                f'<div class="insight-card">'
                f'<div class="insight-icon">{icon}</div>'
                f'<div class="insight-title">{title}</div>'
                f'<div class="insight-text">{desc}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORT
# ═══════════════════════════════════════════════════════════════════════════════


def _export_button(filtered: pd.DataFrame) -> None:
    """Download button for filtered data as CSV."""
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Filtered Data (CSV)",
            data=csv,
            file_name="telco_churn_filtered.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════


def main() -> None:
    """Render the full analytics page."""
    _inject_css()

    df = load_data()
    encoded_all = _prepare_encoded(df)

    st.markdown(
        '<div class="page-header">'
        '<div class="page-title">Customer Churn Analytics</div>'
        '<div class="page-subtitle">'
        "Interactive Business Intelligence Dashboard"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    filtered = _render_sidebar(df)

    _kpi_row(filtered)
    _charts_section(filtered, encoded_all)
    _data_table(filtered)
    _insights_panel(filtered)
    _export_button(filtered)


if __name__ == "__main__":
    main()
