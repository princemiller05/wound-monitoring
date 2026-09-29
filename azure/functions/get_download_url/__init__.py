"""
Item #22 — Give a short-lived, read-only URL to fetch one stored photo back.

Why this exists: the app currently shows only the local image file, so a
reinstall wipes the patient's whole visible history even though every photo is
safe in Blob Storage. Both the app (item #14) and Varsha's dashboard (item #44)
need to pull photos back down. This returns a read SAS URL for a given blob.

    GET /api/get_download_url?blob_path=CASE_001/CASE_001_DAY7_1723100000000.jpg
    -> { "download_url": "https://...blob...?<sas>" }

The link is valid for a few hours, then expires — the raw storage key is never
exposed to the client.

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
    blob_path = req.params.get("blob_path")
    if not blob_path:
        return func.HttpResponse("Missing blob_path", status_code=400)

    sas = generate_blob_sas(
        account_name=ACCOUNT,
        container_name=CONTAINER,
        blob_name=blob_path,
        account_key=KEY,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.datetime.utcnow() + datetime.timedelta(hours=6),
    )
    url = (
        f"https://{ACCOUNT}.blob.core.windows.net/{CONTAINER}/{blob_path}?{sas}"
    )

    return func.HttpResponse(
        json.dumps({"download_url": url}),
        mimetype="application/json",
    )
