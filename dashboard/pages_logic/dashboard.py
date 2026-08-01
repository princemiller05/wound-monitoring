"""
dashboard.py
------------
Main "Dashboard" landing page: KPI summary, patient search, patient
profile, healing prediction and AI insight cards for the selected patient.
"""

import streamlit as st
import pandas as pd

from components.kpi_cards import render_kpi_row
from components.patient_card import render_patient_card
from components.prediction_card import render_prediction_card
from components.insight_cards import (
    render_top_factors, render_recommendations, render_warnings, render_clinical_notes,
)
from components.charts import (
    wound_area_trend_chart, tissue_composition_chart, healing_probability_chart,
    area_reduction_chart, visit_timeline_chart, weekly_progress_chart,
)
from utils.data_generator import (
    generate_visit_timeline, generate_weekly_progress, get_top_factors,
    get_recommendations, get_warnings, get_clinical_notes, get_patient_record,
)


def _render_search_card(df: pd.DataFrame) -> str:
    st.markdown('<div class="uic-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🔍 Patient Search</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        recent = df["patient_id"].tolist()
        selected_id = st.selectbox("Patient ID", recent, index=0, key="search_select")
    with col2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        st.button("🔎 Search", key="search_btn")
    with col3:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        st.button("↻ Recent Patients", key="recent_btn")

    st.markdown('<div class="divider-soft"></div>', unsafe_allow_html=True)
    st.markdown('<p class="muted" style="font-weight:600; margin-bottom:8px;">Filters</p>', unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        st.select_slider("Age Range", options=list(range(30, 91, 5)), value=(40, 80))
    with f2:
        st.multiselect("Gender", ["Male", "Female"], default=[])
    with f3:
        st.multiselect("Diabetes Type", ["Type 1", "Type 2"], default=[])
    with f4:
        st.multiselect("Healing Status", ["Healing", "Stable", "Non Healing"], default=[])

    st.markdown("</div>", unsafe_allow_html=True)
    return selected_id


def render(df: pd.DataFrame) -> None:
    st.markdown('<p class="page-title">🩺 Wound Monitoring Doctor Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Research Prototype – Not for Clinical Use</p>', unsafe_allow_html=True)

    # ---- KPI summary ----
    total_patients = len(df)
    healing_rate = round((df["status"] == "Healing").mean() * 100, 1)
    high_risk = int((df["risk_level"] == "High").sum())
    avg_prob = round(df["healing_probability"].mean(), 1)

    kpis = [
        {"icon": "👥", "value": f"{total_patients}", "label": "Total Patients", "trend": 4.2},
        {"icon": "💚", "value": f"{healing_rate}%", "label": "Healing Rate", "trend": 2.8},
        {"icon": "🚨", "value": f"{high_risk}", "label": "High Risk Cases", "trend": -1.5},
        {"icon": "📈", "value": f"{avg_prob}%", "label": "Avg Healing Probability", "trend": 3.1},
    ]
    render_kpi_row(kpis)

    # ---- Search ----
    selected_id = _render_search_card(df)
    patient = get_patient_record(df, selected_id)
    if patient is None:
        st.error("Patient record not found.")
        return

    # ---- Profile + Prediction ----
    col_left, col_right = st.columns([1, 1.3])
    with col_left:
        render_patient_card(patient)

    timeline = generate_visit_timeline(patient["patient_id"], patient["healing_probability"])
    trend_pct = round(
        timeline["healing_probability"].iloc[-1] - timeline["healing_probability"].iloc[0], 1
    )
    reasons = [f["factor"] for f in get_top_factors()[:3]]

    with col_right:
        render_prediction_card(patient, trend_pct, reasons)

    # ---- AI Insight cards ----
    c1, c2 = st.columns(2)
    with c1:
        render_top_factors(get_top_factors())
        render_warnings(get_warnings(patient["risk_level"]), patient["risk_level"])
    with c2:
        render_recommendations(get_recommendations())
        render_clinical_notes(get_clinical_notes())

    # ---- Charts ----
    st.markdown('<div class="section-title">📈 Wound Progress Analytics</div>', unsafe_allow_html=True)
    weekly = generate_weekly_progress()

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown('<div class="uic-card">', unsafe_allow_html=True)
        st.plotly_chart(wound_area_trend_chart(timeline), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="uic-card">', unsafe_allow_html=True)
        st.plotly_chart(healing_probability_chart(timeline), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="uic-card">', unsafe_allow_html=True)
        st.plotly_chart(visit_timeline_chart(timeline), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with chart_col2:
        st.markdown('<div class="uic-card">', unsafe_allow_html=True)
        st.plotly_chart(tissue_composition_chart(timeline), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="uic-card">', unsafe_allow_html=True)
        st.plotly_chart(area_reduction_chart(timeline), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="uic-card">', unsafe_allow_html=True)
        st.plotly_chart(weekly_progress_chart(weekly), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)
