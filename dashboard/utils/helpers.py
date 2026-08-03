"""
helpers.py
----------
Small, reusable utility functions shared across components and pages.
Keeping these separate enforces a clean split between UI rendering
and generic logic / formatting.
"""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent


def load_css(*relative_paths: str) -> None:
    """Inject one or more CSS files into the Streamlit app."""
    css = ""
    for rel in relative_paths:
        path = ROOT_DIR / rel
        if path.exists():
            css += path.read_text()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def status_badge_class(status: str) -> str:
    """Map a healing status string to its CSS badge class."""
    return {
        "Healing": "badge-healing",
        "Stable": "badge-stable",
        "Non-Healing": "badge-nonhealing",
    }.get(status, "badge-stable")


def risk_badge_class(risk: str) -> str:
    return {
        "Low": "badge-risk-low",
        "Medium": "badge-risk-medium",
        "High": "badge-risk-high",
    }.get(risk, "badge-risk-medium")


def status_color(status: str) -> str:
    return {
        "Healing": "#16A34A",
        "Stable": "#F59E0B",
        "Non-Healing": "#DC2626",
    }.get(status, "#F59E0B")


def trend_html(value: float, suffix: str = "%") -> str:
    """Render a small up/down/flat trend pill as HTML."""
    if value > 0:
        cls, arrow = "trend-up", "▲"
    elif value < 0:
        cls, arrow = "trend-down", "▼"
    else:
        cls, arrow = "trend-flat", "•"
    return f'<span class="kpi-trend {cls}">{arrow} {abs(value)}{suffix}</span>'

def get_initials(name: str) -> str:
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return name[:2].upper()


def df_to_csv_bytes(df) -> bytes:
    """Convert a DataFrame to a download-ready CSV byte string."""
    return df.to_csv(index=False).encode("utf-8")
