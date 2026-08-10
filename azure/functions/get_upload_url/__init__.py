"""
Give the app a short-lived, write-only URL to upload one photo to Blob Storage.

Why this exists: the app must NEVER hold the storage account key (anyone could
extract it from the APK). Instead the app asks this function for a SAS
(Shared Access Signature) URL that lets it upload exactly one blob for one hour,
and nothing else.

    GET /api/get_upload_url?patient_id=CASE_001&filename=CASE_001_DAY7.jpg
    -> { "upload_url": "https://...blob...?<sas>", "blob_path": "CASE_001/CASE_001_DAY7.jpg" }

The blob lands at wound-photos/{patient_id}/{filename}, which is what the
on_image_uploaded trigger watches.

App settings needed:
  AZURE_STORAGE_ACCOUNT_NAME
  AZURE_STORAGE_ACCOUNT_KEY
"""

import json
import os
import datetime

import azure.functions as func
from azure.storage.blob import generate_blob_sas, BlobSasPermissions

ACCOUNT = os.environ["AZURE_STORAGE_ACCOUNT_NAME"]
KEY = os.environ["AZURE_STORAGE_ACCOUNT_KEY"]
CONTAINER = "wound-photos"


def main(req: func.HttpRequest) -> func.HttpResponse:
    patient_id = req.params.get("patient_id")
    filename = req.params.get("filename")
    if not patient_id or not filename:
        return func.HttpResponse("Missing patient_id or filename",
                                 status_code=400)

    blob_path = f"{patient_id}/{filename}"

    sas = generate_blob_sas(
        account_name=ACCOUNT,
        container_name=CONTAINER,
        blob_name=blob_path,
        account_key=KEY,
        permission=BlobSasPermissions(write=True, create=True),
        expiry=datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    )
    upload_url = (
        f"https://{ACCOUNT}.blob.core.windows.net/{CONTAINER}/{blob_path}?{sas}"
    )

    return func.HttpResponse(
        json.dumps({"upload_url": upload_url, "blob_path": blob_path}),
        mimetype="application/json",
    )
