"""
List a patient's analysed wound photos, newest first, each with a short-lived
read-only image URL so the doctor dashboard can show the actual pictures.

    GET /api/get_patient_photos?patient_id=<uid>
    -> { "photos": [ {image_id, day_number, captured_ms, download_url,
                      area_px, area_mm2, healing_probability, predicted_label,
                      granulation_pct, slough_pct, necrosis_pct,
                      wound_location, pain_level, symptoms, notes,
                      detection_failed}, ... ] }

Each download_url is a blob SAS valid a few hours; the storage key is never
exposed. Combining the photo metadata + URL in one call keeps the dashboard to a
single request per patient instead of one per image.

App settings needed:
  FIREBASE_CREDENTIALS
  AZURE_STORAGE_ACCOUNT_NAME
  AZURE_STORAGE_ACCOUNT_KEY
"""

import datetime
import json
import logging
import os

import azure.functions as func
from azure.storage.blob import generate_blob_sas, BlobSasPermissions

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


def _sas_url(blob_path: str) -> str:
    account = os.environ["AZURE_STORAGE_ACCOUNT_NAME"]
    key = os.environ["AZURE_STORAGE_ACCOUNT_KEY"]
    sas = generate_blob_sas(
        account_name=account,
        container_name=CONTAINER,
        blob_name=blob_path,
        account_key=key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.datetime.utcnow() + datetime.timedelta(hours=6),
    )
    return f"https://{account}.blob.core.windows.net/{CONTAINER}/{blob_path}?{sas}"


def main(req: func.HttpRequest) -> func.HttpResponse:
    patient_id = req.params.get("patient_id")
    if not patient_id:
        return func.HttpResponse("Missing patient_id", status_code=400)

    try:
        db = _get_db()
        docs = (db.collection("wound_photos")
                  .where("patient_id", "==", patient_id).stream())

        photos = []
        for d in docs:
            r = d.to_dict()
            blob_path = r.get("blob_path")
            if not blob_path:
                continue
            try:
                url = _sas_url(blob_path)
            except Exception:
                logging.exception("SAS generation failed for %s", blob_path)
                url = None
            photos.append({
                "image_id": d.id,
                "day_number": r.get("day_number", 0),
                "captured_ms": r.get("captured_ms", 0),
                "download_url": url,
                "area_px": r.get("area_px"),
                "area_mm2": r.get("area_mm2"),
                "healing_probability": r.get("healing_probability"),
                "predicted_label": r.get("predicted_label"),
                "granulation_pct": r.get("granulation_pct"),
                "slough_pct": r.get("slough_pct"),
                "necrosis_pct": r.get("necrosis_pct"),
                "wound_location": r.get("wound_location"),
                "pain_level": r.get("pain_level"),
                "symptoms": r.get("symptoms", []),
                "notes": r.get("notes", ""),
                "detection_failed": r.get("detection_failed", False),
                "analyzed": r.get("analyzed", False),
            })

        # Newest first (by capture time, then day).
        photos.sort(key=lambda p: (p["captured_ms"], p["day_number"]),
                    reverse=True)

        return func.HttpResponse(
            json.dumps({"photos": photos}, default=str),
            mimetype="application/json")
    except Exception:
        logging.exception("get_patient_photos failed")
        return func.HttpResponse(
            json.dumps({"status": "error"}),
            status_code=500, mimetype="application/json")
