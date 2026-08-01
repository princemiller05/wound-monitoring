"""
data_generator.py
------------------
Generates realistic, deterministic synthetic data for the Wound Monitoring
Doctor Dashboard demo. In production this module would be replaced with
calls to the hospital EMR / Azure ML inference backend.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Deterministic randomness so the demo looks consistent across reruns
_RNG = np.random.default_rng(42)

FIRST_NAMES = ["Ramesh", "Sunita", "Arvind", "Kavita", "Manoj", "Pooja",
                "Suresh", "Anjali", "Vikram", "Deepa", "Rajesh", "Neha",
                "Ashok", "Meena", "Sanjay", "Lata"]
LAST_NAMES = ["Sharma", "Iyer", "Reddy", "Nair", "Gupta", "Verma",
               "Patel", "Joshi", "Rao", "Menon", "Singh", "Kapoor"]
DOCTORS = ["Dr. A. Krishnan", "Dr. S. Mehta", "Dr. R. Banerjee",
           "Dr. P. Subramaniam", "Dr. N. Fernandes"]
STAGES = ["Granulation", "Inflammatory", "Epithelialization", "Proliferative"]
STATUS_OPTIONS = ["Healing", "Stable", "Non Healing"]
DIABETES_TYPES = ["Type 1", "Type 2"]


def _make_patient_id(i: int) -> str:
    return f"DFU-{2024000 + i}"


def generate_patient_roster(n: int = 48) -> pd.DataFrame:
    """Generate a roster of synthetic DFU patients with summary stats."""
    rows = []
    for i in range(1, n + 1):
        name = f"{_RNG.choice(FIRST_NAMES)} {_RNG.choice(LAST_NAMES)}"
        age = int(_RNG.integers(38, 79))
        gender = _RNG.choice(["Male", "Female"], p=[0.58, 0.42])
        diabetes = _RNG.choice(DIABETES_TYPES, p=[0.12, 0.88])
        status = _RNG.choice(STATUS_OPTIONS, p=[0.52, 0.31, 0.17])
        healing_prob = {
            "Healing": _RNG.uniform(70, 96),
            "Stable": _RNG.uniform(45, 70),
            "Non Healing": _RNG.uniform(10, 45),
        }[status]
        risk = "Low" if healing_prob > 70 else ("Medium" if healing_prob > 45 else "High")
        rows.append({
            "patient_id": _make_patient_id(i),
            "name": name,
            "age": age,
            "gender": gender,
            "diabetes_type": diabetes,
            "doctor": _RNG.choice(DOCTORS),
            "stage": _RNG.choice(STAGES),
            "status": status,
            "healing_probability": round(healing_prob, 1),
            "risk_level": risk,
            "last_visit_days_ago": int(_RNG.integers(0, 14)),
            "wound_area_cm2": round(_RNG.uniform(1.5, 12.0), 1),
            "confidence": round(_RNG.uniform(78, 98), 1),
        })
    return pd.DataFrame(rows)


def get_patient_record(df: pd.DataFrame, patient_id: str) -> pd.Series | None:
    match = df[df["patient_id"] == patient_id]
    if match.empty:
        return None
    return match.iloc[0]


def generate_visit_timeline(patient_id: str, base_prob: float, n_visits: int = 6) -> pd.DataFrame:
    """Generate a longitudinal visit history for a single patient."""
    seed = abs(hash(patient_id)) % (2**32)
    rng = np.random.default_rng(seed)
    days = sorted(rng.choice(range(0, 90), size=n_visits, replace=False))
    days[0] = 0
    days = sorted(days)

    area0 = rng.uniform(6, 14)
    rows = []
    area = area0
    prob = max(10, base_prob - rng.uniform(15, 30))
    for idx, d in enumerate(days):
        reduction = rng.uniform(0.04, 0.14) * area
        area = max(0.3, area - reduction)
        prob = min(98, prob + rng.uniform(2, 9))
        granulation = min(90, 30 + idx * rng.uniform(6, 11))
        necrosis = max(2, 25 - idx * rng.uniform(3, 6))
        slough = max(2, 100 - granulation - necrosis)
        rows.append({
            "visit": idx + 1,
            "day": d,
            "date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=int(d)),
            "wound_area_cm2": round(area, 2),
            "healing_probability": round(prob, 1),
            "granulation_pct": round(granulation, 1),
            "slough_pct": round(slough, 1),
            "necrosis_pct": round(necrosis, 1),
            "area_reduction_pct": round(100 * (area0 - area) / area0, 1),
        })
    return pd.DataFrame(rows)


def generate_weekly_progress(n_weeks: int = 8) -> pd.DataFrame:
    weeks = [f"W{i+1}" for i in range(n_weeks)]
    base = _RNG.uniform(40, 55)
    values = []
    for i in range(n_weeks):
        base += _RNG.uniform(3, 8)
        values.append(min(97, round(base, 1)))
    return pd.DataFrame({"week": weeks, "progress_pct": values})


def get_top_factors() -> list[dict]:
    return [
        {"factor": "Granulation tissue increasing steadily", "impact": "Positive"},
        {"factor": "Wound area reduced 38% over last 3 visits", "impact": "Positive"},
        {"factor": "Peri-wound erythema present", "impact": "Negative"},
        {"factor": "HbA1c trending within target range", "impact": "Positive"},
        {"factor": "Mild slough detected at wound margin", "impact": "Neutral"},
    ]


def get_recommendations() -> list[str]:
    return [
        "Continue current offloading protocol and moist wound therapy.",
        "Reassess in 7 days with standardized imaging under consistent lighting.",
        "Monitor for signs of peri-wound infection at next dressing change.",
        "Reinforce glycemic control counseling — target HbA1c < 7%.",
    ]


def get_warnings(risk_level: str) -> list[str]:
    if risk_level == "High":
        return [
            "Elevated risk of non-healing trajectory — consider vascular referral.",
            "Wound area reduction has plateaued over last 2 visits.",
            "Signs of possible infection should be ruled out clinically.",
        ]
    if risk_level == "Medium":
        return [
            "Healing trend is stable but slower than expected benchmark.",
            "Recommend close monitoring over next 2 visits.",
        ]
    return ["No critical warnings — wound is progressing as expected."]


def get_clinical_notes() -> str:
    return (
        "Patient demonstrates favorable granulation tissue formation with "
        "reducing wound dimensions across recent visits. Offloading compliance "
        "reported as good. Continue current care pathway and reassess in one week."
    )
