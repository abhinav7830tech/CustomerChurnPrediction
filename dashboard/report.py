"""
report.py — Premium business-style PDF report generation.

Renders a single-customer executive report in the visual language used by
top-tier strategy and consulting firms (Deloitte, PwC, EY, McKinsey, BCG):
a dedicated cover page, executive summary, prediction overview, customer
profile, risk assessment, KPI summary, business recommendations, conclusion,
and page-numbered footers.

Presentation layer only. Reads the prediction result and the business
analysis produced by the recommendation engine; it never recomputes or
alters any prediction, SHAP, or business metric. No dashboard logic is
touched — this module only formats values for print.
"""

from __future__ import annotations

import re
from datetime import datetime

from fpdf import FPDF
from fpdf.enums import XPos, YPos

try:
    import prediction
except ModuleNotFoundError:  # pragma: no cover
    import os
    import sys

    _dashboard_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _dashboard_dir not in sys.path:
        sys.path.insert(0, _dashboard_dir)
    import prediction


# ── Brand palette (matches dashboard/theme.css) ────────────────────────────────

NAVY = (15, 48, 64)
NAVY_DEEP = (10, 38, 50)
SURFACE = (22, 57, 73)
CARD = (35, 69, 86)
GOLD = (200, 169, 107)
GOLD_DARK = (176, 144, 85)
GOLD_BRIGHT = (212, 182, 120)
SAGE = (143, 162, 138)
TEAL = (155, 206, 193)
RED = (224, 99, 90)
TEXT = (30, 40, 45)
BODY = (66, 76, 82)
MUTED = (120, 130, 136)
LIGHT = (243, 244, 244)
LINE = (221, 224, 226)
WHITE = (255, 255, 255)

PAGE_W = 210
PAGE_H = 297
MARGIN = 18
CONTENT_W = PAGE_W - 2 * MARGIN


def _ascii(text) -> str:
    """Strip non-Latin-1 characters for fpdf2's core fonts."""
    return re.sub(r"[^\x00-\x7F]", "", str(text))


def _hex2rgb(hex_color) -> tuple:
    """Convert a '#RRGGBB' hex string into an RGB tuple."""
    hex_color = str(hex_color or "").lstrip("#")
    if len(hex_color) != 6:
        return GOLD
    try:
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return GOLD


def _money(value) -> str:
    return f"${value:,.0f}"


class PremiumReport(FPDF):
    """FPDF subclass with a branded header/footer on every content page."""

    def header(self):
        # Cover page stays clean; every content page gets a slim brand band.
        if self.page_no() <= 1:
            return
        self.set_fill_color(*NAVY)
        self.rect(0, 0, PAGE_W, 12, "F")
        self.set_fill_color(*GOLD)
        self.rect(0, 12, PAGE_W, 1.6, "F")
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(*GOLD_BRIGHT)
        self.set_xy(MARGIN, 3.2)
        self.cell(0, 5, "CUSTOMER CHURN ANALYTICS PLATFORM", new_x=XPos.LMARGIN, new_y=YPos.TOP)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(200, 210, 214)
        self.set_y(3.4)
        self.set_x(-MARGIN - 40)
        self.cell(40, 5, "Executive Report", align="R")

    def footer(self):
        if self.page_no() <= 1:
            return
        self.set_y(-16)
        self.set_draw_color(*LINE)
        self.set_line_width(0.3)
        self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*MUTED)
        self.set_y(-13.5)
        self.set_x(MARGIN)
        self.cell(0, 5, "Prepared by the Customer Churn Analytics Platform  |  Confidential")
        self.set_x(-MARGIN)
        self.cell(0, 5, f"Page {self.page_no()} of {{nb}}", align="R")


# ── Drawing helpers (bound to a report instance) ───────────────────────────────


def _set_font(pdf: FPDF, style: str, size: float) -> None:
    pdf.set_font("Helvetica", style, size)


def _section_title(pdf: FPDF, number: str, title: str, subtitle: str = "") -> None:
    """Numbered section heading with a gold number chip and thin rule."""
    pdf.ln(3)
    if pdf.get_y() > PAGE_H - 45:
        pdf.add_page()
    chip_w = 10
    y0 = pdf.get_y()
    pdf.set_fill_color(*GOLD)
    pdf.rect(MARGIN, y0, chip_w, chip_w, style="F")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*NAVY)
    pdf.set_xy(MARGIN, y0 + 1.6)
    pdf.cell(chip_w, chip_w - 3, number, align="C")
    pdf.set_xy(MARGIN + chip_w + 4, y0 + 0.8)
    pdf.set_font("Helvetica", "B", 13.5)
    pdf.set_text_color(*NAVY)
    pdf.cell(CONTENT_W - chip_w - 4, 8.5, _ascii(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if subtitle:
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(CONTENT_W, 4, _ascii(subtitle))
    pdf.ln(2)
    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(0.5)
    pdf.line(MARGIN, pdf.get_y(), MARGIN + CONTENT_W, pdf.get_y())
    pdf.ln(3)


def _label_value(pdf: FPDF, label: str, value: str, label_w: float = 78) -> None:
    """A single bold-label / light-value row."""
    if pdf.get_y() > PAGE_H - 22:
        pdf.add_page()
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*TEXT)
    pdf.cell(label_w, 6, _ascii(label), new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*BODY)
    pdf.cell(CONTENT_W - label_w, 6, _ascii(value), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _bullets(pdf: FPDF, items: list, bullet: str = "-", size: float = 9,
             gap: float = 1.6) -> None:
    for item in items:
        if pdf.get_y() > PAGE_H - 24:
            pdf.add_page()
        pdf.set_font("Helvetica", "", size)
        pdf.set_text_color(*BODY)
        pdf.set_x(MARGIN + 4)
        pdf.cell(6, 5, bullet, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.multi_cell(CONTENT_W - 10, 5, _ascii(item), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(gap)


def _probability_meter(pdf: FPDF, prob_pct: float, risk_color, label: str) -> None:
    """A labeled probability bar with a risk-colored fill."""
    if pdf.get_y() > PAGE_H - 34:
        pdf.add_page()
    y0 = pdf.get_y()
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*NAVY)
    pdf.set_x(MARGIN)
    pdf.cell(0, 5, f"CHURN PROBABILITY   {prob_pct:.1f}%   -   {_ascii(label)}")
    pdf.set_y(y0 + 6.5)
    bar_w = CONTENT_W
    bar_h = 8
    pdf.set_fill_color(*LIGHT)
    pdf.rect(MARGIN, pdf.get_y(), bar_w, bar_h, "F")
    pdf.set_draw_color(*LINE)
    pdf.rect(MARGIN, pdf.get_y(), bar_w, bar_h, "D")
    fill = _hex2rgb(risk_color) if risk_color else GOLD
    pdf.set_fill_color(*fill)
    pdf.rect(MARGIN, pdf.get_y(), max(bar_w * prob_pct / 100.0, 2.2), bar_h, "F")
    pdf.set_y(pdf.get_y() + bar_h + 4)


def _factor_bar(pdf: FPDF, feature: str, value: str, contribution: float,
                max_abs: float) -> None:
    """A horizontal SHAP contribution bar, green for risk-reducing, red for risk-raising."""
    if pdf.get_y() > PAGE_H - 28:
        pdf.add_page()
    mag = abs(contribution) / (max_abs or 1.0)
    bar_w = CONTENT_W * 0.52
    bar_h = 7
    y = pdf.get_y()
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*TEXT)
    pdf.cell(CONTENT_W * 0.34, bar_h, _ascii(f"{feature}  ({value})"),
             new_x=XPos.RIGHT, new_y=YPos.TOP)
    left = MARGIN + CONTENT_W * 0.34
    pdf.set_fill_color(*LIGHT)
    pdf.rect(left, y, bar_w, bar_h, "F")
    color = RED if contribution >= 0 else SAGE
    pdf.set_fill_color(*color)
    fill_w = bar_w * mag
    if contribution >= 0:
        pdf.rect(left, y, fill_w, bar_h, "F")
    else:
        pdf.rect(left + bar_w - fill_w, y, fill_w, bar_h, "F")
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*color)
    pdf.set_x(left + bar_w + 4)
    pdf.cell(0, bar_h, f"{contribution:+.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2.2)


def _table(pdf: FPDF, rows: list, col_w: list, header: list | None = None) -> None:
    """A clean striped table with an optional gold header row."""
    if pdf.get_y() > PAGE_H - 40:
        pdf.add_page()
    row_h = 6.6
    pad = 1.8
    if header:
        pdf.set_fill_color(*NAVY)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 8.5)
        x0 = MARGIN
        for i, text in enumerate(header):
            pdf.set_xy(x0 + sum(col_w[:i]), pdf.get_y(), 0, 0)
            pdf.rect(x0 + sum(col_w[:i]), pdf.get_y(), col_w[i], row_h, "F")
            pdf.set_xy(x0 + sum(col_w[:i]) + pad, pdf.get_y() + 1.2)
            pdf.cell(col_w[i] - 2 * pad, row_h - 2, _ascii(text))
        pdf.set_y(pdf.get_y() + row_h)
        pdf.set_text_color(*BODY)
    for r_i, row in enumerate(rows):
        if pdf.get_y() > PAGE_H - 24:
            pdf.add_page()
        pdf.set_fill_color(*(LIGHT if r_i % 2 == 0 else WHITE))
        pdf.set_font("Helvetica", "", 8.6)
        y = pdf.get_y()
        for i, cell in enumerate(row):
            pdf.rect(MARGIN + sum(col_w[:i]), y, col_w[i], row_h, "F")
            pdf.set_xy(MARGIN + sum(col_w[:i]) + pad, y + 1.4)
            bold = i == 0
            pdf.set_font("Helvetica", "B" if bold else "", 8.6)
            pdf.set_text_color(*(TEXT if bold else BODY))
            pdf.cell(col_w[i] - 2 * pad, row_h - 2, _ascii(cell))
        pdf.set_y(y + row_h)
    pdf.ln(3)


# ── Report content ─────────────────────────────────────────────────────────────


def _cover(pdf: FPDF, result: dict, a: dict, info: dict) -> None:
    """A dedicated cover page in the house style of the big consulting firms."""
    pdf.add_page()
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, PAGE_W, PAGE_H, "F")
    pdf.set_fill_color(*GOLD)
    pdf.rect(0, 0, PAGE_W, 3.4, "F")

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*GOLD_BRIGHT)
    pdf.set_y(38)
    pdf.set_x(MARGIN)
    pdf.cell(0, 6, "CUSTOMER CHURN ANALYTICS PLATFORM")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*SAGE)
    pdf.set_x(MARGIN)
    pdf.cell(0, 6, "EXECUTIVE CUSTOMER RETENTION REPORT")

    pdf.ln(14)
    pdf.set_font("Helvetica", "B", 31)
    pdf.set_text_color(*WHITE)
    pdf.set_x(MARGIN)
    pdf.multi_cell(CONTENT_W - 20, 13, _ascii(result.get("label", "Customer Retention")),
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(2)
    pdf.set_font("Helvetica", "", 13.5)
    pdf.set_text_color(210, 218, 222)
    pdf.set_x(MARGIN)
    pdf.multi_cell(CONTENT_W - 20, 7,
                   f"Churn probability of {a.get('prob', 0.0):.1f}%  -  "
                   f"{a.get('risk', '')}  -  {a.get('segment', '')} segment",
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(0.7)
    pdf.line(MARGIN, pdf.get_y() + 2, MARGIN + 60, pdf.get_y() + 2)

    pdf.ln(26)
    now = datetime.now()
    meta = [
        ("Prepared for", "College Project Evaluation"),
        ("Prepared by", "Abhinav Agnihotri"),
        ("Date", now.strftime("%B %d, %Y")),
        ("Generated", now.strftime("%I:%M %p")),
        ("Version", "1.0  -  Executive Report"),
        ("Deployed model", info.get("label", "XGBoost")),
    ]
    for label, value in meta:
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*GOLD_BRIGHT)
        pdf.set_x(MARGIN)
        pdf.cell(44, 6.4, _ascii(label))
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*WHITE)
        pdf.cell(0, 6.4, _ascii(value), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(160, 178, 186)
    pdf.set_xy(MARGIN, PAGE_H - 24)
    pdf.multi_cell(CONTENT_W, 4,
                   "Prepared with predictive analytics on the IBM Telco Customer "
                   "Churn dataset. Financial figures that are projected are "
                   "modeled estimates. This report is for academic evaluation "
                   "and decision-support purposes.",
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _executive_summary(pdf: FPDF, result: dict, a: dict) -> None:
    _section_title(pdf, "01", "Executive Summary",
                   "The business picture for this customer at a glance")
    risk = a.get("risk", result.get("risk_label", "Medium Risk"))
    prob = a.get("prob", result.get("probability_pct", 0.0))
    if prob >= 70:
        stance = "at immediate risk of churn and requires urgent retention action"
    elif prob >= 40:
        stance = "exposed to a meaningful churn risk that warrants proactive outreach"
    else:
        stance = "in a stable, low-risk position with strong retention upside"

    intro = (
        f"This customer is {stance}. The deployed model estimates a {prob:.1f}% "
        f"churn probability ({risk}), with an associated estimated annual revenue "
        f"at risk of {_money(a.get('revenue_at_risk', 0))} and a 24-month "
        f"customer-lifetime value estimate of {_money(a.get('clv_estimate', 0))}."
    )
    if a.get("top_driver"):
        top = a["top_driver"]
        intro += (
            f" The strongest churn driver identified is {top['feature']} "
            f"({top['value']})."
        )
    pdf.set_font("Helvetica", "", 9.3)
    pdf.set_text_color(*BODY)
    pdf.multi_cell(CONTENT_W, 5.4, _ascii(intro), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2.5)

    pdf.set_fill_color(*LIGHT)
    pdf.rect(MARGIN, pdf.get_y(), CONTENT_W, 4, "F")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*GOLD_DARK)
    pdf.set_x(MARGIN + 3)
    pdf.cell(0, 4, "KEY HIGHLIGHTS")
    pdf.set_y(pdf.get_y() + 4)

    highlights = [
        f"Prediction: {result.get('label', 'Likely to Stay')} "
        f"({prob:.1f}% probability)",
        f"Risk classification: {risk}  |  Priority: {a.get('priority', 'Standard')}",
        f"Segment: {a.get('segment', 'Standard')}",
        f"Estimated annual revenue at risk: {_money(a.get('revenue_at_risk', 0))}",
        f"Estimated net value of recommended plan: "
        f"{_money(a.get('net_benefit', 0))}  ({a.get('roi_pct', 0):.0f}% ROI)",
    ]
    for h in highlights:
        pdf.set_font("Helvetica", "", 8.8)
        pdf.set_text_color(*BODY)
        pdf.set_x(MARGIN + 4)
        pdf.cell(5, 5, "-", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.multi_cell(CONTENT_W - 9, 5, _ascii(h), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(0.6)


def _prediction_overview(pdf: FPDF, result: dict, a: dict, info: dict) -> None:
    _section_title(pdf, "02", "Prediction Overview",
                   "The model verdict and the confidence behind it")
    verdict = result.get("label", "Likely to Stay")
    prob = a.get("prob", result.get("probability_pct", 0.0))
    risk_color = result.get("risk_color") or a.get("risk_color")

    # Verdict banner
    pdf.set_fill_color(*(RED if "churn" in verdict.lower() else SAGE))
    pdf.rect(MARGIN, pdf.get_y(), CONTENT_W, 15, "F")
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(MARGIN + 5, pdf.get_y() + 3.4)
    pdf.cell(0, 7, f"VERDICT:  {_ascii(verdict)}")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_xy(MARGIN + 5, pdf.get_y() + 8.2)
    pdf.cell(0, 5, f"Churn probability {prob:.1f}%  -  {_ascii(a.get('risk', ''))}")
    pdf.set_y(pdf.get_y() + 15 + 3)

    _probability_meter(pdf, prob, risk_color, a.get("risk", ""))

    _label_value(pdf, "Risk level", a.get("risk", ""))
    _label_value(pdf, "Confidence", a.get("confidence", "Moderate"))
    _label_value(pdf, "Model", info.get("label", "XGBoost"))
    _label_value(pdf, "Model accuracy", f"{info.get('accuracy', 0):.1f}%")
    _label_value(pdf, "Model AUC", f"{info.get('auc', 0):.4f}")
    _label_value(pdf, "Priority", a.get("priority", "Standard"))
    _label_value(pdf, "Segment", a.get("segment", "Standard"))


def _customer_details(pdf: FPDF, inputs: dict) -> None:
    _section_title(pdf, "03", "Customer Details",
                   "The full profile used to generate this prediction")
    pairs = [
        (prediction.FEATURE_LABELS.get(feat, feat),
         prediction.display_value(feat, inputs[feat]))
        for feat in prediction.FEATURE_NAMES
    ]
    # Two-column label/value grid, 4 rows per line.
    col_w = CONTENT_W / 2.0
    for i in range(0, len(pairs), 4):
        if pdf.get_y() > PAGE_H - 40:
            pdf.add_page()
        for j in range(4):
            if i + j >= len(pairs):
                break
            label, value = pairs[i + j]
            col = j // 2
            x = MARGIN + col * col_w
            row_y = pdf.get_y() + (j % 2) * 8.4
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*MUTED)
            pdf.set_xy(x, row_y)
            pdf.cell(col_w - 6, 4, _ascii(label.upper()))
            pdf.set_font("Helvetica", "", 9.3)
            pdf.set_text_color(*TEXT)
            pdf.set_xy(x, row_y + 3.6)
            pdf.cell(col_w - 6, 5, _ascii(value))
        pdf.set_y(pdf.get_y() + 16.8)
    pdf.ln(2)


def _risk_assessment(pdf: FPDF, result: dict, a: dict) -> None:
    _section_title(pdf, "04", "Risk Assessment",
                   "How severe the churn risk is and which factors drive it")
    prob = a.get("prob", result.get("probability_pct", 0.0))
    risk_color = result.get("risk_color") or a.get("risk_color")

    risk_map = {
        "Low Risk": ("LOW", SAGE,
                     "The customer is currently stable. Monitor engagement and "
                     "offer value-adding services to keep the relationship strong."),
        "Medium Risk": ("MEDIUM", GOLD_DARK,
                        "A material share of churn pressure exists. Proactive "
                        "retention outreach is recommended before the risk grows."),
        "High Risk": ("HIGH", RED,
                      "The customer shows strong churn signals. Immediate, "
                      "personalized retention action is required."),
    }
    band = risk_map.get(a.get("risk", ""), risk_map["Medium Risk"])
    label, color, blurb = band

    badge_w = 34
    pdf.set_fill_color(*color)
    pdf.rect(MARGIN, pdf.get_y(), badge_w, 12, "F")
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(MARGIN, pdf.get_y() + 2.6)
    pdf.cell(badge_w, 7, label, align="C")
    pdf.set_xy(MARGIN + badge_w + 5, pdf.get_y() - 12)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*BODY)
    pdf.multi_cell(CONTENT_W - badge_w - 5, 4.6, _ascii(blurb),
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    _probability_meter(pdf, prob, risk_color, a.get("risk", ""))

    factors = result.get("factors") or []
    if factors:
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(*NAVY)
        pdf.set_x(MARGIN)
        pdf.cell(0, 6, "Top Contributing Factors (SHAP values)")
        pdf.ln(6)
        max_abs = max(abs(f["contribution"]) for f in factors)
        for f in factors[:5]:
            _factor_bar(pdf, f["feature"], f["value"], f["contribution"], max_abs)
    else:
        _label_value(pdf, "Contributing factors",
                     "No SHAP factors were available for this prediction")


def _kpi_summary(pdf: FPDF, a: dict, result: dict) -> None:
    _section_title(pdf, "05", "KPI Summary",
                   "The key modeled financial and account metrics")
    rows = [
        ("Churn Probability", f"{a.get('prob', 0.0):.1f}%"),
        ("Prediction", result.get("label", "")),
        ("Risk Level", a.get("risk", "")),
        ("Priority", a.get("priority", "")),
        ("Segment", a.get("segment", "")),
        ("Revenue at Risk (12-mo)", _money(a.get("revenue_at_risk", 0))),
        ("CLV Estimate (24-mo)", _money(a.get("clv_estimate", 0))),
        ("Retention Investment", _money(a.get("retention_cost", 0))),
        ("Modeled Benefit (65%)", _money(a.get("potential_savings", 0))),
        ("Net Expected Value", _money(a.get("net_benefit", 0))),
        ("Estimated ROI", f"{a.get('roi_pct', 0):.0f}%"),
        ("Account Confidence", a.get("confidence", "")),
    ]
    _table(pdf, rows, col_w=[70, CONTENT_W - 70])

    scorecard = a.get("scorecard") or []
    if scorecard:
        pdf.ln(1)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(*NAVY)
        pdf.set_x(MARGIN)
        pdf.cell(0, 6, "Business Scorecard (0 - 100)")
        pdf.ln(6)
        _table(pdf, [[s[0], f"{s[1]:.0f} / 100"] for s in scorecard],
               col_w=[70, CONTENT_W - 70])


def _business_recommendations(pdf: FPDF, a: dict) -> None:
    _section_title(pdf, "06", "Business Recommendations",
                   "Prioritized next steps with the business reason for each")
    actions = a.get("actions") or []
    if not actions:
        _label_value(pdf, "No recommendations", "Available for this account")
        return
    for idx, action in enumerate(actions, start=1):
        if pdf.get_y() > PAGE_H - 42:
            pdf.add_page()
        y0 = pdf.get_y()
        pdf.set_fill_color(*NAVY)
        pdf.rect(MARGIN, y0, CONTENT_W, 0.8, "F")
        pdf.set_y(y0 + 4)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*NAVY)
        pdf.set_x(MARGIN)
        pdf.cell(12, 6, f"{idx}.")
        pdf.cell(CONTENT_W - 12, 6, _ascii(action.get("title", "")))
        pdf.ln(6)
        pdf.set_font("Helvetica", "", 8.8)
        pdf.set_text_color(*BODY)
        pdf.set_x(MARGIN + 12)
        reason = action.get("reason", "")
        impact = action.get("impact", "")
        cost = action.get("cost", "")
        pdf.multi_cell(CONTENT_W - 12, 4.6,
                       _ascii(f"Business reason: {reason}.  Impact: {impact}.  "
                              f"Cost: {cost}."),
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)


def _conclusion(pdf: FPDF, result: dict, a: dict) -> None:
    _section_title(pdf, "07", "Conclusion",
                   "A summary judgment and the recommended next action")
    prob = a.get("prob", result.get("probability_pct", 0.0))
    if prob >= 70:
        judgment = ("immediate retention intervention")
    elif prob >= 40:
        judgment = ("a proactive retention campaign")
    else:
        judgment = ("continued relationship building and growth")

    text = (
        f"In conclusion, this account requires {judgment}. With a {prob:.1f}% "
        f"churn probability and an estimated annual revenue exposure of "
        f"{_money(a.get('revenue_at_risk', 0))}, acting on the recommended plan "
        f"— a {_money(a.get('retention_cost', 0))} "
        f"investment for a modeled benefit of "
        f"{_money(a.get('potential_savings', 0))} and an ROI of "
        f"{a.get('roi_pct', 0):.0f}% - offers a compelling business case. "
        f"The recommended next step is: {a.get('campaign', {}).get('name', '')}."
    )
    pdf.set_font("Helvetica", "", 9.3)
    pdf.set_text_color(*BODY)
    pdf.multi_cell(CONTENT_W, 5.4, _ascii(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*NAVY)
    pdf.set_x(MARGIN)
    pdf.cell(0, 5.5, "ACCOUNT MANAGER NOTES")
    pdf.ln(5.5)
    pdf.set_font("Helvetica", "", 8.8)
    pdf.set_text_color(*BODY)
    pdf.multi_cell(CONTENT_W, 4.8, _ascii(a.get("manager_notes", "")),
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(6)
    pdf.set_draw_color(*LINE)
    pdf.line(MARGIN, pdf.get_y(), MARGIN + 70, pdf.get_y())
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*MUTED)
    pdf.set_x(MARGIN)
    pdf.cell(0, 5, "Authorized by the Customer Churn Analytics Platform",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)


# ── Public entry point ─────────────────────────────────────────────────────────


def resolve_analysis(result: dict, inputs: dict, a: dict | None = None) -> dict:
    """Merge the optional business-analysis dict over values derived from the
    prediction so every report key is populated safely.

    `a` is the analysis produced by the recommendation engine; when a key is
    missing (or `a` is None), a presentation-only value is derived from the
    prediction and customer profile. Never modifies the caller's dict.
    """
    prob = result.get("probability_pct", 0.0)
    risk = result.get("risk_label", "")
    priority = "Urgent" if prob >= 70 else "Standard"
    base = {
        "prob": prob,
        "risk": risk,
        "priority": priority,
        "segment": "Standard",
        "revenue_at_risk": 12.0 * inputs.get("MonthlyCharges", 0) * prob / 100.0,
        "clv_estimate": 24.0 * inputs.get("MonthlyCharges", 0) * (1 - prob / 100.0),
        "retention_cost": 0.0,
        "potential_savings": 0.0,
        "net_benefit": 0.0,
        "roi_pct": 0.0,
        "confidence": "High" if prob >= 70 or prob <= 30 else "Moderate",
        "top_driver": (result.get("factors") or [None])[0],
        "actions": [
            {"icon": _icon, "title": title, "reason": text,
             "impact": "Improve retention", "cost": "Low"}
            for _icon, title, text in (result.get("recommendations") or [])
        ],
        "scorecard": [
            ("Churn Risk", prob),
            ("Retention Health", 100.0 - prob),
        ],
        "campaign": {"name": "Retention follow-up"},
        "manager_notes": (
            f"This customer carries a {prob:.0f}% churn probability ({risk}) and "
            f"warrants {'an' if priority.lower() == 'urgent' else 'a'} "
            f"{priority.lower()} response."
        ),
    }
    if a:
        for key, value in a.items():
            if value is not None:
                base[key] = value
    return base


def build_report(result: dict, inputs: dict, a: dict | None = None) -> bytes:
    """Generate the premium PDF report and return it as bytes.

    `result` is the prediction dict produced by `prediction.predict()` (plus
    `factors`, `model_alias`, and `recommendations`). `inputs` is the raw
    customer form values. `a` is the optional business-analysis dict from the
    recommendation engine; missing keys fall back to values derived from the
    prediction itself, so the report renders everywhere. When a partial dict
    is passed, its values take precedence over the derived fallbacks.
    """
    alias = result.get("model_alias", prediction.DEFAULT_MODEL)
    info = prediction.model_info(alias)
    a = resolve_analysis(result, inputs, a)

    pdf = PremiumReport(format="A4", unit="mm")
    pdf.set_margins(MARGIN, 16, MARGIN)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.alias_nb_pages()

    _cover(pdf, result, a, info)

    _executive_summary(pdf, result, a)
    _prediction_overview(pdf, result, a, info)
    _customer_details(pdf, inputs)
    _risk_assessment(pdf, result, a)
    _kpi_summary(pdf, a, result)
    _business_recommendations(pdf, a)
    _conclusion(pdf, result, a)

    return bytes(pdf.output())
