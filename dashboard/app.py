"""
app.py
------
Wound Monitoring — Doctor Dashboard.

A signed-in doctor sees only the patients who added their email in the WoundWatch
app (matched via get_doctor_patients), each patient's real analysis, trend, and
actual wound photos. No generated/fake data.

Run with:
    streamlit run app.py
"""

import streamlit as st


def _auth_state():
    """Return True (logged in), False (login configured, not logged in), or
    None (no auth provider configured — run in open/email-only mode)."""
    try:
        return bool(st.user.is_logged_in)
    except Exception:
        return None


# ----------------------------------------------------------------------
# Auth — if Google login is configured, require it; otherwise fall back to
# email-only mode so the dashboard runs anywhere with just the backend secrets.
# ----------------------------------------------------------------------
_auth = _auth_state()
if _auth is False:
    st.set_page_config(page_title="Wound Monitoring | Doctor Login",
                       page_icon="🩺", layout="centered")
    st.title("🩺 Wound Monitoring — Doctor Dashboard")
    st.write("Please sign in to view your patients.")
    st.login()
    st.stop()

from components.charts import render_chart_grid
from components.footer import render_footer
from components.patient_card import render_patient_card
from components.prediction_card import render_prediction_card
from components.wound_gallery import render_wound_gallery
from utils.helpers import load_css
from utils.backend import (
    backend_configured,
    build_patient_overlay,
    get_doctor_patients,
    get_patient_photos,
    history_to_dataframe,
)

st.set_page_config(
    page_title="Wound Monitoring | Doctor Dashboard",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_css("styles/style.css")

# ----------------------------------------------------------------------
# Sidebar — doctor identity + the email patients share to.
# ----------------------------------------------------------------------
# Safely read identity (st.user may be unavailable when no auth is configured).
def _user_attr(name):
    try:
        return getattr(st.user, name, "") or ""
    except Exception:
        return ""

login_name = _user_attr("name")
login_email = _user_attr("email").strip().lower()

with st.sidebar:
    st.markdown(f"**Dr. {login_name or 'Clinician'}**")
    if login_email:
        st.caption(login_email)

    # Patients add a doctor by email; usually that's the login email, but for
    # demos the shared email may differ — let the doctor confirm/override it.
    doctor_email = st.text_input(
        "Patients share to this email",
        value=st.session_state.get("doctor_email", login_email),
        help="Only patients who added THIS email will appear.",
    ).strip().lower()
    st.session_state.doctor_email = doctor_email

    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if _auth:  # only show Log out when a real login session exists
        st.divider()
        if st.button("Log out", use_container_width=True):
            st.logout()

# ----------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------
st.markdown('<div class="page-title">🩺 Wound Monitoring Doctor Dashboard</div>',
            unsafe_allow_html=True)
st.markdown(
    '<div class="page-subtitle">⚠️ Research Prototype – Not for Clinical Use</div>',
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------
# Guard: backend must be configured.
# ----------------------------------------------------------------------
if not backend_configured():
    st.warning(
        "The dashboard isn't connected to the backend yet. Set "
        "`WOUNDWATCH_FUNCTION_URL` and `WOUNDWATCH_FUNCTION_KEY` in the app's "
        "secrets/environment to load live patients."
    )
    render_footer()
    st.stop()

if not doctor_email:
    st.info("Enter your email in the sidebar to load your patients.")
    render_footer()
    st.stop()

# ----------------------------------------------------------------------
# Load the doctor's real patients (worst-first).
# ----------------------------------------------------------------------
try:
    patients = get_doctor_patients(doctor_email)
except Exception as exc:
    st.error(f"Couldn't load your patient list: {exc}")
    render_footer()
    st.stop()

if not patients:
    st.info(
        f"No patients have shared their wound history with **{doctor_email}** "
        "yet. In the WoundWatch app, a patient adds you from **Add your doctor** "
        "using this exact email."
    )
    render_footer()
    st.stop()

# ----------------------------------------------------------------------
# Worklist — pick a patient (sorted worst-first by the backend).
# ----------------------------------------------------------------------
st.markdown('<div class="section-title">👥 Your Patients</div>',
            unsafe_allow_html=True)

def _label(p: dict) -> str:
    name = p.get("name") or "(name pending)"
    risk = p.get("risk") or "—"
    visits = p.get("visits", 0)
    return f"{name}  ·  {risk} risk  ·  {visits} visit(s)"

labels = [_label(p) for p in patients]
ids = [p["patient_id"] for p in patients]

# Keep selection stable across reruns.
if st.session_state.get("sel_pid") not in ids:
    st.session_state.sel_pid = ids[0]
default_idx = ids.index(st.session_state.sel_pid)

choice = st.selectbox("Select a patient", options=range(len(labels)),
                      format_func=lambda i: labels[i], index=default_idx)
selected_id = ids[choice]
st.session_state.sel_pid = selected_id

# ----------------------------------------------------------------------
# Patient detail.
# ----------------------------------------------------------------------
try:
    patient, history = build_patient_overlay(selected_id)
    timeseries = history_to_dataframe(history)
except Exception as exc:
    # Profile exists but nothing analysed yet, or a transient error.
    st.warning(
        "No analysed wound data for this patient yet — they've registered and "
        "shared with you, but haven't uploaded a photo that finished analysis."
    )
    render_footer()
    st.stop()

col_left, col_right = st.columns([1, 1.55])
with col_left:
    render_patient_card(patient)
with col_right:
    render_prediction_card(patient)

st.markdown('<div class="section-title">📈 Wound Progress Analytics</div>',
            unsafe_allow_html=True)
render_chart_grid(timeseries)

# ----------------------------------------------------------------------
# The actual wound photos.
# ----------------------------------------------------------------------
try:
    photos = get_patient_photos(selected_id)
except Exception:
    photos = []
render_wound_gallery(photos)

render_footer()
