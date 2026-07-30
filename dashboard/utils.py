"""
Utility functions for the Customer Churn Executive Dashboard.

Data loading, cleaning, KPI calculations, and insight generators.
All functions operate on the raw dataset — no ML, no models.
"""

import pandas as pd
import streamlit as st

# ── Paths ──────────────────────────────────────────────────────

DATA_PATH = "data/WA_Fn-UseC_-Telco-Customer-Churn.csv"


# ── Data Loading ───────────────────────────────────────────────

@st.cache_data(show_spinner="Loading dataset...")
def load_data() -> pd.DataFrame:
    """Load and clean the Telco Customer Churn dataset.

    Returns a clean DataFrame with TotalCharges converted to numeric
    and rows with null values removed.
    """
    df = pd.read_csv(DATA_PATH)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df = df.dropna().reset_index(drop=True)
    return df


# ── KPI Calculators ────────────────────────────────────────────

def get_total_customers(df: pd.DataFrame) -> int:
    """Return the total number of customers in the dataset."""
    return len(df)


def get_churn_rate(df: pd.DataFrame) -> float:
    """Return the churn rate as a percentage, rounded to 1 decimal."""
    return round((df["Churn"] == "Yes").mean() * 100, 1)


def get_avg_tenure(df: pd.DataFrame) -> float:
    """Return the average customer tenure in months, rounded to 1 decimal."""
    return round(df["tenure"].mean(), 1)


def get_avg_monthly_charges(df: pd.DataFrame) -> float:
    """Return the average monthly charges, rounded to 2 decimals."""
    return round(df["MonthlyCharges"].mean(), 2)


def get_avg_total_charges(df: pd.DataFrame) -> float:
    """Return the average total charges, rounded to 2 decimals."""
    return round(df["TotalCharges"].mean(), 2)


# ── Insight Generators ─────────────────────────────────────────

def get_top_churn_contract(df: pd.DataFrame) -> tuple[str, float]:
    """Return (contract_type, churn_rate) for the contract with highest churn."""
    rates = df.groupby("Contract")["Churn"].apply(
        lambda x: (x == "Yes").mean()
    )
    top = rates.idxmax()
    pct = round(rates.max() * 100, 1)
    return top, pct


def get_retained_avg_monthly_charges(df: pd.DataFrame) -> float:
    """Return average monthly charges for non-churned customers."""
    return round(
        df[df["Churn"] == "No"]["MonthlyCharges"].mean(), 2
    )


def get_churned_avg_tenure(df: pd.DataFrame) -> float:
    """Return average tenure of customers who churned."""
    return round(
        df[df["Churn"] == "Yes"]["tenure"].mean(), 1
    )


def get_churned_avg_monthly_charges(df: pd.DataFrame) -> float:
    """Return average monthly charges of customers who churned."""
    return round(
        df[df["Churn"] == "Yes"]["MonthlyCharges"].mean(), 2
    )


def get_top_internet_among_churned(df: pd.DataFrame) -> str:
    """Return the most common InternetService among churned customers."""
    return df[df["Churn"] == "Yes"]["InternetService"].mode()[0]
