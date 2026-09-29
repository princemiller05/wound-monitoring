"""
app.py
------
Wound Monitoring — Doctor Dashboard.

A doctor signs in (email), then sees only the patients who added that email in
the WoundWatch app. The sidebar lists those patients (searchable) and flags any
with a new photo since the doctor last reviewed them. Opening a patient shows
their profile, healing prediction, trend charts, and a photo-by-photo review
slider of every wound image they've uploaded.

Run with:  streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Wound Monitoring | Doctor Dashboard",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

from components.charts import render_chart_grid
from components.footer import render_footer
from components.prediction_card import render_prediction_card
from components.photo_review import render_photo_review
from utils.helpers import load_css
from utils import doctor_auth
from utils.backend import (
    backend_configured,
    build_patient_overlay,
    get_doctor_patients,
    get_patient_photos,
    history_to_dataframe,
    mark_reviewed,
)

load_css("styles/style.css")


# ----------------------------------------------------------------------
# SIGN-IN GATE — email/password via Firebase Auth (same as the patient app).
# ----------------------------------------------------------------------
doctor_email = st.session_state.get("doctor_email", "")

if not doctor_email:
    _l, mid, _r = st.columns([1, 1.3, 1])
    with mid:
        st.markdown("<div style='height:6vh'></div>", unsafe_allow_html=True)
        st.markdown('<div class="page-title">Wound Monitoring</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="page-subtitle">Doctor dashboard — sign in to '
                    'view your patients</div>', unsafe_allow_html=True)
        st.write("")

        if not doctor_auth.auth_configured():
            # Fallback so the dashboard still runs without auth configured.
            with st.form("signin_plain"):
                email = st.text_input("Your email",
                                      placeholder="email your patients share to")
                if st.form_submit_button("Continue", use_container_width=True) \
                        and email.strip():
                    st.session_state.doctor_email = email.strip().lower()
                    st.rerun()
            st.caption("Set FIREBASE_WEB_API_KEY in secrets to enable password login.")
            st.stop()

        tab_login, tab_register = st.tabs(["Log in", "Create account"])

        with tab_login:
            with st.form("login"):
                e = st.text_input("Email")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Log in", use_container_width=True):
                    email, err = doctor_auth.sign_in(e, p)
                    if err:
                        st.error(err)
                    else:
                        st.session_state.doctor_email = email
                        st.rerun()

        with tab_register:
            st.caption("New doctor? Create an account with your work email. "
                       "Patients add you using this exact email.")
            with st.form("register"):
                e2 = st.text_input("Email", key="reg_email")
                p2 = st.text_input("Password (min 6 characters)",
                                   type="password", key="reg_pw")
                if st.form_submit_button("Create account",
                                         use_container_width=True):
                    email, err = doctor_auth.sign_up(e2, p2)
                    if err:
                        st.error(err)
                    else:
                        st.session_state.doctor_email = email
                        st.success("Account created.")
                        st.rerun()
    st.stop()

# ----------------------------------------------------------------------
# Backend must be configured.
# ----------------------------------------------------------------------
if not backend_configured():
    st.warning("The dashboard isn't connected to the backend. Set "
               "`WOUNDWATCH_FUNCTION_URL` and `WOUNDWATCH_FUNCTION_KEY` in "
               "`.streamlit/secrets.toml`.")
    st.stop()

# ----------------------------------------------------------------------
# Load the doctor's patients.
# ----------------------------------------------------------------------
try:
    patients = get_doctor_patients(doctor_email)
except Exception as exc:
    st.error(f"Couldn't load your patient list: {exc}")
    st.stop()

# ----------------------------------------------------------------------
# TOP BAR — identity, refresh, sign out (in the main page, always visible).
# ----------------------------------------------------------------------
top_l, top_r = st.columns([3, 1.1])
with top_l:
    st.markdown('<div class="page-title">Wound Monitoring</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Doctor dashboard · '
                f'{doctor_email} · research prototype, not for clinical use</div>',
                unsafe_allow_html=True)
with top_r:
    rc1, rc2 = st.columns(2)
    with rc1:
        if st.button("Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with rc2:
        if st.button("Sign out", use_container_width=True):
            for k in ("doctor_email", "sel_pid"):
                st.session_state.pop(k, None)
            st.rerun()

st.divider()

# ----------------------------------------------------------------------
# PATIENT PICKER — search + list on the left (always shown), detail right.
# ----------------------------------------------------------------------
nav_col, detail_col = st.columns([1, 3], gap="large")

with nav_col:
    needs = sum(1 for p in patients if p.get("needs_review"))
    st.markdown(f"**Your patients** ({len(patients)}) · {needs} to review")
    query = st.text_input("🔍 Search patients", placeholder="Search by name…",
                          label_visibility="collapsed").strip().lower()
    filtered = [p for p in patients
                if not query or query in (p.get("name") or "").lower()]

    if patients and st.session_state.get("sel_pid") not in \
            [p["patient_id"] for p in patients]:
        st.session_state.sel_pid = patients[0]["patient_id"]

    for p in filtered:
        flag = "🔴" if p.get("needs_review") else "🟢"
        name = p.get("name") or "(name pending)"
        is_sel = p["patient_id"] == st.session_state.sel_pid
        if st.button(f"{flag}  {name}", key=f"pt_{p['patient_id']}",
                     use_container_width=True,
                     type="primary" if is_sel else "secondary"):
            st.session_state.sel_pid = p["patient_id"]
            st.rerun()
    if patients and not filtered:
        st.caption("No match.")
    if not patients:
        st.caption("No patients yet.")

# --- Empty state (no patients) — keep the picker visible on the left. ---
if not patients:
    with detail_col:
        st.info(f"No patients have shared their wound history with "
                f"**{doctor_email}** yet. In the WoundWatch app, a patient adds "
                "you from **Add your doctor** using this exact email.")
    render_footer()
    st.stop()

selected = next((p for p in patients
                 if p["patient_id"] == st.session_state.sel_pid), patients[0])
selected_id = selected["patient_id"]

try:
    patient, history = build_patient_overlay(selected_id)
except Exception:
    patient, history = None, None

with detail_col:
    # --- Header + review controls ---
    name = (patient or {}).get("name") or selected.get("name") or "(name pending)"
    st.markdown(f'<div class="patient-name">{name}</div>',
                unsafe_allow_html=True)
    if patient:
        def _v(x, s=""):
            return f"{x}{s}" if x not in (None, "", "—") else "—"
        meta = " &nbsp;•&nbsp; ".join([
            f"{_v(patient.get('age'))} yrs",
            _v(patient.get("gender")),
            f"{_v(patient.get('height_cm'))} cm",
            f"{_v(patient.get('weight_kg'))} kg",
            f"BMI {_v(patient.get('bmi'))}",
            f"{_v(patient.get('visits'))} visit(s)",
        ])
        st.markdown(f'<div class="patient-meta">{meta}</div>',
                    unsafe_allow_html=True)

    if selected.get("needs_review"):
        st.markdown("🔴 **Needs review** — new photo since your last review.")
        if st.button("✓ Mark as reviewed"):
            try:
                mark_reviewed(selected_id, doctor_email)
                st.cache_data.clear()
                st.rerun()
            except Exception as exc:
                st.error(f"Couldn't save: {exc}")
    else:
        st.markdown("🟢 **Reviewed** — up to date.")
        if st.button("↩ Mark as unreviewed"):
            try:
                mark_reviewed(selected_id, doctor_email, undo=True)
                st.cache_data.clear()
                st.rerun()
            except Exception as exc:
                st.error(f"Couldn't save: {exc}")

    st.divider()

    if patient is None:
        st.warning("This patient has registered and shared with you, but hasn't "
                   "uploaded a photo that finished analysis yet.")
    else:
        render_prediction_card(patient)

        st.markdown('<div class="section-title">Wound progress</div>',
                    unsafe_allow_html=True)
        render_chart_grid(history_to_dataframe(history))

        try:
            photos = get_patient_photos(selected_id)
        except Exception:
            photos = []
        render_photo_review(photos, key=selected_id)

render_footer()
