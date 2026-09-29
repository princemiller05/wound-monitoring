"""
History API — the app and Varsha's dashboard call this to read a patient's
longitudinal summary plus their profile.

    GET  /api/get_patient_history?patient_id=CASE_001

Returns:
    {
      "status": "ok",
      "prediction": { ...latest_prediction... },   # None if no photo analysed
      "patient": {  # #23 — details the dashboard displays
        "full_name", "age", "sex", "bmi", "diabetes_type",
        "wound_duration_days", "clinician_name", "clinician_email",
        "smoker", "prior_ulcer", ...
      }
    }

App settings needed: FIREBASE_CREDENTIALS.
"""

import datetime
import json
import logging
import os

import azure.functions as func

# Lazy, error-surfacing Firestore init. The firebase import itself is done here
# (not at module load) so an import failure surfaces as a readable message
# instead of a blank host 500.
_db = None


def _get_db():
    global _db
    if _db is None:
        import firebase_admin
        from firebase_admin import credentials, firestore
        if not firebase_admin._apps:
            cred = credentials.Certificate(
                json.loads(os.environ["FIREBASE_CREDENTIALS"]))
            firebase_admin.initialize_app(cred)
        _db = firestore.client()
    return _db


def _parse_date(s):
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d %b %Y"):
        try:
            return datetime.datetime.strptime(s[:19], fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _age(dob):
    d = _parse_date(dob)
    if not d:
        return None
    today = datetime.date.today()
    # #6 — age computed from DOB, so it never goes stale.
    return today.year - d.year - ((today.month, today.day) < (d.month, d.day))


def _duration_days(onset):
    d = _parse_date(onset)
    if not d:
        return None
    return (datetime.date.today() - d).days


def _patient_view(profile):
    """Shape the stored profile into what the dashboard shows (#23)."""
    if not profile:
        return None
    return {
        "full_name": profile.get("full_name"),
        "phone": profile.get("phone"),
        "age": _age(profile.get("dob")),                  # #6
        "sex": profile.get("sex"),                        # #7
        "bmi": profile.get("bmi"),                        # #8
        "height_cm": profile.get("height_cm"),
        "weight_kg": profile.get("weight_kg"),
        # General wound monitor: a patient may share with several doctors.
        "doctor_emails": profile.get("clinician_emails", []),
        "profile_updated_at": profile.get("profile_updated_at"),
    }


def main(req: func.HttpRequest) -> func.HttpResponse:
    patient_id = req.params.get("patient_id")
    if not patient_id:
        return func.HttpResponse("Missing patient_id", status_code=400)

    try:
        db = _get_db()
        doc = db.collection("patients").document(patient_id).get()
        data = doc.to_dict() if doc.exists else None

        if not data:
            return func.HttpResponse(
                json.dumps({"status": "no_data"}), mimetype="application/json")

        payload = {
            "status": "ok",
            "prediction": data.get("latest_prediction"),
            "patient": _patient_view(data.get("profile")),
        }
        return func.HttpResponse(json.dumps(payload, default=str),
                                 mimetype="application/json")
    except Exception:
        logging.exception("get_patient_history failed")
        return func.HttpResponse(
            json.dumps({"status": "error"}),
            status_code=500, mimetype="application/json")
