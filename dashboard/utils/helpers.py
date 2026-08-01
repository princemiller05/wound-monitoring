"""
helpers.py
----------
Small, reusable, side-effect-free helper functions used across the
dashboard. Kept separate from UI components to keep business logic
testable and independent from Streamlit rendering.
"""

from __future__ import annotations

import streamlit as st
from pathlib import Path


def load_css(css_path: str) -> None:
    """Inject a local CSS file into the Streamlit app."""
    css_file = Path(css_path)
    if css_file.exists():
        st.markdown(f"<style>{css_file.read_text()}</style>", unsafe_allow_html=True)


def status_to_badge_class(status: str) -> str:
    """Map a healing status string to a CSS badge class."""
    mapping = {
        "Healing": "badge-green",
        "Stable": "badge-orange",
        "Non Healing": "badge-red",
    }
    return mapping.get(status, "badge-gray")


def risk_to_badge_class(risk: str) -> str:
    mapping = {"Low": "badge-green", "Medium": "badge-orange", "High": "badge-red"}
    return mapping.get(risk, "badge-gray")


def status_to_hex(status: str) -> str:
    mapping = {
        "Healing": "#16A34A",
        "Stable": "#F59E0B",
        "Non Healing": "#DC2626",
    }
    return mapping.get(status, "#64748B")


def trend_arrow(value: float) -> str:
    """Return an HTML snippet representing an up/down/flat trend chip."""
    if value > 0:
        return f'<span class="kpi-trend trend-up">▲ {value:.1f}%</span>'
    if value < 0:
        return f'<span class="kpi-trend trend-down">▼ {abs(value):.1f}%</span>'
    return '<span class="kpi-trend trend-flat">— 0.0%</span>'


def initials(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return name[:2].upper() if name else "PT"
