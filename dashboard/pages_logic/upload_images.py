"""
upload_images.py
------------------
"Upload Images" page: drag-and-drop uploader, day selection, analyse
trigger, and post-analysis results panel.
"""

import streamlit as st
import pandas as pd

from components.upload_section import render_upload_section
from components.prediction_card import render_prediction_card
from components.charts import wound_area_trend_chart, healing_probability_chart
from utils.data_generator import generate_visit_timeline, get_patient_record, get_top_factors


def render(df: pd.DataFrame) -> None:
    st.markdown('<p class="page-title">📤 Upload Wound Images</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Submit new clinical images for AI-assisted wound assessment</p>', unsafe_allow_html=True)

    st.markdown('<div class="uic-card">', unsafe_allow_html=True)
    patient_id = st.selectbox("Select Patient for Upload", df["patient_id"].tolist())
    st.markdown("</div>", unsafe_allow_html=True)

    uploaded_files, selected_day, analysed = render_upload_section()

    if analysed:
        patient = get_patient_record(df, patient_id)
        timeline = generate_visit_timeline(patient["patient_id"], patient["healing_probability"])
        trend_pct = round(
            timeline["healing_probability"].iloc[-1] - timeline["healing_probability"].iloc[0], 1
        )
        reasons = [f["factor"] for f in get_top_factors()[:3]]

        st.markdown('<div class="section-title">📊 Analysis Results</div>', unsafe_allow_html=True)
        render_prediction_card(patient, trend_pct, reasons)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="uic-card">', unsafe_allow_html=True)
            st.plotly_chart(wound_area_trend_chart(timeline), use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="uic-card">', unsafe_allow_html=True)
            st.plotly_chart(healing_probability_chart(timeline), use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="uic-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Summary</div>', unsafe_allow_html=True)
        st.markdown(
            f"""<p class="muted" style="font-size:13.5px; line-height:1.6;">
            Based on the uploaded image(s) for <b>{selected_day}</b>, the model estimates a healing
            probability of <b>{patient['healing_probability']}%</b> with a confidence of
            <b>{patient['confidence']}%</b>, classifying the wound trajectory as
            <b>{patient['status']}</b>. {len(uploaded_files)} image(s) were processed in this batch.
            </p>""",
            unsafe_allow_html=True,
        )
        st.download_button(
            "⬇️ Download Report (CSV)",
            data=timeline.to_csv(index=False).encode("utf-8"),
            file_name=f"{patient_id}_wound_report.csv",
            mime="text/csv",
        )
        st.markdown("</div>", unsafe_allow_html=True)
