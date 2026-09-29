"""
Item #21 — List the patients who belong to a given doctor.

The dashboard currently invents 48 fake patients. This returns only the patients
who typed THIS doctor's e-mail into their app profile (item #13/#4 stored it,
lower-cased). Each row carries enough for the worklist (#47): name, age, and a
simple risk level so the list can be sorted worst-first.

    GET /api/get_doctor_patients?doctor_email=dr@x.com
    -> { "patients": [ {patient_id, name, age, sex, risk, trend, ...}, ... ] }

App settings needed: FIREBASE_CREDENTIALS.
"""

import datetime
import json
import os
import re

import azure.functions as func
import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(os.environ["FIREBASE_CREDENTIALS"]))
    firebase_admin.initialize_app(cred)
db = firestore.client()


def _age(dob):
    try:
        d = datetime.datetime.strptime((dob or "")[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None
    t = datetime.date.today()
    return t.year - d.year - ((t.month, t.day) < (d.month, d.day))


def _risk(pred):
    """Rough triage so the worklist can sort worst-first (#47)."""
    if not pred or not pred.get("enough_visits"):
        return 1, "New / few visits"
    trend = pred.get("trend")
    necrosis = (pred.get("tissue_series", {}).get("necrosis") or [0])[-1]
    if trend == "worsening" or necrosis >= 20:
        return 3, "High"
    if trend == "stable":
        return 2, "Medium"
    return 1, "Low"


def main(req: func.HttpRequest) -> func.HttpResponse:
    doctor_email = (req.params.get("doctor_email") or "").strip().lower()
    if not doctor_email:
        return func.HttpResponse("Missing doctor_email", status_code=400)

    # A patient can list several doctors, so match against the array (#4 keeps
    # every entry lower-cased/trimmed, so equality inside array_contains works).
    q = (db.collection("patients")
           .where("profile.clinician_emails", "array_contains", doctor_email)
           .stream())

    email_key = re.sub(r"[^a-z0-9]", "_", doctor_email)

    patients = []
    for doc in q:
        d = doc.to_dict()
        profile = d.get("profile", {})
        pred = d.get("latest_prediction")
        rank, risk_label = _risk(pred)

        # Needs review = the patient has a photo newer than this doctor's last
        # review. A brand-new patient with photos is "needs review" too.
        latest_photo_ms = (pred or {}).get("latest_photo_ms", 0) or 0
        reviewed_ms = (d.get("reviews") or {}).get(email_key, 0) or 0
        visits = pred.get("visits", 0) if pred else 0
        # Never reviewed but has data -> needs review. Otherwise, a photo newer
        # than the last review -> needs review again.
        never_reviewed = reviewed_ms == 0 and visits > 0
        needs_review = never_reviewed or (latest_photo_ms > reviewed_ms)

        patients.append({
            "patient_id": doc.id,
            "name": profile.get("full_name"),
            "age": _age(profile.get("dob")),
            "sex": profile.get("sex"),
            "risk": risk_label,
            "risk_rank": rank,
            "trend": pred.get("trend") if pred else None,
            "visits": pred.get("visits", 0) if pred else 0,
            "updated_at": pred.get("updated_at") if pred else None,
            "latest_photo_ms": latest_photo_ms,
            "reviewed_ms": reviewed_ms,
            "needs_review": needs_review,
        })

    # Needs-review first, then worst risk.
    patients.sort(key=lambda p: (p["needs_review"], p["risk_rank"]),
                  reverse=True)

    return func.HttpResponse(
        json.dumps({"patients": patients}, default=str),
        mimetype="application/json")
