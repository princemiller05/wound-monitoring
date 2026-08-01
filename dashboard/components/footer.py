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
            <div>🧪 <b>Research Prototype</b> — Not for Clinical Use</div>
            <div><b>Version 1.0.0</b></div>
            <div>Powered by <b>Azure AI</b> + <b>XGBoost</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
