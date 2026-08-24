"""
patient_card.py
----------------
Renders the patient profile / information card with avatar, key
demographics, and current clinical status badges.
"""

import streamlit as st

from utils.helpers import get_initials, risk_badge_class, status_badge_class


def render_patient_card(patient: dict) -> None:
    
    st.markdown(
        '<div class="section-title">🧑‍⚕️ Patient Information</div>',
        unsafe_allow_html=True,
    )

    col_avatar, col_info = st.columns([1, 3])
    with col_avatar:
        st.markdown(
            f'<div class="patient-avatar">{get_initials(patient["name"])}</div>',
            unsafe_allow_html=True,
        )
    with col_info:
        st.markdown(f'<div class="patient-name">{patient["name"]}</div>',
                    unsafe_allow_html=True)
        st.markdown(
            f'<div class="patient-meta">Case ID: {patient["case_id"]} &nbsp;•&nbsp; '
            f'{patient["age"]} yrs &nbsp;•&nbsp; {patient["gender"]}</div>',
            unsafe_allow_html=True,
        )
        b1, b2 = st.columns(2)
        with b1:
            st.markdown(
                f'<span class="badge {status_badge_class(patient["status"])}">'
                f'{patient["status"]}</span>',
                unsafe_allow_html=True,
            )
        with b2:
            st.markdown(
                f'<span class="badge {risk_badge_class(patient["risk_level"])}">'
                f'{patient["risk_level"]} Risk</span>',
                unsafe_allow_html=True,
            )

    st.markdown(
        f"""
        <div class="info-grid">
            <div class="info-item"><div class="info-label">Diabetes</div>
                <div class="info-value">{patient['diabetes_type']}</div></div>
            <div class="info-item"><div class="info-label">Attending Doctor</div>
                <div class="info-value">{patient['doctor']}</div></div>
            <div class="info-item"><div class="info-label">Last Visit</div>
                <div class="info-value">{patient['last_visit']}</div></div>
            <div class="info-item"><div class="info-label">Current Stage</div>
                <div class="info-value">{patient['stage']}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
