"""
settings.py
------------
Settings page: dark mode toggle, theme selector, language selector.
These are presentation-only in the demo (no persistence backend).
"""

import streamlit as st


def render() -> None:
    st.markdown('<p class="page-title">⚙️ Settings</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Personalize your dashboard experience</p>', unsafe_allow_html=True)

    st.markdown('<div class="uic-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Appearance</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.toggle("🌙 Dark Mode", value=False, help="Toggle dark theme (preview only in this prototype)")
        st.selectbox("Theme", ["Medical Blue (Default)", "Slate Teal", "Midnight Clinical"])
    with col2:
        st.selectbox("Language", ["English", "Hindi", "Kannada", "Tamil", "Telugu"])
        st.selectbox("Date Format", ["DD-MM-YYYY", "MM-DD-YYYY", "YYYY-MM-DD"])
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="uic-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Notifications</div>', unsafe_allow_html=True)
    st.checkbox("Email alerts for high-risk patients", value=True)
    st.checkbox("Weekly summary digest", value=True)
    st.checkbox("New upload notifications", value=False)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="uic-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Account</div>', unsafe_allow_html=True)
    st.text_input("Display Name", value="Dr. A. Krishnan")
    st.text_input("Hospital / Clinic", value="Apex Wound Care Center")
    if st.button("💾 Save Settings"):
        st.success("Settings saved successfully.")
    st.markdown("</div>", unsafe_allow_html=True)
