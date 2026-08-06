"""
Job 4 — History API.

A simple HTTP endpoint the app (and Varsha's doctor dashboard) call to read a
patient's latest_prediction — the longitudinal summary that on_image_uploaded
keeps up to date.

    GET  /api/get_patient_history?patient_id=CASE_001

Returns the stored latest_prediction JSON, or {"status": "no_data"} if the
patient hasn't had a photo analysed yet.

App settings needed: FIREBASE_CREDENTIALS (same service-account JSON string).
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
    patient_id = req.params.get("patient_id")
    if not patient_id:
        return func.HttpResponse("Missing patient_id", status_code=400)

    doc = db.collection("patients").document(patient_id).get()
    data = doc.to_dict() if doc.exists else None

    if not data or "latest_prediction" not in data:
        return func.HttpResponse(
            json.dumps({"status": "no_data"}),
            mimetype="application/json",
        )

    # default=str so the Firestore server timestamp serialises cleanly.
    return func.HttpResponse(
        json.dumps(data["latest_prediction"], default=str),
        mimetype="application/json",
    )
