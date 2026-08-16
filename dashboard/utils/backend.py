import os
from datetime import datetime
import pandas as pd
import requests

FUNCTION_BASE_URL = os.getenv(
    "WOUNDWATCH_FUNCTION_URL",
    "https://woundwatch-api-2026.azurewebsites.net/api",
)
FUNCTION_KEY = os.getenv("WOUNDWATCH_FUNCTION_KEY", "")


def get_patient_history(patient_id: str) -> dict:
    """Fetch the patient's latest longitudinal prediction from Azure Functions."""
    if not FUNCTION_KEY:
        raise RuntimeError("WOUNDWATCH_FUNCTION_KEY is not configured.")

    url = f"{FUNCTION_BASE_URL}/get_patient_history"
    response = requests.get(
        url,
        params={"patient_id": patient_id, "code": FUNCTION_KEY},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    if data.get("status") == "no_data":
        raise ValueError(f"No analyzed wound data found for patient {patient_id}.")

    return data


def history_to_dataframe(history: dict) -> pd.DataFrame:
    """Convert the Azure Function response into the dashboard chart format."""
    days = history.get("day_series", [])
    areas = history.get("area_series", [])
    tissue = history.get("tissue_series", {})
    granulation = tissue.get("granulation", [])
    slough = tissue.get("slough", [])
    necrosis = tissue.get("necrosis", [])
    healing_probability = history.get("healing_probability", 0)

    rows = []
    for i, day in enumerate(days):
        rows.append({
            "visit_date": f"Day {day}",
            "day": f"Day {day}",
            "wound_area_px": areas[i] if i < len(areas) else None,
            "healing_probability": healing_probability * 100,
            "granulation_pct": granulation[i] if i < len(granulation) else None,
            "slough_pct": slough[i] if i < len(slough) else None,
            "necrosis_pct": necrosis[i] if i < len(necrosis) else None,
        })

    return pd.DataFrame(rows)


def get_real_patient_data(patient_id: str):
    """Return both the raw prediction and chart-ready DataFrame."""
    history = get_patient_history(patient_id)
    timeseries = history_to_dataframe(history)
    return history, timeseries
STATUS_MAP = {"healing": "Healing", "non_healing": "Non-Healing", "stable": "Stable"}
RISK_MAP = {"Healing": "Low", "Stable": "Medium", "Non-Healing": "High"}


def build_patient_overlay(patient_id: str, roster) -> tuple[dict, dict]:
    """Merge real backend prediction into patient dict. Falls back to
    placeholder demographics if patient_id isn't in the synthetic roster
    (expected right now, since roster IDs are DFU-#### and real IDs are
    CASE_###)."""
    history = get_patient_history(patient_id)

    match = roster[roster["case_id"] == patient_id]
    if match.empty:
        base = {
            "case_id": patient_id,
            "name": "(Real patient — demographics pending)",
            "age": "—",
            "gender": "—",
            "diabetes_type": "—",
            "doctor": "—",
            "last_visit": "—",
            "stage": "—",
        }
    else:
        base = match.iloc[0].to_dict()

    status = STATUS_MAP.get(history["predicted_label"].lower(), "Stable")
    base["status"] = status
    base["risk_level"] = RISK_MAP[status]
    base["healing_probability"] = round(history["healing_probability"] * 100, 1)
    return base, history


def has_real_data(patient_id: str) -> bool:
    """Check whether the Azure Function has real prediction data for this
    patient ID, without raising. Used to decide which data path to use."""
    try:
        get_patient_history(patient_id)
        return True
    except Exception:
        return False