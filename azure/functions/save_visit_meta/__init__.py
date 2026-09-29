"""
Item #16 — Save the pain level, symptoms and notes the patient entered.

The app collects these on the preview screen but currently discards them. A
patient reporting fever + discharge is more useful to the doctor than any model
output (and Varsha's alerts, item #53, depend on this data being stored).

The photo's analysis record is written by on_image_uploaded, keyed by image_id
(e.g. CASE_001_DAY7_1723100000000). This merges the patient-reported fields into
that same record, so nothing is overwritten.

    POST /api/save_visit_meta
    { "image_id": "...", "patient_id": "...", "pain_level": 4,
      "symptoms": ["Fever","Discharge"], "notes": "sore today" }

App settings needed: FIREBASE_CREDENTIALS.
"""

import json
import os

import azure.functions as func
import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(os.environ["FIREBASE_CREDENTIALS"]))
    firebase_admin.initialize_app(cred)
db = firestore.client()


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON body", status_code=400)

    image_id = body.get("image_id")
    if not image_id:
        return func.HttpResponse("Missing image_id", status_code=400)

    fields = {
        "patient_id": body.get("patient_id"),
        "pain_level": body.get("pain_level"),
        "symptoms": body.get("symptoms", []),
        "notes": body.get("notes", ""),
        "patient_reported": True,
    }
    # Wound location is captured per-photo (general wound monitor); only store it
    # when the patient actually picked one, so we don't blank an earlier value.
    if body.get("wound_location"):
        fields["wound_location"] = body["wound_location"]

    db.collection("wound_photos").document(image_id).set(fields, merge=True)

    return func.HttpResponse(json.dumps({"status": "saved"}),
                             mimetype="application/json")
