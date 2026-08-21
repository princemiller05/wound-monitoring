"""
charts.py
---------
All Plotly chart construction lives here so visual styling is
defined once and reused consistently across pages.
"""

import plotly.graph_objects as go
import streamlit as st

PRIMARY = "#1565C0"
ACCENT = "#00ACC1"
SUCCESS = "#16A34A"
WARNING = "#F59E0B"
DANGER = "#DC2626"
INK_SOFT = "#5C7184"

LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#0F2940", size=12),
    margin=dict(l=10, r=10, t=30, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1, font=dict(size=11)),
    hoverlabel=dict(bgcolor="white", font_size=12,
                     font_family="Inter, sans-serif",
                     bordercolor="#E6ECF3"),
)

GRID_STYLE = dict(showgrid=True, gridcolor="#EEF2F7", zeroline=False)


def wound_area_trend(df, unit_label="cm²", unit_col="wound_area_cm2") -> go.Figure:
    """Smooth line chart of wound area over visits."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["visit_date"], y=df[unit_col],
        mode="lines+markers",
        line=dict(color=PRIMARY, width=3, shape="spline"),
        marker=dict(size=8, color=PRIMARY, line=dict(width=2, color="white")),
        fill="tozeroy", fillcolor="rgba(21,101,192,0.08)",
        hovertemplate=f"<b>%{{x}}</b><br>Wound Area: %{{y}} {unit_label}<extra></extra>",
        name="Wound Area",
    ))
    fig.update_layout(**LAYOUT_DEFAULTS, height=320,
                       title=f"Wound Area Trend ({unit_label})")
    fig.update_xaxes(**GRID_STYLE)
    fig.update_yaxes(**GRID_STYLE, title=f"Area ({unit_label})")
    return fig


def tissue_composition(df) -> go.Figure:
    """Stacked bar chart: Granulation / Slough / Necrosis composition."""
    fig = go.Figure()
    for col, name, color in [
        ("granulation_pct", "Granulation", SUCCESS),
        ("slough_pct", "Slough", WARNING),
        ("necrosis_pct", "Necrosis", DANGER),
    ]:
        fig.add_trace(go.Bar(
            x=df["visit_date"], y=df[col], name=name,
            marker_color=color,
            hovertemplate=f"<b>%{{x}}</b><br>{name}: %{{y}}%<extra></extra>",
        ))
    fig.update_layout(**LAYOUT_DEFAULTS, barmode="stack", height=320,
                       title="Tissue Composition (%)")
    fig.update_xaxes(**GRID_STYLE)
    fig.update_yaxes(**GRID_STYLE, title="% of Wound Bed", range=[0, 100])
    return fig


def healing_probability_over_time(df) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["visit_date"], y=df["healing_probability"],
        mode="lines+markers",
        line=dict(color=ACCENT, width=3, shape="spline"),
        marker=dict(size=8, color=ACCENT, line=dict(width=2, color="white")),
        hovertemplate="<b>%{x}</b><br>Healing Probability: %{y}%<extra></extra>",
    ))
    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(22,163,74,0.06)", line_width=0)
    fig.add_hrect(y0=40, y1=70, fillcolor="rgba(245,158,11,0.06)", line_width=0)
    fig.add_hrect(y0=0, y1=40, fillcolor="rgba(220,38,38,0.06)", line_width=0)
    fig.update_layout(**LAYOUT_DEFAULTS, height=320,
                       title="Healing Probability Over Time")
    fig.update_xaxes(**GRID_STYLE)
    fig.update_yaxes(**GRID_STYLE, title="Probability (%)", range=[0, 100])
    return fig


def area_reduction_pct(df, unit_col="wound_area_cm2") -> go.Figure:
    base = df[unit_col].iloc[0]
    reduction = [round((base - a) / base * 100, 1) for a in df[unit_col]]
    colors = [SUCCESS if r >= 0 else DANGER for r in reduction]
    fig = go.Figure(go.Bar(
        x=df["visit_date"], y=reduction, marker_color=colors,
        hovertemplate="<b>%{x}</b><br>Area Reduction: %{y}%<extra></extra>",
    ))
    fig.update_layout(**LAYOUT_DEFAULTS, height=320,
                       title="Cumulative Area Reduction (%)")
    fig.update_xaxes(**GRID_STYLE)
    fig.update_yaxes(**GRID_STYLE, title="Reduction vs Baseline (%)")
    return fig


def visit_timeline(df) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["visit_date"], y=[1] * len(df),
        mode="markers+text",
        marker=dict(size=22, color=PRIMARY, line=dict(width=3, color="white")),
        text=df["day"], textposition="top center",
        hovertemplate="<b>%{x}</b><br>%{text} visit recorded<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["visit_date"], y=[1] * len(df), mode="lines",
        line=dict(color="#C7D8EA", width=3), hoverinfo="skip",
    ))
    fig.update_layout(**LAYOUT_DEFAULTS, height=200, showlegend=False,
                       title="Timeline of Clinical Visits")
    fig.update_yaxes(visible=False, range=[0.5, 1.6])
    fig.update_xaxes(showgrid=False)
    return fig


def weekly_progress(df) -> go.Figure:
    deltas = [0] + [
        round(df["healing_probability"].iloc[i] - df["healing_probability"].iloc[i - 1], 1)
        for i in range(1, len(df))
    ]
    colors = [SUCCESS if d >= 0 else DANGER for d in deltas]
    fig = go.Figure(go.Bar(
        x=df["visit_date"], y=deltas, marker_color=colors,
        hovertemplate="<b>%{x}</b><br>Weekly Change: %{y} pts<extra></extra>",
    ))
    fig.update_layout(**LAYOUT_DEFAULTS, height=320,
                       title="Weekly Progress (Δ Healing Probability)")
    fig.update_xaxes(**GRID_STYLE)
    fig.update_yaxes(**GRID_STYLE, title="Change (pts)")
    return fig


def render_chart_grid(df) -> None:
    """Render the essential chart grid for a patient: wound area trend and
    tissue composition side by side, with healing probability full-width below."""
    unit_col = "wound_area_px" if "wound_area_px" in df.columns else "wound_area_cm2"
    unit_label = "px²" if unit_col == "wound_area_px" else "cm²"

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(wound_area_trend(df, unit_label, unit_col), use_container_width=True,
                         config={"displayModeBar": False})
    with c2:
        st.plotly_chart(tissue_composition(df), use_container_width=True,
                         config={"displayModeBar": False})

    st.plotly_chart(healing_probability_over_time(df), use_container_width=True,
                     config={"displayModeBar": False})
