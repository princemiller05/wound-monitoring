"""
Delete one of a patient's wound photos and keep everything consistent:

  1. Delete the image blob from storage.
  2. Delete the photo's Firestore record.
  3. Recompute the patient's latest_prediction from the REMAINING analysed
     photos (so the trend, area series, tissue mix, healing and review flag all
     update). If no analysed photos remain, the summary is cleared.

    POST /api/delete_photo
    { "patient_id": "<uid>", "image_id": "<patient>_DAY7_<ts>" }
    -> { "status": "deleted", "visits": <n remaining> }

App settings needed:
  FIREBASE_CREDENTIALS
  AZURE_STORAGE_ACCOUNT_NAME
  AZURE_STORAGE_ACCOUNT_KEY
"""

import json
import logging
import os

import azure.functions as func

CONTAINER = "wound-photos"
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


def _delete_blob(blob_path: str) -> None:
    from azure.storage.blob import BlobServiceClient
    account = os.environ["AZURE_STORAGE_ACCOUNT_NAME"]
    key = os.environ["AZURE_STORAGE_ACCOUNT_KEY"]
    svc = BlobServiceClient(
        account_url=f"https://{account}.blob.core.windows.net",
        credential=key)
    try:
        svc.get_blob_client(CONTAINER, blob_path).delete_blob()
    except Exception:
        logging.warning("blob %s already gone or undeletable", blob_path)


def _trend(area_series):
    if len(area_series) < 2:
        return "stable"
    change = (area_series[-1] - area_series[0]) / max(area_series[0], 1)
    if change <= -0.05:
        return "improving"
    if change >= 0.05:
        return "worsening"
    return "stable"


def _recompute(db, patient_id):
    """Rebuild latest_prediction from the patient's remaining analysed photos."""
    from firebase_admin import firestore
    docs = (db.collection("wound_photos")
              .where("patient_id", "==", patient_id)
              .where("analyzed", "==", True).stream())
    rows_all = [d.to_dict() for d in docs]

    if not rows_all:
        # Nothing analysed left — clear the summary.
        db.collection("patients").document(patient_id).set(
            {"latest_prediction": firestore.DELETE_FIELD}, merge=True)
        return 0

    # One point per day (latest photo that day), same rule as on_image_uploaded.
    by_day = {}
    for r in rows_all:
        d = r.get("day_number", 0)
        if d not in by_day or r.get("captured_ms", 0) >= by_day[d].get("captured_ms", 0):
            by_day[d] = r
    rows = sorted(by_day.values(), key=lambda x: x["day_number"])

    area_series = [r["area_px"] for r in rows]
    n_visits = len(rows)
    enough = n_visits >= 2
    latest = rows[-1]
    latest_photo_ms = max((r.get("captured_ms", 0) for r in rows_all), default=0)

    summary = {
        "visits": n_visits,
        "enough_visits": enough,
        "latest_photo_ms": latest_photo_ms,
        "healing_probability": latest["healing_probability"] if enough else None,
        "predicted_label": latest["predicted_label"] if enough else "pending",
        "trend": _trend(area_series) if enough else "pending",
        "day_series": [r["day_number"] for r in rows],
        "area_series": area_series,
        "area_mm2_series": [r.get("area_mm2") for r in rows],
        "healing_series": [r.get("healing_probability") for r in rows],
        "tissue_series": {
            "granulation": [r["granulation_pct"] for r in rows],
            "slough": [r["slough_pct"] for r in rows],
            "necrosis": [r["necrosis_pct"] for r in rows],
        },
        "last_detection_failed": latest.get("detection_failed", False),
        "last_classifier_warning": latest.get("classifier_warning", ""),
        "updated_at": firestore.SERVER_TIMESTAMP,
    }
    db.collection("patients").document(patient_id).set(
        {"latest_prediction": summary}, merge=True)
    return n_visits


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        b = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON body", status_code=400)

    patient_id = b.get("patient_id")
    image_id = b.get("image_id")
    if not patient_id or not image_id:
        return func.HttpResponse("Missing patient_id or image_id",
                                 status_code=400)

    try:
        db = _get_db()
        ref = db.collection("wound_photos").document(image_id)
        snap = ref.get()
        data = snap.to_dict() if snap.exists else None

        # Only let a patient delete their own photo.
        if data and data.get("patient_id") not in (None, patient_id):
            return func.HttpResponse("Not your photo", status_code=403)

        if data and data.get("blob_path"):
            _delete_blob(data["blob_path"])

        ref.delete()
        remaining = _recompute(db, patient_id)

        return func.HttpResponse(
            json.dumps({"status": "deleted", "visits": remaining}),
            mimetype="application/json")
    except Exception:
        logging.exception("delete_photo failed")
        return func.HttpResponse(
            json.dumps({"status": "error"}),
            status_code=500, mimetype="application/json")
