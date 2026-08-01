"""
ai_analysis.py
----------------
Deep-dive AI analysis page for a selected patient: full chart suite,
insight cards and model explainability notes.
"""

import streamlit as st
import pandas as pd

from components.prediction_card import render_prediction_card
from components.insight_cards import (
    render_top_factors, render_recommendations, render_warnings, render_clinical_notes,
)
from components.charts import (
    wound_area_trend_chart, tissue_composition_chart, healing_probability_chart,
    area_reduction_chart, weekly_progress_chart,
)
from utils.data_generator import (
    generate_visit_timeline, generate_weekly_progress, get_top_factors,
    get_recommendations, get_warnings, get_clinical_notes, get_patient_record,
)


def render(df: pd.DataFrame) -> None:
    st.markdown('<p class="page-title">🤖 AI Analysis</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Model explainability and longitudinal wound trajectory analysis</p>', unsafe_allow_html=True)

    st.markdown('<div class="uic-card">', unsafe_allow_html=True)
    patient_id = st.selectbox("Select Patient", df["patient_id"].tolist(), key="ai_patient_select")
    st.markdown("</div>", unsafe_allow_html=True)

    patient = get_patient_record(df, patient_id)
    timeline = generate_visit_timeline(patient["patient_id"], patient["healing_probability"])
    weekly = generate_weekly_progress()
    trend_pct = round(
        timeline["healing_probability"].iloc[-1] - timeline["healing_probability"].iloc[0], 1
    )
    reasons = [f["factor"] for f in get_top_factors()[:3]]

    render_prediction_card(patient, trend_pct, reasons)

    tab1, tab2, tab3 = st.tabs(["📈 Trend Analysis", "🧬 Tissue & Composition", "🧠 Model Insights"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="uic-card">', unsafe_allow_html=True)
            st.plotly_chart(healing_probability_chart(timeline), use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="uic-card">', unsafe_allow_html=True)
            st.plotly_chart(area_reduction_chart(timeline), use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<div class="uic-card">', unsafe_allow_html=True)
        st.plotly_chart(weekly_progress_chart(weekly), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="uic-card">', unsafe_allow_html=True)
            st.plotly_chart(tissue_composition_chart(timeline), use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="uic-card">', unsafe_allow_html=True)
            st.plotly_chart(wound_area_trend_chart(timeline), use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            render_top_factors(get_top_factors())
            render_warnings(get_warnings(patient["risk_level"]), patient["risk_level"])
        with c2:
            render_recommendations(get_recommendations())
            render_clinical_notes(get_clinical_notes())
