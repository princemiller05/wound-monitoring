"""
Local test of the auto-run pipeline logic — WITHOUT any Azure resources.

This does exactly what the on_image_uploaded Azure Function will do, but you run
it from your laptop against a LOCAL image. It proves, before you deploy anything:
  - your Firebase credentials work (it writes to Firestore)
  - the ML endpoint call works
  - the per-photo -> patient-summary aggregation is correct

Run it a few times with different day numbers to build a real healing trend in
Firestore, then open the Firebase console (Firestore) and watch the documents
appear. That's your Jobs 2 & 3 logic validated with zero Azure.

Setup (one time):
    pip install firebase-admin requests

Run (PowerShell):
    $env:WW_KEY = "<Shubam's endpoint primary key>"
    $env:FIREBASE_CRED_PATH = "C:\\path\\to\\your\\firebase-key.json"
    python azure/local_test_pipeline.py "dfu_pipeline/data/sample_inputs/woundtst.jpg" CASE_001 0
    python azure/local_test_pipeline.py "dfu_pipeline/data/sample_inputs/woundtst2.jpg" CASE_001 7
"""

import base64
import json
import os
import sys

import requests
import firebase_admin
from firebase_admin import credentials, firestore

SCORING_URL = "https://woundwatch-endpoint-v2.eastus.inference.ml.azure.com/score"
ML_KEY = os.environ.get("WW_KEY")
CRED_PATH = os.environ.get("FIREBASE_CRED_PATH")

if not ML_KEY:
    sys.exit('Set the endpoint key:  $env:WW_KEY = "<primary key>"')
if not CRED_PATH or not os.path.exists(CRED_PATH):
    sys.exit('Set the Firebase key path:  $env:FIREBASE_CRED_PATH = "C:\\...\\firebase-key.json"')

# --- args ---
if len(sys.argv) < 4:
    sys.exit("Usage: python local_test_pipeline.py <image> <patient_id> <day_number>")
image_path, patient_id, day_number = sys.argv[1], sys.argv[2], int(sys.argv[3])
image_id = f"{patient_id}_DAY{day_number}"

# --- init Firebase ---
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(CRED_PATH))
db = firestore.client()


def call_ml(path, case_id, img_id):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    payload = {"image_base64": b64, "case_id": case_id, "image_id": img_id,
               "simulate_mode": "healing", "seed": 42, "save": False}
    r = requests.post(SCORING_URL, data=json.dumps(payload), timeout=180,
                      headers={"Authorization": "Bearer " + ML_KEY,
                               "Content-Type": "application/json"})
    r.raise_for_status()
    body = r.json()
    if body.get("status") != "success":
        raise RuntimeError(body)
    return body["result"]


def trend(area_series):
    if len(area_series) < 2:
        return "stable"
    change = (area_series[-1] - area_series[0]) / max(area_series[0], 1)
    return "improving" if change <= -0.05 else "worsening" if change >= 0.05 else "stable"


print(f"Analysing {image_path} as {image_id} ...")
result = call_ml(image_path, patient_id, image_id)
seg, tis, heal = result["segmentation"], result["tissue"], result["healing"]

# 1) per-photo result
db.collection("wound_photos").document(image_id).set({
    "patient_id": patient_id,
    "day_number": day_number,
    "area_px": seg["area_px"],
    "granulation_pct": tis["granulation_pct"],
    "slough_pct": tis["slough_pct"],
    "necrosis_pct": tis["necrosis_pct"],
    "healing_probability": heal["healing_probability"],
    "predicted_label": heal["predicted_label"],
    "analyzed": True,
}, merge=True)
print(f"  wound_photos/{image_id}: area={seg['area_px']}px, "
      f"healing={heal['healing_probability']}")

# 2) rebuild the patient summary from all analysed photos
docs = (db.collection("wound_photos")
          .where("patient_id", "==", patient_id)
          .where("analyzed", "==", True).stream())
rows = sorted([d.to_dict() for d in docs], key=lambda x: x["day_number"])
area_series = [r["area_px"] for r in rows]
latest = rows[-1]
summary = {
    "healing_probability": latest["healing_probability"],
    "predicted_label": latest["predicted_label"],
    "trend": trend(area_series),
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

print(f"\npatients/{patient_id}.latest_prediction:")
print(json.dumps({k: v for k, v in summary.items() if k != "updated_at"}, indent=2))
print("\nDone. Open Firebase console -> Firestore to see the documents.")
