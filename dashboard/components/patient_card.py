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

    def _v(val, suffix=""):
        if val is None or val == "" or val == "—":
            return "—"
        return f"{val}{suffix}"

    smoker = patient.get("smoker")
    smoker_txt = "—" if smoker is None else ("Yes" if smoker else "No")

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
            f'<div class="patient-meta">{_v(patient.get("age"))} yrs '
            f'&nbsp;•&nbsp; {_v(patient.get("gender"))} '
            f'&nbsp;•&nbsp; {_v(patient.get("visits"))} visit(s)</div>',
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
            <div class="info-item"><div class="info-label">BMI</div>
                <div class="info-value">{_v(patient.get('bmi'))}</div></div>
            <div class="info-item"><div class="info-label">Smoker</div>
                <div class="info-value">{smoker_txt}</div></div>
            <div class="info-item"><div class="info-label">Visits recorded</div>
                <div class="info-value">{_v(patient.get('visits'))}</div></div>
            <div class="info-item"><div class="info-label">Shared with</div>
                <div class="info-value">{_v(patient.get('doctor_email'))}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
