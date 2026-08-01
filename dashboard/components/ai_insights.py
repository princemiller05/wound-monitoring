"""
ai_insights.py
--------------
Renders the AI insight grid: Top Factors, Recommendations, Warnings,
Clinical Notes, and Risk Indicators.
"""

import streamlit as st


def _list_card(title: str, icon: str, items, dot_default="dot-blue"):
    rows = ""
    for item in items:
        if isinstance(item, tuple):
            text, dot = item
        else:
            text, dot = item, dot_default
        rows += (
            f'<div class="insight-row"><span class="dot {dot}"></span>'
            f'<span>{text}</span></div>'
        )
    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-title">{icon} {title}</div>
            {rows}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ai_insights(insights: dict) -> None:
    st.markdown(
        '<div class="section-title">✨ AI Clinical Insights</div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        _list_card("Top Factors", "🔬", insights["top_factors"])
    with c2:
        _list_card("Recommendations", "📋", insights["recommendations"], "dot-green")
    with c3:
        _list_card("Warnings", "⚠️", insights["warnings"], "dot-red")

    c4, c5 = st.columns([1.4, 1])
    with c4:
        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-title">📝 Clinical Notes</div>
                <div style="font-size:13.3px; color:var(--ink-soft); line-height:1.6;">
                    {insights['clinical_notes']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c5:
        rows = "".join(
            f'<div class="insight-row"><span class="dot dot-orange"></span>'
            f'<span>{name} — <b>{level}</b></span></div>'
            for name, level in insights["risk_indicators"]
        )
        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-title">🛡️ Risk Indicators</div>
                {rows}
            </div>
            """,
            unsafe_allow_html=True,
        )
