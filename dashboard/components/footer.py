"""
footer.py
---------
Renders the application footer with versioning and compliance text.
"""

import streamlit as st


def render_footer() -> None:
    st.markdown(
        """
        <div class="app-footer">
            <div><b>Research prototype</b> — not for clinical use</div>
            <div>Wound Monitoring · v1.0</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
