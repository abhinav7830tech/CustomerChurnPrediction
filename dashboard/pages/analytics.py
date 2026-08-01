"""
Analytics Module — Customer Churn Analytics Platform
Sprint 3: Interactive BI dashboard with Plotly visualizations.
All metrics update in real time based on sidebar filters.
"""

import theme

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
    """Inject the shared design-system styles and counter animation JS."""
    theme.inject_css()
    theme.inject_kpi_counter()


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




CHURN_COLORS = {"No": "#8FA28A", "Yes": "#C8A96B"}

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
            '<div style="font-size:1.1rem;font-weight:700;color:#C8A96B;'
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
            f'<div style="font-size:0.8rem;color:rgba(255,255,255,0.3);text-align:center;">'
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
    avg_total = get_avg_total_charges(filtered)
    churned_count = int((filtered['Churn'] == 'Yes').sum()) if len(filtered) > 0 else 0

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    row1 = st.columns(3, gap="medium")
    kpi1 = [
        ("Total Customers", f"{total:,}", False, total, "number", "", "Based on filtered data", "👥", "customers"),
        ("Churn Rate", f"{churn_rate}%", False, churn_rate, "percent", "", "Of filtered customer base", "📉", "churn"),
        ("Average Tenure", f"{avg_tenure} mo", False, avg_tenure, "suffix", " mo", "Filtered customer average", "⏳", "retention"),
    ]
    for col, (label, value, accent, dv, dfmt, dsuf, sub, icon, tone) in zip(row1, kpi1):
        with col:
            st.markdown(
                theme.kpi_card(
                    label, value, subtext=sub, accent=accent,
                    data_value=dv, data_format=dfmt, data_suffix=dsuf,
                    icon=icon, tone=tone,
                ),
                unsafe_allow_html=True,
            )

    row2 = st.columns(3, gap="medium")
    kpi2 = [
        ("Avg. Monthly Charges", f"${avg_monthly:.2f}", False, avg_monthly, "currency", "", "Per customer average", "💰", "revenue"),
        ("Total Charges", f"${avg_total:.2f}", False, avg_total, "currency", "", "Average per customer", "💳", "health"),
        ("Churned Customers", f"{churned_count:,}", True, churned_count, "number", "", "In filtered dataset", "🚪", "churn"),
    ]
    for col, (label, value, accent, dv, dfmt, dsuf, sub, icon, tone) in zip(row2, kpi2):
        with col:
            st.markdown(
                theme.kpi_card(
                    label, value, subtext=sub, accent=accent,
                    data_value=dv, data_format=dfmt, data_suffix=dsuf,
                    icon=icon, tone=tone,
                ),
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
    fig.update_layout(template=theme.TEMPLATE)
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
    fig.update_layout(template=theme.TEMPLATE)
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
    fig.update_layout(template=theme.TEMPLATE)
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
        template=theme.TEMPLATE,
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
        template=theme.TEMPLATE,
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
        template=theme.TEMPLATE,
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
    fig.update_layout(template=theme.TEMPLATE)
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
            colorscale=[[0, "#C8A96B"], [0.5, "#234556"], [1, "#8FA28A"]],
            zmin=-1, zmax=1,
            text=np.round(corr.values, 2),
            texttemplate="%{text}",
            textfont=dict(size=8, color="#F4F2EE"),
            hovertemplate=(
                "<b>%{x}</b> vs <b>%{y}</b><br>"
                "Correlation: %{z:.3f}<extra></extra>"
            ),
        ),
    )
    fig.update_layout(
        template=theme.TEMPLATE,
        title="Feature Correlation Heatmap",
        height=500,
        xaxis=dict(tickangle=-45, tickfont_size=9),
        yaxis=dict(tickfont_size=9),
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# CHART PACK MEMOIZATION
# ═══════════════════════════════════════════════════════════════════════════════


_CHART_COLUMNS = [
    "gender", "SeniorCitizen", "Partner", "Dependents",
    "InternetService", "Contract", "PaymentMethod",
]

_CHART_CACHE_KEY = "_analytics_chart_pack"


def _chart_pack(filtered: pd.DataFrame, encoded_all: pd.DataFrame) -> tuple:
    """Build all 8 figures once per distinct filter state.

    The filtered DataFrame is fully determined by the sidebar multiselect
    values, so the memo is keyed on those values (cheap to derive, fast to
    hash) rather than on the DataFrame itself — hashing the full dataset on
    every rerun would cost more than rebuilding the charts.
    """
    key = tuple(tuple(filtered[c].unique()) for c in _CHART_COLUMNS)
    cache = st.session_state.setdefault(_CHART_CACHE_KEY, {})
    if len(cache) > 4:
        cache.clear()
    pack = cache.get(key)
    if pack is None:
        idxs = set(filtered.index)
        enc_filtered = encoded_all[encoded_all.index.isin(idxs)].reset_index(drop=True)
        pack = (
            _churn_donut(filtered),
            _contract_chart(filtered),
            _internet_chart(filtered),
            _payment_chart(filtered),
            _monthly_hist(filtered),
            _tenure_hist(filtered),
            _senior_chart(filtered),
            _correlation_heatmap(enc_filtered),
        )
        cache[key] = pack
    return pack


# ═══════════════════════════════════════════════════════════════════════════════
# CHARTS SECTION
# ═══════════════════════════════════════════════════════════════════════════════


def _charts_section(filtered: pd.DataFrame, encoded_all: pd.DataFrame) -> None:
    """Render the 8-chart grid (4 rows x 2 columns) with descriptions."""
    if len(filtered) == 0:
        return

    st.markdown(
        '<div class="section-header">Visualizations</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-sub">'
        "Interactive charts — hover, zoom, and pan for deeper exploration"
        "</div>",
        unsafe_allow_html=True,
    )

    donut_fig, contract_fig, internet_fig, payment_fig, \
        monthly_fig, tenure_fig, senior_fig, corr_fig = _chart_pack(
            filtered, encoded_all
        )

    # Row 1: Churn donut + Contract chart
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown(
            '<div class="chart-title">Churn Distribution</div>'
            '<div class="chart-desc">Overview of churn vs retained customer proportions</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(donut_fig, width="stretch")
    with c2:
        st.markdown(
            '<div class="chart-title">Contract Type vs Churn</div>'
            '<div class="chart-desc">Comparison of churn rates across contract types</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(contract_fig, width="stretch")

    # Row 2: Internet service + Payment method
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown(
            '<div class="chart-title">Internet Service vs Churn</div>'
            '<div class="chart-desc">Churn distribution by internet service type</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(internet_fig, width="stretch")
    with c2:
        st.markdown(
            '<div class="chart-title">Payment Method vs Churn</div>'
            '<div class="chart-desc">Churn rates segmented by payment method</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(payment_fig, width="stretch")

    # Row 3: Monthly charges + Tenure histograms
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown(
            '<div class="chart-title">Monthly Charges Distribution</div>'
            '<div class="chart-desc">Distribution of monthly charges for churned and retained customers</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(monthly_fig, width="stretch")
    with c2:
        st.markdown(
            '<div class="chart-title">Tenure Distribution</div>'
            '<div class="chart-desc">Distribution of customer tenure by churn status</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(tenure_fig, width="stretch")

    # Row 4: Senior citizen + Correlation heatmap
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown(
            '<div class="chart-title">Churn by Senior Citizen</div>'
            '<div class="chart-desc">Churn rate comparison between senior and non-senior customers</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(senior_fig, width="stretch")
    with c2:
        st.markdown(
            '<div class="chart-title">Feature Correlation Heatmap</div>'
            '<div class="chart-desc">Feature correlation matrix highlighting relationships with churn</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(corr_fig, width="stretch")


# ═══════════════════════════════════════════════════════════════════════════════
# DATA TABLE
# ═══════════════════════════════════════════════════════════════════════════════


def _data_table(filtered: pd.DataFrame) -> None:
    """Interactive data table with sorting, search, and scrolling."""
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header">Filtered Dataset</div>',
        unsafe_allow_html=True,
    )

    if len(filtered) == 0:
        st.markdown(
            '<div class="empty-state">'
            '<div class="empty-state-icon">◆</div>'
            '<div class="empty-state-title">No Data Matches Filters</div>'
            '<div class="empty-state-text">Try adjusting your filter selections to view data.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f'<div class="section-sub">{len(filtered):,} records shown</div>',
        unsafe_allow_html=True,
    )

    display = filtered.drop(columns=["customerID"], errors="ignore")
    st.dataframe(
        display,
        width="stretch",
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
        '<div class="section-header">Business Insights</div>',
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
            "◆",
            "Highest Churn Contract",
            f"{top_contract} — {top_contract_pct}% of churned customers.",
        ),
        (
            "◆",
            "Highest Churn Payment",
            f"{top_payment} — {top_payment_pct}% of churned customers.",
        ),
        (
            "◆",
            "Avg Monthly Charges",
            f"Churned: ${avg_mc_churned:.2f} | Retained: ${avg_mc_retained:.2f}",
        ),
        (
            "◆",
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
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        csv = filtered.to_csv(index=False).encode("utf-8")
        clicked = theme.download_button(
            label="📥 Download Filtered Data (CSV)",
            data=csv,
            file_name="telco_churn_filtered.csv",
            mime="text/csv",
        )
        if clicked:
            st.toast("Filtered data (CSV) download started", icon="📥")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════


def main() -> None:
    """Render the full analytics page."""
    _inject_css()

    placeholder = st.empty()
    with placeholder.container():
        st.markdown(
            '<div class="page-header">'
            '<div class="skeleton" style="height:40px;width:60%;margin-bottom:0.5rem"></div>'
            '<div class="skeleton" style="height:20px;width:40%"></div>'
            "</div>",
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
        st.markdown(
            '<div class="skeleton" style="height:28px;width:30%;margin-bottom:0.5rem"></div>',
            unsafe_allow_html=True,
        )
        for _ in range(2):
            cols = st.columns(2, gap="medium")
            for col in cols:
                with col:
                    st.markdown(
                        '<div class="skeleton skeleton-chart"></div>',
                        unsafe_allow_html=True,
                    )

    df = load_data()
    encoded_all = _prepare_encoded(df)

    placeholder.empty()

    theme.page_header(
        "Customer Churn Analytics",
        subtitle="Interactive Business Intelligence Dashboard",
        rule=False,
        back_link=False,
    )

    filtered = _render_sidebar(df)

    _kpi_row(filtered)
    if len(filtered) > 0:
        _charts_section(filtered, encoded_all)
    else:
        st.markdown(
            '<div class="empty-state">'
            '<div class="empty-state-icon">◆</div>'
            '<div class="empty-state-title">No Data Matches Filters</div>'
            '<div class="empty-state-text">Charts are unavailable when no records match the current filter selection.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    _data_table(filtered)
    if len(filtered) > 0:
        _insights_panel(filtered)
    _export_button(filtered)


if __name__ == "__main__":
    main()
