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
from components.patient_card import render_patient_card
from components.patient_search import render_patient_search
from components.prediction_card import render_prediction_card
from utils.data_generator import (
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
active_page = "Dashboard"

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

# ----------------------------------------------------------------------
# Footer
# ----------------------------------------------------------------------
render_footer()
