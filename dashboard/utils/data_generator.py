"""
data_generator.py
------------------
Generates realistic synthetic data for the Wound Monitoring Dashboard.
In production, this module would be replaced by API calls to the
Azure-hosted backend / clinical database. Kept isolated here so the
UI layer never needs to know where data actually comes from.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

FIRST_NAMES = ["Ramesh", "Sunita", "Arvind", "Lakshmi", "Mohammed", "Priya",
               "Vijay", "Anjali", "Suresh", "Kavitha", "Rajesh", "Meera"]
LAST_NAMES = ["Kumar", "Sharma", "Reddy", "Iyer", "Nair", "Patel",
              "Singh", "Rao", "Gupta", "Menon"]
DOCTORS = ["Dr. Anil Mehta", "Dr. Kavya Subramanian", "Dr. Rohan Desai",
           "Dr. Fatima Khan"]
DIABETES_TYPES = ["Type 1", "Type 2"]
STAGES = ["Inflammatory", "Proliferative", "Remodeling", "Granulation"]
STATUSES = ["Healing", "Stable", "Non-Healing"]
RISK_LEVELS = ["Low", "Medium", "High"]


def _random_date(days_back: int = 30) -> str:
    d = datetime.now() - timedelta(days=random.randint(0, days_back))
    return d.strftime("%d %b %Y")


def generate_patient_list(n: int = 48) -> pd.DataFrame:
    """Generate the master patient roster used across the dashboard."""
    rows = []
    for i in range(1, n + 1):
        status = random.choices(STATUSES, weights=[0.5, 0.32, 0.18])[0]
        risk = {"Healing": "Low", "Stable": "Medium",
                "Non-Healing": "High"}[status]
        rows.append({
            "case_id": f"DFU-{1000 + i}",
            "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "age": random.randint(38, 78),
            "gender": random.choice(["Male", "Female"]),
            "diabetes_type": random.choice(DIABETES_TYPES),
            "doctor": random.choice(DOCTORS),
            "last_visit": _random_date(14),
            "stage": random.choice(STAGES),
            "status": status,
            "risk_level": risk,
            "healing_probability": {
                "Healing": random.randint(72, 96),
                "Stable": random.randint(45, 71),
                "Non-Healing": random.randint(10, 44),
            }[status],
        })
    return pd.DataFrame(rows)


def get_patient_detail(case_id: str, roster: pd.DataFrame) -> dict:
    """Fetch a single patient record as a dict, with sensible fallback."""
    match = roster[roster["case_id"] == case_id]
    if match.empty:
        match = roster.iloc[[0]]
    return match.iloc[0].to_dict()


def generate_wound_timeseries(visits: int = 6) -> pd.DataFrame:
    """Generate longitudinal wound metrics (area, probability, tissue mix)."""
    start_area = random.uniform(8.0, 14.0)
    dates = [datetime.now() - timedelta(days=7 * (visits - i - 1))
             for i in range(visits)]
    area, prob, granulation, slough, necrosis = [], [], [], [], []
    cur_area = start_area
    cur_prob = random.uniform(28, 40)
    for i in range(visits):
        cur_area *= random.uniform(0.80, 0.94)
        cur_prob = min(97, cur_prob + random.uniform(4, 11))
        area.append(round(cur_area, 2))
        prob.append(round(cur_prob, 1))
        g = max(5, min(85, 30 + i * 9 + random.uniform(-5, 5)))
        n = max(2, 25 - i * 4 + random.uniform(-3, 3))
        s = max(2, 100 - g - n)
        total = g + n + s
        granulation.append(round(g / total * 100, 1))
        necrosis.append(round(n / total * 100, 1))
        slough.append(round(s / total * 100, 1))

    return pd.DataFrame({
        "visit_date": [d.strftime("%d %b") for d in dates],
        "day": [f"Day {i*7}" for i in range(visits)],
        "wound_area_cm2": area,
        "healing_probability": prob,
        "granulation_pct": granulation,
        "slough_pct": slough,
        "necrosis_pct": necrosis,
    })


def compute_kpis(roster: pd.DataFrame) -> dict:
    """Aggregate roster-level KPIs for the top dashboard cards."""
    total = len(roster)
    healing_rate = round((roster["status"] == "Healing").mean() * 100, 1)
    high_risk = int((roster["risk_level"] == "High").sum())
    avg_prob = round(roster["healing_probability"].mean(), 1)
    return {
        "total_patients": total,
        "healing_rate": healing_rate,
        "high_risk_cases": high_risk,
        "avg_healing_probability": avg_prob,
    }


def generate_ai_insights(status: str) -> dict:
    """Return canned-but-plausible AI insight content keyed by status."""
    base = {
        "top_factors": [
            ("Granulation tissue increasing steadily", "dot-green"),
            ("Wound edge contraction visible week-over-week", "dot-green"),
            ("Peri-wound erythema reduced vs last visit", "dot-blue"),
            ("Patient-reported pain score trending down", "dot-blue"),
        ],
        "recommendations": [
            "Continue current offloading regimen",
            "Maintain moist wound dressing protocol",
            "Re-image in 7 days for trend confirmation",
            "Reinforce glycemic control counselling",
        ],
        "warnings": [
            "Mild maceration noted at wound margin",
            "HbA1c last recorded > 90 days ago",
        ],
        "clinical_notes": (
            "Wound bed shows predominantly red granulation tissue with "
            "reducing slough percentage. No signs of clinical infection. "
            "Continue current treatment trajectory and monitor for "
            "epithelial migration at margins."
        ),
        "risk_indicators": [
            ("Peripheral neuropathy", "Moderate"),
            ("Peripheral arterial disease", "Low"),
            ("Infection risk", "Low"),
            ("Re-ulceration risk", "Moderate"),
        ],
    }
    if status == "Non-Healing":
        base["top_factors"] = [
            ("Slough coverage increased since last visit", "dot-red"),
            ("Wound area reduction stalled (<5% / 2 weeks)", "dot-red"),
            ("Possible biofilm formation at wound bed", "dot-orange"),
            ("Elevated peri-wound temperature differential", "dot-orange"),
        ]
        base["warnings"] = [
            "Signs suggestive of localized infection — clinical review advised",
            "HbA1c elevated — refer for endocrinology follow-up",
            "Vascular assessment recommended (ABI screening)",
        ]
        base["clinical_notes"] = (
            "Wound shows delayed healing trajectory with increased slough "
            "and stalled area reduction. Recommend urgent in-person "
            "evaluation, wound culture, and vascular workup."
        )
    elif status == "Stable":
        base["warnings"] = [
            "Healing rate plateauing — consider advanced therapy options",
            "Monitor for early infection signs at next visit",
        ]
    return base


def generate_reasons(status: str) -> list[str]:
    mapping = {
        "Healing": ["Area reduced 18% over 2 weeks", "Granulation tissue dominant",
                    "No infection markers detected"],
        "Stable": ["Area reduction below expected rate", "Mixed tissue composition",
                   "Pain score unchanged"],
        "Non-Healing": ["Area increased since last visit", "High slough/necrosis ratio",
                         "Possible infection indicators"],
    }
    return mapping.get(status, mapping["Stable"])
