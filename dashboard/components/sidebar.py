"""
sidebar.py
----------
Renders the left navigation sidebar: hospital brand block, nav menu,
and footer meta information.
"""

import streamlit as st

NAV_ITEMS = [
    ("📊", "Dashboard"),
    ("🗂️", "Patient History"),
    ("📤", "Upload Images"),
    ("🤖", "AI Analysis"),
    ("📄", "Reports"),
    ("⚙️", "Settings"),
]


def render_sidebar() -> str:
    """Render sidebar UI and return the selected nav item label."""
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand-icon">🩺</div>
                <div class="sidebar-brand-text">
                    <div class="title">CareTrack Wound AI</div>
                    <div class="subtitle">Apex Hospitals Network</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        labels = [f"{icon}  {name}" for icon, name in NAV_ITEMS]
        choice = st.radio("Navigation", labels, label_visibility="collapsed")
        selected = choice.split("  ", 1)[1]

        st.markdown(
            """
            <div class="sidebar-foot">
                Logged in as <b style="color:#fff !important;">Dr. Anil Mehta</b><br>
                Endocrinology &amp; Wound Care<br><br>
                🔒 HIPAA / DPDP compliant session
            </div>
            """,
            unsafe_allow_html=True,
        )
    return selected
