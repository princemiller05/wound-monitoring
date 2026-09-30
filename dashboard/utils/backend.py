"""
Adapter between the dashboard and the Azure Functions backend.

Updated for the new get_patient_history response shape ({status, prediction,
patient}) and the review items:
  #59 — the function key goes in the x-functions-key HEADER, not the ?code= URL
        (which leaks into server logs and browser history). Default hostname is
        empty so a live URL isn't baked into the code.
  #40 — one cached call per patient instead of three separate 30s calls.
  #49 — real patient demographics come from the backend, not a fake roster.
  #55 — per-visit healing values (no more flat line).
  #56 — "pending" status handled; None values guarded.
"""

import os

import pandas as pd
import requests
import streamlit as st

# #59 — read from Streamlit secrets first, then environment, EACH CALL (not once
# at import) so secrets added after the app first loads are picked up. Never
# hardcoded, so no live host/key is baked into the repo.
def _cfg(name: str) -> str:
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.getenv(name, "")


def _base_url() -> str:
    return _cfg("WOUNDWATCH_FUNCTION_URL")


def _key() -> str:
    return _cfg("WOUNDWATCH_FUNCTION_KEY")

STATUS_MAP = {
    "healing": "Healing",
    "non_healing": "Non-Healing",
    "stable": "Stable",
    "pending": "Pending",  # #56
}
RISK_MAP = {"Healing": "Low", "Stable": "Medium",
            "Non-Healing": "High", "Pending": "Low"}


def _call(path: str, params: dict) -> dict:
    base, key = _base_url(), _key()
    if not base or not key:
        raise RuntimeError("WOUNDWATCH_FUNCTION_URL / _KEY not configured.")
    resp = requests.get(
        f"{base}/{path}",
        params=params,
        headers={"x-functions-key": key},  # #59 — key in header
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def _post(path: str, body: dict) -> dict:
    base, key = _base_url(), _key()
    if not base or not key:
        raise RuntimeError("WOUNDWATCH_FUNCTION_URL / _KEY not configured.")
    resp = requests.post(
        f"{base}/{path}",
        json=body,
        headers={"x-functions-key": key},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def mark_reviewed(patient_id: str, doctor_email: str, undo: bool = False) -> dict:
    """Mark reviewed up to the newest photo, or undo (undo=True → needs review)."""
    return _post("mark_reviewed",
                 {"patient_id": patient_id, "doctor_email": doctor_email,
                  "undo": undo})


@st.cache_data(ttl=60, show_spinner=False)
def _fetch_patient(patient_id: str) -> dict:
    """#40 — cached so the page hits the backend once, not three times."""
    return _call("get_patient_history", {"patient_id": patient_id})


def get_patient_history(patient_id: str) -> dict:
    data = _fetch_patient(patient_id)
    if data.get("status") == "no_data" or data.get("prediction") is None:
        raise ValueError(f"No analyzed wound data for patient {patient_id}.")
    return data  # {status, prediction, patient}


def get_doctor_patients(doctor_email: str) -> list:
    """#21 / #38 — the logged-in doctor's real patient list (worst-first)."""
    return _call("get_doctor_patients", {"doctor_email": doctor_email}).get(
        "patients", [])


@st.cache_data(ttl=60, show_spinner=False)
def get_patient_photos(patient_id: str) -> list:
    """The patient's analysed wound photos, each with a short-lived image URL."""
    return _call("get_patient_photos", {"patient_id": patient_id}).get(
        "photos", [])


def backend_configured() -> bool:
    """True when the Azure Function URL + key are set (else we're in demo mode)."""
    return bool(_base_url() and _key())


def history_to_dataframe(history: dict) -> pd.DataFrame:
    """Chart-ready frame. #55 uses per-visit healing; #30 carries mm²."""
    pred = history.get("prediction", {}) or {}
    days = pred.get("day_series", [])
    areas_px = pred.get("area_series", [])
    areas_mm2 = pred.get("area_mm2_series", [])
    healing = pred.get("healing_series", [])
    tissue = pred.get("tissue_series", {})
    gran = tissue.get("granulation", [])
    slough = tissue.get("slough", [])
    necro = tissue.get("necrosis", [])

    def at(seq, i):
        return seq[i] if i < len(seq) else None

    rows = []
    for i, day in enumerate(days):
        hp = at(healing, i)
        rows.append({
            "visit_date": f"Day {day}",
            "day": f"Day {day}",
            "wound_area_px": at(areas_px, i),      # #57 — a pixel count IS an area (px, not px²)
            "wound_area_mm2": at(areas_mm2, i),    # #30 — real measurement when a marker is present
            "healing_probability": (hp * 100) if hp is not None else None,  # #55/#56
            "granulation_pct": at(gran, i),
            "slough_pct": at(slough, i),
            "necrosis_pct": at(necro, i),
        })
    return pd.DataFrame(rows)


def build_patient_overlay(patient_id: str, roster=None) -> tuple[dict, dict]:
    """#49 — real patient details straight from the backend (roster ignored)."""
    history = get_patient_history(patient_id)
    pred = history.get("prediction", {}) or {}
    p = history.get("patient") or {}

    status = STATUS_MAP.get(
        (pred.get("predicted_label") or "pending").lower(), "Pending")
    prob = pred.get("healing_probability")

    base = {
        "case_id": patient_id,
        "name": p.get("full_name") or "(name pending)",
        "age": p.get("age", "—"),
        "gender": p.get("sex", "—"),
        "bmi": p.get("bmi", "—"),
        "height_cm": p.get("height_cm"),
        "weight_kg": p.get("weight_kg"),
        "phone": p.get("phone"),
        # General wound monitor: no diabetes/prior-ulcer registration field.
        "diabetes_type": "—",
        "wound_duration_days": p.get("wound_duration_days"),
        "smoker": p.get("smoker"),          # #50 risk factor
        "prior_ulcer": p.get("prior_ulcer"),
        "doctor": "—",
        # A patient can share with several doctors; show them all.
        "doctor_email": ", ".join(p.get("doctor_emails") or []) or "—",
        "status": status,
        "risk_level": RISK_MAP.get(status, "Low"),
        # #54 — None when there aren't two visits yet; the card shows a message.
        "healing_probability": round(prob * 100, 1) if prob is not None else None,
        "enough_visits": pred.get("enough_visits", False),
        "visits": pred.get("visits", 0),
        # #48 — quality warnings for the banner.
        "last_detection_failed": pred.get("last_detection_failed", False),
        "last_classifier_warning": pred.get("last_classifier_warning", ""),
        # #51 — so old values can be shown with their date.
        "profile_updated_at": p.get("profile_updated_at"),
    }
    return base, history


def get_real_patient_data(patient_id: str):
    history = get_patient_history(patient_id)
    return history, history_to_dataframe(history)


def has_real_data(patient_id: str) -> bool:
    try:
        get_patient_history(patient_id)
        return True
    except Exception:
        return False
