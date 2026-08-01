"""
settings_section.py
--------------------
Renders the Settings page: appearance and localization preferences.
Note: Streamlit's theming is config-driven, so toggles here simulate
the experience and persist to session_state for demo purposes.
"""

import streamlit as st


def render_settings_section() -> None:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">⚙️ Application Settings</div>',
                unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.toggle("🌙 Dark Mode", value=False,
                   help="Theme toggling requires app restart in this prototype")
        st.selectbox("🎨 Theme", ["Clinical Blue", "Slate Gray", "Teal Accent"])
        st.selectbox("🌐 Language", ["English", "हिन्दी", "ಕನ್ನಡ", "தமிழ்"])
    with c2:
        st.markdown(
            """
            <div class="insight-card">
                <div class="insight-title">🔔 Notification Preferences</div>
                <div class="insight-row"><span class="dot dot-blue"></span>
                    <span>High-risk patient alerts</span></div>
                <div class="insight-row"><span class="dot dot-green"></span>
                    <span>Weekly healing summary email</span></div>
                <div class="insight-row"><span class="dot dot-orange"></span>
                    <span>Re-image reminder (7-day cadence)</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.button("💾 Save Settings")
    st.markdown("</div>", unsafe_allow_html=True)
