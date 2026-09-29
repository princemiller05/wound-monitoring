"""
upload_section.py
------------------
Renders the wound-image upload workflow: drag-and-drop uploader,
day-of-treatment selector, image previews, and a simulated AI
analysis run with loading state + success feedback.
"""

import time

import streamlit as st

from utils.data_generator import generate_reasons


def render_upload_section() -> None:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-title">📤 Upload Wound Images</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="upload-zone">
            <div class="upload-icon">🖼️</div>
            <div style="font-weight:700; color:var(--ink); font-size:15px;">
                Drag & drop wound images here
            </div>
            <div style="color:var(--ink-soft); font-size:12.5px; margin-top:4px;">
                Supports JPG, PNG, HEIC &nbsp;•&nbsp; Multiple files allowed &nbsp;•&nbsp; Max 10MB each
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    files = st.file_uploader(
        "Upload files", type=["jpg", "jpeg", "png", "heic"],
        accept_multiple_files=True, label_visibility="collapsed",
    )

    col_day, col_btn = st.columns([2, 1])
    with col_day:
        day = st.radio(
            "Select Day of Treatment", ["Day 0", "Day 7", "Day 14", "Day 21"],
            horizontal=True,
        )
    with col_btn:
        st.write("")
        analyse_clicked = st.button("🤖 Analyse Images", use_container_width=True)

    if files:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        preview_cols = st.columns(min(4, len(files)))
        for i, f in enumerate(files):
            with preview_cols[i % len(preview_cols)]:
                st.image(f, use_container_width=True, caption=f.name)

    if analyse_clicked:
        if not files:
            st.warning("Please upload at least one wound image before analysis.")
        else:
            with st.spinner("Running AI wound segmentation & healing inference…"):
                time.sleep(1.8)
            st.success(f"✅ Analysis complete for {len(files)} image(s) — {day}")
            _render_analysis_result(day)

    


def _render_analysis_result(day: str) -> None:
    """Render a results block after a simulated analysis run."""
    import random
    prob = round(random.uniform(55, 92), 1)
    status = "Healing" if prob >= 70 else ("Stable" if prob >= 45 else "Non-Healing")
    reasons = generate_reasons(status)

    
    st.markdown(
        f'<div class="section-title">📊 AI Analysis Result — {day}</div>',
        unsafe_allow_html=True,
    )
    r1, r2, r3 = st.columns(3)
    r1.metric("Healing Probability", f"{prob}%", "▲ 3.2%")
    r2.metric("Predicted Trend", "Improving" if status == "Healing" else "Watch closely")
    r3.metric("Confidence Score", f"{min(99, prob + 5):.1f}%")

    chips = "".join(f'<span class="reason-chip">🔹 {r}</span>' for r in reasons)
    st.markdown(f"<div class='info-label'>Reasons</div>{chips}", unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.download_button(
        "⬇️ Download Analysis Report",
        data=f"Wound Analysis Report\nDay: {day}\nHealing Probability: {prob}%\n"
             f"Status: {status}\nReasons: {', '.join(reasons)}",
        file_name=f"wound_analysis_{day.replace(' ', '_').lower()}.txt",
        mime="text/plain",
    )
    
