"""
prediction_card.py
-------------------
Renders the AI healing-prediction card: circular gauge (Plotly),
predicted label, trend, confidence score, status badge, and reasons.
"""

import plotly.graph_objects as go
import streamlit as st

from utils.helpers import status_badge_class, status_color


def _build_gauge(probability: float, color: str) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=probability,
            number={"suffix": "%", "font": {"size": 34, "color": "#0F2940"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 0, "tickcolor": "white"},
                "bar": {"color": color, "thickness": 0.28},
                "bgcolor": "white",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 40], "color": "#FDECEC"},
                    {"range": [40, 70], "color": "#FFF7E6"},
                    {"range": [70, 100], "color": "#E9F9EF"},
                ],
            },
        )
    )
    fig.update_layout(
        height=220,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif"},
    )
    return fig


def render_prediction_card(patient: dict) -> None:
    status = patient["status"]
    prob = patient["healing_probability"]
    color = status_color(status)
    confidence = min(99, prob + 6) if status != "Stable" else prob - 4

    
    st.markdown(
        '<div class="section-title">🧠 AI Healing Prediction</div>',
        unsafe_allow_html=True,
    )

    g_col, info_col = st.columns([1, 1.4])
    with g_col:
        st.plotly_chart(_build_gauge(prob, color), use_container_width=True,
                         config={"displayModeBar": False})
    with info_col:
        st.markdown(
            f'<span class="badge {status_badge_class(status)}" '
            f'style="font-size:14px;padding:7px 16px;">{status}</span>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div style="margin-top:14px;">
                <div class="info-label">Predicted Label</div>
                <div class="info-value" style="font-size:16px;">{status} Wound Trajectory</div>
            </div>
            <div style="margin-top:10px; display:flex; gap:24px;">
                <div>
                    <div class="info-label">Confidence Score</div>
                    <div class="info-value">{confidence:.1f}%</div>
                </div>
                <div>
                    <div class="info-label">7-Day Trend</div>
                    <div class="info-value">{'↑ Improving' if status=='Healing' else ('↓ Declining' if status=='Non-Healing' else '→ Plateauing')}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    
    
