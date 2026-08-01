# Phase 9.0.5 — Performance Optimization Report

**Scope:** Reduce per-rerun compute on the Streamlit app without changing
business logic or rendered outputs. No training changes, no output changes.

**Environment:** Streamlit 1.60.0, Python 3.14.3, dataset 7,032 × 21
(`WA_Fn-UseC_-Telco-Customer-Churn.csv`, ~956 KB).

---

## 1. What was already cached (verified, unchanged)

| Function | Mechanism | Notes |
|---|---|---|
| `utils.load_data()` | `@st.cache_data` | Reads + cleans the CSV once per session; all pages share the same DataFrame object across reruns |
| `executive_dashboard._build_metrics(df)` | `@st.cache_data` | Executives KPIs / cohorts / revenue groupbys computed once |
| `prediction.load_model(alias)` | `@st.cache_resource` | 22 MB Random Forest stays in memory — never pickled to the disk cache |
| `prediction.get_explainer(alias)` | `@st.cache_resource` | SHAP `TreeExplainer` built once per model per session |

---

## 2. Changes made

### 2.1 `dashboard/prediction.py` — cached SHAP computation

Added `get_shap_values(alias, features)` backed by `@st.cache_data(max_entries=64)`,
keyed on the model alias + the 19-feature encoded vector. It returns
`(base_rate, per-feature_contributions)` and is shared by the Explainable AI page.

- **XGBoost:** `0.74 ms` → `0.07 ms` per call (cached).
- **Random Forest:** `31.8 ms` → `0.07 ms` per call.
- Fix: RF's SHAP output shape is `(1, 19, 2)` (one slice per class); the helper
  selects the churn-class slice (`arr[:, :, 1]`) and `expected_value[-1]`, so the
  Random Forest now produces a correct waterfall/factors on the XAI page. This
  path previously crashed with an unhandled exception (the values were used with
  `float()` directly). XGBoost output is byte-identical to before.

`prediction.top_factors()` was intentionally left unchanged (AI Prediction Lab,
Business Recommendation Engine) so its Random Forest feature-importance fallback
output stays exactly as shipped.

### 2.2 `dashboard/pages/Explainable_AI.py` — single SHAP pass per rerun

Previously the results section ran `explainer.shap_values()` **twice per rerun**
(once in `_shap_factors`, once in `_waterfall_figure`). Now both call the shared
cached `prediction.get_shap_values()`, so SHAP is computed once per
(model, feature-vector) and both sections read the cache. The waterfall figure is
rebuilt fresh each render (deterministic, byte-identical) — see §4.2.

Saving per results-section rerun: **~63.5 ms for Random Forest**, ~1.3 ms for
XGBoost (each what-if / presentation toggle previously re-triggered both SHAP
computations).

### 2.3 `dashboard/pages/analytics.py` — filter-state chart memo

`_charts_section` previously rebuilt all 8 charts (~77 ms) on every sidebar
interaction. Added `_chart_pack(filtered, encoded_all)`, which builds the 8
Plotly figures once per distinct filter state and memoizes them in
`st.session_state["_analytics_chart_pack"]` (bounded to 5 states).

The memo key is derived from the 7 sidebar multiselect values (~0.5 ms to derive)
rather than the DataFrame, because at this dataset size hashing the full
7,032-row DataFrame costs ~10 ms per call — see §4.1.

- Baseline chart section: **77.1 ms** per rerun.
- With memo (filters unchanged): **0.6 ms** per rerun.
- Filter change → rebuild (same cost as before); revert filter → cache hit.

---

## 3. Measured results

| Page / operation | Before | After | Saving |
|---|---|---|---|
| Analytics — 8 charts per filter rerun | 77.1 ms | 0.6 ms | ~76.5 ms/rerun |
| XAI — RF SHAP ×2 per results rerun | 63.6 ms | 0.1 ms | ~63.5 ms/rerun |
| XAI — waterfall figure | rebuilt per rerun | rebuilt fresh (SHAP cached) | — |
| Model load (RF, 22 MB) | cached | cached | — |

Cold (first-visit) costs are unchanged or slightly higher (e.g. chart pack builds
8 figures on first render); the wins are on every subsequent rerun, which is the
interaction path users hit repeatedly.

---

## 4. Measurement-driven decisions (what we deliberately did NOT do)

### 4.1 `@st.cache_data` keyed on DataFrames is a net regression here

Measured: full analytics page compute was **84.8 ms** uncached vs **95.3 ms**
with per-chart `@st.cache_data(df)` (hashing the 7,032 × 21 DataFrame costs
~10 ms per call, which exceeds the ~10 ms per-chart build). The df-keyed
decorators were removed in favor of the cheap filter-state key (§2.3).

### 4.2 Caching matplotlib figures changes render bytes

`@st.cache_data` on the waterfall figure (pickled `plt` Figure) rendered PNG
bytes that differ from a fresh build (pickle state drift). The figure rebuild is
~15 ms; the expensive part is SHAP, which is now cached. The figure-level cache
was dropped to guarantee byte-identical output.

### 4.3 `_prepare_encoded`, KPI helpers, insights, exec charts

All under ~5 ms per call (KPI ~0.2 ms, insights ~1.1 ms). Not worth caching.

---

## 5. Cache inventory (final)

| Cache | Type | Key | Size |
|---|---|---|---|
| `load_data` | `st.cache_data` | — | 7,032-row df |
| `_build_metrics` | `st.cache_data` | df | metrics dict |
| `get_shap_values` | `st.cache_data` (max 64) | (alias, 19-float vector) | 2 floats + 19-float array |
| `_chart_pack` | `st.session_state` memo (max 5) | 7 filter-value tuples | 8 Plotly figures |
| `load_model` / `get_explainer` | `st.cache_resource` | alias | 22 MB RF / explainer |

---

## 6. Verification

- All 6 pages (`/`, `/analytics`, `/prediction_lab`, `/Explainable_AI`,
  `/Business_Recommendation_Engine`, `/executive_dashboard`) render with **zero**
  `stException` / error alerts.
- XAI: submit → full 12-section output renders; presentation toggle + what-if
  reruns clean.
- Analytics: filter interactions re-render all 8 charts with no exceptions.
- Output equivalence: chart-pack figures JSON-identical to fresh builds; XAI
  waterfall PNG byte-identical to the pre-optimization build (XGBoost); factor
  contributions match direct `shap_values` within 1e-12.
- Server log clean (no exceptions).
