"""
patient_search.py
------------------
Renders the patient search card: a single "Search by Case ID" box and
its search button.
"""

import streamlit as st


def render_patient_search(roster) -> str:
    """Render the patient search UI. Returns the selected case_id."""

    st.markdown(
        '<div class="section-title">🔍 Patient Search</div>',
        unsafe_allow_html=True,
    )

    # With no dropdown, keep showing whichever patient is already selected
    # until a new search is run. Streamlit reruns this script on every widget
    # interaction, so falling back to the persisted id (rather than the first
    # roster entry) stops the selection resetting on unrelated interactions.
    selected_case_id = st.session_state.get(
        "selected_case_id", roster.iloc[0]["case_id"]
    )

    c1, c2 = st.columns([3, 1])
    with c1:
        manual_id = st.text_input("Search by Case ID", placeholder="e.g. DFU-1007")
    with c2:
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
