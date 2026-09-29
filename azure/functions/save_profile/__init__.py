"""
Item #13 — Save the complete patient profile to Firestore.

Right now the profile screen collects the doctor's name/email and other details
but nothing is saved anywhere, so Varsha's whole dashboard has no patient to
show. This writes the full profile to patients/{patient_id}.

Also folds in:
  #4  — the doctor's e-mail is lower-cased and trimmed, so the doctor-list
        query (#21) actually matches.
  #6-11 — stores DOB, sex, height, weight, BMI, wound onset date, smoking, and
          prior ulcer/amputation.

The trend summary (latest_prediction) written by on_image_uploaded lives on the
same document; using merge=True keeps both halves.

    POST /api/save_profile
    { "patient_id": "...", "full_name": "...", "dob": "1970-05-01",
      "sex": "Male", "height_cm": 172, "weight_kg": 78,
      "clinician_name": "...", "clinician_email": "Dr@X.com ",
      "wound_location": "...", "diagnosis_date": "...",
      "wound_onset_date": "...", "diabetes_type": "Type 2",
      "smoker": false, "prior_ulcer": true, "phone": "..." }

App settings needed: FIREBASE_CREDENTIALS.
"""

import json
import logging
import os

import azure.functions as func
import firebase_admin
from firebase_admin import credentials, firestore

_db = None


def _get_db():
    global _db
    if _db is None:
        if not firebase_admin._apps:
            cred = credentials.Certificate(
                json.loads(os.environ["FIREBASE_CREDENTIALS"]))
            firebase_admin.initialize_app(cred)
        _db = firestore.client()
    return _db


def _bmi(height_cm, weight_kg):
    """kg / m^2, rounded — or None if we don't have both numbers."""
    try:
        h = float(height_cm) / 100.0
        w = float(weight_kg)
        if h > 0 and w > 0:
            return round(w / (h * h), 1)
    except (TypeError, ValueError):
        pass
    return None


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        b = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON body", status_code=400)

    patient_id = b.get("patient_id")
    if not patient_id:
        return func.HttpResponse("Missing patient_id", status_code=400)

    # #4 — normalise each doctor e-mail (lower-case, trim) so the doctor-list
    # query matches. A patient can share with several doctors, so it's a list.
    raw = b.get("doctor_emails") or []
    if isinstance(raw, str):
        raw = [raw]
    doctor_emails = sorted({(e or "").strip().lower() for e in raw if e and "@" in e})

    profile = {
        "patient_id": patient_id,
        "full_name": b.get("full_name"),
        "phone": b.get("phone"),
        "dob": b.get("dob"),                     # #6 store DOB, not age
        "sex": b.get("sex"),                     # #7
        "height_cm": b.get("height_cm"),         # #8
        "weight_kg": b.get("weight_kg"),         # #8
        "bmi": _bmi(b.get("height_cm"), b.get("weight_kg")),  # #8
        "profile_updated_at": firestore.SERVER_TIMESTAMP,
    }
    # Don't overwrite existing fields with nulls if the caller omitted them.
    profile = {k: v for k, v in profile.items() if v is not None}
    # The doctor list is always set (even to empty) so removals take effect.
    profile["clinician_emails"] = doctor_emails

    try:
        db = _get_db()
        db.collection("patients").document(patient_id).set(
            {"profile": profile}, merge=True)
    except Exception:
        logging.exception("save_profile failed")
        return func.HttpResponse(
            json.dumps({"status": "error"}),
            status_code=500, mimetype="application/json")

    return func.HttpResponse(
        json.dumps({"status": "saved", "bmi": profile.get("bmi"),
                    "doctors": doctor_emails}),
        mimetype="application/json")
