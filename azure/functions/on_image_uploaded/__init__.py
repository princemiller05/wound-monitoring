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
import time

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
    blob_name looks like 'wound-photos/CASE_001/CASE_001_DAY7_1723100000000.jpg'
    (it may or may not include the container prefix). The trailing number is the
    capture timestamp in milliseconds, which makes each photo unique so nothing
    overwrites and multiple photos on the same day can coexist honestly.

    Returns (patient_id, day_number, image_id, captured_ms).
    """
    # Drop the container prefix if present, keep the rest of the path.
    path = blob_name.split("wound-photos/", 1)[-1]
    parts = path.split("/")
    filename = parts[-1]                       # CASE_001_DAY7_1723100000000.jpg
    patient_id = parts[0] if len(parts) > 1 else filename.split("_DAY")[0]

    m = re.search(r"_DAY(\d+)", filename)
    if not m:
        raise ValueError(f"Filename '{filename}' has no _DAY<n> — cannot parse day.")
    day_number = int(m.group(1))

    # Unique per-photo id (the whole filename without extension). Because it
    # includes the timestamp, two photos on the same day get different ids.
    image_id = os.path.splitext(filename)[0]

    ts = re.search(r"_(\d+)\.jpg$", filename, re.IGNORECASE)
    captured_ms = int(ts.group(1)) if ts else 0

    return patient_id, day_number, image_id, captured_ms


def _call_ml(image_bytes: bytes, case_id: str, image_id: str) -> dict:
    """Send the photo to the ML endpoint (base64) and return its `result`.

    The managed endpoint can cold-start or hiccup, which used to drop the photo
    from the trend entirely. Retry a few times before giving up so transient
    failures recover on their own.
    """
    payload = {
        "image_base64": base64.b64encode(image_bytes).decode("utf-8"),
        "case_id": case_id,
        "image_id": image_id,
        "simulate_mode": "healing",
        "seed": 42,
        "save": False,
    }
    last_err = None
    for attempt in range(3):
        try:
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
        except Exception as exc:
            last_err = exc
            if attempt < 2:
                time.sleep(5 * (attempt + 1))  # 5s, then 10s — let a cold start warm up
    raise last_err


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
    patient_id, day_number, image_id, captured_ms = _parse_ids(blob.name)
    blob_path = blob.name.split("wound-photos/", 1)[-1]

    # 1) analyse this one photo.
    #    #26 — if analysis fails, write analyzed:false with the error instead of
    #    silently doing nothing (otherwise the app shows "analysing" forever).
    try:
        result = _call_ml(blob.read(), patient_id, image_id)
    except Exception as exc:
        db.collection("wound_photos").document(image_id).set({
            "patient_id": patient_id,
            "day_number": day_number,
            "captured_ms": captured_ms,
            "blob_path": blob_path,
            "analyzed": False,
            "error": str(exc),
        }, merge=True)
        raise  # let Azure log/retry it too

    seg = result["segmentation"]
    tis = result["tissue"]
    heal = result["healing"]

    # 2) save the per-photo result. Keyed by the unique image_id (which includes
    #    the timestamp), so every photo is its own record — no overwriting.
    #    #24 — also save the quality flags the model already produced.
    db.collection("wound_photos").document(image_id).set({
        "patient_id": patient_id,
        "day_number": day_number,
        "captured_ms": captured_ms,
        "blob_path": blob_path,
        "area_px": seg["area_px"],
        "area_mm2": seg.get("area_mm2"),          # #30 real measurement (or None)
        "pixels_per_mm": seg.get("pixels_per_mm"),
        "granulation_pct": tis["granulation_pct"],
        "slough_pct": tis["slough_pct"],
        "necrosis_pct": tis["necrosis_pct"],
        "healing_probability": heal["healing_probability"],
        "predicted_label": heal["predicted_label"],
        # #24 quality flags
        "detection_failed": seg.get("detection_failed", False),
        "classifier_warning": tis.get("classifier_warning", ""),
        "total_patches": tis.get("total_patches"),
        "yolo_conf": seg.get("yolo_conf"),
        "analyzed": True,
        "error": firestore.DELETE_FIELD,  # clear any earlier failure marker
    }, merge=True)

    # 3) gather every analysed photo for this patient
    docs = (db.collection("wound_photos")
              .where("patient_id", "==", patient_id)
              .where("analyzed", "==", True).stream())
    all_rows = [d.to_dict() for d in docs]

    # The healing trend is one point per DAY, so if a patient took several
    # photos on the same day we keep the most recent one for that day.
    by_day = {}
    for r in all_rows:
        d = r.get("day_number", 0)
        if d not in by_day or r.get("captured_ms", 0) >= by_day[d].get("captured_ms", 0):
            by_day[d] = r
    rows = sorted(by_day.values(), key=lambda x: x["day_number"])

    area_series = [r["area_px"] for r in rows]
    n_visits = len(rows)

    # 4) build the summary the app + dashboard read, and store it on the patient.
    #    #25 — a healing score from a single photo is meaningless (it comes from
    #    an artificial simulated shrink). Show "waiting for second visit" until
    #    there are at least two real visits.
    latest = rows[-1]
    enough = n_visits >= 2
    # Newest capture time across ALL photos (not just the per-day trend) — the
    # dashboard uses this to flag "new since last review".
    latest_photo_ms = max((r.get("captured_ms", 0) for r in all_rows), default=0)
    summary = {
        "visits": n_visits,
        "enough_visits": enough,
        "latest_photo_ms": latest_photo_ms,
        "healing_probability": latest["healing_probability"] if enough else None,
        "predicted_label": latest["predicted_label"] if enough else "pending",
        "trend": _trend(area_series) if enough else "pending",
        "day_series": [r["day_number"] for r in rows],
        "area_series": area_series,
        "area_mm2_series": [r.get("area_mm2") for r in rows],  # #30
        # #55 — per-visit healing values so the dashboard graph isn't a flat line.
        "healing_series": [r.get("healing_probability") for r in rows],
        "tissue_series": {
            "granulation": [r["granulation_pct"] for r in rows],
            "slough": [r["slough_pct"] for r in rows],
            "necrosis": [r["necrosis_pct"] for r in rows],
        },
        # carry the latest photo's quality flags up to the summary (#48)
        "last_detection_failed": latest.get("detection_failed", False),
        "last_classifier_warning": latest.get("classifier_warning", ""),
        "updated_at": firestore.SERVER_TIMESTAMP,
    }
    db.collection("patients").document(patient_id).set(
        {"latest_prediction": summary}, merge=True)
