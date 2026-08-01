"""
theme.py — Central design system for the Customer Churn Analytics Platform.

Single source of truth for the entire presentation layer:
  · design tokens (colors, typography, spacing, radii, shadows)
  · the shared stylesheet (`theme.css`, generated from every page's base CSS)
  · reusable HTML components (KPI cards, section headers, badges, alerts)
  · the shared Plotly dark template and chart helpers

Consumed by every page. No business, ML, or SHAP logic lives here.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st
import plotly.graph_objects as go

_CSS_PATH = Path(__file__).with_name("theme.css")

# ═══════════════════════════════════════════════════════════════════════════════
# DESIGN TOKENS
# ═══════════════════════════════════════════════════════════════════════════════

COLORS = {
    "bg": "#0F3040",
    "surface": "#163949",
    "card": "#234556",
    "card_bottom": "#1f3d4d",
    "plot": "#0B2A38",
    "text": "#F4F2EE",
    "sub": "#D6D8D8",
    "gold": "#C8A96B",
    "gold_dark": "#b09055",
    "gold_bright": "#d4b678",
    "sage": "#8FA28A",
    "teal": "#9BCEC1",
    "red": "#D97C7C",
    "red_bright": "#E0635A",
    "blue": "#6EA8FE",
    "green": "#5FCE8B",
    "emerald": "#3FD6C0",
    "purple": "#A78BFA",
    "border": "rgba(255,255,255,0.08)",
    "border_strong": "rgba(255,255,255,0.12)",
    "border_gold": "rgba(200,169,107,0.35)",
    "grid": "rgba(255,255,255,0.05)",
}

# Per-metric accent tones for KPI cards (kept in sync with theme.css).
KPI_TONES = {
    "customers": COLORS["blue"],
    "revenue": COLORS["green"],
    "retention": COLORS["emerald"],
    "churn": COLORS["red_bright"],
    "accuracy": COLORS["purple"],
    "health": COLORS["gold"],
}

# Mirrors the `:root` block in theme.css so Python components and the
# stylesheet always stay in sync.
CSS_VARS = COLORS

FONT = "Inter, -apple-system, BlinkMacSystemFont, sans-serif"

TYPOGRAPHY = {
    "hero": "2.75rem",
    "hero_laptop": "2.3rem",
    "hero_desktop": "3rem",
    "hero_mobile": "1.7rem",
    "kicker": "0.72rem",
    "section_title": "1.55rem",
    "card_title": "0.85rem",
    "body": "0.92rem",
    "caption": "0.8rem",
    "meta": "0.72rem",
}

SPACING = {
    "section": "2.75rem 0 1.25rem",
    "page_header": "2.25rem",
    "card_padding": "1.6rem",
    "block_pad": "1.75rem 3rem 2.25rem",
    "grid_gap": "1.1rem",
}

RADIUS = {"outer": "20px", "inner": "14px", "pill": "100px"}

SHADOW = {
    "card": "0 2px 12px rgba(0,0,0,0.18)",
    "hover": "0 14px 32px rgba(0,0,0,0.32)",
}

TRANSITION = "all 0.25s ease"

RISK_COLORS = {
    "Low": COLORS["sage"],
    "Medium": COLORS["gold"],
    "High": COLORS["red"],
}

RISK_PILL_COLORS = {
    "Low Risk": COLORS["sage"],
    "Medium Risk": COLORS["gold"],
    "High Risk": COLORS["red"],
}

VERDICT_COLORS = {
    "Likely to Stay": COLORS["sage"],
    "Likely to Churn": COLORS["red"],
}

SEVERITY_COLORS = {
    "Critical": COLORS["red"],
    "Warning": COLORS["gold"],
    "Information": COLORS["teal"],
}

STATUS_COLORS = {
    "Good": COLORS["sage"],
    "At Risk": COLORS["red"],
    "Opportunity": COLORS["gold"],
    "Stable": COLORS["teal"],
}

CHURN_COLORS = [COLORS["sage"], COLORS["gold"], COLORS["teal"], COLORS["sub"]]

# Default trace sequence for charts that rely on Plotly's colorway.
PALETTE_SEQUENCE = [
    COLORS["sage"],
    COLORS["gold"],
    COLORS["teal"],
    COLORS["blue"],
    COLORS["purple"],
    COLORS["green"],
    COLORS["emerald"],
    COLORS["red"],
    COLORS["sub"],
]

# ═══════════════════════════════════════════════════════════════════════════════
# SHARED STYLESHEET
# ═══════════════════════════════════════════════════════════════════════════════

BASE_CSS = _CSS_PATH.read_text(encoding="utf-8")


def inject_css(extra_css: str = "") -> None:
    """Inject the shared stylesheet, optionally followed by page-specific CSS."""
    st.markdown(f"<style>{BASE_CSS}\n{extra_css}</style>", unsafe_allow_html=True)


_KPI_COUNTER_JS = """
<script>
setTimeout(function() {
    var els = document.querySelectorAll('.kpi-value[data-value]');
    els.forEach(function(el) {
        var target = parseFloat(el.getAttribute('data-value'));
        if (isNaN(target)) return;
        var fmt = el.getAttribute('data-format') || 'number';
        var sfx = el.getAttribute('data-suffix') || '';
        var dur = 800;
        var start = null;
        function tick(ts) {
            if (!start) start = ts;
            var p = Math.min((ts - start) / dur, 1);
            var e = 1 - Math.pow(1 - p, 3);
            var v = e * target;
            if (fmt === 'percent') el.textContent = v.toFixed(1) + '%';
            else if (fmt === 'currency') el.textContent = '$' + v.toFixed(2);
            else if (fmt === 'suffix') el.textContent = Math.round(v) + sfx;
            else el.textContent = Math.round(v).toLocaleString();
            if (p < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    });
}, 150);
</script>
"""


def inject_kpi_counter() -> None:
    """Inject the count-up animation script for KPI cards."""
    st.markdown(_KPI_COUNTER_JS, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# REUSABLE HTML COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════════


def kpi_card(
    title: str,
    value: str,
    subtext: str = "",
    cls: str = "",
    accent: bool = False,
    delay: float | None = None,
    data_value: float | None = None,
    data_format: str = "number",
    data_suffix: str = "",
    icon: str = "",
    tone: str = "",
) -> str:
    """HTML for a KPI metric card (optionally animated + count-up).

    `icon` renders a small glyph in the top-right corner; `tone` selects a
    per-metric accent color (blue/green/emerald/red/purple/gold) used for the
    card's accent border and glow.
    """
    val_class = "kpi-value"
    if accent:
        val_class += " accent"
    if cls:
        val_class += f" {cls}"
    card_class = "kpi-card"
    if tone:
        card_class += f" kpi-tone-{tone}"
    style = f' style="animation-delay:{delay}s"' if delay is not None else ""
    data_attrs = ""
    if data_value is not None:
        data_attrs = (
            f' data-value="{data_value}" data-format="{data_format}"'
            f' data-suffix="{data_suffix}"'
        )
    icon_html = f'<div class="kpi-icon">{icon}</div>' if icon else ""
    subtext_html = f'<div class="kpi-subtext">{subtext}</div>' if subtext else ""
    return (
        f'<div class="{card_class}"{style}>'
        f"{icon_html}"
        f'<div class="kpi-label">{title}</div>'
        f'<div class="{val_class}"{data_attrs}>{value}</div>'
        f"{subtext_html}"
        f"</div>"
    )


def section_head(num: str, icon: str, title: str, sub: str) -> str:
    """HTML for a numbered section header."""
    return (
        f'<div class="section-head">'
        f'<span class="sec-num">{num}</span>'
        f'<span class="sec-icon">{icon}</span>'
        f'<div><div class="sec-title">{title}</div>'
        f'<div class="sec-sub">{sub}</div></div>'
        f"</div>"
    )


def pill(text: str, color: str, cls: str = "") -> str:
    """HTML for a pill / status badge."""
    class_attr = f' class="{cls}"' if cls else ""
    return f'<span{class_attr} style="background:{color}">{text}</span>'


def alert_card(severity: str, icon: str, title: str, text: str, color: str) -> str:
    """HTML for an alert card keyed by severity."""
    return (
        f'<div class="alert-card" style="border-left-color:{color};">'
        f'<div class="alert-icon">{icon}</div>'
        f"<div>"
        f'<span class="alert-pill" style="background:{color}">{severity}</span>'
        f'<div class="alert-title">{title}</div>'
        f'<div class="alert-text">{text}</div>'
        f"</div></div>"
    )


def info_card(icon: str, title: str, text: str, delay: float | None = None) -> str:
    """HTML for an insight card."""
    style = f' style="animation-delay:{delay}s"' if delay is not None else ""
    return (
        f'<div class="insight-card"{style}>'
        f'<div class="insight-icon">{icon}</div>'
        f'<div class="insight-title">{title}</div>'
        f'<div class="insight-text">{text}</div>'
        f"</div>"
    )


def note(text: str) -> str:
    """HTML for a manager-note / executive-summary box."""
    return f'<div class="notes-box">{text}</div>'


def figure_container(title: str, desc: str) -> None:
    """Render the title + description above a Plotly figure."""
    st.markdown(
        f'<div class="chart-title">{title}</div>'
        f'<div class="chart-desc">{desc}</div>',
        unsafe_allow_html=True,
    )


def chart_card(title: str, desc: str, fig: go.Figure) -> None:
    """Render a Plotly figure inside a polished rounded card container."""
    with st.container(border=True):
        figure_container(title, desc)
        st.plotly_chart(fig, width="stretch")


def page_header(
    title: str,
    kicker: str = "",
    subtitle: str = "",
    rule: bool = True,
    back_link: bool = True,
) -> None:
    """Render a hero page header (kicker + title + subtitle + gold rule)."""
    html = ""
    if back_link:
        html += '<a class="back-link" href="/" target="_self">← Back to Dashboard</a>'
    html += '<div class="page-header">'
    if kicker:
        html += f'<div class="page-kicker">{kicker}</div>'
    html += f'<div class="page-title">{title}</div>'
    if subtitle:
        html += f'<div class="page-subtitle">{subtitle}</div>'
    if rule:
        html += '<div class="page-rule"></div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def section_header(title: str, sub: str = "", num: str | None = None, icon: str = "") -> None:
    """Render a section header.

    Pass `num` (and optionally `icon`) for the numbered badge variant;
    otherwise a plain `.section-header` is rendered.
    """
    if num is not None:
        num_html = f'<span class="sec-num">{num}</span>'
        icon_html = f'<span class="sec-icon">{icon}</span>' if icon else ""
        sub_html = f'<div class="sec-sub">{sub}</div>' if sub else ""
        st.markdown(
            f'<div class="section-head">{num_html}{icon_html}'
            f'<div><div class="sec-title">{title}</div>{sub_html}</div></div>',
            unsafe_allow_html=True,
        )
        return
    sub_html = f'<div class="section-sub">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="section-header">{title}</div>{sub_html}',
        unsafe_allow_html=True,
    )


def metric_badge(text: str, color: str = "", cls: str = "") -> str:
    """HTML for a light metric pill badge (bordered, optional tint)."""
    style = f' style="background:{color};"' if color else ""
    class_attr = f' {cls}' if cls else ""
    return f'<span class="metric-badge{class_attr}"{style}>{text}</span>'


def status_badge(text: str, color: str, cls: str = "") -> str:
    """HTML for a solid status badge with a leading dot."""
    class_attr = f' {cls}' if cls else ""
    return (
        f'<span class="status-badge{class_attr}" style="background:{color};">'
        f'<span class="badge-dot"></span>{text}</span>'
    )


def download_button(
    label: str,
    data,
    file_name: str,
    mime: str,
    key: str | None = None,
) -> bool:
    """Consistent gold download button (full width) for CSV/PDF/TXT/PPTX exports.

    Returns whether the button was just clicked so callers can show a toast.
    """
    kwargs = {
        "label": label,
        "data": data,
        "file_name": file_name,
        "mime": mime,
        "width": "stretch",
    }
    if key is not None:
        kwargs["key"] = key
    return bool(st.download_button(**kwargs))


# ═══════════════════════════════════════════════════════════════════════════════
# SHARED PLOTLY THEME
# ═══════════════════════════════════════════════════════════════════════════════


def dark_template() -> go.layout.Template:
    """Corporate dark theme for all Plotly charts."""
    return go.layout.Template(
        layout=dict(
            font=dict(family=FONT, size=13, color=COLORS["sub"]),
            title=dict(
                font=dict(size=18, color=COLORS["text"], family=FONT),
                x=0.5,
                xanchor="center",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor=COLORS["plot"],
            height=420,
            autosize=True,
            transition=dict(duration=350, easing="cubic-in-out"),
            margin=dict(l=64, r=42, t=88, b=64),
            xaxis=dict(
                gridcolor="rgba(255,255,255,0.06)",
                zerolinecolor="rgba(255,255,255,0.10)",
                linecolor="rgba(255,255,255,0.12)",
                tickfont=dict(size=12, color=COLORS["sub"]),
                title=dict(font=dict(size=13, color=COLORS["sub"])),
                ticks="outside",
            ),
            yaxis=dict(
                gridcolor="rgba(255,255,255,0.06)",
                zerolinecolor="rgba(255,255,255,0.10)",
                linecolor="rgba(255,255,255,0.12)",
                tickfont=dict(size=12, color=COLORS["sub"]),
                title=dict(font=dict(size=13, color=COLORS["sub"])),
            ),
            legend=dict(
                font=dict(size=12, color=COLORS["sub"]),
                bgcolor="rgba(0,0,0,0)",
                orientation="h",
                x=0.5,
                xanchor="center",
                y=1.14,
            ),
            hoverlabel=dict(
                bgcolor=COLORS["surface"],
                font_color=COLORS["text"],
                font_size=13,
                font_family=FONT,
                bordercolor=COLORS["border_strong"],
            ),
            colorway=PALETTE_SEQUENCE,
        )
    )


TEMPLATE = dark_template()


def apply(fig: go.Figure) -> go.Figure:
    """Apply the shared dark template to a figure."""
    return fig.update_layout(template=TEMPLATE)


def gauge_figure(
    value: float,
    color: str,
    title: str,
    height: int = 280,
    number_size: int = 34,
    title_size: int = 15,
) -> go.Figure:
    """Plotly gauge for a single 0-100 business score."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"font": {"color": COLORS["text"], "size": number_size}},
        title={"text": title, "font": {"color": COLORS["gold"], "size": title_size}},
        gauge={
            "shape": "angular",
            "axis": {
                "range": [0, 100],
                "tickcolor": COLORS["sub"],
                "tickfont": {"color": COLORS["sub"], "size": 10},
            },
            "bar": {"color": color, "thickness": 0.32},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40], "color": "rgba(217,124,124,0.16)"},
                {"range": [40, 70], "color": "rgba(200,169,107,0.20)"},
                {"range": [70, 100], "color": "rgba(143,162,138,0.24)"},
            ],
        },
    ))
    fig.update_layout(
        height=height,
        margin=dict(t=58, b=12, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": FONT},
    )
    return fig
