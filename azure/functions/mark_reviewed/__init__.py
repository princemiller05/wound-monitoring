"""
Mark a patient as reviewed by a doctor.

Records, on the patient document, the latest-photo timestamp the doctor has seen.
The dashboard compares that against the patient's newest photo: if a newer photo
arrives later, the patient flips back to "needs review" so the doctor knows to
look again.

    POST /api/mark_reviewed
    { "patient_id": "<uid>", "doctor_email": "dr@x.com" }
    -> { "status": "reviewed", "reviewed_up_to_ms": 1723... }

App settings needed: FIREBASE_CREDENTIALS.
"""

import json
import logging
import os
import re

import azure.functions as func

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


def _email_key(email: str) -> str:
    """Firestore map keys can't contain '.' — make a safe key from the email."""
    return re.sub(r"[^a-z0-9]", "_", (email or "").strip().lower())


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        b = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON body", status_code=400)

    patient_id = b.get("patient_id")
    doctor_email = (b.get("doctor_email") or "").strip().lower()
    if not patient_id or not doctor_email:
        return func.HttpResponse("Missing patient_id or doctor_email",
                                 status_code=400)

    undo = bool(b.get("undo"))

    try:
        db = _get_db()

        if undo:
            # Undo: clear this doctor's review so the patient shows "needs review".
            reviewed_up_to = 0
        else:
            snap = db.collection("patients").document(patient_id).get()
            data = snap.to_dict() if snap.exists else {}
            pred = (data or {}).get("latest_prediction") or {}
            # Anchor the review to the patient's actual newest photo timestamp, so
            # a genuinely newer upload later flips the flag back. Prefer the
            # summary's value; if absent (older data), read from the photos.
            reviewed_up_to = pred.get("latest_photo_ms", 0) or 0
            if not reviewed_up_to:
                photos = (db.collection("wound_photos")
                            .where("patient_id", "==", patient_id).stream())
                reviewed_up_to = max((p.to_dict().get("captured_ms", 0) or 0
                                      for p in photos), default=0)

        db.collection("patients").document(patient_id).set(
            {"reviews": {_email_key(doctor_email): reviewed_up_to}},
            merge=True)

        return func.HttpResponse(
            json.dumps({"status": "reviewed",
                        "reviewed_up_to_ms": reviewed_up_to}),
            mimetype="application/json")
    except Exception:
        logging.exception("mark_reviewed failed")
        return func.HttpResponse(
            json.dumps({"status": "error"}),
            status_code=500, mimetype="application/json")
