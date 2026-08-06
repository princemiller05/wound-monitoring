"""
Job 3 — Auto-run the model on every uploaded photo.

This function fires automatically whenever a patient's app uploads a photo to
Blob Storage. It:

  1. Reads the photo bytes straight from the blob trigger.
  2. Works out the patient id and day number from the filename
     (CASE_001/CASE_001_DAY7.jpg  ->  patient=CASE_001, day=7).
  3. Sends the photo (base64) to Shubam's Azure ML endpoint and gets back
     segmentation + tissue + healing.
  4. Saves those numbers onto that photo's Firestore document.
  5. Gathers ALL of the patient's analysed photos so far, builds the
     longitudinal series + a simple trend, and saves it as the patient's
     latest_prediction (that's what the doctor dashboard / app read).

Why we build the summary ourselves instead of a second endpoint call: the live
endpoint analyses ONE image and returns a healing estimate for it — it has no
"aggregate" mode. So the day-by-day trend is just the stored per-photo results
read back together.

App settings this function needs (set in the Function App -> Configuration):
  AZURE_STORAGE_CONNECTION_STRING   (used by the blob trigger)
  ML_ENDPOINT_URI                   (Shubam's scoring URL)
  ML_ENDPOINT_KEY                   (Shubam's primary key — secret!)
  FIREBASE_CREDENTIALS              (Firebase service-account JSON, as one string)
"""

import base64
import json
import os
import re

import requests
import azure.functions as func

import firebase_admin
from firebase_admin import credentials, firestore

# --- Initialise Firebase once per worker ---
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(os.environ["FIREBASE_CREDENTIALS"]))
    firebase_admin.initialize_app(cred)
db = firestore.client()

ML_URI = os.environ["ML_ENDPOINT_URI"]
ML_KEY = os.environ["ML_ENDPOINT_KEY"]


def _parse_ids(blob_name: str):
    """
    blob_name looks like 'wound-photos/CASE_001/CASE_001_DAY7.jpg' (it may or
    may not include the container prefix). Returns (patient_id, day_number,
    image_id) or raises ValueError if the filename doesn't follow the rule.
    """
    # Drop the container prefix if present, keep the rest of the path.
    path = blob_name.split("wound-photos/", 1)[-1]
    parts = path.split("/")
    filename = parts[-1]                       # CASE_001_DAY7.jpg
    patient_id = parts[0] if len(parts) > 1 else filename.split("_DAY")[0]

    m = re.search(r"_DAY(\d+)", filename)
    if not m:
        raise ValueError(f"Filename '{filename}' has no _DAY<n> — cannot parse day.")
    day_number = int(m.group(1))
    image_id = os.path.splitext(filename)[0]   # CASE_001_DAY7
    return patient_id, day_number, image_id


def _call_ml(image_bytes: bytes, case_id: str, image_id: str) -> dict:
    """Send the photo to the ML endpoint (base64) and return its `result`."""
    payload = {
        "image_base64": base64.b64encode(image_bytes).decode("utf-8"),
        "case_id": case_id,
        "image_id": image_id,
        "simulate_mode": "healing",
        "seed": 42,
        "save": False,
    }
    r = requests.post(
        ML_URI,
        data=json.dumps(payload),
        headers={"Authorization": "Bearer " + ML_KEY,
                 "Content-Type": "application/json"},
        timeout=180,
    )
    r.raise_for_status()
    body = r.json()
    if body.get("status") != "success":
        raise RuntimeError(f"Endpoint error: {body}")
    return body["result"]


def _trend(area_series):
    """Improving if the wound is shrinking overall, worsening if growing."""
    if len(area_series) < 2:
        return "stable"
    change = (area_series[-1] - area_series[0]) / max(area_series[0], 1)
    if change <= -0.05:
        return "improving"
    if change >= 0.05:
        return "worsening"
    return "stable"


def main(blob: func.InputStream):
    patient_id, day_number, image_id = _parse_ids(blob.name)

    # 1) analyse this one photo
    result = _call_ml(blob.read(), patient_id, image_id)
    seg = result["segmentation"]
    tis = result["tissue"]
    heal = result["healing"]

    # 2) save the per-photo result. We key the doc by image_id so this is
    #    idempotent and doesn't depend on the app having written the doc first.
    db.collection("wound_photos").document(image_id).set({
        "patient_id": patient_id,
        "day_number": day_number,
        "blob_path": blob.name.split("wound-photos/", 1)[-1],
        "area_px": seg["area_px"],
        "granulation_pct": tis["granulation_pct"],
        "slough_pct": tis["slough_pct"],
        "necrosis_pct": tis["necrosis_pct"],
        "healing_probability": heal["healing_probability"],
        "predicted_label": heal["predicted_label"],
        "analyzed": True,
    }, merge=True)

    # 3) gather every analysed photo for this patient, sorted by day
    docs = (db.collection("wound_photos")
              .where("patient_id", "==", patient_id)
              .where("analyzed", "==", True).stream())
    rows = sorted([d.to_dict() for d in docs], key=lambda x: x["day_number"])

    area_series = [r["area_px"] for r in rows]

    # 4) build the summary the app + dashboard read, and store it on the patient
    latest = rows[-1]
    summary = {
        "healing_probability": latest["healing_probability"],
        "predicted_label": latest["predicted_label"],
        "trend": _trend(area_series),
        "day_series": [r["day_number"] for r in rows],
        "area_series": area_series,
        "tissue_series": {
            "granulation": [r["granulation_pct"] for r in rows],
            "slough": [r["slough_pct"] for r in rows],
            "necrosis": [r["necrosis_pct"] for r in rows],
        },
        "updated_at": firestore.SERVER_TIMESTAMP,
    }
    db.collection("patients").document(patient_id).set(
        {"latest_prediction": summary}, merge=True)
