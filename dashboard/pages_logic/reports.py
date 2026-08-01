"""
reports.py
-----------
Reports page: generate / export patient reports as PDF or CSV, and a
print-friendly summary view.
"""

import io
import streamlit as st
import pandas as pd

from utils.data_generator import generate_visit_timeline, get_patient_record


def _build_pdf_bytes(patient: pd.Series, timeline: pd.DataFrame) -> bytes:
    """Builds a simple one-page PDF report using reportlab if available,
    otherwise falls back to a plain-text byte stream."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        c.setFont("Helvetica-Bold", 18)
        c.drawString(40, height - 60, "Wound Monitoring — Clinical Report")
        c.setFont("Helvetica", 10)
        c.drawString(40, height - 78, "Research Prototype – Not for Clinical Use")

        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, height - 110, f"Patient: {patient['name']}  (Case ID: {patient['patient_id']})")
        c.setFont("Helvetica", 10)
        lines = [
            f"Age: {patient['age']}   Gender: {patient['gender']}   Diabetes: {patient['diabetes_type']}",
            f"Doctor: {patient['doctor']}   Stage: {patient['stage']}",
            f"Status: {patient['status']}   Risk Level: {patient['risk_level']}",
            f"Healing Probability: {patient['healing_probability']}%   Confidence: {patient['confidence']}%",
        ]
        y = height - 130
        for line in lines:
            c.drawString(40, y, line)
            y -= 16

        c.setFont("Helvetica-Bold", 12)
        y -= 14
        c.drawString(40, y, "Visit History")
        y -= 18
        c.setFont("Helvetica", 9)
        for _, row in timeline.iterrows():
            c.drawString(
                40, y,
                f"Visit {row['visit']}  |  {row['date'].date()}  |  "
                f"Area: {row['wound_area_cm2']} cm²  |  Healing: {row['healing_probability']}%"
            )
            y -= 14
            if y < 60:
                c.showPage()
                y = height - 60

        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer.read()
    except ImportError:
        text = (
            f"Wound Monitoring Report\nPatient: {patient['name']} ({patient['patient_id']})\n"
            f"Status: {patient['status']}, Risk: {patient['risk_level']}\n"
            f"Healing Probability: {patient['healing_probability']}%\n\n"
            + timeline.to_string(index=False)
        )
        return text.encode("utf-8")


def render(df: pd.DataFrame) -> None:
    st.markdown('<p class="page-title">📑 Reports</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Generate, export and print patient wound assessment reports</p>', unsafe_allow_html=True)

    st.markdown('<div class="uic-card">', unsafe_allow_html=True)
    patient_id = st.selectbox("Select Patient", df["patient_id"].tolist(), key="report_patient_select")
    patient = get_patient_record(df, patient_id)
    timeline = generate_visit_timeline(patient["patient_id"], patient["healing_probability"])

    st.markdown('<div class="divider-soft"></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        pdf_bytes = _build_pdf_bytes(patient, timeline)
        st.download_button(
            "📄 Generate PDF Report",
            data=pdf_bytes,
            file_name=f"{patient_id}_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "📊 Export CSV Data",
            data=timeline.to_csv(index=False).encode("utf-8"),
            file_name=f"{patient_id}_data.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col3:
        if st.button("🖨️ Print Report", use_container_width=True):
            st.info("Use your browser's Print dialog (Ctrl/Cmd + P) to print this view.")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="uic-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Report Preview</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <p style="font-size:14px; line-height:1.7;">
        <b>Patient:</b> {patient['name']} &nbsp;|&nbsp; <b>Case ID:</b> {patient['patient_id']}<br>
        <b>Age/Gender:</b> {patient['age']} / {patient['gender']} &nbsp;|&nbsp;
        <b>Diabetes:</b> {patient['diabetes_type']}<br>
        <b>Status:</b> {patient['status']} &nbsp;|&nbsp; <b>Risk:</b> {patient['risk_level']} &nbsp;|&nbsp;
        <b>Healing Probability:</b> {patient['healing_probability']}%
        </p>
        """,
        unsafe_allow_html=True,
    )
    st.dataframe(timeline, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)
