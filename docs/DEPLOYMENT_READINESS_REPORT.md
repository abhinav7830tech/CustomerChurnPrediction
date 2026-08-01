# 🚀 Deployment Readiness Report

**Phase 9.0.6 — Production Deployment Readiness**

| | |
|---|---|
| **Project** | Customer Churn Prediction — AI-Powered Retention Analytics Platform |
| **Entry Point** | `dashboard/app.py` |
| **Verified On** | Python 3.14.3, Streamlit 1.60.0, macOS (local), headless browser smoke test |
| **Date** | 2026-08-02 |
| **Overall Verdict** | ✅ **READY** (with 5 non-blocking warnings to action before/at deploy time) |

---

## 🏁 Overall Status

| Status | Count | Summary |
|---|---|---|
| ✅ Ready | 12 | Verified working features & deployment prerequisites |
| ⚠ Warnings | 5 | Non-blocking; recommended fixes for smooth production launch |
| ❌ Blocking | 0 | Nothing blocks deployment today |

---

## ✅ Verified Ready

1. **Correct entry point identified** — the real multipage app is `dashboard/app.py`; the 6-page navigation tree resolves correctly (`/`, `/analytics`, `/prediction_lab`, `/Explainable_AI`, `/Business_Recommendation_Engine`, `/executive_dashboard`).
2. **All 6 pages render** — headless Chromium smoke test passed every page with **0 page errors** and a clean server log.
3. **Every export pipeline works end-to-end** and the produced files were validated:

   | Page | Export | Validated |
   |---|---|---|
   | Analytics | CSV | ✅ 970 KB, 7,043-row filtered dataset |
   | AI Prediction Lab | PDF · PPTX | ✅ 5-page PDF · ✅ valid OOXML deck |
   | Explainable AI | PDF | ✅ 2-page SHAP report |
   | Business Recommendation Engine | PDF · PPTX | ✅ 5-page PDF · ✅ valid OOXML deck |
   | Executive Dashboard (BI) | PDF | ✅ 3-page board report |

4. **PDF / PPTX generation is cloud-safe** — `fpdf2` and `python-pptx` are pure-Python with zero system-library requirements; no `apt`/`packages.txt` needed.
5. **Model loading is deployment-safe** — `prediction.py` resolves `models/` via `os.path.dirname(os.path.dirname(__file__))` (`prediction.py:23`), so the 22 MB Random Forest + 360 KB XGBoost pickles load regardless of working directory.
6. **Dataset is git-tracked** — `data/WA_Fn-UseC_-Telco-Customer-Churn.csv` is committed, so no external storage/LFS is required for the app to boot.
7. **Models are git-tracked** — `models/*.pkl` are committed and `.gitignore` does **not** exclude `data/` or `models/` (correct for deployment).
8. **All 10 app files are git-tracked** — including the emoji-named `💼_Business_Recommendation_Engine.py` page.
9. **Page imports are path-independent** — every page bootstraps `sys.path` from `Path(__file__)` parent-dirs, so imports (`theme`, `utils`, `prediction`, `report`, `pptx_report`) resolve correctly from any working directory on any platform.
10. **Only one CWD-relative reference in the entire app** — `DATA_PATH = "data/..."` (`utils.py:13`). Every platform starts the process from the repo root, so this resolves correctly.
11. **Page configuration complete** — all 5 pages + `app.py` call `st.set_page_config` with a `page_title`, emoji `page_icon` (favicon), and `layout="wide"`. Browser tab icons render correctly.
12. **Repo footprint is deployable** — ~35 MB working tree / 7.4 MB `.git`; far below Streamlit Cloud's ~1 GB, Render, and Railway limits.

---

## ⚠ Warnings (non-blocking — recommended before production launch)

1. **Root `app.py` is an auto-detect trap (highest priority warning).**
   `app.py` at the repository root is the legacy Sprint-1 landing-page stub (310 lines, no multipage). Streamlit Cloud **auto-detects a root-level `app.py` as the entry point**, which would deploy the stub instead of the real dashboard.
   → **Mitigation:** on Streamlit Cloud set **Main file path = `dashboard/app.py`**; on Render/Railway use a start command that targets `dashboard/app.py` (see Platform Guides below). Optional cleanup: rename or delete the root stub.

2. **Heavy notebook-only dependencies bloat every cloud build.**
   `jupyter` + `ipykernel` are installed on every platform build (~2–4 minutes extra) but are never used by the app at runtime.
   → **Mitigation:** move them to a `requirements-dev.txt` (or delete), leaving `requirements.txt` runtime-only. README lines 91/281 also still reference `openpyxl`, which was removed in Phase 9.0.4 — update the docs.

3. **Pin the platform Python runtime to 3.12 or 3.13.**
   `shap>=0.52.0` pulls `numba 0.65.1` → `llvmlite` (compiled wheels). Guaranteed prebuilt wheels exist for Python 3.11–3.13 on all three platforms; do not select 3.14/3.15 unless you accept source-build risk.
   → **Mitigation:** Streamlit Cloud `Advanced settings → Python version`; Render env `PYTHON_VERSION`; Railway default (3.13).

4. **Duplicate export filenames across pages.**
   AI Prediction Lab and Business Recommendation Engine both emit `customer_churn_executive_report.pdf` / `.pptx`. Harmless (separate pages), but could confuse users; consider per-page prefixes.
   → **Mitigation:** optional; prefix filenames with page name (e.g. `prediction_lab_report.pdf`).

5. **No `.streamlit/config.toml` committed.**
   The app relies on platform defaults. Works, but a committed config would centralize the port, server address, headless mode, and usage-stats privacy for all three platforms.
   → **Mitigation:** optional; add `.streamlit/config.toml` with `server.headless=true` and `browser.gatherUsageStats=false`.

---

## ❌ Blocking Items

None. The application boots, renders all pages, and produces every export with zero errors.

---

## 🖥️ Platform Compatibility Guides

### 1. Streamlit Community Cloud (recommended)

| Setting | Value |
|---|---|
| **Repo** | GitHub `abhinav7830tech/CustomerChurnPrediction` |
| **Main file path** | `dashboard/app.py` ← **must set explicitly** (root `app.py` is auto-detected otherwise) |
| **Dependencies** | auto-installed from `requirements.txt` |
| **Python version** | 3.12 or 3.13 (Advanced settings) |
| **System packages** | none required (pure-Python export libs) |
| **Data/Models** | already committed — no extra config |

### 2. Render (Web Service)

| Setting | Value |
|---|---|
| **Build command** | `pip install -r requirements.txt` |
| **Start command** | `streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port $PORT` |
| **Env** | `PYTHON_VERSION=3.13` (or 3.12) |
| **Instance type** | Starter or higher recommended (Free tier 512 MB is sufficient for 7,043-row dataset; watch cold-start time from XGBoost + SHAP import) |
| **Health check** | Streamlit serves `/` — use the app root path |

### 3. Railway

| Setting | Value |
|---|---|
| **Start command** | `streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port $PORT` |
| **Python** | Railway default (3.13) or `PYTHON_VERSION=3.12` |
| **Deploy mode** | single service, no DB needed |

---

## 🔬 Smoke-Test Evidence

- Server launched: `streamlit run dashboard/app.py --server.port 8602 --server.headless true`
- Playwright (headless Chromium 151) visited all 6 pages → 0 `pageerror`, 0 console errors (the only 404s were caused by intentionally-wrong test URLs, not the app).
- Export buttons clicked through Playwright's `expect_download`; every file saved and inspected:
  - `telco_churn_filtered.csv` — CSV, 970,164 bytes
  - `customer_churn_executive_report.pdf` — PDF v1.3, 5 pages (Prediction Lab & Business Rec)
  - `executive_dashboard_report.pdf` — PDF v1.3, 3 pages
  - `explainable_ai_report.pdf` — PDF v1.3, 2 pages
  - `customer_churn_executive_report.pptx` — Microsoft OOXML (valid zip container)
- Server log scanned post-test: no Tracebacks, no Exceptions.

---

## 📋 Recommended Pre-Launch Checklist

- [ ] Set `dashboard/app.py` as the entry point on Streamlit Cloud (or rename root `app.py`).
- [ ] Trim `jupyter`/`ipykernel` from `requirements.txt` into `requirements-dev.txt`.
- [ ] Pin cloud Python to **3.12 / 3.13**.
- [ ] Refresh README (lines 91 & 281) — remove stale `openpyxl`; document deployment commands.
- [ ] (Optional) Commit `.streamlit/config.toml`.
- [ ] Push to GitHub and deploy once; verify all 6 pages + one export per page on the live URL.
