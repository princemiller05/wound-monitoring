"""
patient_history.py
-------------------
Renders the Patient History page: a filterable, sortable roster of
all patients with status pills and quick stats.
"""

import streamlit as st

from utils.helpers import risk_badge_class, status_badge_class


def render_patient_history(roster) -> None:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🗂️ Patient History</div>',
                unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        status_filter = st.multiselect(
            "Filter by status", ["Healing", "Stable", "Non-Healing"],
            default=["Healing", "Stable", "Non-Healing"],
        )
    with c2:
        doctor_filter = st.multiselect(
            "Filter by doctor", sorted(roster["doctor"].unique()),
            default=sorted(roster["doctor"].unique()),
        )
    with c3:
        sort_by = st.selectbox(
            "Sort by", ["Last Visit", "Healing Probability", "Risk Level"],
        )

    filtered = roster[
        roster["status"].isin(status_filter) & roster["doctor"].isin(doctor_filter)
    ].copy()

    sort_map = {
        "Last Visit": "last_visit",
        "Healing Probability": "healing_probability",
        "Risk Level": "risk_level",
    }
    filtered = filtered.sort_values(
        sort_map[sort_by], ascending=(sort_by == "Last Visit")
    )

    st.markdown(f"<div class='info-label'>{len(filtered)} patients found</div>",
                unsafe_allow_html=True)

    display_df = filtered[[
        "case_id", "name", "age", "gender", "diabetes_type", "doctor",
        "last_visit", "stage", "status", "risk_level", "healing_probability",
    ]].rename(columns={
        "case_id": "Case ID", "name": "Name", "age": "Age", "gender": "Gender",
        "diabetes_type": "Diabetes", "doctor": "Doctor", "last_visit": "Last Visit",
        "stage": "Stage", "status": "Status", "risk_level": "Risk",
        "healing_probability": "Healing %",
    })

    st.dataframe(
        display_df, use_container_width=True, hide_index=True, height=520,
        column_config={
            "Healing %": st.column_config.ProgressColumn(
                "Healing %", min_value=0, max_value=100, format="%d%%"
            ),
        },
    )
    st.markdown("</div>", unsafe_allow_html=True)
