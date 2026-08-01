"""
kpi_cards.py
------------
Renders the top-of-dashboard KPI summary cards (Total Patients,
Healing Rate, High Risk Cases, Avg Healing Probability).
"""

import streamlit as st

from utils.helpers import trend_html

KPI_CONFIG = [
    {"key": "total_patients", "icon": "👥", "label": "Total Patients",
     "suffix": "", "trend": 4.2},
    {"key": "healing_rate", "icon": "✅", "label": "Healing Rate",
     "suffix": "%", "trend": 2.8},
    {"key": "high_risk_cases", "icon": "⚠️", "label": "High Risk Cases",
     "suffix": "", "trend": -1.5},
    {"key": "avg_healing_probability", "icon": "📈", "label": "Avg. Healing Probability",
     "suffix": "%", "trend": 3.1},
]


def render_kpi_row(kpis: dict) -> None:
    """Render a responsive 4-column row of KPI cards."""
    cols = st.columns(4)
    for col, cfg in zip(cols, KPI_CONFIG):
        value = kpis[cfg["key"]]
        with col:
            st.markdown(
                f"""
                <div class="kpi-card">
                    {trend_html(cfg['trend'])}
                    <div class="kpi-icon">{cfg['icon']}</div>
                    <div class="kpi-value">{value}{cfg['suffix']}</div>
                    <div class="kpi-label">{cfg['label']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
