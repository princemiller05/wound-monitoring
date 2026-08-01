"""
app.py
------
Entry point for the "Wound Monitoring – Doctor Dashboard" Streamlit
application. Handles page configuration, global styling, sidebar
navigation and routing to individual page modules.

Run with:
    streamlit run app.py
"""

import streamlit as st

from utils.helpers import load_css
from utils.data_generator import generate_patient_roster
from components.sidebar_nav import render_sidebar
from components.footer import render_footer
from pages_logic import dashboard, patient_history, upload_images, ai_analysis, reports, settings


def configure_page() -> None:
    st.set_page_config(
        page_title="Wound Monitoring – Doctor Dashboard",
        page_icon="🩺",
        layout="wide",
        initial_sidebar_state="expanded",
    )


@st.cache_data(show_spinner=False)
def load_patient_roster():
    """Cached synthetic patient roster — replace with EMR/DB query in production."""
    return generate_patient_roster(n=48)


def main() -> None:
    configure_page()
    load_css("styles/custom.css")

    df = load_patient_roster()
    selected_page = render_sidebar()

    routes = {
        "Dashboard": lambda: dashboard.render(df),
        "Patient History": lambda: patient_history.render(df),
        "Upload Images": lambda: upload_images.render(df),
        "AI Analysis": lambda: ai_analysis.render(df),
        "Reports": lambda: reports.render(df),
        "Settings": lambda: settings.render(),
    }

    routes[selected_page]()
    render_footer()


if __name__ == "__main__":
    main()
