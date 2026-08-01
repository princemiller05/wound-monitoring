"""
patient_history.py
--------------------
Displays the full patient roster as a searchable, filterable table,
plus a quick distribution chart.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.helpers import status_to_hex


def render(df: pd.DataFrame) -> None:
    st.markdown('<p class="page-title">📋 Patient History</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Complete roster of monitored diabetic foot ulcer patients</p>', unsafe_allow_html=True)

    st.markdown('<div class="uic-card">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.multiselect("Healing Status", df["status"].unique().tolist())
    with col2:
        risk_filter = st.multiselect("Risk Level", df["risk_level"].unique().tolist())
    with col3:
        doctor_filter = st.multiselect("Doctor", df["doctor"].unique().tolist())

    filtered = df.copy()
    if status_filter:
        filtered = filtered[filtered["status"].isin(status_filter)]
    if risk_filter:
        filtered = filtered[filtered["risk_level"].isin(risk_filter)]
    if doctor_filter:
        filtered = filtered[filtered["doctor"].isin(doctor_filter)]

    st.dataframe(
        filtered[
            ["patient_id", "name", "age", "gender", "diabetes_type", "doctor",
             "stage", "status", "risk_level", "healing_probability", "last_visit_days_ago"]
        ].rename(columns={
            "patient_id": "Case ID", "name": "Name", "age": "Age", "gender": "Gender",
            "diabetes_type": "Diabetes", "doctor": "Doctor", "stage": "Stage",
            "status": "Status", "risk_level": "Risk", "healing_probability": "Healing %",
            "last_visit_days_ago": "Last Visit (days ago)",
        }),
        use_container_width=True,
        hide_index=True,
        height=420,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="uic-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Status Distribution</div>', unsafe_allow_html=True)
        status_counts = filtered["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        fig = px.pie(
            status_counts, names="status", values="count", hole=0.55,
            color="status",
            color_discrete_map={s: status_to_hex(s) for s in status_counts["status"]},
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", y=-0.1),
        )
        fig.update_traces(textinfo="percent+label", hovertemplate="%{label}: %{value} patients<extra></extra>")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="uic-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Risk Level Breakdown</div>', unsafe_allow_html=True)
        risk_counts = filtered["risk_level"].value_counts().reset_index()
        risk_counts.columns = ["risk", "count"]
        color_map = {"Low": "#16A34A", "Medium": "#F59E0B", "High": "#DC2626"}
        fig2 = px.bar(
            risk_counts, x="risk", y="count", color="risk",
            color_discrete_map=color_map, text="count",
        )
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=300, showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        fig2.update_traces(hovertemplate="%{x}: %{y} patients<extra></extra>")
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)
