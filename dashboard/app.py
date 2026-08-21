"""
app.py
------
Entry point for the Wound Monitoring – Doctor Dashboard.

This file is intentionally thin: it wires together reusable
components (sidebar, cards, charts) and page-level renderers,
keeping business logic in `utils/` and presentation in `components/`.

Run with:
    streamlit run app.py
"""

import streamlit as st

if not st.user.is_logged_in:
    st.login()
    st.stop()

st.sidebar.success(f"Welcome {st.user.name}")
st.sidebar.write(st.user.email)
from components.charts import render_chart_grid
from components.footer import render_footer
from components.kpi_cards import render_kpi_row
from components.patient_card import render_patient_card
from components.patient_history import render_patient_history
from components.patient_search import render_patient_search
from components.prediction_card import render_prediction_card
from components.reports_section import render_reports_section
from components.settings_section import render_settings_section
from components.sidebar import render_sidebar
from components.upload_section import render_upload_section
from utils.data_generator import (
    compute_kpis,
    generate_patient_list,
    generate_wound_timeseries,
    get_patient_detail,
)
from utils.helpers import load_css
from utils.backend import build_patient_overlay, get_real_patient_data, has_real_data

# ----------------------------------------------------------------------
# Page configuration — must be the first Streamlit call
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Wound Monitoring | Doctor Dashboard",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css("styles/style.css")


# ----------------------------------------------------------------------
# Cached data layer (simulates a backend / clinical DB call)
# ----------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _load_roster():
    return generate_patient_list(n=48)


roster = _load_roster()

# ----------------------------------------------------------------------
# Sidebar navigation
# ----------------------------------------------------------------------
active_page = render_sidebar()

# ----------------------------------------------------------------------
# Page header
# ----------------------------------------------------------------------
st.markdown('<div class="page-title">🩺 Wound Monitoring Doctor Dashboard</div>',
            unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">⚠️ Research Prototype – Not for Clinical Use</div>',
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------
# Persisted state: selected patient
# ----------------------------------------------------------------------
if "selected_case_id" not in st.session_state:
    st.session_state.selected_case_id = roster.iloc[0]["case_id"]


# ========================================================================
# PAGE: DASHBOARD
# ========================================================================
if active_page == "Dashboard":
    kpis = compute_kpis(roster)
    render_kpi_row(kpis)
    selected_id = render_patient_search(roster)
    st.session_state.selected_case_id = selected_id

    if has_real_data(selected_id):
        try:
            patient, history = build_patient_overlay(selected_id, roster)
            _, timeseries = get_real_patient_data(selected_id)
            st.info("📡 Live data from Azure ML pipeline", icon="📡")
        except Exception as exc:
            st.error(f"Could not load real data for {selected_id}: {exc}")
            patient = get_patient_detail(selected_id, roster)
            timeseries = generate_wound_timeseries()
    else:
        patient = get_patient_detail(st.session_state.selected_case_id, roster)
        timeseries = generate_wound_timeseries()

    col_left, col_right = st.columns([1, 1.55])
    with col_left:
        render_patient_card(patient)
    with col_right:
        render_prediction_card(patient)

    st.markdown('<div class="section-title">📈 Wound Progress Analytics</div>',
                unsafe_allow_html=True)
    render_chart_grid(timeseries)

# ========================================================================
# PAGE: PATIENT HISTORY
# ========================================================================
elif active_page == "Patient History":
    render_patient_history(roster)

# ========================================================================
# PAGE: UPLOAD IMAGES
# ========================================================================
elif active_page == "Upload Images":
    patient = get_patient_detail(st.session_state.selected_case_id, roster)
    st.markdown(
        f'<div class="info-label">Active patient: '
        f'<span style="color:var(--primary)">{patient["name"]} '
        f'({patient["case_id"]})</span></div>',
        unsafe_allow_html=True,
    )
    render_upload_section()

# ========================================================================
# PAGE: AI ANALYSIS
# ========================================================================
elif active_page == "AI Analysis":
    patient = get_patient_detail(st.session_state.selected_case_id, roster)
    timeseries = generate_wound_timeseries()

    render_prediction_card(patient)
    st.markdown('<div class="section-title">📈 Supporting Analytics</div>',
                unsafe_allow_html=True)
    render_chart_grid(timeseries)

# ========================================================================
# PAGE: REPORTS
# ========================================================================
elif active_page == "Reports":
    patient = get_patient_detail(st.session_state.selected_case_id, roster)
    timeseries = generate_wound_timeseries()
    render_reports_section(roster, patient, timeseries)

# ========================================================================
# PAGE: SETTINGS
# ========================================================================
elif active_page == "Settings":
    render_settings_section()

# ----------------------------------------------------------------------
# Footer
# ----------------------------------------------------------------------
render_footer()
