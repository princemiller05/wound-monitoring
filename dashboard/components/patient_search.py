"""
patient_search.py
------------------
Renders the patient search card: case ID search box, recent patients
dropdown, and demographic / clinical filters.
"""

import streamlit as st


def render_patient_search(roster) -> str:
    """Render search & filter UI. Returns the selected case_id."""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-title">🔍 Patient Search</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([2.2, 1, 1.4])
    with c1:
        recent = st.selectbox(
            "Recent patients",
            options=roster["case_id"] + " — " + roster["name"],
            index=0,
        )
        selected_case_id = recent.split(" — ")[0]
    with c2:
        manual_id = st.text_input("Search by Case ID", placeholder="e.g. DFU-1007")
    with c3:
        st.write("")
        st.write("")
        search_clicked = st.button("🔎 Search Patient", use_container_width=True)

    if search_clicked and manual_id.strip():
        match = roster[roster["case_id"].str.lower() == manual_id.strip().lower()]
        if not match.empty:
            selected_case_id = match.iloc[0]["case_id"]
        else:
            st.warning(f"No patient found with Case ID '{manual_id}'.")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        st.select_slider("Age range", options=list(range(30, 90, 5)),
                          value=(40, 80))
    with f2:
        st.multiselect("Gender", ["Male", "Female"], default=["Male", "Female"])
    with f3:
        st.multiselect("Diabetes Type", ["Type 1", "Type 2"],
                        default=["Type 1", "Type 2"])
    with f4:
        st.multiselect("Healing Status", ["Healing", "Stable", "Non-Healing"],
                        default=["Healing", "Stable", "Non-Healing"])

    st.markdown("</div>", unsafe_allow_html=True)
    return selected_case_id
