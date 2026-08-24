"""
patient_search.py
------------------
Renders the patient search card: case ID search box, recent patients
dropdown, and demographic / clinical filters.
"""

import streamlit as st


def render_patient_search(roster) -> str:
    """Render search & filter UI. Returns the selected case_id."""
    
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
        typed_id = manual_id.strip()
        match = roster[roster["case_id"].str.lower() == typed_id.lower()]
        if not match.empty:
            selected_case_id = match.iloc[0]["case_id"]
        else:
            selected_case_id = typed_id

    
    
    return selected_case_id
